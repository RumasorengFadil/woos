"""Tahap 8 — Publish hasil model ke PostgreSQL (PRD §42–§45, §65, §73–§74).

Model result menjadi single source of truth (PRD §95). Dashboard hanya membaca tabel/view.

Aturan (D-031):
    - Model tervalidasi WAJIB validation_status = APPROVED (approval.json dari s07b); bila tidak, publish ditolak.
    - Model terbaik algoritma lain dipublish sebagai EXPERIMENT (pembanding), label cluster generik.
    - Publish idempotent: data untuk dataset_version yang sama dihapus lalu ditulis ulang dalam SATU transaksi.

Jalankan:  ml/.venv/bin/python ml/pipeline/s08_publish.py [--dataset=v2] [--database=woos_test]
"""
import hashlib
import json
import shutil
import sys

import numpy as np
import pandas as pd
from psycopg2.extras import Json, execute_values

from sklearn.decomposition import PCA
from sklearn.preprocessing import RobustScaler, StandardScaler

from config import GRADE_GROUPS, OUTPUTS, RANDOM_SEED, ROOT, dataset
from db import connect
from s06_evaluation import eligible as eligibility
from s07_interpretation import profile_stats

VALIDATED_EXPERIMENT = "EXP-KM-067"
COMPARISON_EXPERIMENTS = ["EXP-HC-044", "EXP-DB-067"]     # terbaik per algoritma (S06, D-028)
PERIOD = "2026-09-25"
SCALERS = {"standard": StandardScaler, "robust": RobustScaler}
# Figure riset yang tidak dapat direkonstruksi dari tabel -> disalin untuk dashboard (D-033)
DASHBOARD_FIGURES = {"05_experiments": ["E01_kmeans_elbow.png", "E04_dendrograms.png", "E06_dbscan_noise_vs_clusters.png"],
                     "06_evaluation": ["V01_eligibility_funnel.png", "V02_silhouette_vs_stability.png"],
                     "07_interpretation": ["P01_cluster_profile_heatmap.png"]}
FEATURE_COLS = ["ftk", "realization", "gap", "fulfillment_ratio", "staffing_ratio", "balance_index", "position_rows",
                "position_count", "dormant_position_count", "vacant_position_count", "vacant_share",
                "avg_realization_per_position", "unbudgeted_filled_count", "marked_position_count",
                "extreme_position_count"]


# ---------------------------------------------------------------- fungsi murni (diuji)

class PublishRefused(Exception):
    pass


def assert_publishable(metrics, approval):
    """Gerbang PRD §45: hanya model APPROVED dengan catatan approval yang cocok."""
    if metrics.get("validation_status") != "APPROVED":
        raise PublishRefused(f"validation_status = {metrics.get('validation_status')} (harus APPROVED)")
    if not approval or approval.get("experiment_id") != metrics.get("experiment_id"):
        raise PublishRefused("approval.json tidak ada atau tidak cocok dengan model")
    return True


