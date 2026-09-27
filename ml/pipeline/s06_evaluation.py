"""Tahap 6 — Evaluasi, Perbandingan & Pemilihan Model (PRD §36–§38, §45, §55).

Kriteria ditetapkan SEBELUM peringkat dilihat (D-027 kelayakan, D-028 multi-kriteria).

Langkah:
    1. Filter kelayakan run Tahap 5 (D-027)
    2. Hitung 6 kriteria: silhouette, DBI, stabilitas bootstrap (ARI), keseimbangan,
       relevansi workforce (η² balance_index & vacant_share), Cramér's V × level
       + pelaporan: Cramér's V × direktorat, ARI vs baseline tanda gap
    3. Agregasi peringkat bobot sama + sensitivitas bobot
    4. Model terbaik per algoritma -> tabel perbandingan PRD §55
    5. Robustness model terpilih: seed, rollup (D-001), tanpa outlier (D-024), varian unique
    6. Status: SELECTED_CANDIDATE (APPROVED setelah validasi bisnis Tahap 7, PRD §45)

Output: ml/outputs/06_evaluation/<dataset_version>/
    eligible_runs.csv, model_comparison.csv, selection.json, robustness.json,
    rank_sensitivity.csv, baseline.csv, selected_labels.csv, figures/V01..V05

Jalankan:  ml/.venv/bin/python ml/pipeline/s06_evaluation.py [--dataset=v2]
"""
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.stats import chi2_contingency
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import RobustScaler, StandardScaler

import viz_style as vs
from config import OUTPUTS, RANDOM_SEED, dataset
from s03_feature_engineering import FEATURE_SETS

SCALERS = {"standard": StandardScaler, "robust": RobustScaler}
N_BOOT, BOOT_FRAC = 50, 0.8
CRITERIA = {"silhouette": "max", "davies_bouldin": "min", "stability_ari": "max",
            "size_entropy_norm": "max", "workforce_eta2": "max", "cramers_v_level": "min"}
ALGO_LABEL = {"KMEANS": "K-Means", "HIERARCHICAL": "Hierarchical", "DBSCAN": "DBSCAN"}


# ---------------------------------------------------------------- fungsi murni (diuji)

def eligible(reg):
    """Filter kelayakan D-027. Mengembalikan mask boolean dan alasan penolakan per run."""
    reasons = pd.Series("", index=reg.index)
    rules = [
        ("variant_not_all", reg.variant != "all"),
        ("clusters_out_of_2_8", (reg.n_clusters < 2) | (reg.n_clusters > 8)),
        ("degenerate_max_ge_95pct", reg.max_cluster_share.fillna(1) >= 0.95),
        ("min_cluster_lt_2pct", reg.min_cluster_share.fillna(0) < 0.02),
        ("noise_gt_15pct", reg.noise_share > 0.15),
        ("silhouette_artifact_ge_0_99", reg.silhouette.fillna(0) >= 0.99),
    ]
    for name, cond in rules:
        reasons[cond & (reasons == "")] = name
    return reasons == "", reasons


def cramers_v(a, b):
    """Cramér's V dengan koreksi bias (Bergsma, 2013). 0 = independen, 1 = asosiasi sempurna."""
    ct = pd.crosstab(np.asarray(a), np.asarray(b)).to_numpy()
    if ct.shape[0] < 2 or ct.shape[1] < 2:
        return 0.0
    chi2 = chi2_contingency(ct, correction=False)[0]
    n = ct.sum()
    r, k = ct.shape
    phi2 = max(0.0, chi2 / n - (k - 1) * (r - 1) / (n - 1))
    rc, kc = r - (r - 1) ** 2 / (n - 1), k - (k - 1) ** 2 / (n - 1)
    den = min(kc - 1, rc - 1)
    return float(np.sqrt(phi2 / den)) if den > 0 else 0.0


def eta_squared(values, labels, noise_label=-1):
    """Proporsi varians feature yang dijelaskan cluster (noise dikecualikan)."""
    values, labels = np.asarray(values, float), np.asarray(labels)
    m = labels != noise_label
    v, lab = values[m], labels[m]
    ss_tot = ((v - v.mean()) ** 2).sum()
    if ss_tot == 0:
        return 0.0
    ss_b = sum((lab == c).sum() * (v[lab == c].mean() - v.mean()) ** 2 for c in np.unique(lab))
    return float(ss_b / ss_tot)


