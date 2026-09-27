import numpy as np
import pandas as pd

from s03_feature_engineering import (FEATURE_SETS, aggregate, balance_index, descendants_map, safe_ratio,
                                     validate)


def test_balance_index_bounds_and_zero_case():
    b = balance_index([0, 10, 0, 5], [0, 7, 3, 5])
    assert b[0] == 0.0
    assert np.isclose(b[1], -3 / 17)
    assert b[2] == 1.0
    assert b[3] == 0.0


def test_safe_ratio_returns_nan_on_zero_denominator():
    r = safe_ratio([90, 5], [100, 0])
    assert np.isclose(r[0], 0.9) and np.isnan(r[1])


def _positions():
    rows = [
        # org, id, ftk, real, grade_group
        ("P", 1, 1, 1, "MM"),
        ("P", 2, 0, 0, "SPESIALIS"),     # dormant: tidak dihitung jabatan aktif
        ("C1", 3, 3, 2, "GENERALIS"),
        ("C1", 4, 1, 0, "MD"),           # kosong
        ("C2", 5, 0, 2, "GENERALIS"),    # terisi tanpa formasi
    ]
    df = pd.DataFrame(rows, columns=["organization_id", "position_id", "ftk", "realization", "grade_group"])
    df["is_active"] = (df.ftk > 0) | (df.realization > 0)
    df["is_dormant"] = (df.ftk == 0) & (df.realization == 0)
    df["is_vacant"] = (df.ftk > 0) & (df.realization == 0)
    df["is_unbudgeted_filled"] = (df.ftk == 0) & (df.realization > 0)
    df["is_marked_position"] = False
    df["is_extreme_realization"] = False
    return df


def _orgs():
    return pd.DataFrame({"organization_id": ["P", "C1", "C2"], "parent_organization_id": [None, "P", "P"]})


def test_direct_aggregation_matches_prd_examples():
    pos = _positions()
    f = aggregate(pos, pd.DataFrame({"unit_id": ["P", "C1", "C2"], "organization_id": ["P", "C1", "C2"]}))
    c1 = f.loc["C1"]
    assert (c1.ftk, c1.realization, c1.gap) == (4, 2, 2)
    assert np.isclose(c1.fulfillment_ratio, 0.5) and np.isclose(c1.staffing_ratio, -0.5)
    assert c1.position_count == 2 and c1.vacant_position_count == 1
    assert np.isclose(c1.pct_GENERALIS, 0.5) and np.isclose(c1.pct_MD, 0.5)
    p = f.loc["P"]
    assert p.position_rows == 2 and p.position_count == 1 and p.dormant_position_count == 1
    assert p.pct_SPESIALIS == 0 and p.pct_MM == 1
    c2 = f.loc["C2"]
    assert np.isnan(c2.fulfillment_ratio) and c2.ftk_zero == 1 and c2.balance_index == 1.0
    assert c2.unbudgeted_filled_count == 1
    assert all(validate(f, pos, "direct").values())


def test_rollup_includes_descendants():
    pos, orgs = _positions(), _orgs()
    desc = descendants_map(orgs)
    assert sorted(desc["P"]) == ["C1", "C2", "P"] and desc["C1"] == ["C1"]
    umap = pd.DataFrame([(u, o) for u in desc for o in desc[u]], columns=["unit_id", "organization_id"])
    f = aggregate(pos, umap)
    assert f.loc["P", "ftk"] == 5 and f.loc["P", "realization"] == 5 and f.loc["P", "position_count"] == 4
    assert f.loc["C1", "ftk"] == 4  # daun tidak berubah
    assert all(validate(f, pos, "rollup").values())


def test_feature_sets_exclude_linearly_dependent_features():
    for cols in FEATURE_SETS.values():
        assert "gap" not in cols                       # D-009
        assert "staffing_ratio" not in cols and "fulfillment_ratio" not in cols  # D-003
        assert "pct_UNKNOWN" not in cols                # D-018 (closure komposisi)


def test_feature_sets_f2_resolve_eda_multicollinearity():
    assert "avg_realization_per_position" not in FEATURE_SETS["B"]   # D-020
    assert "pct_GENERALIS" not in FEATURE_SETS["C"]                  # D-020 (kategori referensi)
    assert set(FEATURE_SETS["B"]) <= set(FEATURE_SETS["C"])
