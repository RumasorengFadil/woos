"""Tahap 1b — Dataset Adequacy Assessment.

Menjawab: apakah dataset cukup untuk (a) PRD 1.0 dan (b) publikasi jurnal?

PENTING: feature di sini PROVISIONAL, hanya untuk mengukur kecukupan data.
Feature final ditetapkan di Tahap 3 setelah keputusan D-001..D-007 disetujui.
Asumsi provisional: VP->MM, AM->MD, jenjang kosong->UNKNOWN (D-004);
jabatan aktif = FTK>0 atau Realisasi>0 (D-002); balance_index (D-003).

Output: ml/outputs/01b_dataset_adequacy/<dataset_version>/
    adequacy.json, field_coverage.csv, feature_set_adequacy.csv,
    provisional_org_features.csv, figures/*.png

Jalankan:  ml/.venv/bin/python ml/pipeline/s01b_dataset_adequacy.py [--dataset=v1|v2]
Prasyarat: s01_data_understanding.py untuk dataset yang sama (memakai org_hierarchy_check.csv).
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import RobustScaler, StandardScaler

from config import COLUMN_MAP, GRADE_GROUP, OUTPUTS, RANDOM_SEED, dataset
from config import GRADE_GROUPS as GROUPS
from s01_data_understanding import parse_grade

# Kebutuhan field PRD §13.1 (minimum), §15 (ideal), §89 (tambahan)
PRD_FIELDS = [
    ("ID Organisasi", "Wajib", "organization_id"), ("Nama Organisasi", "Wajib", "organization_name"),
    ("Parent Organisasi", "Disarankan", "parent_name"), ("ID Parent", "Disarankan (§13.1 parent)", "parent_organization_id"), ("Level Organisasi", "Wajib", "organization_level"),
    ("ID Jabatan", "Wajib", "position_id"), ("Nama Jabatan", "Wajib", "position_name"),
    ("Jenjang Jabatan", "Wajib", "grade"), ("FTK Jabatan", "Wajib", "ftk"),
    ("Realisasi Jabatan", "Wajib", "realization"), ("Periode Data", "Sangat disarankan", "period"),
    ("Data historis multi-periode", "Sangat direkomendasikan (§15, §16, §90)", None),
    ("Status jabatan", "Ideal (§15, §89)", None), ("Status pegawai", "Ideal (§15)", None),
    ("Jenis organisasi", "Opsional (§89)", None), ("Kategori jabatan", "Opsional (§89)", None),
]


def hopkins(X, rng, frac=0.1):
    """Hopkins statistic (konvensi: ~0.5 acak, >0.75 kecenderungan cluster kuat).

    H = sum(u) / (sum(u) + sum(w)); u = jarak titik uniform ke data terdekat,
    w = jarak titik sampel ke tetangga terdekat lain di data.
    """
    n, d = X.shape
    m = max(1, int(frac * n))
    nn = NearestNeighbors(n_neighbors=2).fit(X)
    idx = rng.choice(n, m, replace=False)
    w = nn.kneighbors(X[idx], n_neighbors=2)[0][:, 1]
    U = rng.uniform(X.min(0), X.max(0), size=(m, d))
    u = nn.kneighbors(U, n_neighbors=1)[0][:, 0]
    return float(u.sum() / (u.sum() + w.sum()))


def build_features(df, orgs_hier, rollup):
    """Feature provisional per organisasi, direct atau roll-up sub-tree."""
    df = df.copy()
    df["grade_group"] = df.grade.apply(lambda g: GRADE_GROUP.get(parse_grade(g)[0], "UNKNOWN"))
    df["active"] = (df.ftk > 0) | (df.realization > 0)
    df["vacant"] = (df.ftk > 0) & (df.realization == 0)

    if rollup:
        children = orgs_hier.groupby("parent_organization_id").organization_id.apply(list).to_dict()

        def subtree(o):
            out = [o]
            for c in children.get(o, []):
                out += subtree(c)
            return out

        mapping = [(o, s) for o in orgs_hier.organization_id for s in subtree(o)]
        m = pd.DataFrame(mapping, columns=["unit_id", "organization_id"])
        df = m.merge(df, on="organization_id")
    else:
        df["unit_id"] = df.organization_id

    g = df.groupby("unit_id")
    f = pd.DataFrame({
        "ftk": g.ftk.sum(), "realization": g.realization.sum(),
        "position_count": g.active.sum(), "vacant_position_count": g.vacant.sum(),
    })
    f["gap"] = f.ftk - f.realization
    denom = f.ftk + f.realization
    f["balance_index"] = np.where(denom > 0, (f.realization - f.ftk) / denom.replace(0, 1), 0.0)
    f["fulfillment_ratio"] = np.where(f.ftk > 0, f.realization / f.ftk.replace(0, 1), np.nan)
    f["avg_realization_per_position"] = np.where(f.position_count > 0,
                                                 f.realization / f.position_count.replace(0, 1), 0.0)
    act = df[df.active]
    # distribusi jenjang berbasis FTK jabatan aktif (struktur formasi); realisasi dipakai sebagai cadangan bila FTK=0
    wt = act.assign(w=np.where(act.ftk > 0, act.ftk, act.realization))
    pct = wt.pivot_table(index="unit_id", columns="grade_group", values="w", aggfunc="sum", fill_value=0)
    pct = pct.reindex(columns=GROUPS, fill_value=0)
    pct = pct.div(pct.sum(1).replace(0, 1), axis=0)
    pct.columns = [f"pct_{c}" for c in pct.columns]
    f = f.join(pct).fillna({c: 0 for c in pct.columns})
    return f


FEATURE_SETS = {
    "A_core": ["ftk", "realization", "gap", "balance_index"],
    "A_core_nonredundant": ["ftk", "realization", "balance_index"],
    "B_structure": ["ftk", "realization", "balance_index", "position_count", "vacant_position_count",
                    "avg_realization_per_position"],
    "C_grade": ["ftk", "realization", "balance_index", "position_count", "vacant_position_count",
                "avg_realization_per_position"] + [f"pct_{g}" for g in GROUPS],
    "R_ratio_only": ["balance_index", "vacant_share", "avg_realization_per_position"],
}


def assess(f, name, cols, unit, rng_seed):
    X_raw = f[cols].to_numpy(float)
    n, d = X_raw.shape
    vec = pd.Series([tuple(r) for r in X_raw])
    counts = vec.map(vec.value_counts())
    rank = np.linalg.matrix_rank(X_raw - X_raw.mean(0))
    corr = pd.DataFrame(X_raw, columns=cols).corr().abs()
    high = [(a, b, round(corr.loc[a, b], 3)) for i, a in enumerate(cols) for b in cols[i + 1:]
            if corr.loc[a, b] >= 0.9]
    res = {"unit": unit, "feature_set": name, "n": n, "d": d,
           "n_required_70d (Dolnicar 2014)": 70 * d, "meets_70d": n >= 70 * d,
           "n_required_2pow_d (Formann 1984)": 2 ** d, "meets_2pow_d": n >= 2 ** d,
           "n_per_feature": round(n / d, 1), "matrix_rank": int(rank), "rank_deficient": bool(rank < d),
           "unique_vectors": int(vec.nunique()), "unique_vector_share": round(vec.nunique() / n, 3),
           "share_orgs_in_tied_vectors": round(float((counts > 1).mean()), 3),
           "largest_tie_group": int(counts.max()), "pairs_corr_ge_0_9": high}
    for sname, scaler in [("standard", StandardScaler()), ("robust", RobustScaler())]:
        Xs = scaler.fit_transform(X_raw)
        hs = [hopkins(Xs, np.random.default_rng(rng_seed + i)) for i in range(50)]
        res[f"hopkins_{sname}_mean"] = round(float(np.mean(hs)), 3)
        res[f"hopkins_{sname}_sd"] = round(float(np.std(hs)), 3)
    # Data diskret -> banyak titik identik (jarak tetangga = 0) yang menggelembungkan Hopkins.
    # Kontrol: hitung ulang pada vektor unik saja.
    Xu = StandardScaler().fit_transform(np.unique(X_raw, axis=0))
    hu = [hopkins(Xu, np.random.default_rng(rng_seed + i)) for i in range(50)]
    res["hopkins_dedup_mean"] = round(float(np.mean(hu)), 3)
    res["hopkins_dedup_sd"] = round(float(np.std(hu)), 3)
    return res


def main():
    ds = dataset()
    OUT = OUTPUTS / "01b_dataset_adequacy" / ds["version"]
    FIG = OUT / "figures"
    FIG.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(ds["file"]).rename(columns=COLUMN_MAP)
    hier = pd.read_csv(OUTPUTS / "01_data_understanding" / ds["version"] / "org_hierarchy_check.csv")

    # ---------- cakupan field PRD ----------
    cov = []
    for label, req, col in PRD_FIELDS:
        if col is None or col not in df.columns:
            status = "TIDAK ADA"
            note = "Tidak tersedia di dataset"
        else:
            miss = int(df[col].isna().sum())
            status = "ADA" if miss == 0 else "ADA (ada nilai kosong)"
            note = f"{miss} kosong, {df[col].nunique()} nilai unik"
            if col == "period":
                status, note = "ADA (1 periode)", f"hanya {df[col].unique().tolist()}"
            if col == "parent_name" and "parent_organization_id" not in df.columns:
                vc = hier.status.value_counts()
                status = "ADA (berupa nama, bukan ID)"
                note = f"diresolusi via nama+level; {vc.get('RESOLVED_NAME_LEVEL', 0)}/{len(hier)} tepat"
            if col == "parent_organization_id":
                vc = hier.status.value_counts()
                note = f"{vc.get('RESOLVED_BY_ID', 0)}/{len(hier)} valid; {vc.get('PARENT_NOT_IN_DATASET', 0)} parent tidak ada di dataset"
        cov.append({"field": label, "prd_requirement": req, "status": status, "note": note})
    cov = pd.DataFrame(cov)
    cov.to_csv(OUT / "field_coverage.csv", index=False)

    # ---------- feature provisional & kecukupan statistik ----------
    rows, feats = [], {}
    for unit, rollup in [("direct", False), ("rollup", True)]:
        f = build_features(df, hier, rollup)
        f["vacant_share"] = np.where(f.position_count > 0, f.vacant_position_count / f.position_count.replace(0, 1), 0)
        feats[unit] = f
        for name, cols in FEATURE_SETS.items():
            rows.append(assess(f, name, cols, unit, RANDOM_SEED))
    res = pd.DataFrame(rows)
    res.drop(columns=["pairs_corr_ge_0_9"]).to_csv(OUT / "feature_set_adequacy.csv", index=False)
    feats["direct"].to_csv(OUT / "provisional_org_features.csv")

    # baseline Hopkins pada data uniform acak berukuran sama (kontrol sanity)
    rng = np.random.default_rng(RANDOM_SEED)
    base = [hopkins(StandardScaler().fit_transform(rng.uniform(size=(len(df.organization_id.unique()), 6))), np.random.default_rng(i)) for i in range(50)]

    fd = feats["direct"]
    distinct = {c: int(fd[c].nunique()) for c in ["ftk", "realization", "gap", "balance_index",
                                                   "fulfillment_ratio", "position_count",
                                                   "vacant_position_count", "avg_realization_per_position"]}
    overlap = feats["rollup"]
    adequacy = {
        "note": "Feature PROVISIONAL untuk uji kecukupan, bukan feature final (Tahap 3).",
        "n_organizations": int(len(fd)),
        "n_orgs_ftk_gt_0": int((fd.ftk > 0).sum()),
        "orgs_per_level": df.groupby("organization_level").organization_id.nunique().to_dict(),
        "distinct_values_per_feature_direct": distinct,
        "hopkins_uniform_baseline_mean": round(float(np.mean(base)), 3),
        "rollup_note": "Pada roll-up, unit induk memuat sub-unit sehingga observasi tidak independen.",
        "rollup_leaf_share": round(float((overlap.position_count == fd.position_count).mean()), 3),
        "feature_sets": rows,
    }
    (OUT / "adequacy.json").write_text(json.dumps(adequacy, indent=2, ensure_ascii=False, default=str))

    # ---------- figure: Hopkins per feature set ----------
    fig, ax = plt.subplots(figsize=(8, 3.6))
    names = list(FEATURE_SETS)
    xs = np.arange(len(names))
    bars = [("direct", "hopkins_standard", -0.27, "#9DB4D6", "direct (semua titik)"),
            ("direct", "hopkins_dedup", 0.0, "#4C72B0", "direct (vektor unik)"),
            ("rollup", "hopkins_dedup", 0.27, "#DD8452", "roll-up (vektor unik)")]
    for unit, key, off, col, label in bars:
        r = res[res.unit == unit].set_index("feature_set").loc[names]
        ax.bar(xs + off, r[f"{key}_mean"], 0.27, yerr=r[f"{key}_sd"], color=col, label=label)
    ax.axhline(0.5, color="k", ls="--", lw=.8, label="acak (0.5)")
    ax.axhline(0.75, color="g", ls=":", lw=.8, label="kuat (0.75)")
    ax.set_xticks(xs); ax.set_xticklabels(names, rotation=15); ax.set_ylim(0, 1)
    ax.set_ylabel("Hopkins (StandardScaler)"); ax.set_title("Clustering tendency per feature set (50 run)")
    ax.legend(fontsize=7, ncol=4, loc="lower right")
    fig.tight_layout(); fig.savefig(FIG / "01_hopkins_by_feature_set.png", dpi=130); plt.close(fig)

    adequacy["dataset_version"] = ds["version"]
    (OUT / "adequacy.json").write_text(json.dumps(adequacy, indent=2, ensure_ascii=False, default=str))
    print(cov.to_string(index=False))
    print()
    print(res[["unit", "feature_set", "n", "d", "meets_70d", "rank_deficient", "unique_vectors",
               "share_orgs_in_tied_vectors", "largest_tie_group", "hopkins_standard_mean",
               "hopkins_standard_sd", "hopkins_robust_mean", "hopkins_dedup_mean"]].to_string(index=False))
    print("\nhigh corr pairs:")
    for r in rows:
        if r["pairs_corr_ge_0_9"]:
            print(r["unit"], r["feature_set"], r["pairs_corr_ge_0_9"])
    print("\ndistinct values (direct):", distinct)
    print("hopkins uniform baseline:", adequacy["hopkins_uniform_baseline_mean"])


if __name__ == "__main__":
    main()
