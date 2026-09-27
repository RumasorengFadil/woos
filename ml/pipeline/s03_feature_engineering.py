"""Tahap 3 — Feature Engineering & Feature Scaling (PRD §6–§12, §17, §23, §24, §79–§81).

Agregasi jabatan bersih (Tahap 2) menjadi 1 baris = 1 organisasi + 1 periode, dalam dua
definisi unit (D-001):
    direct  — hanya jabatan yang tercatat langsung pada organisasi (analisis utama)
    rollup  — organisasi + seluruh sub-unitnya (analisis sensitivitas)

Keputusan yang diterapkan: D-002, D-003, D-009, D-012, D-016..D-018, D-020 (decision_log.md).

Output: ml/outputs/03_feature_engineering/<dataset_version>/
    features_direct.csv, features_rollup.csv   feature + metadata per organisasi
    feature_schema.json                        kamus feature, feature set, versi (PRD §73)
    scalers/<unit>_<set>_<scaler>.joblib        scaler ter-fit (PRD §24)
    scaling_summary.csv                        center/scale per feature per scaler
    feature_log.json                           populasi, validasi, ringkasan

Jalankan:  ml/.venv/bin/python ml/pipeline/s03_feature_engineering.py [--dataset=v2]
"""
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler, StandardScaler

from config import GRADE_GROUPS, OUTPUTS, dataset

FEATURE_VERSION = "F2"

# Kelompok jenjang untuk INPUT MODEL (D-018): MAK digabung ke MA; UNKNOWN tidak dipakai
# (komposisi berjumlah 1 -> satu kategori harus dibuang agar tidak linear-dependen).
MODEL_GRADE_GROUPS = {"MA_MAK": ["MAK", "MA"], "MM": ["MM"], "MD": ["MD"],
                      "SPESIALIS": ["SPESIALIS"], "GENERALIS": ["GENERALIS"]}

# Feature set F1 (D-019, SUPERSEDED) — dipertahankan agar Tahap 4 (EDA) tetap reproducible.
FEATURE_SETS_F1 = {
    "A": ["ftk", "realization", "balance_index"],
    "B": ["ftk", "realization", "balance_index", "position_count", "vacant_position_count",
          "avg_realization_per_position"],
    "C": ["ftk", "realization", "balance_index", "position_count", "vacant_position_count",
          "avg_realization_per_position"] + [f"pct_{g}" for g in MODEL_GRADE_GROUPS],
    "R": ["balance_index", "vacant_share", "avg_realization_per_position"],
}
# Feature set F2 (D-020, hasil EDA): B tanpa avg_realization_per_position (turunan
# realization/position_count, VIF 11,3); C memakai GENERALIS sebagai kategori referensi
# (near-closure, VIF 75,9). Set R dari PRD §81 (absolute vs ratio).
FEATURE_SETS = {
    "A": ["ftk", "realization", "balance_index"],
    "B": ["ftk", "realization", "balance_index", "position_count", "vacant_position_count"],
    "C": ["ftk", "realization", "balance_index", "position_count", "vacant_position_count",
          "pct_MA_MAK", "pct_MM", "pct_MD", "pct_SPESIALIS"],
    "R": ["balance_index", "vacant_share", "avg_realization_per_position"],
}
SCALERS = {"standard": StandardScaler, "robust": RobustScaler}