def rank_aggregate(df, criteria=CRITERIA):
    """Peringkat per kriteria (1 = terbaik, ties = rata-rata) lalu rata-rata bobot sama."""
    ranks = pd.DataFrame({c: df[c].rank(ascending=(d == "min"), method="average") for c, d in criteria.items()})
    return ranks, ranks.mean(axis=1)


def gap_sign_baseline(gap):
    return np.sign(np.asarray(gap)).astype(int)


def balance_pole_rule(balance):
    """Aturan satu-feature pembanding (D-029, post-hoc): −1 (kosong) / +1 (tanpa formasi) / lainnya."""
    b = np.asarray(balance, float)
    return np.where(b == -1, 0, np.where(b == 1, 1, 2))


def ari_excluding_noise(ref, lab, noise_label=-1):
    ref, lab = np.asarray(ref), np.asarray(lab)
    m = lab != noise_label
    return float(adjusted_rand_score(ref[m], lab[m]))


def fit_predict(algo, params, X, seed=RANDOM_SEED):
    if algo == "KMEANS":
        return KMeans(n_clusters=params["n_clusters"], n_init=10, random_state=seed).fit_predict(X)
    if algo == "HIERARCHICAL":
        return fcluster(linkage(X, method=params["linkage"]), t=params["n_clusters"], criterion="maxclust") - 1
    if algo == "DBSCAN":
        return DBSCAN(eps=params["eps"], min_samples=params["min_samples"]).fit_predict(X)
    raise ValueError(algo)


def bootstrap_stability(algo, params, X, ref, n_boot=N_BOOT, frac=BOOT_FRAC, seed=RANDOM_SEED):
    """Rata-rata & sd ARI antara label referensi dan refit pada subsample (tanpa pengembalian)."""
    rng = np.random.default_rng(seed)
    n = len(X)
    scores = []
    for b in range(n_boot):
        idx = rng.choice(n, int(frac * n), replace=False)
        lab = fit_predict(algo, params, X[idx], seed=seed + b)
        scores.append(adjusted_rand_score(ref[idx], lab))
    return float(np.mean(scores)), float(np.std(scores))


# ---------------------------------------------------------------- pipeline

