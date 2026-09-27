"""Tahap 7 — Interpretasi Cluster, Profiling & Validasi (PRD §39–§45, §73, §85).

Model kandidat (D-029): EXP-KM-067 = K-Means, feature set R, StandardScaler, K = 5.

Langkah:
    1. Refit model final (seed tetap) dan verifikasi identik dengan registri Tahap 5
    2. Profil statistik per cluster (mean/median/min/max/std, PRD §39) + z-relatif
    3. Label bisnis USULAN diberikan per cluster_id SETELAH profiling (PRD §41) — diverifikasi
       terhadap "tanda tangan" profil agar label tidak tertukar bila model dijalankan ulang
    4. Hasil per organisasi (PRD §42) + penjelasan feature vs rata-rata cluster (PRD §85)
    5. Organisasi representatif (terdekat centroid) & atipikal (jarak > P95 dalam cluster)
    6. Distribusi per direktorat & level; organisasi tidak tersegmentasi (D-017)
    7. Artefak model (PRD §73) dengan validation_status = PENDING_BUSINESS_VALIDATION

Output: ml/outputs/07_interpretation/<dataset_version>/
Jalankan:  ml/.venv/bin/python ml/pipeline/s07_interpretation.py [--dataset=v2]
"""
import json
from datetime import datetime, timezone

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import StandardScaler

import viz_style as vs
from config import OUTPUTS, RANDOM_SEED, dataset
from s03_feature_engineering import FEATURE_SETS, FEATURE_VERSION

EXPERIMENT_ID = "EXP-KM-067"
MODEL_NAME, MODEL_VERSION, FEATURE_SET, K = "KMEANS", "v1", "R", 5
VALIDATION_STATUS = "PENDING_BUSINESS_VALIDATION"

PROFILE_FEATURES = ["ftk", "realization", "gap", "fulfillment_ratio", "staffing_ratio", "balance_index",
                    "position_count", "vacant_position_count", "vacant_share", "avg_realization_per_position",
                    "unbudgeted_filled_count", "pct_MA_MAK", "pct_MM", "pct_MD", "pct_SPESIALIS", "pct_GENERALIS",
                    "organization_level"]
EXPLAIN_FEATURES = ["gap", "fulfillment_ratio", "balance_index", "vacant_share", "vacant_position_count",
                    "avg_realization_per_position"]

# Label bisnis USULAN (PRD §41) — ditulis setelah membaca profil Tahap 6/7, bukan aturan klasifikasi.
# `signature` hanya memverifikasi bahwa cluster_id masih merujuk ke profil yang sama.
CLUSTER_LABELS = {
    0: {"code": "UNBUDGETED", "label": "Terisi Tanpa Formasi",
        "prd_archetype": "Potensi Overstaffing (struktural)",
        "interpretation": "Unit memiliki pegawai pada jabatan yang tidak berformasi (FTK ≈ 0). Realisasi tidak "
                          "tercakup rencana formasi; perlu penataan formasi atau penempatan.",
        "signature": lambda p: p.ftk_mean < 0.5 and p.balance_index_mean > 0.7},
    1: {"code": "PARTIAL_UNDER", "label": "Understaffing Parsial",
        "prd_archetype": "Understaffing",
        "interpretation": "Formasi sebagian terisi: rata-rata ±1/3 jabatan kosong dan fulfillment < 100 %. "
                          "Kekurangan tersebar pada beberapa jabatan, bukan kekosongan total.",
        "signature": lambda p: 0.2 < p.vacant_share_mean < 0.6 and p.fulfillment_ratio_mean < 1},
    2: {"code": "STABLE", "label": "Relatif Stabil",
        "prd_archetype": "Relatif Stabil",
        "interpretation": "Realisasi ≈ FTK, hampir tanpa jabatan kosong. Didominasi unit kecil (±2 jabatan). "
                          "'Stabil' berarti seimbang pada snapshot ini, bukan rendah volatilitas (D-008).",
        "signature": lambda p: p.vacant_share_mean < 0.05 and 0.9 <= p.fulfillment_ratio_mean <= 1.2},
    3: {"code": "VACANT", "label": "Understaffing Kritis (Belum Terisi)",
        "prd_archetype": "Understaffing",
        "interpretation": "Hampir seluruh jabatan berformasi belum terisi (≈ 94 % kosong, fulfillment ≈ 6 %). "
                          "Termasuk unit baru/struktur yang belum diisi.",
        "signature": lambda p: p.vacant_share_mean > 0.85 and p.fulfillment_ratio_mean < 0.2},
    4: {"code": "OVER", "label": "Potensi Overstaffing",
        "prd_archetype": "Potensi Overstaffing",
        "interpretation": "Realisasi melebihi FTK (fulfillment rata-rata ≈ 145 %) dengan ±2,5 pegawai per jabatan; "
                          "unit relatif lebih besar.",
        "signature": lambda p: p.fulfillment_ratio_mean > 1.2 and p.avg_realization_per_position_mean > 1.8},
}
NOT_SEGMENTED = {"code": "NOT_SEGMENTED", "label": "Tidak Tersegmentasi",
                 "interpretation": "Tidak memiliki jabatan aktif (seluruh jabatan FTK = 0 dan realisasi = 0), "
                                   "sehingga tidak ada data workforce untuk di-cluster (D-017)."}