DICTIONARY = {
    "ftk": ("Σ FTK jabatan", "model+display", "PRD §6"),
    "realization": ("Σ realisasi jabatan", "model+display", "PRD §6"),
    "gap": ("ftk − realization", "display", "PRD §7; dikeluarkan dari model (D-009: linear-dependen)"),
    "fulfillment_ratio": ("realization / ftk; NULL bila ftk = 0", "display", "PRD §8; D-003"),
    "staffing_ratio": ("(realization − ftk) / ftk; NULL bila ftk = 0", "display",
                       "PRD §9; = fulfillment − 1 (redundan), D-003"),
    "balance_index": ("(realization − ftk) / (realization + ftk); 0 bila keduanya 0; ∈ [−1, 1]",
                      "model", "D-003; transformasi monoton dari fulfillment untuk ftk > 0"),
    "ftk_zero": ("1 bila ftk = 0", "flag", "D-003"),
    "position_rows": ("jumlah baris jabatan (termasuk dormant)", "display", "D-002"),
    "position_count": ("jumlah jabatan aktif (FTK > 0 atau realisasi > 0)", "model+display", "PRD §6; D-002"),
    "dormant_position_count": ("jabatan FTK = 0 & realisasi = 0", "display", "D-002"),
    "vacant_position_count": ("jabatan FTK > 0 & realisasi = 0", "model+display", "PRD §10"),
    "vacant_share": ("vacant_position_count / position_count; 0 bila tanpa jabatan aktif", "model", "PRD §81"),
    "avg_realization_per_position": ("realization / position_count; 0 bila tanpa jabatan aktif",
                                     "display (+ model set R)", "PRD §11; D-002; D-020"),
    "unbudgeted_filled_count": ("jabatan FTK = 0 & realisasi > 0", "display", "D-003"),
    "marked_position_count": ("jabatan bertanda *)", "display", "D-005"),
    "extreme_position_count": ("jabatan realisasi ekstrem", "display", "D-006"),
    "pct_<GRUP>": ("proporsi jabatan aktif pada kelompok jenjang (7 kelompok PRD §12)", "display",
                   "PRD §12; D-016"),
    "pct_MA_MAK, pct_MM, pct_MD, pct_SPESIALIS": ("proporsi jabatan aktif; MAK+MA digabung; GENERALIS = kategori "
                                                  "referensi dan UNKNOWN tidak dipakai", "model (set C)",
                                                  "D-016, D-018, D-020"),
    "ftk_<GRUP>, real_<GRUP>": ("Σ FTK / Σ realisasi per kelompok jenjang (komposisi tenaga kerja)",
                                "display", "PRD §12, §60; D-016"),
    "has_active_positions": ("1 bila position_count > 0", "flag", "D-017"),
    "in_model_population": ("1 bila memiliki jabatan aktif dan bukan wadah virtual", "flag", "D-017"),
}


# ---------------------------------------------------------------- fungsi murni (diuji)

def balance_index(ftk, realization):
    ftk, realization = np.asarray(ftk, float), np.asarray(realization, float)
    denom = ftk + realization
    return np.where(denom > 0, (realization - ftk) / np.where(denom > 0, denom, 1), 0.0)


def safe_ratio(num, den):
    """num/den; NULL (NaN) bila den = 0 — tidak ada pembagian langsung (PRD §8)."""
    num, den = np.asarray(num, float), np.asarray(den, float)
    return np.where(den > 0, num / np.where(den > 0, den, 1), np.nan)


def descendants_map(orgs):
    """{organization_id: [dirinya + seluruh keturunan]} dari parent_organization_id."""
    children = orgs.dropna(subset=["parent_organization_id"]).groupby("parent_organization_id") \
        .organization_id.apply(list).to_dict()
    memo = {}

    def walk(o):
        if o not in memo:
            out = [o]
            for c in children.get(o, []):
                out += walk(c)
            memo[o] = out
        return memo[o]

    return {o: walk(o) for o in orgs.organization_id}


def aggregate(positions, unit_map):
    """Agregasi jabatan ke unit. unit_map: DataFrame [unit_id, organization_id]."""
    df = unit_map.merge(positions, on="organization_id", how="inner")
    g = df.groupby("unit_id")
    f = pd.DataFrame({
        "position_rows": g.size(),
        "ftk": g.ftk.sum(), "realization": g.realization.sum(),
        "position_count": g.is_active.sum(), "dormant_position_count": g.is_dormant.sum(),
        "vacant_position_count": g.is_vacant.sum(), "unbudgeted_filled_count": g.is_unbudgeted_filled.sum(),
        "marked_position_count": g.is_marked_position.sum(), "extreme_position_count": g.is_extreme_realization.sum(),
    })
    f["gap"] = f.ftk - f.realization
    f["fulfillment_ratio"] = safe_ratio(f.realization, f.ftk)
    f["staffing_ratio"] = safe_ratio(f.realization - f.ftk, f.ftk)
    f["balance_index"] = balance_index(f.ftk, f.realization)
    f["ftk_zero"] = (f.ftk == 0).astype(int)
    f["avg_realization_per_position"] = np.nan_to_num(safe_ratio(f.realization, f.position_count))
    f["vacant_share"] = np.nan_to_num(safe_ratio(f.vacant_position_count, f.position_count))

    act = df[df.is_active]
    cnt = act.pivot_table(index="unit_id", columns="grade_group", values="position_id",
                          aggfunc="count", fill_value=0).reindex(columns=GRADE_GROUPS, fill_value=0)
    share = cnt.div(cnt.sum(1), axis=0)
    for gname in GRADE_GROUPS:
        f[f"pct_{gname}"] = share[gname]
    for mname, members in MODEL_GRADE_GROUPS.items():
        if len(members) > 1:
            f[f"pct_{mname}"] = share[members].sum(1)
    for col, src in [("ftk", "ftk"), ("real", "realization")]:
        tot = df.pivot_table(index="unit_id", columns="grade_group", values=src, aggfunc="sum",
                             fill_value=0).reindex(columns=GRADE_GROUPS, fill_value=0)
        for gname in GRADE_GROUPS:
            f[f"{col}_{gname}"] = tot[gname]
    pct_cols = [c for c in f.columns if c.startswith("pct_")]
    f[pct_cols] = f[pct_cols].fillna(0.0)
    f[[c for c in f.columns if c.startswith(("ftk_", "real_")) and c != "ftk_zero"]] = \
        f[[c for c in f.columns if c.startswith(("ftk_", "real_")) and c != "ftk_zero"]].fillna(0).astype(int)
    f["has_active_positions"] = (f.position_count > 0).astype(int)
    return f