def main():
    vs.apply()
    ds = dataset()
    ex = OUTPUTS / "05_experiments" / ds["version"]
    fe = OUTPUTS / "03_feature_engineering" / ds["version"]
    eda = OUTPUTS / "04_eda" / ds["version"]
    OUT = OUTPUTS / "06_evaluation" / ds["version"]
    FIG = OUT / "figures"
    FIG.mkdir(parents=True, exist_ok=True)

    reg = pd.read_json(ex / "experiments.json")
    labels = pd.read_csv(ex / "labels.csv.gz", index_col=0)
    feats = pd.read_csv(fe / "features_direct.csv", index_col=0)
    pop = feats.loc[labels.index]
    rollup = pd.read_csv(fe / "features_rollup.csv", index_col=0)
    outliers = set(pd.read_csv(eda / "outliers_multivariate_setB.csv", index_col=0).index)
    X_cache = {(f, s): SCALERS[s]().fit_transform(pop[c].to_numpy(float))
               for f, c in FEATURE_SETS.items() for s in SCALERS}
    baseline = gap_sign_baseline(pop.gap)
    poles = balance_pole_rule(pop.balance_index)

    # ---------- 1. kelayakan ----------
    ok, reasons = eligible(reg)
    reg["eligible"], reg["rejection_reason"] = ok, reasons
    funnel = reasons.replace("", "ELIGIBLE").value_counts()
    cand = reg[ok].copy()

    # ---------- 2. kriteria ----------
    rows = []
    for _, r in cand.iterrows():
        X = X_cache[(r.feature_set, r.scaler)]
        lab = labels[r.experiment_id].to_numpy()
        mean_ari, sd_ari = bootstrap_stability(r.model_name, r.hyperparameters, X, lab)
        rows.append({
            "experiment_id": r.experiment_id, "stability_ari": round(mean_ari, 4), "stability_ari_sd": round(sd_ari, 4),
            "workforce_eta2": round(np.mean([eta_squared(pop.balance_index, lab), eta_squared(pop.vacant_share, lab)]), 4),
            "eta2_balance_index": round(eta_squared(pop.balance_index, lab), 4),
            "eta2_vacant_share": round(eta_squared(pop.vacant_share, lab), 4),
            "cramers_v_level": round(cramers_v(lab, pop.organization_level), 4),
            "cramers_v_directorate": round(cramers_v(lab, pop.directorate_name), 4),
            "ari_vs_gap_sign": round(adjusted_rand_score(baseline, lab), 4),
            "ari_vs_balance_poles": round(ari_excluding_noise(poles, lab), 4),
        })
    cand = cand.merge(pd.DataFrame(rows), on="experiment_id")
    ranks, score = rank_aggregate(cand)
    cand["rank_score"] = score.round(3)
    cand["overall_rank"] = cand.rank_score.rank(method="min").astype(int)
    for c in CRITERIA:
        cand[f"rank_{c}"] = ranks[c]
    cand = cand.sort_values("rank_score")
    cand["params"] = cand.hyperparameters.map(lambda h: ", ".join(f"{k}={v}" for k, v in h.items() if k != "n_init"))
    keep = ["experiment_id", "model_name", "feature_set", "scaler", "params", "n_clusters", "noise_share",
            "silhouette", "davies_bouldin", "stability_ari", "stability_ari_sd", "size_entropy_norm",
            "min_cluster_share", "max_cluster_share", "workforce_eta2", "eta2_balance_index", "eta2_vacant_share",
            "cramers_v_level", "cramers_v_directorate", "ari_vs_gap_sign", "ari_vs_balance_poles", "rank_score",
            "overall_rank"]
    cand[keep].to_csv(OUT / "eligible_runs.csv", index=False)

    # ---------- 3. sensitivitas bobot ----------
    sens = []
    variants = {"all_6_criteria": CRITERIA, "metrics_only (silhouette+DBI)":
                {"silhouette": "max", "davies_bouldin": "min"}}
    for c in CRITERIA:
        variants[f"without_{c}"] = {k: v for k, v in CRITERIA.items() if k != c}
    for name, crit in variants.items():
        _, sc = rank_aggregate(cand, crit)
        top = cand.loc[sc.idxmin()]
        best_by_algo = {a: cand.loc[sc[cand.model_name == a].idxmin(), "experiment_id"]
                        for a in cand.model_name.unique()}
        sens.append({"variant": name, "top_experiment": top.experiment_id, "top_model": top.model_name,
                     "top_config": f"{top.feature_set}/{top.scaler}/{top.params}", **{f"best_{k}": v for k, v in best_by_algo.items()}})
    sens = pd.DataFrame(sens)
    sens.to_csv(OUT / "rank_sensitivity.csv", index=False)

    # ---------- 4. terbaik per algoritma -> PRD §55 ----------
    best = cand.groupby("model_name").head(1).set_index("model_name")
    selected = cand.iloc[0]
    comp = pd.DataFrame({ALGO_LABEL[a]: {
        "Experiment": r.experiment_id, "Konfigurasi": f"set {r.feature_set} / {r.scaler} / {r.params}",
        "Silhouette": r.silhouette, "Davies-Bouldin": r.davies_bouldin, "Cluster Count": int(r.n_clusters),
        "Noise": f"{r.noise_share:.1%}", "Stability (ARI)": f"{r.stability_ari:.3f} ± {r.stability_ari_sd:.3f}",
        "Balance (entropy)": r.size_entropy_norm, "Workforce η²": r.workforce_eta2,
        "Cramér's V level": r.cramers_v_level, "Cramér's V direktorat": r.cramers_v_directorate,
        "ARI vs tanda gap": r.ari_vs_gap_sign, "Rank score": r.rank_score, "Overall rank": int(r.overall_rank),
        "Validation": "SELECTED_CANDIDATE" if r.experiment_id == selected.experiment_id else "EXPERIMENT",
    } for a, r in best.iterrows()})
    comp = comp[[ALGO_LABEL[a] for a in ["KMEANS", "HIERARCHICAL", "DBSCAN"] if a in best.index]]
    comp.to_csv(OUT / "model_comparison.csv")

    # ---------- baseline tanda gap ----------
    base_rows = []
    for (f, s), X in X_cache.items():
        base_rows.append({"feature_set": f, "scaler": s, "baseline": "gap_sign(-/0/+)",
                          "silhouette": round(float(silhouette_score(X, baseline)), 4),
                          "group_sizes": json.dumps({int(k): int(v) for k, v in zip(*np.unique(baseline, return_counts=True))})})
    pd.DataFrame(base_rows).to_csv(OUT / "baseline.csv", index=False)

    # ---------- 5. robustness: model terbaik tiap algoritma ----------
    def robustness(r, algo):
        lab = labels[r.experiment_id].to_numpy()
        cols = FEATURE_SETS[r.feature_set]
        X = X_cache[(r.feature_set, r.scaler)]
        res = {"experiment_id": r.experiment_id, "model_name": algo}
        if algo == "KMEANS":
            seeds = [adjusted_rand_score(lab, fit_predict("KMEANS", r.hyperparameters, X, seed=s)) for s in range(100, 110)]
            res["seed_stability_ari_mean"] = round(float(np.mean(seeds)), 4)
            res["seed_stability_ari_min"] = round(float(np.min(seeds)), 4)
        rp = rollup.loc[pop.index]                                          # D-001, irisan 1.280 org
        Xr = SCALERS[r.scaler]().fit_transform(rp[cols].to_numpy(float))
        res["rollup_ari_vs_direct"] = round(float(adjusted_rand_score(lab, fit_predict(algo, r.hyperparameters, Xr))), 4)
        keep_mask = ~pop.index.isin(outliers)                               # D-024
        Xo = SCALERS[r.scaler]().fit_transform(pop.loc[keep_mask, cols].to_numpy(float))
        res["without_outliers_n_removed"] = int((~keep_mask).sum())
        res["without_outliers_ari_vs_full"] = round(float(adjusted_rand_score(
            lab[keep_mask], fit_predict(algo, r.hyperparameters, Xo))), 4)
        u = reg[(reg.variant == "unique") & (reg.model_name == algo) & (reg.feature_set == r.feature_set) &
                (reg.scaler == r.scaler) & (reg.hyperparameters.map(json.dumps) == json.dumps(r.hyperparameters))]
        if len(u):
            res["unique_variant_experiment"] = u.experiment_id.iloc[0]
            res["unique_variant_ari_vs_all"] = round(float(adjusted_rand_score(lab, labels[u.experiment_id.iloc[0]])), 4)
        return res

    sel_lab = labels[selected.experiment_id].to_numpy()
    Xs = X_cache[(selected.feature_set, selected.scaler)]
    ids = best.experiment_id.to_dict()
    rob = {"selected": selected.experiment_id,
           "best_per_algorithm": {ALGO_LABEL[a]: robustness(r, a) for a, r in best.iterrows()},
           "ari_between_best_models": {f"{ALGO_LABEL[a]} vs {ALGO_LABEL[b]}":
                                       round(float(adjusted_rand_score(labels[ids[a]], labels[ids[b]])), 4)
                                       for i, a in enumerate(ids) for b in list(ids)[i + 1:]}}
    (OUT / "robustness.json").write_text(json.dumps(rob, indent=2))

    # profil ringkas model terbaik tiap algoritma (bahan Tahap 7; tanpa label bisnis)
    prof_cols = ["ftk", "realization", "gap", "balance_index", "fulfillment_ratio", "vacant_share",
                 "position_count", "avg_realization_per_position"]
    prof = []
    for a, r in best.iterrows():
        g = pop.assign(cluster=labels[r.experiment_id]).groupby("cluster")
        t = g[prof_cols].median().add_prefix("median_")
        t.insert(0, "n", g.size()); t.insert(1, "share", (g.size() / len(pop)).round(4))
        t["share_gap_pos"] = g.gap.apply(lambda v: (v > 0).mean()).round(3)
        t["share_gap_neg"] = g.gap.apply(lambda v: (v < 0).mean()).round(3)
        prof.append(t.reset_index().assign(experiment_id=r.experiment_id, model=ALGO_LABEL[a]))
    pd.concat(prof).round(3).to_csv(OUT / "finalist_cluster_profiles.csv", index=False)

    out = pop[["organization_name", "directorate_name", "organization_level"]].copy()
    for a, r in best.iterrows():
        out[f"cluster_{ALGO_LABEL[a].lower().replace('-', '')}"] = labels[r.experiment_id]
    out["cluster_selected"] = sel_lab
    out["gap_sign_baseline"] = baseline
    out.to_csv(OUT / "selected_labels.csv")

    # ---------- diagnostik post-hoc D-029: segmentasi yang identik dengan aturan satu feature ----------
    nontrivial = cand[cand.ari_vs_balance_poles < 0.90].copy()
    _, sc2 = rank_aggregate(nontrivial)
    nontrivial["rank_score_posthoc"] = sc2.round(3)
    nontrivial = nontrivial.sort_values("rank_score_posthoc")
    nontrivial[keep + ["rank_score_posthoc"]].to_csv(OUT / "eligible_runs_nontrivial_posthoc.csv", index=False)
    posthoc = {
        "rule": "D-029 (post-hoc, PROPOSED): keluarkan run dengan ARI (tanpa noise) terhadap aturan "
                "balance_index −1/+1/lainnya ≥ 0,90",
        "n_trivial": int(len(cand) - len(nontrivial)),
        "trivial_by_algorithm": cand[cand.ari_vs_balance_poles >= 0.90].model_name.value_counts().to_dict(),
        "top_posthoc": nontrivial.iloc[0][keep + ["rank_score_posthoc"]].to_dict(),
        "best_posthoc_by_algorithm": nontrivial.groupby("model_name").head(1)[
            ["experiment_id", "model_name", "feature_set", "scaler", "params", "rank_score_posthoc"]].to_dict("records"),
        "selected_rule_D028_ari_vs_poles": float(selected.ari_vs_balance_poles),
    }
    (OUT / "selection_posthoc_D029.json").write_text(json.dumps(posthoc, indent=2, ensure_ascii=False, default=str))

    selection = {
        "dataset_version": ds["version"], "selection_rule": "D-027 + D-028 (rank aggregation, 6 kriteria, bobot sama)",
        "eligibility_funnel": funnel.to_dict(), "n_eligible": int(len(cand)),
        "eligible_by_algorithm": cand.model_name.value_counts().to_dict(),
        "selected": {k: (v if not isinstance(v, (np.integer, np.floating)) else v.item())
                     for k, v in selected[keep].to_dict().items()},
        "selected_hyperparameters": selected.hyperparameters,
        "validation_status": "SELECTED_CANDIDATE",
        "top10": cand[keep].head(10).to_dict("records"),
        "rank_sensitivity_top_changes": int((sens.top_experiment != selected.experiment_id).sum()),
    }
    (OUT / "selection.json").write_text(json.dumps(selection, indent=2, ensure_ascii=False, default=str))

    figures(reg, funnel, cand, best, selected, pop, Xs, sel_lab, sens, FIG)

    print(funnel.to_string()); print("eligible by algo:", selection["eligible_by_algorithm"])
    print(cand[keep].head(15).to_string(index=False))
    print(comp.to_string())
    print(sens.to_string(index=False))
    print(json.dumps(rob, indent=1))
    print(json.dumps(posthoc, indent=1, default=str))
    print(nontrivial[keep + ["rank_score_posthoc"]].head(10).to_string(index=False))
    print(pd.DataFrame(base_rows).to_string(index=False))