# ---------------------------------------------------------------- fungsi murni (diuji)

def profile_stats(df, cluster_col, features):
    """mean/median/min/max/std per feature per cluster (PRD §39); format panjang."""
    g = df.groupby(cluster_col)[features]
    out = pd.concat({s: getattr(g, s)() for s in ["mean", "median", "min", "max", "std"]}, axis=1)
    out.columns = [f"{feat}_{stat}" for stat, feat in out.columns]
    out.insert(0, "organization_count", df.groupby(cluster_col).size())
    return out


def relative_z(cluster_means, pop_mean, pop_std):
    """Selisih rata-rata cluster terhadap populasi dalam satuan SD populasi."""
    return (cluster_means - pop_mean) / pop_std.replace(0, np.nan)


def describe_characteristics(z_row, threshold=0.5, top=4):
    """Kalimat karakteristik dari z-relatif terbesar (bahasa bisnis, PRD §56)."""
    names = {"ftk": "FTK", "realization": "realisasi", "gap": "gap", "fulfillment_ratio": "fulfillment",
             "balance_index": "keseimbangan realisasi-FTK", "position_count": "jumlah jabatan",
             "vacant_position_count": "jabatan kosong", "vacant_share": "porsi jabatan kosong",
             "avg_realization_per_position": "pegawai per jabatan", "unbudgeted_filled_count": "jabatan terisi tanpa formasi"}
    z = z_row.dropna()
    z = z[[k for k in z.index if k in names]]
    z = z[z.abs() >= threshold]
    z = z.loc[z.abs().sort_values(ascending=False).index][:top]
    return [f"{names[k][0].upper() + names[k][1:]} {'tinggi' if v > 0 else 'rendah'} ({v:+.1f} SD)" for k, v in z.items()]


def verify_signatures(stats, labels=CLUSTER_LABELS):
    """Pastikan setiap cluster_id masih cocok dengan profil yang dilabeli. Error bila tertukar."""
    bad = [cid for cid, spec in labels.items() if not spec["signature"](stats.loc[cid])]
    if bad:
        raise ValueError(f"Profil cluster tidak cocok dengan label usulan: {bad}. Tinjau ulang label.")
    return True


# ---------------------------------------------------------------- pipeline

