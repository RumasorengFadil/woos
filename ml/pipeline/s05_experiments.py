"""Tahap 5 — Eksperimen Model: K-Means, Hierarchical, DBSCAN (PRD §26–§36, §44, §71–§72).

Tiga algoritma dijalankan pada dataset, feature set, dan scaler yang SAMA (PRD §26):
    feature set  A, B, C, R  (F2, D-020)
    scaler       standard (utama), robust (pembanding) — D-022
    unit         direct, populasi model n = 1.280 (rollup = Tahap 6, sensitivitas)

Grid:
    K-Means        K = 2..8, n_init = 20, random_state = RANDOM_SEED        (PRD §28)
    Hierarchical   linkage ward / complete / average, K = 2..8           (PRD §32)
    DBSCAN         min_samples ∈ {5, 10, 20, 40}; eps dari kuantil k-distance (PRD §34)

Varian "unique" (D-009/D-025): clustering pada vektor feature unik tanpa bobot, label
dipetakan balik ke seluruh organisasi — menguji pengaruh titik kembar. (Varian berbobot
setara matematis dengan data penuh untuk K-Means & DBSCAN, sehingga tidak informatif.)

Tahap ini HANYA menjalankan & mengukur. Pemilihan model, stabilitas, kontrol artefak,
baseline, dan sensitivitas rollup/outlier adalah Tahap 6.

Output: ml/outputs/05_experiments/<dataset_version>/
    experiments.csv / experiments.json   registri seluruh run + metadata PRD §44
    labels.csv.gz                        label cluster per organisasi per run
    kdistance.csv, cophenetic.csv, elbow.csv
    figures/E01..E06

Jalankan:  ml/.venv/bin/python ml/pipeline/s05_experiments.py [--dataset=v2]
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import cophenet, dendrogram, fcluster, linkage
from scipy.spatial.distance import pdist
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import RobustScaler, StandardScaler

import viz_style as vs
from config import OUTPUTS, RANDOM_SEED, dataset
from s03_feature_engineering import FEATURE_SETS, FEATURE_VERSION

MODEL_VERSION = "v1"
K_RANGE = range(2, 9)
LINKAGES = ["ward", "complete", "average"]
MIN_SAMPLES = [5, 10, 20, 40]
EPS_QUANTILES = [0.50, 0.70, 0.80, 0.90, 0.95]
SCALERS = {"standard": StandardScaler, "robust": RobustScaler}
PREFIX = {"KMEANS": "KM", "HIERARCHICAL": "HC", "DBSCAN": "DB"}


# ---------------------------------------------------------------- fungsi murni (diuji)

def internal_metrics(X, labels, noise_label=-1):
    """Metrik internal. Noise (DBSCAN) dikeluarkan dari Silhouette/DBI/CH (PRD §36)."""
    labels = np.asarray(labels)
    mask = labels != noise_label
    clusters = np.unique(labels[mask])
    sizes = np.array([(labels == c).sum() for c in clusters])
    out = {"n_clusters": int(len(clusters)), "noise_count": int((~mask).sum()),
           "noise_share": round(float((~mask).mean()), 4),
           "min_cluster_share": round(float(sizes.min() / len(labels)), 4) if len(sizes) else None,
           "max_cluster_share": round(float(sizes.max() / len(labels)), 4) if len(sizes) else None,
           "cluster_sizes": sizes.tolist(),
           "size_entropy_norm": round(float(-(p := sizes / sizes.sum()) @ np.log(p) / np.log(len(sizes))), 4)
           if len(sizes) > 1 else None,
           "silhouette": None, "davies_bouldin": None, "calinski_harabasz": None}
    Xm, lm = X[mask], labels[mask]
    if len(clusters) >= 2 and len(clusters) < len(Xm):
        out["silhouette"] = round(float(silhouette_score(Xm, lm)), 4)
        out["davies_bouldin"] = round(float(davies_bouldin_score(Xm, lm)), 4)
        out["calinski_harabasz"] = round(float(calinski_harabasz_score(Xm, lm)), 2)
    return out


def knee_point(x, y):
    """Kneedle sederhana: titik dengan jarak terbesar ke garis penghubung ujung kurva."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    xn = (x - x.min()) / (np.ptp(x) or 1)
    yn = (y - y.min()) / (np.ptp(y) or 1)
    p1, p2 = np.array([xn[0], yn[0]]), np.array([xn[-1], yn[-1]])
    d = np.abs(np.cross(p2 - p1, np.column_stack([xn, yn]) - p1)) / (np.linalg.norm(p2 - p1) or 1)
    return int(np.argmax(d))


