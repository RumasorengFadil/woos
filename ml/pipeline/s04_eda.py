"""Tahap 4 — Exploratory Data Analysis (PRD §25) + analisis tambahan protokol §6.

Tujuan: memahami struktur data sebelum training, BUKAN menentukan cluster secara manual.

Visualisasi minimum PRD §25 (F01–F07) dan tambahan protokol (F08–F14):
    F01 distribusi FTK, Realisasi, Gap, Fulfillment, Staffing ratio
    F02 FTK vs Realisasi (bubble: jumlah organisasi per kombinasi)
    F03 gap per organisasi (terurut) + per direktorat
    F04 korelasi feature (Spearman)
    F05 distribusi jenjang (keseluruhan & per direktorat)
    F06 missing value
    F07 outlier (z-score per feature)
    F08 feature per level organisasi (kontrol artefak)
    F09 PCA 2D (visual saja, PRD §52) — small multiples per level
    F10 StandardScaler vs RobustScaler
    F11 skewness mentah vs log1p
    F12 multiplisitas vektor (titik kembar)
    F13 Hopkins feature set final F1
    F14 DLMHC vs direktorat lain (sub-analisis D-012)

Output: ml/outputs/04_eda/<dataset_version>/  figures/*.png + tabel CSV + eda_summary.json
Jalankan:  ml/.venv/bin/python ml/pipeline/s04_eda.py [--dataset=v2]
"""
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import RobustScaler, StandardScaler

import viz_style as vs
from config import COLUMN_MAP, GRADE_GROUPS, OUTPUTS, RANDOM_SEED, dataset
from s01b_dataset_adequacy import hopkins
from s03_feature_engineering import FEATURE_SETS_F1 as FEATURE_SETS  # EDA dilakukan pada F1

DLMHC = "DIREKTORAT LEGAL DAN MANAJEMEN HUMAN CAPITAL"
MODEL_FEATURES = ["ftk", "realization", "balance_index", "position_count", "vacant_position_count",
                  "avg_realization_per_position", "vacant_share", "pct_MA_MAK", "pct_MM", "pct_MD",
                  "pct_SPESIALIS", "pct_GENERALIS"]
COUNT_FEATURES = ["ftk", "realization", "position_count", "vacant_position_count", "avg_realization_per_position"]

# Kandidat feature set F2 (usulan D-020, hasil EDA): B tanpa avg_realization_per_position (turunan
# realization/position_count); C memakai GENERALIS sebagai kategori referensi (near-closure).
CANDIDATE_SETS_F2 = {
    "A": FEATURE_SETS["A"],
    "B": ["ftk", "realization", "balance_index", "position_count", "vacant_position_count"],
    "C": ["ftk", "realization", "balance_index", "position_count", "vacant_position_count",
          "pct_MA_MAK", "pct_MM", "pct_MD", "pct_SPESIALIS"],
    "R": FEATURE_SETS["R"],
}


def log1p_counts(frame, cols):
    out = frame[cols].copy()
    for c in cols:
        if c in COUNT_FEATURES:
            out[c] = np.log1p(out[c])
    return out


# ---------------------------------------------------------------- fungsi murni (diuji)

def vif(X, names):
    """Variance Inflation Factor: 1 / (1 − R²_j), R²_j dari regresi fitur j pada fitur lain."""
    X = np.asarray(X, float)
    out = {}
    for j, name in enumerate(names):
        y = X[:, j]
        others = np.delete(X, j, axis=1)
        A = np.column_stack([np.ones(len(y)), others])
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        resid = y - A @ coef
        ss_tot = ((y - y.mean()) ** 2).sum()
        r2 = 1 - (resid ** 2).sum() / ss_tot if ss_tot > 0 else 0.0
        out[name] = float(np.inf) if r2 >= 1 - 1e-12 else float(1 / (1 - r2))
    return out


def epsilon_squared(values, groups):
    """Effect size Kruskal–Wallis: ε² = H / (n − 1). 0 = tidak ada efek, 1 = maksimal."""
    values, groups = np.asarray(values), np.asarray(groups)
    samples = [values[groups == g] for g in np.unique(groups)]
    samples = [s for s in samples if len(s) > 0]
    if len(samples) < 2 or np.all(values == values[0]):
        return 0.0, 1.0
    h, p = stats.kruskal(*samples)
    return float(h / (len(values) - 1)), float(p)


def mahalanobis_sq(Z):
    """Jarak Mahalanobis kuadrat pada data terstandardisasi (pseudo-inverse bila singular)."""
    Z = np.asarray(Z, float)
    inv = np.linalg.pinv(np.cov(Z, rowvar=False))
    c = Z - Z.mean(0)
    return np.einsum("ij,jk,ik->i", c, inv, c)


