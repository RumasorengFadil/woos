import numpy as np
import pandas as pd
import pytest

from s07_interpretation import (CLUSTER_LABELS, describe_characteristics, profile_stats, relative_z,
                                verify_signatures)


def _pop():
    return pd.DataFrame({"c": [0, 0, 1, 1], "x": [1.0, 3.0, 10.0, 14.0]})


def test_profile_stats_prd39_statistics():
    s = profile_stats(_pop(), "c", ["x"])
    assert list(s.organization_count) == [2, 2]
    assert s.loc[0, "x_mean"] == 2 and s.loc[1, "x_median"] == 12 and s.loc[1, "x_max"] == 14
    assert {"x_min", "x_std"} <= set(s.columns)


def test_relative_z_and_characteristics_text():
    means = pd.DataFrame({"vacant_share": [0.9], "ftk": [3.0], "gap": [0.0]})
    z = relative_z(means, pd.Series({"vacant_share": 0.2, "ftk": 3.0, "gap": 0.0}),
                   pd.Series({"vacant_share": 0.3, "ftk": 2.0, "gap": 0.0}))
    text = describe_characteristics(z.iloc[0])
    assert text == ["Porsi jabatan kosong tinggi (+2.3 SD)"]   # gap SD=0 -> NaN dibuang; ftk z=0 di bawah ambang


def _stats_row(**kv):
    base = {"ftk_mean": 3, "balance_index_mean": 0, "vacant_share_mean": 0, "fulfillment_ratio_mean": 1,
            "avg_realization_per_position_mean": 1}
    base.update(kv)
    return pd.Series(base)


def _good_stats():
    return pd.DataFrame({
        0: _stats_row(ftk_mean=0.1, balance_index_mean=0.9, fulfillment_ratio_mean=3.6),
        1: _stats_row(vacant_share_mean=0.37, fulfillment_ratio_mean=0.88),
        2: _stats_row(vacant_share_mean=0.0, fulfillment_ratio_mean=1.07),
        3: _stats_row(vacant_share_mean=0.94, fulfillment_ratio_mean=0.05),
        4: _stats_row(fulfillment_ratio_mean=1.45, avg_realization_per_position_mean=2.5),
    }).T


def test_signatures_accept_expected_profiles():
    assert verify_signatures(_good_stats())


def test_signatures_detect_swapped_cluster_ids():
    s = _good_stats()
    s.loc[[3, 4]] = s.loc[[4, 3]].to_numpy()   # label tertukar setelah refit
    with pytest.raises(ValueError):
        verify_signatures(s)


def test_every_label_has_business_fields():
    for spec in CLUSTER_LABELS.values():
        assert spec["code"] and spec["label"] and spec["interpretation"] and spec["prd_archetype"]