def main():
    vs.apply()
    ds = dataset()
    fe = OUTPUTS / "03_feature_engineering" / ds["version"]
    ex = OUTPUTS / "05_experiments" / ds["version"]
    eda = OUTPUTS / "04_eda" / ds["version"]
    OUT = OUTPUTS / "07_interpretation" / ds["version"]
    FIG, ART = OUT / "figures", OUT / "model_artifacts"
    FIG.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    feats = pd.read_csv(fe / "features_direct.csv", index_col=0)
    pop = feats[feats.in_model_population == 1].copy()
    cols = FEATURE_SETS[FEATURE_SET]

    # 1. refit & verifikasi
    scaler = StandardScaler().fit(pop[cols].to_numpy(float))
    X = scaler.transform(pop[cols].to_numpy(float))
    model = KMeans(n_clusters=K, n_init=20, random_state=RANDOM_SEED).fit(X)
    registry_labels = pd.read_csv(ex / "labels.csv.gz", index_col=0).loc[pop.index, EXPERIMENT_ID].to_numpy()
    identical = float(adjusted_rand_score(model.labels_, registry_labels))
    if not np.array_equal(model.labels_, registry_labels):
        raise SystemExit(f"Refit tidak identik dengan {EXPERIMENT_ID} (ARI={identical})")
    pop["cluster_id"] = model.labels_
    dist = np.linalg.norm(X - model.cluster_centers_[model.labels_], axis=1)
    pop["cluster_distance"] = dist.round(4)

    # 2. profil
    stats = profile_stats(pop, "cluster_id", PROFILE_FEATURES)
    verify_signatures(stats)
    stats.round(4).to_csv(OUT / "cluster_profile_stats.csv")
    means = pop.groupby("cluster_id")[PROFILE_FEATURES].mean()
    z = relative_z(means, pop[PROFILE_FEATURES].mean(), pop[PROFILE_FEATURES].std())
    z.round(3).to_csv(OUT / "cluster_relative_z.csv")

    # 3. profil dataset PRD §43
    prof = []
    for cid, spec in CLUSTER_LABELS.items():
        g = pop[pop.cluster_id == cid]
        prof.append({
            "model_version": MODEL_VERSION, "experiment_id": EXPERIMENT_ID, "cluster_id": cid,
            "cluster_code": spec["code"], "cluster_label": spec["label"], "prd_archetype": spec["prd_archetype"],
            "organization_count": int(len(g)), "organization_share": round(len(g) / len(pop), 4),
            "mean_ftk": round(g.ftk.mean(), 3), "mean_realization": round(g.realization.mean(), 3),
            "mean_gap": round(g.gap.mean(), 3), "mean_fulfillment": round(g.fulfillment_ratio.mean(), 4),
            "median_fulfillment": round(g.fulfillment_ratio.median(), 4),
            "mean_staffing_ratio": round(g.staffing_ratio.mean(), 4),
            "mean_position_count": round(g.position_count.mean(), 3),
            "mean_vacant_position": round(g.vacant_position_count.mean(), 3),
            "mean_vacant_share": round(g.vacant_share.mean(), 4),
            "mean_avg_realization_per_position": round(g.avg_realization_per_position.mean(), 3),
            "sum_ftk": int(g.ftk.sum()), "sum_realization": int(g.realization.sum()), "sum_gap": int(g.gap.sum()),
            "ftk_zero_orgs": int((g.ftk == 0).sum()),
            "characteristics": describe_characteristics(z.loc[cid]),
            "interpretation": spec["interpretation"],
            "centroid_scaled": dict(zip(cols, np.round(model.cluster_centers_[cid], 4))),
            "centroid_original": dict(zip(cols, np.round(scaler.inverse_transform(model.cluster_centers_[[cid]])[0], 4))),
        })
    prof_df = pd.DataFrame(prof)
    prof_df.drop(columns=["centroid_scaled", "centroid_original"]).assign(
        characteristics=prof_df.characteristics.map("; ".join)).to_csv(OUT / "cluster_profile.csv", index=False)

    # 4. hasil per organisasi (PRD §42) + penjelasan (PRD §85)
    lab = {cid: s["label"] for cid, s in CLUSTER_LABELS.items()}
    code = {cid: s["code"] for cid, s in CLUSTER_LABELS.items()}
    cmean = pop.groupby("cluster_id")[EXPLAIN_FEATURES].mean()
    res = pop[["organization_name", "parent_organization_id", "organization_level", "directorate_id", "directorate_name",
               "ftk", "realization", "gap", "fulfillment_ratio", "staffing_ratio", "balance_index", "position_count",
               "vacant_position_count", "vacant_share", "avg_realization_per_position"]].copy()
    res.insert(0, "experiment_id", EXPERIMENT_ID)
    res.insert(1, "model_name", MODEL_NAME)
    res.insert(2, "model_version", MODEL_VERSION)
    res.insert(3, "period", "2026-09-25")
    res["cluster_id"] = pop.cluster_id
    res["cluster_code"] = pop.cluster_id.map(code)
    res["cluster_label"] = pop.cluster_id.map(lab)
    res["cluster_distance"] = pop.cluster_distance
    p95 = pop.groupby("cluster_id").cluster_distance.quantile(0.95)
    res["is_atypical_member"] = pop.cluster_distance > pop.cluster_id.map(p95)
    for f in EXPLAIN_FEATURES:
        res[f"cluster_avg_{f}"] = pop.cluster_id.map(cmean[f]).round(4)
    res["created_at"] = now
    excl = feats[feats.in_model_population == 0]
    ex_rows = excl[["organization_name", "parent_organization_id", "organization_level", "directorate_id",
                    "directorate_name", "ftk", "realization", "gap"]].copy()
    for c_, v in {"experiment_id": EXPERIMENT_ID, "model_name": MODEL_NAME, "model_version": MODEL_VERSION,
                  "period": "2026-09-25", "cluster_code": NOT_SEGMENTED["code"],
                  "cluster_label": NOT_SEGMENTED["label"], "created_at": now}.items():
        ex_rows[c_] = v
    results = pd.concat([res, ex_rows], sort=False)
    results.index.name = "organization_id"
    results.to_csv(OUT / "organization_results.csv")

    # 5. representatif & atipikal
    rep = pop.sort_values("cluster_distance").groupby("cluster_id").head(5)
    rep_cols = ["cluster_id", "organization_name", "directorate_name", "organization_level", "ftk", "realization", "gap",
                "fulfillment_ratio", "vacant_share", "avg_realization_per_position", "cluster_distance"]
    rep.sort_values(["cluster_id", "cluster_distance"])[rep_cols].to_csv(OUT / "representative_organizations.csv")
    aty = res[res.is_atypical_member].sort_values(["cluster_id", "cluster_distance"], ascending=[True, False])
    aty[["cluster_id", "cluster_label", "organization_name", "directorate_name", "ftk", "realization", "gap",
         "fulfillment_ratio", "vacant_share", "avg_realization_per_position", "cluster_distance"]].to_csv(OUT / "atypical_members.csv")
    outliers = set(pd.read_csv(eda / "outliers_multivariate_setB.csv", index_col=0).index)
    out_place = pop.loc[pop.index.isin(outliers), "cluster_id"].map(lab).value_counts().to_dict()

    # 6. distribusi
    by_dir = pd.crosstab(pop.directorate_name, pop.cluster_id.map(code))
    by_dir.to_csv(OUT / "cluster_by_directorate.csv")
    by_lvl = pd.crosstab(pop.organization_level, pop.cluster_id.map(code))
    by_lvl.to_csv(OUT / "cluster_by_level.csv")
    dl = pop.directorate_name == "DIREKTORAT LEGAL DAN MANAJEMEN HUMAN CAPITAL"
    dlmhc = pd.DataFrame({"DLMHC": pop[dl].cluster_id.map(code).value_counts(normalize=True),
                          "Direktorat lain": pop[~dl].cluster_id.map(code).value_counts(normalize=True)}).round(4)
    dlmhc.to_csv(OUT / "cluster_dlmhc_vs_other.csv")

    # 7. artefak (PRD §73) — status menunggu validasi bisnis
    joblib.dump(model, ART / "model.joblib")
    joblib.dump(scaler, ART / "scaler.joblib")
    (ART / "feature_schema.json").write_text(json.dumps({
        "feature_version": FEATURE_VERSION, "feature_set": FEATURE_SET, "features": cols,
        "scaler": "StandardScaler", "unit": "direct", "model_population_rule": "in_model_population = 1 (D-017)"},
        indent=2))
    ev = pd.read_csv(OUTPUTS / "06_evaluation" / ds["version"] / "eligible_runs.csv").set_index("experiment_id").loc[EXPERIMENT_ID]
    metrics = {"experiment_id": EXPERIMENT_ID, "model_name": MODEL_NAME, "model_version": MODEL_VERSION,
               "training_timestamp": now, "dataset_version": ds["version"], "feature_version": FEATURE_VERSION,
               "features_used": cols, "scaler": "StandardScaler",
               "hyperparameters": {"n_clusters": K, "n_init": 20, "random_state": RANDOM_SEED},
               "silhouette_score": float(ev.silhouette), "davies_bouldin_score": float(ev.davies_bouldin),
               "stability_ari": float(ev.stability_ari), "size_entropy_norm": float(ev.size_entropy_norm),
               "workforce_eta2": float(ev.workforce_eta2), "cramers_v_level": float(ev.cramers_v_level),
               "cramers_v_directorate": float(ev.cramers_v_directorate), "cluster_count": K, "noise_count": 0,
               "n_samples": int(len(pop)), "n_not_segmented": int(len(excl)),
               "refit_identical_to_registry": True, "selection_decisions": ["D-027", "D-028", "D-029"],
               "validation_status": VALIDATION_STATUS}
    approval = ART / "approval.json"                     # dicatat oleh s07b (validasi bisnis, PRD §45)
    if approval.exists() and json.loads(approval.read_text()).get("experiment_id") == EXPERIMENT_ID:
        a = json.loads(approval.read_text())
        metrics["validation_status"] = "APPROVED"
        metrics["approval"] = {k: a[k] for k in ["decision", "approved_by", "approved_on"]}
    (ART / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    (ART / "cluster_profile.json").write_text(json.dumps(prof, indent=2, ensure_ascii=False, default=float))

    summary = {"refit_ari": identical, "cluster_sizes": pop.cluster_id.value_counts().sort_index().to_dict(),
               "atypical_members": int(res.is_atypical_member.sum()), "not_segmented": int(len(excl)),
               "multivariate_outliers_placement": out_place, "validation_status": VALIDATION_STATUS}
    (OUT / "interpretation_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    figures(pop, z, prof_df, by_dir, by_lvl, X, FIG)
    print(json.dumps(summary, indent=1, ensure_ascii=False))
    print(prof_df[["cluster_id", "cluster_label", "organization_count", "mean_ftk", "mean_realization", "mean_gap",
                   "mean_fulfillment", "mean_vacant_share", "mean_avg_realization_per_position", "characteristics"]].to_string())
    print(rep[rep_cols].sort_values(["cluster_id", "cluster_distance"]).to_string())
    print(by_dir.to_string()); print(dlmhc.to_string())


def figures(pop, z, prof_df, by_dir, by_lvl, X, FIG):
    labels = [f"{r.cluster_id} · {r.cluster_label}\n(n={r.organization_count})" for r in prof_df.itertuples()]
    order = list(prof_df.cluster_id)
    feats = ["ftk", "realization", "gap", "fulfillment_ratio", "balance_index", "vacant_share",
             "avg_realization_per_position", "position_count", "unbudgeted_filled_count", "organization_level"]
    # P01 heatmap z-relatif
    M = z.loc[order, feats].to_numpy()
    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    im = ax.imshow(np.clip(M, -3, 3), cmap=vs.DIVERGING, vmin=-3, vmax=3, aspect="auto")
    ax.set_xticks(range(len(feats))); ax.set_xticklabels(feats, rotation=30, ha="right")
    ax.set_yticks(range(len(order))); ax.set_yticklabels(labels, fontsize=7.5); ax.grid(False)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, f"{M[i, j]:+.1f}", ha="center", va="center", fontsize=7,
                    color="white" if abs(M[i, j]) > 1.8 else vs.TEXT)
    fig.colorbar(im, ax=ax, fraction=0.03, label="z relatif thd populasi (SD)")
    ax.set_title("P01 — Profil cluster EXP-KM-067: rata-rata cluster relatif terhadap populasi", loc="left")
    fig.savefig(FIG / "P01_cluster_profile_heatmap.png"); plt.close(fig)

    # P02 ukuran cluster + per direktorat
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.8), gridspec_kw={"width_ratios": [1, 2.2], "wspace": 0.8})
    sizes = prof_df.set_index("cluster_id").organization_count.loc[order]
    axes[0].barh([l.replace("\n", " ") for l in labels][::-1], sizes.values[::-1],
                 color=[vs.SERIES[c] for c in order][::-1], edgecolor=vs.SURFACE)
    for y, v in enumerate(sizes.values[::-1]):
        axes[0].text(v + 5, y, f"{v} ({v / sizes.sum():.0%})", va="center", fontsize=7.5, color=vs.TEXT_2)
    axes[0].set_xlim(0, sizes.max() * 1.3); axes[0].set_title("P02a — Ukuran cluster", loc="left")
    codes = list(prof_df.cluster_code)
    d = by_dir.drop(index=[i for i in by_dir.index if "KANTOR PUSAT" in i]).reindex(columns=codes, fill_value=0)
    d = d.div(d.sum(1), axis=0).sort_values("VACANT")
    d.index = d.index.str.replace("DIREKTORAT ", "").str.title()
    left = np.zeros(len(d))
    for k, (cid, c) in enumerate(zip(order, codes)):
        axes[1].barh(d.index, d[c] * 100, left=left, color=vs.SERIES[cid], edgecolor=vs.SURFACE, linewidth=1,
                     label=prof_df.set_index("cluster_id").cluster_label[cid])
        left += d[c].values * 100
    axes[1].set_xlim(0, 100); axes[1].set_xlabel("% organisasi")
    axes[1].legend(ncol=3, loc="upper center", bbox_to_anchor=(0.4, -0.12), fontsize=7.5)
    axes[1].set_title("P02b — Komposisi cluster per direktorat", loc="left")
    fig.savefig(FIG / "P02_cluster_sizes_by_directorate.png"); plt.close(fig)

    # P03 distribusi feature per cluster
    show = [("fulfillment_ratio", "Fulfillment (FTK > 0)"), ("vacant_share", "Porsi jabatan kosong"),
            ("avg_realization_per_position", "Pegawai per jabatan"), ("gap", "Gap")]
    fig, axes = plt.subplots(1, 4, figsize=(15, 3.4))
    for ax, (f, t) in zip(axes, show):
        data = [pop.loc[pop.cluster_id == c, f].dropna() for c in order]
        bp = ax.boxplot(data, tick_labels=[str(c) for c in order], widths=0.55, patch_artist=True,
                        flierprops={"marker": "o", "markersize": 2.5, "markerfacecolor": vs.NEUTRAL, "markeredgewidth": 0},
                        medianprops={"color": vs.TEXT, "linewidth": 1.5})
        for patch, c in zip(bp["boxes"], order):
            patch.set_facecolor(vs.SERIES[c]); patch.set_alpha(0.75); patch.set_edgecolor(vs.TEXT_2)
        ax.set_title(t, loc="left"); ax.set_xlabel("cluster")
    fig.suptitle("P03 — Distribusi feature kunci per cluster", x=0.01, ha="left", y=1.04)
    fig.savefig(FIG / "P03_feature_distribution_by_cluster.png"); plt.close(fig)

    # P04 PCA small multiples (visual saja, PRD §52)
    P = PCA(n_components=2, random_state=RANDOM_SEED).fit(X)
    Q = P.transform(X) + np.random.default_rng(RANDOM_SEED).normal(0, 0.03, (len(X), 2))
    fig, axes = plt.subplots(1, len(order), figsize=(3.1 * len(order), 3.1), sharex=True, sharey=True)
    for ax, c in zip(axes, order):
        m = pop.cluster_id.values == c
        ax.scatter(Q[~m, 0], Q[~m, 1], s=4, color=vs.NEUTRAL, alpha=0.3, linewidth=0)
        ax.scatter(Q[m, 0], Q[m, 1], s=10, color=vs.SERIES[c], alpha=0.8, edgecolor=vs.SURFACE, linewidth=0.4)
        ax.set_title(f"{c} · {prof_df.set_index('cluster_id').cluster_label[c]}", loc="left", fontsize=8)
        ax.set_xlabel(f"PC1 ({P.explained_variance_ratio_[0]:.0%})")
    axes[0].set_ylabel(f"PC2 ({P.explained_variance_ratio_[1]:.0%})")
    fig.suptitle("P04 — PCA 2D set R (visual saja; model memakai 3 feature asli)", x=0.01, ha="left", y=1.05)
    fig.savefig(FIG / "P04_pca_by_cluster.png"); plt.close(fig)

    # P05 per level
    l = by_lvl.reindex(columns=codes, fill_value=0)
    l = l.div(l.sum(1), axis=0)
    fig, ax = plt.subplots(figsize=(8, 3.4))
    left = np.zeros(len(l))
    for cid, c in zip(order, codes):
        ax.barh([f"L{i} (n={by_lvl.loc[i].sum()})" for i in l.index], l[c] * 100, left=left, color=vs.SERIES[cid],
                edgecolor=vs.SURFACE, linewidth=1, label=prof_df.set_index("cluster_id").cluster_label[cid])
        left += l[c].values * 100
    ax.set_xlim(0, 100); ax.set_xlabel("% organisasi"); ax.invert_yaxis()
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.45, -0.2), fontsize=7.5)
    ax.set_title("P05 — Komposisi cluster per level organisasi", loc="left")
    fig.savefig(FIG / "P05_cluster_by_level.png"); plt.close(fig)


if __name__ == "__main__":
    main()