def eps_grid(X, min_samples, quantiles=EPS_QUANTILES, floor=0.05):
    """Kandidat eps = kuantil jarak ke tetangga ke-(min_samples − 1) yang > 0, plus knee."""
    k = max(1, min_samples - 1)
    dist = NearestNeighbors(n_neighbors=k + 1).fit(X).kneighbors(X)[0][:, k]
    pos = np.sort(dist[dist > 0])
    cands = [float(np.quantile(pos, q)) for q in quantiles] if len(pos) else []
    srt = np.sort(dist)
    cands.append(float(srt[knee_point(np.arange(len(srt)), srt)]))
    cands = sorted({round(max(c, floor), 3) for c in cands})
    return cands, np.sort(dist)


def map_back(unique_labels, inverse):
    return np.asarray(unique_labels)[inverse]


# ---------------------------------------------------------------- pipeline

def main():
    vs.apply()
    ds = dataset()
    fe = OUTPUTS / "03_feature_engineering" / ds["version"]
    OUT = OUTPUTS / "05_experiments" / ds["version"]
    FIG = OUT / "figures"
    FIG.mkdir(parents=True, exist_ok=True)
    feats = pd.read_csv(fe / "features_direct.csv", index_col=0)
    pop = feats[feats.in_model_population == 1]
    code_version = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:12]
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")

    registry, label_cols, counters = [], {}, {k: 0 for k in PREFIX}
    kdist_rows, coph_rows, elbow_rows, linkages_cache = [], [], [], {}

    def record(algo, fset, scaler, variant, params, X, labels, extra=None):
        counters[algo] += 1
        exp_id = f"EXP-{PREFIX[algo]}-{counters[algo]:03d}"
        m = internal_metrics(X, labels)
        row = {"experiment_id": exp_id, "model_name": algo, "model_version": MODEL_VERSION,
               "training_timestamp": ts, "dataset_version": ds["version"], "feature_version": FEATURE_VERSION,
               "unit": "direct", "feature_set": fset, "features_used": FEATURE_SETS[fset], "scaler": scaler,
               "variant": variant, "hyperparameters": params, "random_seed": RANDOM_SEED,
               "code_version": code_version, "n_samples": int(len(labels)), **m,
               "validation_status": "EXPERIMENT", **(extra or {})}
        registry.append(row)
        label_cols[exp_id] = np.asarray(labels, int)

    for fset, cols in FEATURE_SETS.items():
        raw = pop[cols].to_numpy(float)
        for sname, cls in SCALERS.items():
            X = cls().fit_transform(raw)
            U, inverse = np.unique(X, axis=0, return_inverse=True)
            inverse = inverse.ravel()
            variants = [("all", X, None)] + ([("unique", U, inverse)] if sname == "standard" else [])

            for variant, Xv, inv in variants:
                # ---- K-Means ----
                for k in K_RANGE:
                    km = KMeans(n_clusters=k, n_init=20, random_state=RANDOM_SEED).fit(Xv)
                    lab = km.labels_ if inv is None else map_back(km.labels_, inv)
                    record("KMEANS", fset, sname, variant, {"n_clusters": k, "n_init": 20}, X, lab,
                           {"inertia": round(float(km.inertia_), 4)})
                    if variant == "all":
                        elbow_rows.append({"feature_set": fset, "scaler": sname, "k": k, "inertia": km.inertia_})

                # ---- Hierarchical (scipy linkage = AgglomerativeClustering; satu pohon per konfigurasi) ----
                for method in LINKAGES:
                    Z = linkage(Xv, method=method, metric="euclidean")
                    if variant == "all":
                        c, _ = cophenet(Z, pdist(Xv))
                        coph_rows.append({"feature_set": fset, "scaler": sname, "linkage": method,
                                          "cophenetic_corr": round(float(c), 4)})
                        linkages_cache[(fset, sname, method)] = Z
                    for k in K_RANGE:
                        lab = fcluster(Z, t=k, criterion="maxclust") - 1
                        lab = lab if inv is None else map_back(lab, inv)
                        record("HIERARCHICAL", fset, sname, variant, {"linkage": method, "n_clusters": k}, X, lab)

                # ---- DBSCAN ----
                for ms in MIN_SAMPLES:
                    eps_list, srt = eps_grid(Xv, ms)
                    if variant == "all":
                        for q, v in zip(np.linspace(0, 1, 101), np.quantile(srt, np.linspace(0, 1, 101))):
                            kdist_rows.append({"feature_set": fset, "scaler": sname, "min_samples": ms,
                                               "quantile": round(q, 2), "k_distance": v})
                    for eps in eps_list:
                        db = DBSCAN(eps=eps, min_samples=ms).fit(Xv)
                        lab = db.labels_ if inv is None else map_back(db.labels_, inv)
                        record("DBSCAN", fset, sname, variant, {"eps": eps, "min_samples": ms}, X, lab)

    reg = pd.DataFrame(registry)
    reg.to_json(OUT / "experiments.json", orient="records", indent=1, force_ascii=False)
    flat = reg.copy()
    for c in ["features_used", "hyperparameters", "cluster_sizes"]:
        flat[c] = flat[c].map(json.dumps)
    flat.to_csv(OUT / "experiments.csv", index=False)
    labels = pd.DataFrame(label_cols, index=pop.index)
    labels.to_csv(OUT / "labels.csv.gz", compression="gzip")
    pd.DataFrame(kdist_rows).to_csv(OUT / "kdistance.csv", index=False)
    coph = pd.DataFrame(coph_rows)
    coph.to_csv(OUT / "cophenetic.csv", index=False)
    elbow = pd.DataFrame(elbow_rows)
    knees = {}
    for (fset, sname), g in elbow.groupby(["feature_set", "scaler"]):
        g = g.sort_values("k")
        knees[(fset, sname)] = int(g.k.iloc[knee_point(g.k, g.inertia)])
    elbow["elbow_k"] = [knees[(f, s)] for f, s in zip(elbow.feature_set, elbow.scaler)]
    elbow.to_csv(OUT / "elbow.csv", index=False)

    figures(reg, elbow, knees, pd.DataFrame(kdist_rows), coph, linkages_cache, FIG)

    summary = {"dataset_version": ds["version"], "feature_version": FEATURE_VERSION, "model_version": MODEL_VERSION,
               "code_version": code_version, "n_samples": int(len(pop)), "runs": int(len(reg)),
               "runs_by_algorithm": reg.model_name.value_counts().to_dict(),
               "runs_by_variant": reg.variant.value_counts().to_dict(),
               "elbow_k": {f"{f}/{s}": k for (f, s), k in knees.items()}}
    (OUT / "experiment_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=1))


def figures(reg, elbow, knees, kd, coph, Zs, FIG):
    sets = list(FEATURE_SETS)
    # E01 elbow
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.2))
    for ax, fset in zip(axes, sets):
        for k_, (sname, color) in enumerate([("standard", vs.SERIES[0]), ("robust", vs.SERIES[1])]):
            g = elbow[(elbow.feature_set == fset) & (elbow.scaler == sname)].sort_values("k")
            y = g.inertia / g.inertia.iloc[0]
            ax.plot(g.k, y, color=color, marker="o", markersize=4, label=sname)
            kk = knees[(fset, sname)]
            ax.scatter([kk], [y[g.k == kk].iloc[0]], s=70, facecolor="none", edgecolor=color, linewidth=1.5)
        ax.set_title(f"Set {fset}", loc="left"); ax.set_xlabel("K")
    axes[0].set_ylabel("inertia (relatif thd K=2)"); axes[0].legend()
    fig.suptitle("E01 — Elbow K-Means (lingkaran = elbow terdeteksi)", x=0.01, ha="left", y=1.03)
    fig.savefig(FIG / "E01_kmeans_elbow.png"); plt.close(fig)

    # E02/E03 silhouette & DBI vs K
    series = [("KMEANS", None, "K-Means"), ("HIERARCHICAL", "ward", "HC ward"),
              ("HIERARCHICAL", "complete", "HC complete"), ("HIERARCHICAL", "average", "HC average")]
    for tag, sname in [("E02", "standard"), ("E03", "robust")]:
        fig, axes = plt.subplots(2, 4, figsize=(14, 5.6), sharex=True)
        for j, fset in enumerate(sets):
            for k_, (algo, link, label) in enumerate(series):
                g = reg[(reg.model_name == algo) & (reg.feature_set == fset) & (reg.scaler == sname) &
                        (reg.variant == "all")].copy()
                if link:
                    g = g[g.hyperparameters.map(lambda h: h.get("linkage")) == link]
                g["k"] = g.hyperparameters.map(lambda h: h["n_clusters"])
                g = g.sort_values("k")
                axes[0, j].plot(g.k, g.silhouette, color=vs.SERIES[k_], marker="o", markersize=3.5, label=label)
                axes[1, j].plot(g.k, g.davies_bouldin, color=vs.SERIES[k_], marker="o", markersize=3.5, label=label)
            axes[0, j].set_title(f"Set {fset}", loc="left"); axes[1, j].set_xlabel("K")
        axes[0, 0].set_ylabel("Silhouette (↑)"); axes[1, 0].set_ylabel("Davies–Bouldin (↓)")
        axes[0, 0].legend(fontsize=7)
        fig.suptitle(f"{tag} — Silhouette & Davies–Bouldin vs K ({sname} scaler)", x=0.01, ha="left")
        fig.tight_layout(); fig.savefig(FIG / f"{tag}_metrics_vs_k_{sname}.png"); plt.close(fig)

    # E04 dendrogram (standard)
    fig, axes = plt.subplots(len(LINKAGES), 4, figsize=(15, 8.5))
    for i, method in enumerate(LINKAGES):
        for j, fset in enumerate(sets):
            ax = axes[i, j]
            dendrogram(Zs[(fset, "standard", method)], truncate_mode="lastp", p=30, ax=ax,
                       color_threshold=0, above_threshold_color=vs.SERIES[0], no_labels=True)
            c = coph[(coph.feature_set == fset) & (coph.scaler == "standard") & (coph.linkage == method)]
            ax.set_title(f"Set {fset} · {method} (cophenetic r = {c.cophenetic_corr.iloc[0]:.2f})", loc="left",
                         fontsize=8.5)
            ax.grid(False)
            if j == 0:
                ax.set_ylabel("jarak")
    fig.suptitle("E04 — Dendrogram (30 merge terakhir, StandardScaler)", x=0.01, ha="left")
    fig.tight_layout(); fig.savefig(FIG / "E04_dendrograms.png"); plt.close(fig)

    # E05 k-distance
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.2))
    for ax, fset in zip(axes, sets):
        for k_, ms in enumerate(MIN_SAMPLES):
            g = kd[(kd.feature_set == fset) & (kd.scaler == "standard") & (kd.min_samples == ms)]
            ax.plot(g["quantile"] * 100, g.k_distance, color=vs.SERIES[k_], label=f"min_samples={ms}")
        ax.set_title(f"Set {fset}", loc="left"); ax.set_xlabel("persentil organisasi")
    axes[0].set_ylabel("jarak ke tetangga ke-(min_samples−1)"); axes[0].legend(fontsize=7)
    fig.suptitle("E05 — Kurva k-distance DBSCAN (StandardScaler)", x=0.01, ha="left", y=1.03)
    fig.savefig(FIG / "E05_dbscan_kdistance.png"); plt.close(fig)

    # E06 DBSCAN: noise vs jumlah cluster
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.4), sharey=True)
    for ax, fset in zip(axes, sets):
        for k_, ms in enumerate(MIN_SAMPLES):
            g = reg[(reg.model_name == "DBSCAN") & (reg.feature_set == fset) & (reg.scaler == "standard") &
                    (reg.variant == "all")]
            g = g[g.hyperparameters.map(lambda h: h["min_samples"]) == ms]
            g = g.assign(eps=g.hyperparameters.map(lambda h: h["eps"])).sort_values("eps")
            ax.plot(g.n_clusters, g.noise_share * 100, color=vs.SERIES[k_], marker="o", markersize=4,
                    linewidth=1.2, label=f"min_samples={ms}")  # garis mengikuti eps naik
        ax.set_title(f"Set {fset}", loc="left"); ax.set_xlabel("jumlah cluster (tanpa noise)")
    axes[0].set_ylabel("% noise"); axes[0].legend(fontsize=7)
    fig.suptitle("E06 — DBSCAN: jumlah cluster vs % noise per konfigurasi (StandardScaler)", x=0.01, ha="left", y=1.03)
    fig.savefig(FIG / "E06_dbscan_noise_vs_clusters.png"); plt.close(fig)


if __name__ == "__main__":
    main()