def validate(f, positions, unit):
    """Invarian feature. Mengembalikan dict {nama_cek: bool}."""
    v = {
        "gap_identity": bool((f.gap == f.ftk - f.realization).all()),
        "fulfillment_null_iff_ftk_zero": bool((f.fulfillment_ratio.isna() == (f.ftk == 0)).all()),
        "staffing_eq_fulfillment_minus_1": bool(np.allclose((f.fulfillment_ratio - 1).dropna(),
                                                            f.staffing_ratio.dropna())),
        "balance_in_range": bool(f.balance_index.between(-1, 1).all()),
        "vacant_le_active": bool((f.vacant_position_count <= f.position_count).all()),
        "active_le_rows": bool((f.position_count <= f.position_rows).all()),
        "pct_sum_1_when_active": bool(np.allclose(
            f.loc[f.position_count > 0, [f"pct_{g}" for g in GRADE_GROUPS]].sum(1), 1)),
        "pct_zero_when_inactive": bool((f.loc[f.position_count == 0, [f"pct_{g}" for g in GRADE_GROUPS]] == 0).all().all()),
        "grade_ftk_sum_matches": bool((f[[f"ftk_{g}" for g in GRADE_GROUPS]].sum(1) == f.ftk).all()),
        "grade_real_sum_matches": bool((f[[f"real_{g}" for g in GRADE_GROUPS]].sum(1) == f.realization).all()),
    }
    if unit == "direct":
        v["totals_match_positions"] = bool(f.ftk.sum() == positions.ftk.sum()
                                           and f.realization.sum() == positions.realization.sum())
    return v


def build_matrix(features, set_name):
    """Matriks input model (belum di-scale) untuk populasi model."""
    pop = features[features.in_model_population == 1]
    return pop.index, pop[FEATURE_SETS[set_name]].to_numpy(float)


# ---------------------------------------------------------------- pipeline

