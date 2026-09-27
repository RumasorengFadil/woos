import numpy as np

from s04_eda import epsilon_squared, log1p_counts, mahalanobis_sq, vif


def test_vif_independent_features_near_one():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(2000, 3))
    assert all(abs(v - 1) < 0.05 for v in vif(X, ["a", "b", "c"]).values())


def test_vif_detects_exact_and_near_collinearity():
    rng = np.random.default_rng(1)
    a, b = rng.normal(size=500), rng.normal(size=500)
    exact = vif(np.column_stack([a, b, a + b]), ["a", "b", "ab"])
    assert np.isinf(exact["ab"])
    near = vif(np.column_stack([a, b, a + b + rng.normal(scale=0.1, size=500)]), ["a", "b", "ab"])
    assert near["ab"] > 50


def test_epsilon_squared_bounds():
    groups = np.repeat([0, 1, 2], 50)
    strong, p = epsilon_squared(groups * 10.0 + np.random.default_rng(2).normal(size=150), groups)
    none, _ = epsilon_squared(np.ones(150), groups)
    assert strong > 0.8 and p < 1e-10
    assert none == 0.0


def test_mahalanobis_flags_planted_outlier():
    rng = np.random.default_rng(3)
    Z = rng.normal(size=(300, 3))
    Z[0] = [8, -8, 8]
    d2 = mahalanobis_sq(Z)
    assert d2.argmax() == 0


def test_log1p_counts_only_transforms_count_features():
    import pandas as pd
    f = pd.DataFrame({"ftk": [0, 3], "balance_index": [-1.0, 0.5]})
    out = log1p_counts(f, ["ftk", "balance_index"])
    assert np.allclose(out.ftk, np.log1p([0, 3])) and np.allclose(out.balance_index, [-1.0, 0.5])
