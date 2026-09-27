import numpy as np
import pandas as pd

from s06_evaluation import (bootstrap_stability, cramers_v, eligible, eta_squared, gap_sign_baseline,
                            rank_aggregate)


def _reg(**over):
    base = {"variant": "all", "n_clusters": 3, "max_cluster_share": 0.6, "min_cluster_share": 0.1,
            "noise_share": 0.0, "silhouette": 0.5}
    base.update(over)
    return pd.DataFrame([base])


def test_eligibility_rules_d027():
    assert eligible(_reg())[0].iloc[0]
    for over, reason in [({"variant": "unique"}, "variant_not_all"), ({"n_clusters": 12}, "clusters_out_of_2_8"),
                         ({"max_cluster_share": 0.97}, "degenerate_max_ge_95pct"),
                         ({"min_cluster_share": 0.01}, "min_cluster_lt_2pct"), ({"noise_share": 0.2}, "noise_gt_15pct"),
                         ({"silhouette": 1.0}, "silhouette_artifact_ge_0_99")]:
        ok, why = eligible(_reg(**over))
        assert not ok.iloc[0] and why.iloc[0] == reason


def test_cramers_v_independent_vs_identical():
    rng = np.random.default_rng(0)
    a = rng.integers(0, 3, 3000)
    assert cramers_v(a, rng.integers(0, 4, 3000)) < 0.05
    assert cramers_v(a, a) > 0.99


def test_eta_squared_excludes_noise():
    v = np.array([0, 0, 10, 10, 99.0])
    lab = np.array([0, 0, 1, 1, -1])
    assert np.isclose(eta_squared(v, lab), 1.0)


def test_rank_aggregate_direction():
    df = pd.DataFrame({"silhouette": [0.9, 0.1], "davies_bouldin": [0.2, 0.9]})
    _, score = rank_aggregate(df, {"silhouette": "max", "davies_bouldin": "min"})
    assert score.idxmin() == 0


def test_gap_sign_baseline():
    assert list(gap_sign_baseline([3, 0, -2])) == [1, 0, -1]


def test_bootstrap_stability_high_for_clear_structure():
    rng = np.random.default_rng(1)
    X = np.vstack([rng.normal(0, .1, (60, 2)), rng.normal(4, .1, (60, 2))])
    ref = np.repeat([0, 1], 60)
    mean, sd = bootstrap_stability("KMEANS", {"n_clusters": 2}, X, ref, n_boot=5)
    assert mean > 0.99 and sd < 0.01


def test_balance_pole_rule_and_noise_excluded_ari():
    from s06_evaluation import ari_excluding_noise, balance_pole_rule
    poles = balance_pole_rule([-1, 1, 0.2, -1, 1, 0])
    assert list(poles) == [0, 1, 2, 0, 1, 2]
    lab = np.array([5, 6, 7, 5, 6, -1])          # identik dengan aturan kecuali 1 noise
    assert np.isclose(ari_excluding_noise(poles, lab), 1.0)
