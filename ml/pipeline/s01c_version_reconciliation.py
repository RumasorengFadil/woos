"""Tahap 1c — Rekonsiliasi dataset v1 (DLMHC) vs v2 (seluruh Kantor Pusat).

v2 memuat seluruh jabatan v1 dengan tanggal periode yang sama. Script ini memastikan
apakah v2 adalah superset konsisten dari v1 dan mencatat setiap nilai yang berubah.

Output: ml/outputs/01c_version_reconciliation/
    reconciliation.json, changed_positions.csv

Jalankan:  ml/.venv/bin/python ml/pipeline/s01c_version_reconciliation.py
"""
import json

import pandas as pd

from config import COLUMN_MAP, DATASETS, OUTPUTS

OUT = OUTPUTS / "01c_version_reconciliation"
OUT.mkdir(parents=True, exist_ok=True)
COMPARE = ["organization_name", "parent_name", "organization_level", "position_name", "grade",
           "ftk", "realization", "period"]


def main():
    v1 = pd.read_csv(DATASETS["v1"]["file"]).rename(columns=COLUMN_MAP)
    v2 = pd.read_csv(DATASETS["v2"]["file"]).rename(columns=COLUMN_MAP)
    m = v1.merge(v2, on="position_id", how="left", suffixes=("_v1", "_v2"), indicator=True)
    both = m[m._merge == "both"]
    diff_counts = {c: int((both[f"{c}_v1"].fillna("").astype(str) != both[f"{c}_v2"].fillna("").astype(str)).sum())
                   for c in COMPARE}
    changed = both[both.realization_v1 != both.realization_v2]
    changed = changed[["position_id", "organization_id_v1", "organization_id_v2", "organization_name_v1",
                       "organization_level_v1", "position_name_v1", "grade_v1", "ftk_v1",
                       "realization_v1", "realization_v2"]].assign(
        delta=lambda d: d.realization_v2 - d.realization_v1)
    changed.to_csv(OUT / "changed_positions.csv", index=False)

    id_map = both[["organization_id_v1", "organization_id_v2"]].drop_duplicates()
    summary = {
        "v1": DATASETS["v1"]["version"], "v2": DATASETS["v2"]["version"],
        "v1_positions": int(len(v1)), "v1_positions_found_in_v2": int(len(both)),
        "v1_positions_missing_in_v2": int((m._merge == "left_only").sum()),
        "field_differences": diff_counts,
        "realization_changed_positions": int(len(changed)),
        "realization_total_v1": int(both.realization_v1.sum()),
        "realization_total_v2_same_positions": int(both.realization_v2.sum()),
        "realization_delta": int(changed.delta.sum()),
        "delta_distribution": changed.delta.value_counts().sort_index().to_dict(),
        "organization_id_renumbered": bool((id_map.organization_id_v1 != id_map.organization_id_v2).any()),
        "organization_id_mapping_is_one_to_one": bool(id_map.organization_id_v1.is_unique and id_map.organization_id_v2.is_unique),
        "v1_org_ids_in_v2": sorted(id_map.organization_id_v2.unique().tolist()),
    }
    (OUT / "reconciliation.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print({k: v for k, v in summary.items() if k != "v1_org_ids_in_v2"})
    print(changed[["organization_name_v1", "position_name_v1", "ftk_v1", "realization_v1", "realization_v2"]].to_string(index=False))


if __name__ == "__main__":
    main()