def clean(v):
    """Nilai pandas/numpy -> tipe Python yang aman untuk psycopg2 (NaN -> NULL)."""
    if v is None:
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        return None if not np.isfinite(v) else float(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    return v


def grade_distribution(row):
    return {"pct": {g: round(float(row[f"pct_{g}"]), 4) for g in GRADE_GROUPS},
            "ftk": {g: int(row[f"ftk_{g}"]) for g in GRADE_GROUPS},
            "realization": {g: int(row[f"real_{g}"]) for g in GRADE_GROUPS}}


def viz_coordinates(frame, features, scaler):
    """PCA 2D (visual saja, PRD §52) pada feature ter-skala model yang sama."""
    X = SCALERS[scaler]().fit_transform(frame[features].to_numpy(float))
    pca = PCA(n_components=2, random_state=RANDOM_SEED).fit(X)
    xy = pca.transform(X)
    return pd.DataFrame(xy, index=frame.index, columns=["x", "y"]).round(4), [round(float(v), 4) for v in pca.explained_variance_ratio_]


def generic_label(cluster_id):
    return ("NOISE", "Noise") if cluster_id == -1 else (f"C{cluster_id}", f"Cluster {cluster_id}")


# ---------------------------------------------------------------- pipeline

def main():
    ds = dataset()
    ver = ds["version"]
    target_db = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--database=")), None)
    out = {k: OUTPUTS / k / ver for k in ["02_preprocessing", "03_feature_engineering", "05_experiments",
                                          "06_evaluation", "07_interpretation"]}
    art = out["07_interpretation"] / "model_artifacts"
    metrics = json.loads((art / "metrics.json").read_text())
    approval_path = art / "approval.json"
    approval = json.loads(approval_path.read_text()) if approval_path.exists() else None
    assert_publishable(metrics, approval)

    orgs = pd.read_csv(out["02_preprocessing"] / "organizations_clean.csv")
    feats = pd.read_csv(out["03_feature_engineering"] / "features_direct.csv", index_col=0)
    reg = pd.read_json(out["05_experiments"] / "experiments.json")
    labels = pd.read_csv(out["05_experiments"] / "labels.csv.gz", index_col=0)
    elig = pd.read_csv(out["06_evaluation"] / "eligible_runs.csv").set_index("experiment_id")
    posthoc = pd.read_csv(out["06_evaluation"] / "eligible_runs_nontrivial_posthoc.csv").set_index("experiment_id")
    results = pd.read_csv(out["07_interpretation"] / "organization_results.csv", index_col=0)
    profile = json.loads((art / "cluster_profile.json").read_text())
    pos_rows = int(pd.read_csv(out["02_preprocessing"] / "positions_clean.csv").shape[0])

    ok_mask, reasons = eligibility(reg)
    reg_idx = reg.set_index("experiment_id")
    pop_all = feats[feats.in_model_population == 1]
    viz = {e: viz_coordinates(pop_all, reg_idx.loc[e, "features_used"], reg_idx.loc[e, "scaler"])
           for e in [VALIDATED_EXPERIMENT] + COMPARISON_EXPERIMENTS}

    conn = connect(target_db)
    with conn, conn.cursor() as cur:
        # --- bersihkan publikasi sebelumnya untuk dataset ini (idempotent) ---
        cur.execute("DELETE FROM woos.cluster_result WHERE dataset_version = %s", (ver,))
        cur.execute("DELETE FROM woos.cluster_profile WHERE model_id IN (SELECT model_id FROM woos.model WHERE dataset_version = %s)", (ver,))
        cur.execute("DELETE FROM woos.model WHERE dataset_version = %s", (ver,))
        cur.execute("DELETE FROM woos.experiment WHERE dataset_version = %s", (ver,))
        cur.execute("DELETE FROM woos.organization_feature WHERE dataset_version = %s", (ver,))
        cur.execute("DELETE FROM woos.organization WHERE dataset_version = %s", (ver,))
        cur.execute("DELETE FROM woos.dataset_version WHERE dataset_version = %s", (ver,))

        # --- dataset_version ---
        cur.execute("""INSERT INTO woos.dataset_version (dataset_version, source_file, source_sha256, scope, period, status,
                       position_rows, organization_rows) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (ver, ds["file"].name, hashlib.sha256(ds["file"].read_bytes()).hexdigest(), ds["scope"], PERIOD,
                     ds["status"], pos_rows, int(orgs.has_positions.sum())))

        # --- organization ---
        execute_values(cur, """INSERT INTO woos.organization (dataset_version, organization_id, organization_name,
            parent_organization_id, parent_status, organization_level, directorate_id, directorate_name, directorate_source,
            is_virtual_container, is_leaf, n_children) VALUES %s""",
                       [(ver, r.organization_id, r.organization_name, clean(r.parent_organization_id) if pd.notna(r.parent_organization_id) else None,
                         r.parent_status, int(r.organization_level), r.directorate_id, r.directorate_name,
                         r.directorate_source, bool(r.is_virtual_container), bool(r.is_leaf), int(r.n_children))
                        for r in orgs.itertuples()])

        # --- organization_feature (direct) ---
        rows = []
        for oid, r in feats.iterrows():
            rows.append((ver, r.feature_version, oid, "direct", *[clean(r[c]) for c in FEATURE_COLS],
                         Json(grade_distribution(r)), bool(r.in_model_population)))
        execute_values(cur, f"""INSERT INTO woos.organization_feature (dataset_version, feature_version, organization_id,
            unit_definition, {", ".join(FEATURE_COLS)}, grade_distribution, in_model_population) VALUES %s""", rows)

        # --- experiment registry (619 run) ---
        rows = []
        for i, r in reg.iterrows():
            e = elig.loc[r.experiment_id] if r.experiment_id in elig.index else None
            rows.append((r.experiment_id, r.model_name, r.model_version, ver, r.feature_version, r.unit, r.feature_set,
                         Json(r.features_used), r.scaler, r.variant, Json(r.hyperparameters), int(r.random_seed),
                         r.code_version, r.training_timestamp, int(r.n_samples), int(r.n_clusters), int(r.noise_count),
                         clean(r.noise_share), clean(r.silhouette), clean(r.davies_bouldin), clean(r.calinski_harabasz),
                         clean(r.min_cluster_share), clean(r.max_cluster_share), clean(r.size_entropy_norm),
                         Json(r.cluster_sizes), clean(r.get("inertia")), bool(ok_mask[i]), reasons[i] or None,
                         *[clean(e[c]) if e is not None else None for c in
                           ["stability_ari", "workforce_eta2", "cramers_v_level", "cramers_v_directorate",
                            "ari_vs_gap_sign", "ari_vs_balance_poles", "rank_score"]],
                         clean(posthoc.loc[r.experiment_id, "rank_score_posthoc"]) if r.experiment_id in posthoc.index else None,
                         "APPROVED" if r.experiment_id == VALIDATED_EXPERIMENT else "EXPERIMENT"))
        execute_values(cur, """INSERT INTO woos.experiment (experiment_id, model_name, model_version, dataset_version,
            feature_version, unit_definition, feature_set, features_used, scaler, variant, hyperparameters, random_seed,
            code_version, training_timestamp, n_samples, n_clusters, noise_count, noise_share, silhouette, davies_bouldin,
            calinski_harabasz, min_cluster_share, max_cluster_share, size_entropy_norm, cluster_sizes, inertia, eligible,
            rejection_reason, stability_ari, workforce_eta2, cramers_v_level, cramers_v_directorate, ari_vs_gap_sign,
            ari_vs_balance_poles, rank_score, rank_score_posthoc, validation_status) VALUES %s""", rows)

        # --- models ---
        model_ids = {}
        for exp_id in [VALIDATED_EXPERIMENT] + COMPARISON_EXPERIMENTS:
            r = reg.set_index("experiment_id").loc[exp_id]
            validated = exp_id == VALIDATED_EXPERIMENT
            m = metrics if validated else {k: clean(elig.loc[exp_id][k]) for k in
                                           ["silhouette", "davies_bouldin", "stability_ari", "size_entropy_norm",
                                            "workforce_eta2", "cramers_v_level", "cramers_v_directorate", "n_clusters",
                                            "noise_share"]}
            cur.execute("""INSERT INTO woos.model (experiment_id, model_name, model_version, dataset_version, feature_version,
                features_used, scaler, hyperparameters, metrics, validation_status, is_validated_model, selection_decisions,
                approved_by, approved_on, trained_at, viz_explained_variance)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING model_id""",
                        (exp_id, r.model_name, r.model_version, ver, r.feature_version, Json(r.features_used), r.scaler,
                         Json(r.hyperparameters), Json(m), "APPROVED" if validated else "EXPERIMENT", validated,
                         Json(metrics["selection_decisions"] if validated else ["D-028"]),
                         approval["approved_by"] if validated else None, approval["approved_on"] if validated else None,
                         r.training_timestamp, Json(viz[exp_id][1])))
            model_ids[exp_id] = cur.fetchone()[0]

        # --- cluster_profile: model tervalidasi (label bisnis) ---
        vid = model_ids[VALIDATED_EXPERIMENT]
        execute_values(cur, """INSERT INTO woos.cluster_profile (model_id, cluster_id, cluster_code, cluster_label,
            prd_archetype, is_business_label, organization_count, organization_share, mean_ftk, mean_realization, mean_gap,
            mean_fulfillment, median_fulfillment, mean_staffing_ratio, mean_position_count, mean_vacant_position,
            mean_vacant_share, mean_avg_realization_per_position, sum_ftk, sum_realization, sum_gap, characteristics,
            interpretation, centroid) VALUES %s""",
                       [(vid, p["cluster_id"], p["cluster_code"], p["cluster_label"], p["prd_archetype"], True,
                         p["organization_count"], p["organization_share"], *[clean(p[k]) for k in
                          ["mean_ftk", "mean_realization", "mean_gap", "mean_fulfillment", "median_fulfillment",
                           "mean_staffing_ratio", "mean_position_count", "mean_vacant_position", "mean_vacant_share",
                           "mean_avg_realization_per_position"]],
                         p["sum_ftk"], p["sum_realization"], p["sum_gap"], Json(p["characteristics"]), p["interpretation"],
                         Json({"scaled": p["centroid_scaled"], "original": p["centroid_original"]})) for p in profile])

        # --- cluster_profile: model pembanding (label generik) ---
        pop = feats[feats.in_model_population == 1]
        for exp_id in COMPARISON_EXPERIMENTS:
            g = pop.assign(cluster=labels.loc[pop.index, exp_id])
            st = profile_stats(g, "cluster", ["ftk", "realization", "gap", "fulfillment_ratio", "staffing_ratio",
                                              "position_count", "vacant_position_count", "vacant_share",
                                              "avg_realization_per_position"])
            sums = g.groupby("cluster")[["ftk", "realization", "gap"]].sum()
            rows = []
            for cid, s in st.iterrows():
                code, lab = generic_label(int(cid))
                rows.append((model_ids[exp_id], int(cid), code, lab, None, False, int(s.organization_count),
                             round(s.organization_count / len(pop), 4), clean(s.ftk_mean), clean(s.realization_mean),
                             clean(s.gap_mean), clean(s.fulfillment_ratio_mean), clean(s.fulfillment_ratio_median),
                             clean(s.staffing_ratio_mean), clean(s.position_count_mean),
                             clean(s.vacant_position_count_mean), clean(s.vacant_share_mean),
                             clean(s.avg_realization_per_position_mean), int(sums.loc[cid, "ftk"]),
                             int(sums.loc[cid, "realization"]), int(sums.loc[cid, "gap"]), Json([]),
                             "Model pembanding (EXPERIMENT) — tidak diberi label bisnis (D-031).", None))
            execute_values(cur, """INSERT INTO woos.cluster_profile (model_id, cluster_id, cluster_code, cluster_label,
                prd_archetype, is_business_label, organization_count, organization_share, mean_ftk, mean_realization,
                mean_gap, mean_fulfillment, median_fulfillment, mean_staffing_ratio, mean_position_count,
                mean_vacant_position, mean_vacant_share, mean_avg_realization_per_position, sum_ftk, sum_realization,
                sum_gap, characteristics, interpretation, centroid) VALUES %s""", rows)

        # --- cluster_result: model tervalidasi ---
        rows = []
        for oid, r in results.iterrows():
            seg = r.cluster_code != "NOT_SEGMENTED"
            xy = viz[VALIDATED_EXPERIMENT][0]
            rows.append((vid, VALIDATED_EXPERIMENT, ver, PERIOD, oid, "SEGMENTED" if seg else "NOT_SEGMENTED",
                         int(r.cluster_id) if seg else None, r.cluster_code, r.cluster_label,
                         clean(r.cluster_distance) if seg else None, bool(r.is_atypical_member) if seg else False,
                         r.created_at, clean(xy.x.get(oid)) if seg else None, clean(xy.y.get(oid)) if seg else None))
        # --- cluster_result: model pembanding ---
        created = results.created_at.iloc[0]
        not_seg = feats.index[feats.in_model_population == 0]
        for exp_id in COMPARISON_EXPERIMENTS:
            for oid, c in labels[exp_id].items():
                code, lab = generic_label(int(c))
                xy = viz[exp_id][0]
                rows.append((model_ids[exp_id], exp_id, ver, PERIOD, oid, "SEGMENTED", int(c), code, lab, None, False,
                             created, clean(xy.x[oid]), clean(xy.y[oid])))
            rows += [(model_ids[exp_id], exp_id, ver, PERIOD, oid, "NOT_SEGMENTED", None, "NOT_SEGMENTED",
                      "Tidak Tersegmentasi", None, False, created, None, None) for oid in not_seg]
        execute_values(cur, """INSERT INTO woos.cluster_result (model_id, experiment_id, dataset_version, period,
            organization_id, segmentation_status, cluster_id, cluster_code, cluster_label, cluster_distance,
            is_atypical_member, created_at, viz_x, viz_y) VALUES %s""", rows)

        # --- validasi pasca-publish (dalam transaksi yang sama; gagal -> rollback) ---
        checks = {}
        q = lambda sql, *a: (cur.execute(sql, a), cur.fetchone()[0])[1]  # noqa: E731
        checks["organizations"] = q("SELECT count(*) FROM woos.organization WHERE dataset_version=%s", ver) == len(orgs)
        checks["features"] = q("SELECT count(*) FROM woos.organization_feature WHERE dataset_version=%s", ver) == len(feats)
        checks["experiments"] = q("SELECT count(*) FROM woos.experiment WHERE dataset_version=%s", ver) == len(reg)
        checks["one_validated_model"] = q("SELECT count(*) FROM woos.v_validated_model WHERE dataset_version=%s", ver) == 1
        checks["validated_results_1301"] = q("SELECT count(*) FROM woos.v_validated_organization WHERE dataset_version=%s", ver) == len(feats)
        checks["segmented_1280"] = q("SELECT count(*) FROM woos.v_validated_organization WHERE dataset_version=%s AND segmentation_status='SEGMENTED'", ver) == int(feats.in_model_population.sum())
        checks["profile_counts_match"] = q("""SELECT count(*) FROM woos.cluster_profile p JOIN (
            SELECT model_id, cluster_id, count(*) n FROM woos.cluster_result WHERE cluster_id IS NOT NULL GROUP BY 1,2) r
            USING (model_id, cluster_id) WHERE p.organization_count <> r.n""") == 0
        checks["totals_ftk_match"] = q("SELECT sum(ftk) FROM woos.v_validated_organization WHERE dataset_version=%s", ver) == int(feats.ftk.sum())
        checks["viz_coordinates_complete"] = q("SELECT count(*) FROM woos.cluster_result WHERE dataset_version=%s AND segmentation_status='SEGMENTED' AND viz_x IS NULL", ver) == 0
        checks["comparison_models"] = q("SELECT count(*) FROM woos.v_model_comparison WHERE dataset_version=%s", ver) == 3
        if not all(checks.values()):
            raise SystemExit(f"VALIDASI PUBLISH GAGAL (rollback): {checks}")

    conn.close()
    fig_dir = ROOT / "assets" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for stage, names in DASHBOARD_FIGURES.items():
        for name in names:
            shutil.copy2(OUTPUTS / stage / ver / "figures" / name, fig_dir / name)
            copied.append(name)
    summary = {"dataset_version": ver, "database": target_db or "woos (dari .env)", "validated_model": VALIDATED_EXPERIMENT,
               "model_ids": model_ids, "checks": checks,
               "figures_copied": copied}
    (OUTPUTS / "08_publish").mkdir(exist_ok=True)
    (OUTPUTS / "08_publish" / f"publish_log_{ver}_{target_db or 'woos'}.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