# ---------------------------------------------------------------- figure helpers

def _save(fig, path):
    fig.savefig(path)
    plt.close(fig)


def main():
    vs.apply()
    ds = dataset()
    fe = OUTPUTS / "03_feature_engineering" / ds["version"]
    pp = OUTPUTS / "02_preprocessing" / ds["version"]
    OUT = OUTPUTS / "04_eda" / ds["version"]
    FIG = OUT / "figures"
    FIG.mkdir(parents=True, exist_ok=True)

    direct = pd.read_csv(fe / "features_direct.csv", index_col=0)
    rollup = pd.read_csv(fe / "features_rollup.csv", index_col=0)
    pos = pd.read_csv(pp / "positions_clean.csv")
    raw = pd.read_csv(ds["file"]).rename(columns=COLUMN_MAP)
    pop = direct[direct.in_model_population == 1].copy()
    n = len(pop)
    short_dir = pop.directorate_name.str.replace("DIREKTORAT ", "", regex=False).str.title()
    pop["dir_short"] = short_dir
    summary = {"dataset_version": ds["version"], "n_model_population": n}

    # ---------- F01 distribusi inti ----------
    ftk_pos = pop[pop.ftk > 0]
    panels = [("ftk", pop.ftk, "FTK", 1), ("realization", pop.realization, "Realisasi", 1),
              ("gap", pop.gap, "Gap (FTK − Realisasi)", 1),
              ("fulfillment_ratio", ftk_pos.fulfillment_ratio, "Fulfillment ratio (FTK > 0)", 0.1),
              ("staffing_ratio", ftk_pos.staffing_ratio, "Staffing ratio (FTK > 0)", 0.1)]
    fig, axes = plt.subplots(1, 5, figsize=(15, 3))
    for ax, (_, s, title, w) in zip(axes, panels):
        lo, hi = np.floor(s.min() / w) * w, np.ceil(s.max() / w) * w
        ax.hist(s, bins=np.arange(lo, hi + 2 * w, w) - w / 2, **vs.bar_kw())
        ax.set_title(title, loc="left")
        ax.set_ylabel("organisasi")
        ax.text(0.98, 0.95, f"n={len(s)}\nmedian={s.median():.2f}\nskew={stats.skew(s):.2f}",
                transform=ax.transAxes, ha="right", va="top", color=vs.TEXT_2, fontsize=7.5)
    fig.suptitle("F01 — Distribusi feature inti per organisasi (direct, populasi model)", x=0.01, ha="left")
    _save(fig, FIG / "F01_distributions_core.png")
    summary["distribution"] = {k: {"n": int(len(s)), "mean": round(float(s.mean()), 4),
                                   "median": round(float(s.median()), 4), "std": round(float(s.std()), 4),
                                   "skew": round(float(stats.skew(s)), 3), "min": float(s.min()), "max": float(s.max())}
                               for k, s, *_ in panels}

    # ---------- F02 FTK vs realisasi (bubble) ----------
    combo = pop.groupby(["ftk", "realization"]).size().rename("orgs").reset_index()
    fig, ax = plt.subplots(figsize=(5.6, 4.6))
    ax.scatter(combo.ftk, combo.realization, s=combo.orgs * 4 + 8, color=vs.SERIES[0], alpha=0.55,
               edgecolor=vs.SURFACE, linewidth=1)
    lim = max(combo.ftk.max(), combo.realization.max()) + 1
    ax.plot([0, lim], [0, lim], color=vs.TEXT_2, lw=1, ls="--")
    ax.text(lim * 0.72, lim * 0.78, "Realisasi = FTK", color=vs.TEXT_2, rotation=37)
    for _, r in combo.nlargest(4, "orgs").iterrows():
        ax.annotate(f"{int(r.orgs)} org", (r.ftk, r.realization), xytext=(8, -10), textcoords="offset points",
                    color=vs.TEXT_2, fontsize=7.5)
    ax.set_xlabel("FTK per organisasi"); ax.set_ylabel("Realisasi per organisasi")
    ax.set_title("F02 — FTK vs Realisasi (luas lingkaran = jumlah organisasi)", loc="left")
    _save(fig, FIG / "F02_ftk_vs_realization.png")
    combo.sort_values("orgs", ascending=False).to_csv(OUT / "ftk_realization_combinations.csv", index=False)
    summary["ftk_realization"] = {
        "distinct_combinations": int(len(combo)),
        "top8_share": round(float(combo.orgs.nlargest(8).sum() / n), 4),
        "on_diagonal_share": round(float((pop.ftk == pop.realization).mean()), 4),
        "below_diagonal_share": round(float((pop.realization < pop.ftk).mean()), 4),
        "above_diagonal_share": round(float((pop.realization > pop.ftk).mean()), 4),
        "spearman": round(float(stats.spearmanr(pop.ftk, pop.realization)[0]), 4),
    }

    # ---------- F03 gap per organisasi & per direktorat ----------
    g = pop.sort_values("gap", ascending=False).reset_index()
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.4), gridspec_kw={"width_ratios": [1.2, 1], "wspace": 0.55})
    colors = np.where(g.gap > 0, vs.SERIES[7], np.where(g.gap < 0, vs.SERIES[0], vs.NEUTRAL))
    axes[0].bar(np.arange(len(g)), g.gap, width=1.0, color=colors, linewidth=0)
    axes[0].axhline(0, color=vs.TEXT_2, lw=0.8)
    axes[0].set_xlabel("organisasi (diurutkan menurut gap)"); axes[0].set_ylabel("gap")
    axes[0].set_title("F03a — Gap per organisasi, terurut\nmerah = kekurangan (gap > 0) · biru = kelebihan (gap < 0)", loc="left")
    for _, r in g.head(3).iterrows():
        axes[0].annotate(f"{r.organization_name[:34].title()} (gap {int(r.gap)})", (_, r.gap),
                         xytext=(60, -2 - 13 * _), textcoords="offset points", fontsize=7, color=vs.TEXT_2,
                         arrowprops={"arrowstyle": "-", "color": vs.NEUTRAL, "lw": 0.6})
    d = pop[pop.organization_level > 2].groupby("dir_short").agg(gap=("gap", "sum"), ftk=("ftk", "sum")).sort_values("gap")
    axes[1].barh(d.index, d.gap, color=np.where(d.gap > 0, vs.SERIES[7], vs.SERIES[0]), edgecolor=vs.SURFACE)
    axes[1].axvline(0, color=vs.TEXT_2, lw=0.8)
    for y, (v, f) in enumerate(zip(d.gap, d.ftk)):
        axes[1].text(v + (3 if v >= 0 else -3), y, f"{int(v)}", va="center", ha="left" if v >= 0 else "right",
                     fontsize=7.5, color=vs.TEXT_2)
    axes[1].set_xlim(d.gap.min() * 1.25, d.gap.max() * 1.12)
    axes[1].set_title("F03b — Σ gap per direktorat\n(tanpa root Kantor Pusat, 1 org)", loc="left"); axes[1].set_xlabel("Σ gap")
    _save(fig, FIG / "F03_gap_per_organization.png")
    g[["organization_id", "organization_name", "directorate_name", "organization_level", "ftk", "realization", "gap"]] \
        .to_csv(OUT / "gap_per_organization.csv", index=False)
    summary["gap"] = {"positive": int((pop.gap > 0).sum()), "zero": int((pop.gap == 0).sum()),
                      "negative": int((pop.gap < 0).sum()),
                      "top_positive": g.head(5)[["organization_id", "organization_name", "gap"]].to_dict("records"),
                      "top_negative": g.tail(5)[["organization_id", "organization_name", "gap"]].to_dict("records")}

    # ---------- F04 korelasi ----------
    sp = pop[MODEL_FEATURES].corr(method="spearman")
    pe = pop[MODEL_FEATURES].corr(method="pearson")
    sp.round(4).to_csv(OUT / "correlation_spearman.csv"); pe.round(4).to_csv(OUT / "correlation_pearson.csv")
    fig, ax = plt.subplots(figsize=(7.4, 6.2))
    im = ax.imshow(sp, cmap=vs.DIVERGING, vmin=-1, vmax=1)
    ax.set_xticks(range(len(MODEL_FEATURES))); ax.set_xticklabels(MODEL_FEATURES, rotation=55, ha="right")
    ax.set_yticks(range(len(MODEL_FEATURES))); ax.set_yticklabels(MODEL_FEATURES)
    ax.grid(False)
    for i in range(len(MODEL_FEATURES)):
        for j in range(len(MODEL_FEATURES)):
            v = sp.iloc[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.5,
                    color="white" if abs(v) > 0.6 else vs.TEXT)
    fig.colorbar(im, ax=ax, fraction=0.04, label="Spearman ρ")
    ax.set_title("F04 — Korelasi Spearman feature model", loc="left")
    _save(fig, FIG / "F04_correlation_spearman.png")
    pairs = [(a, b, round(float(sp.loc[a, b]), 3), round(float(pe.loc[a, b]), 3))
             for i, a in enumerate(MODEL_FEATURES) for b in MODEL_FEATURES[i + 1:] if abs(sp.loc[a, b]) >= 0.7]
    summary["high_correlation_pairs_spearman_ge_0_7"] = pairs

    # VIF per feature set
    vif_rows = []
    for sname, cols in FEATURE_SETS.items():
        for f, v in vif(StandardScaler().fit_transform(pop[cols]), cols).items():
            vif_rows.append({"set": sname, "feature": f, "vif": round(v, 3)})
    vif_df = pd.DataFrame(vif_rows)
    vif_df.to_csv(OUT / "vif_by_feature_set.csv", index=False)
    summary["vif_max_by_set"] = {sname: vif_df.loc[vif_df[vif_df.set == sname].vif.idxmax(), ["feature", "vif"]].to_dict()
                                 for sname in FEATURE_SETS}

    # ---------- F05 distribusi jenjang ----------
    act = pos[pos.is_active]
    overall = act.grade_group.value_counts(normalize=True).reindex(GRADE_GROUPS).fillna(0)
    by_dir = act.assign(dir_short=act.directorate_name.str.replace("DIREKTORAT ", "", regex=False).str.title()) \
        .pivot_table(index="dir_short", columns="grade_group", values="position_id", aggfunc="count", fill_value=0) \
        .reindex(columns=GRADE_GROUPS, fill_value=0)
    by_dir = by_dir.drop(index=[i for i in by_dir.index if "Kantor Pusat" in i])
    by_dir_share = by_dir.div(by_dir.sum(1), axis=0).sort_values("GENERALIS")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), gridspec_kw={"width_ratios": [1, 2.2], "wspace": 0.75})
    axes[0].barh(overall.index[::-1], overall.values[::-1] * 100, **vs.bar_kw())
    for y, v in enumerate(overall.values[::-1] * 100):
        axes[0].text(v + 0.8, y, f"{v:.1f}%", va="center", fontsize=7.5, color=vs.TEXT_2)
    axes[0].set_xlim(0, overall.max() * 100 * 1.25)
    axes[0].set_xlabel("% jabatan aktif"); axes[0].set_title("F05a — Seluruh Kantor Pusat", loc="left")
    left = np.zeros(len(by_dir_share))
    for k, gname in enumerate(GRADE_GROUPS):
        axes[1].barh(by_dir_share.index, by_dir_share[gname] * 100, left=left, color=vs.SERIES[k],
                     edgecolor=vs.SURFACE, linewidth=1, label=gname)
        left += by_dir_share[gname].values * 100
    axes[1].set_xlim(0, 100); axes[1].set_xlabel("% jabatan aktif")
    axes[1].legend(ncol=7, loc="upper center", bbox_to_anchor=(0.45, -0.12), fontsize=7.5)
    axes[1].set_title("F05b — Per direktorat (root Kantor Pusat tidak ditampilkan)", loc="left")
    _save(fig, FIG / "F05_grade_distribution.png")
    by_dir.assign(total=by_dir.sum(1)).to_csv(OUT / "grade_distribution_by_directorate.csv")
    summary["grade_share_overall_active"] = overall.round(4).to_dict()

    # ---------- F06 missing value ----------
    miss_raw = raw.isna().sum()
    miss_feat = direct[["fulfillment_ratio", "staffing_ratio"]].isna().sum()
    miss = pd.concat([miss_raw.rename(lambda c: f"raw:{c}"), miss_feat.rename(lambda c: f"feature:{c}")])
    miss = miss[miss > 0]
    fig, ax = plt.subplots(figsize=(6.5, 2.6))
    ax.barh(miss.index, miss.values, **vs.bar_kw(vs.SERIES[1]))
    for y, v in enumerate(miss.values):
        ax.text(v + 1, y, str(int(v)), va="center", fontsize=7.5, color=vs.TEXT_2)
    ax.set_xlabel("jumlah nilai kosong")
    ax.set_title("F06 — Missing value: data mentah (baris jabatan) & feature (organisasi)", loc="left")
    _save(fig, FIG / "F06_missing_values.png")
    summary["missing"] = {k: int(v) for k, v in miss.items()}
    summary["missing_note"] = "feature ratio NULL hanya karena FTK = 0 (D-003); feature input model tanpa NaN"

    # ---------- F07 outlier ----------
    Z = pd.DataFrame(StandardScaler().fit_transform(pop[MODEL_FEATURES]), columns=MODEL_FEATURES, index=pop.index)
    fig, ax = plt.subplots(figsize=(8, 4.4))
    ax.boxplot([Z[c] for c in MODEL_FEATURES], vert=False, tick_labels=MODEL_FEATURES, widths=0.5,
               flierprops={"marker": "o", "markersize": 3, "markerfacecolor": vs.SERIES[1], "markeredgewidth": 0,
                           "alpha": 0.6}, medianprops={"color": vs.SERIES[0], "linewidth": 2},
               boxprops={"color": vs.TEXT_2}, whiskerprops={"color": vs.TEXT_2}, capprops={"color": vs.TEXT_2})
    ax.axvline(3, color=vs.SERIES[7], lw=1, ls=":"); ax.axvline(-3, color=vs.SERIES[7], lw=1, ls=":")
    ax.set_xlabel("z-score (StandardScaler)")
    ax.set_title("F07 — Outlier univariat per feature (garis titik: |z| = 3)", loc="left")
    _save(fig, FIG / "F07_outliers.png")
    uni = []
    for c in MODEL_FEATURES:
        q1, q3 = pop[c].quantile([.25, .75]); iqr = q3 - q1
        uni.append({"feature": c, "iqr": round(float(iqr), 4),
                    "n_outside_1_5_iqr": int(((pop[c] < q1 - 1.5 * iqr) | (pop[c] > q3 + 1.5 * iqr)).sum()),
                    "n_abs_z_gt_3": int((Z[c].abs() > 3).sum()), "max_abs_z": round(float(Z[c].abs().max()), 2)})
    pd.DataFrame(uni).to_csv(OUT / "outliers_univariate.csv", index=False)
    Zb = StandardScaler().fit_transform(pop[FEATURE_SETS["B"]])
    d2 = mahalanobis_sq(Zb)
    thr = stats.chi2.ppf(0.999, Zb.shape[1])
    mv = pop.assign(mahalanobis_sq=d2).loc[d2 > thr].sort_values("mahalanobis_sq", ascending=False)
    mv[["organization_name", "directorate_name", "organization_level", "ftk", "realization", "gap",
        "position_count", "vacant_position_count", "avg_realization_per_position", "mahalanobis_sq"]] \
        .round(3).to_csv(OUT / "outliers_multivariate_setB.csv")
    summary["outliers"] = {"univariate": uni, "multivariate_setB_chi2_0999_threshold": round(float(thr), 3),
                           "multivariate_setB_count": int(len(mv)),
                           "multivariate_setB_top5": mv.head(5)[["organization_name", "ftk", "realization"]]
                           .reset_index().to_dict("records")}

    # ---------- F08 feature per level (kontrol artefak) ----------
    levels = sorted(pop.organization_level.unique())
    show = ["ftk", "balance_index", "vacant_share", "avg_realization_per_position", "pct_MM", "pct_GENERALIS"]
    fig, axes = plt.subplots(2, 3, figsize=(13, 6))
    for ax, c in zip(axes.ravel(), show):
        data = [pop.loc[pop.organization_level == lv, c] for lv in levels]
        ax.boxplot(data, tick_labels=[f"L{lv}\n(n={len(x)})" for lv, x in zip(levels, data)], widths=0.55,
                   flierprops={"marker": "o", "markersize": 2.5, "markerfacecolor": vs.NEUTRAL, "markeredgewidth": 0},
                   medianprops={"color": vs.SERIES[0], "linewidth": 2}, boxprops={"color": vs.TEXT_2},
                   whiskerprops={"color": vs.TEXT_2}, capprops={"color": vs.TEXT_2})
        e2, _ = epsilon_squared(pop[c], pop.organization_level)
        ax.set_title(f"{c}  (ε² level = {e2:.2f})", loc="left")
    fig.suptitle("F08 — Feature menurut level organisasi (kontrol artefak)", x=0.01, ha="left")
    fig.tight_layout()
    _save(fig, FIG / "F08_features_by_level.png")
    assoc = []
    for c in MODEL_FEATURES:
        e_l, p_l = epsilon_squared(pop[c], pop.organization_level)
        e_d, p_d = epsilon_squared(pop[c], pop.directorate_name)
        assoc.append({"feature": c, "spearman_level": round(float(stats.spearmanr(pop[c], pop.organization_level)[0]), 3),
                      "epsilon2_level": round(e_l, 3), "p_level": p_l,
                      "epsilon2_directorate": round(e_d, 3), "p_directorate": p_d})
    assoc_df = pd.DataFrame(assoc)
    assoc_df.to_csv(OUT / "association_level_directorate.csv", index=False)
    summary["association"] = assoc_df.round(4).to_dict("records")

    # ---------- F09 PCA (visual saja) ----------
    pca_rows = []
    fig, axes = plt.subplots(2, len(levels), figsize=(2.3 * len(levels), 5), sharex="row", sharey="row")
    for r, sname in enumerate(["B", "C"]):
        Xs = StandardScaler().fit_transform(pop[FEATURE_SETS[sname]])
        pca = PCA(n_components=min(len(FEATURE_SETS[sname]), 5), random_state=RANDOM_SEED).fit(Xs)
        P = pca.transform(Xs)[:, :2]
        jit = np.random.default_rng(RANDOM_SEED).normal(0, 0.03, P.shape)
        P = P + jit
        for k, v in enumerate(pca.explained_variance_ratio_):
            pca_rows.append({"set": sname, "component": k + 1, "explained_variance_ratio": round(float(v), 4)})
        for ax, lv in zip(axes[r], levels):
            m = (pop.organization_level == lv).values
            ax.scatter(P[~m, 0], P[~m, 1], s=4, color=vs.NEUTRAL, alpha=0.35, linewidth=0)
            ax.scatter(P[m, 0], P[m, 1], s=9, color=vs.SERIES[0], alpha=0.7, edgecolor=vs.SURFACE, linewidth=0.5)
            ax.set_title(f"Set {sname} · L{lv} (n={m.sum()})", loc="left", fontsize=8)
        axes[r][0].set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.0%})")
        for ax in axes[r]:
            ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.0%})", fontsize=7.5)
    fig.suptitle("F09 — PCA 2D (visualisasi saja; biru = level terpilih, abu = lainnya)", x=0.01, ha="left")
    fig.tight_layout()
    _save(fig, FIG / "F09_pca_by_level.png")
    pd.DataFrame(pca_rows).to_csv(OUT / "pca_explained_variance.csv", index=False)

    # ---------- F10 scaler ----------
    cols = FEATURE_SETS["C"]
    S = StandardScaler().fit_transform(pop[cols]); R = RobustScaler().fit_transform(pop[cols])
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for ax, M, title in [(axes[0], S, "StandardScaler"), (axes[1], R, "RobustScaler")]:
        ax.boxplot([M[:, j] for j in range(len(cols))], vert=False, tick_labels=cols, widths=0.5,
                   flierprops={"marker": "o", "markersize": 2.5, "markerfacecolor": vs.SERIES[1], "markeredgewidth": 0},
                   medianprops={"color": vs.SERIES[0], "linewidth": 2}, boxprops={"color": vs.TEXT_2},
                   whiskerprops={"color": vs.TEXT_2}, capprops={"color": vs.TEXT_2})
        ax.set_title(f"F10 — {title} (set C)", loc="left"); ax.set_xlabel("nilai ter-skala")
    _save(fig, FIG / "F10_scaler_comparison.png")
    scale_cmp = pd.DataFrame({"feature": cols, "standard_range": S.max(0) - S.min(0), "robust_range": R.max(0) - R.min(0),
                              "standard_max_abs": np.abs(S).max(0), "robust_max_abs": np.abs(R).max(0)}).round(3)
    scale_cmp["robust_to_standard_range_ratio"] = (scale_cmp.robust_range / scale_cmp.standard_range).round(3)
    scale_cmp.to_csv(OUT / "scaler_comparison_setC.csv", index=False)
    summary["scaler_comparison_setC"] = scale_cmp.to_dict("records")

    # ---------- F11 skewness ----------
    sk = pd.DataFrame({"feature": MODEL_FEATURES,
                       "skew_raw": [stats.skew(pop[c]) for c in MODEL_FEATURES],
                       "skew_log1p": [stats.skew(np.log1p(pop[c])) if c in COUNT_FEATURES else np.nan
                                      for c in MODEL_FEATURES]}).round(3)
    sk.to_csv(OUT / "skewness.csv", index=False)
    cf = sk[sk.feature.isin(COUNT_FEATURES)]
    fig, ax = plt.subplots(figsize=(7, 3.2))
    x = np.arange(len(cf))
    ax.bar(x - 0.2, cf.skew_raw, 0.38, label="mentah", **vs.bar_kw(vs.SERIES[0]))
    ax.bar(x + 0.2, cf.skew_log1p, 0.38, label="log1p", **vs.bar_kw(vs.SERIES[1]))
    for xi, (a, b) in enumerate(zip(cf.skew_raw, cf.skew_log1p)):
        ax.text(xi - 0.2, a + 0.1, f"{a:.1f}", ha="center", fontsize=7, color=vs.TEXT_2)
        ax.text(xi + 0.2, b + 0.1, f"{b:.1f}", ha="center", fontsize=7, color=vs.TEXT_2)
    ax.axhline(0, color=vs.TEXT_2, lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels(cf.feature, rotation=15); ax.set_ylabel("skewness")
    ax.legend(loc="upper right"); ax.set_title("F11 — Skewness feature hitungan: mentah vs log1p", loc="left")
    _save(fig, FIG / "F11_skewness.png")
    summary["skewness"] = sk.to_dict("records")

    # ---------- F12 multiplisitas vektor ----------
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    mult = []
    for k, (sname, cols) in enumerate(FEATURE_SETS.items()):
        vc = pop[cols].round(6).value_counts().values
        ax.plot(np.arange(1, len(vc) + 1), vc, color=vs.SERIES[k], label=f"Set {sname} ({len(vc)} vektor unik)")
        mult.append({"set": sname, "unique_vectors": int(len(vc)), "largest_group": int(vc[0]),
                     "top10_share": round(float(vc[:10].sum() / n), 4),
                     "share_in_tied": round(float(vc[vc > 1].sum() / n), 4)})
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("peringkat vektor"); ax.set_ylabel("jumlah organisasi identik")
    ax.legend(); ax.set_title("F12 — Multiplisitas vektor feature (titik kembar)", loc="left")
    _save(fig, FIG / "F12_vector_multiplicity.png")
    summary["vector_multiplicity"] = mult

    # ---------- F13 Hopkins F1 ----------
    hop = []
    for unit, f in [("direct", direct), ("rollup", rollup)]:
        p_ = f[f.in_model_population == 1]
        for sname, cols in FEATURE_SETS.items():
            X = StandardScaler().fit_transform(p_[cols])
            Xu = StandardScaler().fit_transform(np.unique(p_[cols].to_numpy(float), axis=0))
            h_all = [hopkins(X, np.random.default_rng(RANDOM_SEED + i)) for i in range(50)]
            h_u = [hopkins(Xu, np.random.default_rng(RANDOM_SEED + i)) for i in range(50)]
            hop.append({"unit": unit, "set": sname, "hopkins_all_mean": round(float(np.mean(h_all)), 3),
                        "hopkins_all_sd": round(float(np.std(h_all)), 3), "hopkins_dedup_mean": round(float(np.mean(h_u)), 3),
                        "hopkins_dedup_sd": round(float(np.std(h_u)), 3)})
    hop_df = pd.DataFrame(hop)
    hop_df.to_csv(OUT / "hopkins_F1.csv", index=False)
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    sets = list(FEATURE_SETS)
    for k, (unit, off) in enumerate([("direct", -0.2), ("rollup", 0.2)]):
        t = hop_df[hop_df.unit == unit].set_index("set").loc[sets]
        ax.bar(np.arange(len(sets)) + off, t.hopkins_dedup_mean, 0.38, yerr=t.hopkins_dedup_sd,
               label=f"{unit} (vektor unik)", **vs.bar_kw(vs.SERIES[k]))
    ax.axhline(0.5, color=vs.TEXT_2, ls="--", lw=1); ax.text(3.45, 0.52, "acak", fontsize=7.5, color=vs.TEXT_2)
    ax.axhline(0.75, color=vs.SERIES[5], ls=":", lw=1); ax.text(3.45, 0.77, "kuat", fontsize=7.5, color=vs.TEXT_2)
    ax.set_xticks(range(len(sets))); ax.set_xticklabels([f"Set {s}" for s in sets]); ax.set_ylim(0, 1.05)
    ax.set_ylabel("Hopkins"); ax.legend(loc="lower left")
    ax.set_title("F13 — Clustering tendency feature set F1 (50 run)", loc="left")
    _save(fig, FIG / "F13_hopkins_F1.png")
    summary["hopkins_F1"] = hop

    # ---------- F14 DLMHC vs lainnya ----------
    grp = np.where(pop.directorate_name == DLMHC, "DLMHC", "Direktorat lain")
    comp_feats = ["balance_index", "vacant_share", "avg_realization_per_position", "position_count"]
    fig, axes = plt.subplots(1, 4, figsize=(14, 3))
    comp = []
    for ax, c in zip(axes, comp_feats):
        a, b = pop.loc[grp == "DLMHC", c], pop.loc[grp != "DLMHC", c]
        bins = np.histogram_bin_edges(pop[c], bins=20)
        ax.hist(b, bins=bins, density=True, color=vs.SERIES[0], alpha=0.55, label=f"Direktorat lain (n={len(b)})")
        ax.hist(a, bins=bins, density=True, histtype="step", color=vs.SERIES[1], linewidth=2, label=f"DLMHC (n={len(a)})")
        u, p = stats.mannwhitneyu(a, b)
        r_rb = 1 - 2 * u / (len(a) * len(b))
        comp.append({"feature": c, "median_dlmhc": float(a.median()), "median_other": float(b.median()),
                     "mean_dlmhc": round(float(a.mean()), 4), "mean_other": round(float(b.mean()), 4),
                     "mannwhitney_p": float(p), "rank_biserial": round(float(r_rb), 3)})
        ax.set_title(f"{c}\n(rank-biserial = {r_rb:.2f})", loc="left")
    axes[0].legend(fontsize=7, loc="upper left")
    fig.suptitle("F14 — DLMHC vs direktorat lain (densitas)", x=0.01, ha="left", y=1.05)
    _save(fig, FIG / "F14_dlmhc_vs_other.png")
    summary["dlmhc_vs_other"] = comp

    # ---------- F15 kandidat F2: VIF & Hopkins ----------
    cand = []
    for version, sets in [("F1", FEATURE_SETS), ("F2", CANDIDATE_SETS_F2)]:
        for sname, cols in sets.items():
            for transform in ["raw", "log1p"]:
                X = pop[cols] if transform == "raw" else log1p_counts(pop, cols)
                v = vif(StandardScaler().fit_transform(X), cols)
                row = {"feature_version": version, "set": sname, "transform": transform, "d": len(cols),
                       "max_vif": round(max(v.values()), 2), "max_vif_feature": max(v, key=v.get),
                       "vif": {k: round(x, 2) for k, x in v.items()}}
                if transform == "raw":
                    Xu = StandardScaler().fit_transform(np.unique(pop[cols].to_numpy(float), axis=0))
                    hs = [hopkins(Xu, np.random.default_rng(RANDOM_SEED + i)) for i in range(50)]
                    row["hopkins_dedup_mean"] = round(float(np.mean(hs)), 3)
                    row["unique_vectors"] = int(len(Xu))
                cand.append(row)
    cand_df = pd.DataFrame(cand)
    cand_df.drop(columns="vif").to_csv(OUT / "feature_set_candidates_vif.csv", index=False)
    summary["feature_set_candidates"] = cand
    fig, ax = plt.subplots(figsize=(7, 3.4))
    variants = [("F1", "raw", "F1 mentah"), ("F2", "raw", "F2 mentah (usulan)"), ("F2", "log1p", "F2 log1p")]
    for k, (fv, tr, label) in enumerate(variants):
        t = cand_df[(cand_df["feature_version"] == fv) & (cand_df["transform"] == tr)].set_index("set").loc[list(FEATURE_SETS)]
        xs = np.arange(len(t)) + (k - 1) * 0.27
        ax.bar(xs, t.max_vif, 0.26, label=label, **vs.bar_kw(vs.SERIES[k]))
        for x_, v_ in zip(xs, t.max_vif):
            ax.text(x_, v_ * 1.08, f"{v_:.0f}" if v_ >= 10 else f"{v_:.1f}", ha="center", fontsize=6.5, color=vs.TEXT_2)
    ax.axhline(10, color=vs.SERIES[7], ls=":", lw=1); ax.text(3.5, 11, "VIF = 10", fontsize=7, color=vs.TEXT_2, ha="right")
    ax.set_yscale("log"); ax.set_xticks(range(len(FEATURE_SETS))); ax.set_xticklabels([f"Set {s}" for s in FEATURE_SETS])
    ax.set_ylabel("VIF maksimum (log)"); ax.legend(loc="upper left")
    ax.set_title("F15 — Multikolinearitas: F1 vs kandidat F2, mentah vs log1p", loc="left")
    _save(fig, FIG / "F15_vif_candidates.png")

    # ---------- ringkasan per direktorat ----------
    by = pop.groupby("directorate_name").agg(orgs=("ftk", "size"), ftk=("ftk", "sum"), realization=("realization", "sum"),
                                              gap=("gap", "sum"), vacant=("vacant_position_count", "sum"),
                                              positions=("position_count", "sum"),
                                              median_balance=("balance_index", "median"))
    by["fulfillment"] = (by.realization / by.ftk).round(4)
    by.to_csv(OUT / "summary_by_directorate.csv")

    (OUT / "eda_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
    print(json.dumps({k: summary[k] for k in ["ftk_realization", "gap", "high_correlation_pairs_spearman_ge_0_7",
                                              "vif_max_by_set", "vector_multiplicity"]}, indent=1, default=str))
    print(assoc_df.to_string(index=False))
    print(sk.to_string(index=False))
    print(hop_df.to_string(index=False))
    print(pd.DataFrame(pca_rows).to_string(index=False))
    print(pd.DataFrame(comp).to_string(index=False))
    print("multivariate outliers set B:", len(mv), "threshold", round(thr, 2))
    print(cand_df.drop(columns="vif").to_string(index=False))
    print(pd.DataFrame(uni).to_string(index=False))


if __name__ == "__main__":
    main()