def main():
    ds = dataset()
    src = OUTPUTS / "02_preprocessing" / ds["version"]
    OUT = OUTPUTS / "03_feature_engineering" / ds["version"]
    (OUT / "scalers").mkdir(parents=True, exist_ok=True)
    pos = pd.read_csv(src / "positions_clean.csv")
    orgs = pd.read_csv(src / "organizations_clean.csv")

    meta_cols = ["organization_id", "organization_name", "parent_organization_id", "organization_level",
                 "directorate_id", "directorate_name", "is_leaf", "n_children", "is_virtual_container"]
    meta = orgs[meta_cols].set_index("organization_id")
    units = orgs.loc[orgs.has_positions, "organization_id"]  # wadah virtual tidak punya jabatan

    desc = descendants_map(orgs)
    unit_maps = {
        "direct": pd.DataFrame({"unit_id": units, "organization_id": units}),
        "rollup": pd.DataFrame([(u, o) for u in units for o in desc[u]], columns=["unit_id", "organization_id"]),
    }

    log = {"dataset_version": ds["version"], "feature_version": FEATURE_VERSION, "units": {}}
    scaling_rows, results = [], {}
    for unit, umap in unit_maps.items():
        f = aggregate(pos, umap)
        f.index.name = "organization_id"
        f = meta.join(f, how="inner")
        f["in_model_population"] = ((f.has_active_positions == 1) & (~f.is_virtual_container)).astype(int)
        f["unit_definition"] = unit
        f["dataset_version"] = ds["version"]
        f["feature_version"] = FEATURE_VERSION
        checks = validate(f, pos, unit)
        if unit == "rollup":
            tops = orgs[orgs.parent_organization_id.isna() | ~orgs.parent_organization_id.isin(orgs.organization_id)]
            top_total = sum(pos[pos.organization_id.isin(desc[t])].ftk.sum() for t in tops.organization_id)
            checks["rollup_tops_cover_all_ftk"] = bool(top_total == pos.ftk.sum())
            checks["rollup_ge_direct"] = bool((f.ftk.values >= results["direct"].ftk.reindex(f.index).values).all())
        f.to_csv(OUT / f"features_{unit}.csv")
        results[unit] = f

        pop = f[f.in_model_population == 1]
        info = {"units": int(len(f)), "model_population": int(len(pop)),
                "excluded_no_active_positions": int((f.has_active_positions == 0).sum()),
                "validation": checks, "sets": {}}
        for sname, cols in FEATURE_SETS.items():
            X = pop[cols].to_numpy(float)
            n, d = X.shape
            info["sets"][sname] = {
                "features": cols, "d": d, "n": n, "meets_70d": n >= 70 * d,
                "matrix_rank": int(np.linalg.matrix_rank(X - X.mean(0))),
                "unique_vectors": int(len(np.unique(X, axis=0))),
                "nan_count": int(np.isnan(X).sum()),
            }
            for scname, cls in SCALERS.items():
                sc = cls().fit(X)
                joblib.dump({"scaler": sc, "features": cols, "unit": unit, "set": sname,
                             "dataset_version": ds["version"], "feature_version": FEATURE_VERSION},
                            OUT / "scalers" / f"{unit}_{sname}_{scname}.joblib")
                center = sc.mean_ if scname == "standard" else sc.center_
                for c, ce, s in zip(cols, center, sc.scale_):
                    raw_iqr = np.subtract(*np.percentile(pop[c], [75, 25]))
                    scaling_rows.append({"unit": unit, "set": sname, "scaler": scname, "feature": c,
                                         "center": round(float(ce), 6), "scale": round(float(s), 6),
                                         "iqr_is_zero": bool(raw_iqr == 0) if scname == "robust" else None})
        log["units"][unit] = info

    pd.DataFrame(scaling_rows).to_csv(OUT / "scaling_summary.csv", index=False)

    # Ringkasan deskriptif feature model (populasi model, direct) — bahan dokumen riset
    pop = results["direct"][results["direct"].in_model_population == 1]
    model_feats = sorted({c for cols in FEATURE_SETS.values() for c in cols})
    desc_stats = pop[model_feats + ["gap", "fulfillment_ratio"]].describe().T.round(4)
    desc_stats["n_unique"] = pop[model_feats + ["gap", "fulfillment_ratio"]].nunique()
    desc_stats["share_zero"] = (pop[model_feats + ["gap", "fulfillment_ratio"]] == 0).mean().round(4)
    desc_stats.to_csv(OUT / "feature_descriptives_direct.csv")
    log["excluded_orgs"] = results["direct"].loc[results["direct"].in_model_population == 0,
                                                  ["organization_name", "directorate_name", "position_rows"]] \
        .reset_index().to_dict("records")
    log["all_validation_passed"] = all(all(u["validation"].values()) for u in log["units"].values())

    schema = {
        "feature_version": FEATURE_VERSION, "dataset_version": ds["version"],
        "unit_of_analysis": "1 organisasi + 1 periode (PRD §17)",
        "unit_definitions": {"direct": "jabatan langsung (utama)", "rollup": "organisasi + sub-unit (sensitivitas)"},
        "model_population_rule": "has_active_positions = 1 dan bukan wadah virtual (D-017)",
        "feature_sets": FEATURE_SETS,
        "model_grade_groups": MODEL_GRADE_GROUPS,
        "scalers": {"default": "standard", "alternative": "robust"},
        "dictionary": {k: {"formula": a, "role": b, "reference": c} for k, (a, b, c) in DICTIONARY.items()},
    }
    (OUT / "feature_schema.json").write_text(json.dumps(schema, indent=2, ensure_ascii=False))
    (OUT / "feature_log.json").write_text(json.dumps(log, indent=2, ensure_ascii=False, default=str))

    for unit, info in log["units"].items():
        print(unit, {k: v for k, v in info.items() if k != "sets"})
        for s, d in info["sets"].items():
            print("   ", s, {k: v for k, v in d.items() if k != "features"})
    print("excluded:", len(log["excluded_orgs"]), "| all_validation_passed:", log["all_validation_passed"])
    if not log["all_validation_passed"]:
        raise SystemExit("VALIDASI GAGAL")


if __name__ == "__main__":
    main()
