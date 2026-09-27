import numpy as np

from s05_experiments import eps_grid, internal_metrics, knee_point, map_back


def _blobs():
    rng = np.random.default_rng(0)
    return np.vstack([rng.normal(0, 0.1, (50, 2)), rng.normal(5, 0.1, (50, 2))])


def test_internal_metrics_separated_clusters():
    X = _blobs()
    m = internal_metrics(X, np.repeat([0, 1], 50))
    assert m["n_clusters"] == 2 and m["noise_count"] == 0
    assert m["silhouette"] > 0.9 and m["davies_bouldin"] < 0.1
    assert m["min_cluster_share"] == 0.5 and np.isclose(m["size_entropy_norm"], 1.0)


def test_internal_metrics_excludes_noise():
    X = _blobs()
    lab = np.repeat([0, 1], 50)
    lab[:5] = -1
    m = internal_metrics(X, lab)
    assert m["noise_count"] == 5 and m["noise_share"] == 0.05 and m["n_clusters"] == 2


def test_internal_metrics_single_cluster_has_no_silhouette():
    m = internal_metrics(_blobs(), np.zeros(100, int))
    assert m["silhouette"] is None and m["size_entropy_norm"] is None


def test_knee_point_on_elbow_curve():
    k = np.arange(2, 9)
    inertia = np.array([100, 40, 30, 27, 25, 24, 23])
    assert k[knee_point(k, inertia)] == 3


def test_eps_grid_positive_and_sorted():
    X = np.vstack([_blobs(), np.zeros((30, 2))])  # tambah titik kembar
    eps, dist = eps_grid(X, 5)
    assert all(e > 0 for e in eps) and eps == sorted(eps)
    assert (dist == 0).sum() >= 30


def test_map_back():
    assert list(map_back([7, 8], np.array([0, 1, 1, 0]))) == [7, 8, 8, 7]