def figures(reg, funnel, cand, best, selected, pop, Xs, sel_lab, sens, FIG):
    # V01 funnel
    order = ["variant_not_all", "clusters_out_of_2_8", "degenerate_max_ge_95pct", "min_cluster_lt_2pct",
             "noise_gt_15pct", "silhouette_artifact_ge_0_99", "ELIGIBLE"]
    f = funnel.reindex(order).fillna(0)
    fig, ax = plt.subplots(figsize=(7, 3.2))
    colors = [vs.NEUTRAL] * (len(f) - 1) + [vs.SERIES[0]]
    ax.barh(f.index[::-1], f.values[::-1], color=colors[::-1], edgecolor=vs.SURFACE)
    for y, v in enumerate(f.values[::-1]):
        ax.text(v + 4, y, str(int(v)), va="center", fontsize=7.5, color=vs.TEXT_2)
    ax.set_xlabel("jumlah run"); ax.set_title(f"V01 — Kelayakan run (D-027): {int(f['ELIGIBLE'])} dari {len(reg)} layak", loc="left")
    fig.savefig(FIG / "V01_eligibility_funnel.png"); plt.close(fig)

    # V02 silhouette vs stabilitas
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    for k, a in enumerate(["KMEANS", "HIERARCHICAL", "DBSCAN"]):
        g = cand[cand.model_name == a]
        ax.scatter(g.silhouette, g.stability_ari, s=26, color=vs.SERIES[k], alpha=0.8, edgecolor=vs.SURFACE,
                   linewidth=1, label=f"{ALGO_LABEL[a]} (n={len(g)})")
    ax.scatter([selected.silhouette], [selected.stability_ari], s=160, facecolor="none", edgecolor=vs.TEXT, linewidth=1.5)
    ax.annotate(f"terpilih: {selected.experiment_id}", (selected.silhouette, selected.stability_ari), xytext=(10, -14),
                textcoords="offset points", fontsize=7.5)
    ax.set_xlabel("Silhouette"); ax.set_ylabel("Stabilitas bootstrap (ARI)"); ax.legend(loc="lower left")
    ax.set_title("V02 — Kualitas vs stabilitas run layak", loc="left")
    fig.savefig(FIG / "V02_silhouette_vs_stability.png"); plt.close(fig)

    # V03 heatmap kriteria top 12
    top = cand.head(12)
    crit_cols = [f"rank_{c}" for c in CRITERIA]
    M = top[crit_cols].to_numpy()
    fig, ax = plt.subplots(figsize=(8.4, 5))
    im = ax.imshow(M, cmap=vs.SEQUENTIAL.reversed(), aspect="auto")
    ax.set_xticks(range(len(CRITERIA))); ax.set_xticklabels(list(CRITERIA), rotation=25, ha="right")
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels([f"#{int(r.overall_rank)} {r.experiment_id} · {r.feature_set}/{r.scaler} · {r.params}" for _, r in top.iterrows()],
                       fontsize=7)
    ax.grid(False)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, f"{M[i, j]:.0f}", ha="center", va="center", fontsize=7,
                    color="white" if M[i, j] < M.max() * 0.4 else vs.TEXT)
    fig.colorbar(im, ax=ax, fraction=0.03, label="peringkat (1 = terbaik)")
    ax.set_title("V03 — Peringkat per kriteria, 12 run teratas", loc="left")
    fig.savefig(FIG / "V03_criteria_ranks_top12.png"); plt.close(fig)

    # V04 perbandingan model terbaik per algoritma (small multiples)
    metrics = [("silhouette", "Silhouette ↑"), ("davies_bouldin", "Davies–Bouldin ↓"), ("stability_ari", "Stabilitas ARI ↑"),
               ("size_entropy_norm", "Keseimbangan ↑"), ("workforce_eta2", "Workforce η² ↑"), ("cramers_v_level", "Cramér's V level ↓")]
    fig, axes = plt.subplots(1, 6, figsize=(15, 2.8), sharey=True)
    names = [ALGO_LABEL[a] for a in best.index]
    for ax, (m, title) in zip(axes, metrics):
        vals = best[m].to_numpy(float)
        ax.barh(names, vals, color=[vs.SERIES[["KMEANS", "HIERARCHICAL", "DBSCAN"].index(a)] for a in best.index],
                edgecolor=vs.SURFACE)
        for y, v in enumerate(vals):
            ax.text(v, y, f" {v:.2f}", va="center", fontsize=7.5, color=vs.TEXT_2)
        ax.set_xlim(0, max(vals) * 1.35); ax.set_title(title, loc="left", fontsize=8.5)
    fig.suptitle("V04 — Model terbaik per algoritma (PRD §55)", x=0.01, ha="left", y=1.05)
    fig.savefig(FIG / "V04_best_per_algorithm.png"); plt.close(fig)

    # V05 PCA model terpilih (visual saja, PRD §52) — small multiples per cluster
    P = PCA(n_components=2, random_state=RANDOM_SEED).fit(Xs)
    Q = P.transform(Xs) + np.random.default_rng(RANDOM_SEED).normal(0, 0.03, (len(Xs), 2))
    cl = [c for c in np.unique(sel_lab)]
    fig, axes = plt.subplots(1, len(cl), figsize=(3.2 * len(cl), 3.2), sharex=True, sharey=True)
    axes = np.atleast_1d(axes)
    for ax, c in zip(axes, cl):
        m = sel_lab == c
        ax.scatter(Q[~m, 0], Q[~m, 1], s=4, color=vs.NEUTRAL, alpha=0.35, linewidth=0)
        ax.scatter(Q[m, 0], Q[m, 1], s=10, color=vs.SERIES[0] if c != -1 else vs.SERIES[7], alpha=0.75,
                   edgecolor=vs.SURFACE, linewidth=0.4)
        ax.set_title(f"{'Noise' if c == -1 else f'Cluster {c}'} (n={m.sum()}, {m.mean():.0%})", loc="left", fontsize=8.5)
        ax.set_xlabel(f"PC1 ({P.explained_variance_ratio_[0]:.0%})")
    axes[0].set_ylabel(f"PC2 ({P.explained_variance_ratio_[1]:.0%})")
    fig.suptitle(f"V05 — Model terpilih {selected.experiment_id} ({ALGO_LABEL[selected.model_name]}, set {selected.feature_set}/"
                 f"{selected.scaler}): PCA 2D, visual saja", x=0.01, ha="left", y=1.04)
    fig.savefig(FIG / "V05_selected_model_pca.png"); plt.close(fig)


if __name__ == "__main__":
    main()
