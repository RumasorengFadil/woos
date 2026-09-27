"""Tahap 1 — Data Understanding (PRD §21).

Membaca dataset mentah TANPA mengubahnya, lalu menghasilkan profil dan daftar
temuan kualitas data. Tidak ada cleaning / imputasi di tahap ini.

Output: ml/outputs/01_data_understanding/<dataset_version>/
    profile.json            ringkasan angka (dipakai laporan)
    issues.csv              temuan kualitas data per kategori
    org_hierarchy_check.csv hasil resolusi parent per organisasi
    org_direct_aggregate.csv agregat FTK/realisasi per organisasi (jabatan langsung)
    figures/*.png

Jalankan:  ml/.venv/bin/python ml/pipeline/s01_data_understanding.py [--dataset=v1|v2]
"""
import hashlib
import json
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import COLUMN_MAP, OUTPUTS, RANDOM_SEED, dataset

GRADE_PATTERN = re.compile(r"^(?P<family>.+?) \((?P<code>[A-Z0-9]+)\) - (?P<number>\d+)$")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_grade(value):
    """Pecah 'MANAJEMEN DASAR (MD) - 16' -> (MD, 16). Label non-standar -> (label, None)."""
    if pd.isna(value):
        return None, None
    m = GRADE_PATTERN.match(value)
    if not m:
        return value, None
    return m.group("code"), int(m.group("number"))


def resolve_parents(orgs):
    """Resolusi parent.

    v2 memiliki kolom ID Parent -> dipakai langsung, divalidasi terhadap nama & level parent.
    v1 hanya punya NAMA parent -> nama sama + level = level anak - 1; fallback nama saja bila
    kandidat tunggal.
    """
    if "parent_organization_id" in orgs.columns:
        ref = orgs.set_index("organization_id")
        rows = []
        for _, o in orgs.iterrows():
            pid = o.parent_organization_id
            if pid not in ref.index:
                status = "PARENT_NOT_IN_DATASET"
            elif ref.loc[pid, "organization_name"] != o.parent_name:
                status = "PARENT_ID_NAME_MISMATCH"
            elif ref.loc[pid, "organization_level"] != o.organization_level - 1:
                status = "RESOLVED_ID_LEVEL_MISMATCH"
            else:
                status = "RESOLVED_BY_ID"
            rows.append({"organization_id": o.organization_id, "organization_name": o.organization_name,
                         "organization_level": o.organization_level, "parent_name": o.parent_name,
                         "parent_candidates": 1, "parent_organization_id": pid if pid in ref.index else None,
                         "declared_parent_id": pid, "status": status})
        return pd.DataFrame(rows)
    rows = []
    for _, o in orgs.iterrows():
        cand = orgs[orgs.organization_name == o.parent_name]
        exact = cand[cand.organization_level == o.organization_level - 1]
        if len(exact) == 1:
            status, pid = "RESOLVED_NAME_LEVEL", exact.organization_id.iloc[0]
        elif len(cand) == 1:
            status, pid = "RESOLVED_NAME_ONLY_LEVEL_MISMATCH", cand.organization_id.iloc[0]
        elif len(cand) == 0:
            status, pid = "PARENT_NOT_IN_DATASET", None
        else:
            status, pid = "AMBIGUOUS", None
        rows.append({
            "organization_id": o.organization_id,
            "organization_name": o.organization_name,
            "organization_level": o.organization_level,
            "parent_name": o.parent_name,
            "parent_candidates": len(cand),
            "parent_organization_id": pid,
            "status": status,
        })
    return pd.DataFrame(rows)


def main():
    ds = dataset()
    RAW_DATA, DATASET_VERSION = ds["file"], ds["version"]
    OUT = OUTPUTS / "01_data_understanding" / DATASET_VERSION
    FIG = OUT / "figures"
    FIG.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(RAW_DATA)
    raw_columns = list(raw.columns)
    df = raw.rename(columns=COLUMN_MAP)
    n = len(df)
    issues = []

    def issue(code, severity, description, count, needs_decision, examples=""):
        issues.append({"code": code, "severity": severity, "description": description,
                       "affected_rows": int(count), "needs_user_decision": needs_decision,
                       "examples": examples})

    # ---------- struktur ----------
    profile = {
        "dataset_version": DATASET_VERSION,
        "source_file": RAW_DATA.name,
        "sha256": sha256(RAW_DATA),
        "random_seed": RANDOM_SEED,
        "rows": n,
        "columns": raw_columns,
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "unique": {c: int(df[c].nunique()) for c in df.columns},
        "missing": {c: int(df[c].isna().sum()) for c in df.columns},
        "periods": sorted(df.period.unique().tolist()),
    }

    # ---------- periode ----------
    if df.period.nunique() == 1:
        issue("SINGLE_PERIOD", "HIGH",
              "Dataset hanya 1 periode (snapshot). Feature workforce volatility (PRD §16, §82, §90) tidak dapat dibentuk.",
              n, False, str(df.period.iloc[0]))

    # ---------- missing ----------
    for col in ["grade", "position_name"]:
        miss = df[df[col].isna()]
        if len(miss):
            issue(f"MISSING_{col.upper()}", "MEDIUM",
                  f"Nilai kosong pada kolom {col}.", len(miss), col == "grade",
                  "; ".join(miss.organization_id.astype(str) + ":" + miss.position_id.astype(str))[:500])

    # ---------- duplikat ----------
    dup_full = df.duplicated().sum()
    dup_key = df.duplicated(["period", "organization_id", "position_id"]).sum()
    dup_name = df.duplicated(["period", "organization_id", "position_name"]).sum()
    profile["duplicates"] = {"full_row": int(dup_full), "period_org_position_id": int(dup_key),
                             "period_org_position_name": int(dup_name),
                             "position_id_globally_unique": bool(df.position_id.is_unique)}
    if dup_full or dup_key:
        issue("DUPLICATE_ROWS", "HIGH", "Baris duplikat berdasarkan periode+organisasi+jabatan.",
              max(dup_full, dup_key), True)

    # ---------- nilai invalid / edge case ----------
    for col in ["ftk", "realization"]:
        neg = (df[col] < 0).sum()
        profile[f"{col}_negative"] = int(neg)
        if neg:
            issue(f"NEGATIVE_{col.upper()}", "BLOCKER", f"{col} < 0 (invalid, PRD §22).", neg, True)
    profile["position_edge_cases"] = {
        "ftk_0": int((df.ftk == 0).sum()),
        "realization_0": int((df.realization == 0).sum()),
        "ftk_0_and_realization_0": int(((df.ftk == 0) & (df.realization == 0)).sum()),
        "ftk_0_and_realization_gt_0": int(((df.ftk == 0) & (df.realization > 0)).sum()),
        "ftk_gt_0_and_realization_0 (vacant)": int(((df.ftk > 0) & (df.realization == 0)).sum()),
        "realization_gt_ftk": int((df.realization > df.ftk).sum()),
        "realization_eq_ftk": int((df.realization == df.ftk).sum()),
        "realization_lt_ftk": int((df.realization < df.ftk).sum()),
    }
    zz = df[(df.ftk == 0) & (df.realization == 0)]
    issue("POSITION_FTK0_REAL0", "MEDIUM",
          "Jabatan dengan FTK=0 dan Realisasi=0 (jabatan 'tidur'/tidak berformasi). Memengaruhi definisi Jumlah Jabatan (PRD §6, §11).",
          len(zz), True)
    zp = df[(df.ftk == 0) & (df.realization > 0)]
    issue("POSITION_FTK0_REAL_GT0", "MEDIUM",
          "Jabatan dengan FTK=0 tetapi ada realisasi (tidak berformasi namun terisi). Rasio tidak terdefinisi (PRD §8 edge case).",
          len(zp), True, "; ".join(zp.position_name.fillna("").head(8)))

    # ---------- nilai ekstrem (IQR 1.5 & 3.0 pada level jabatan) ----------
    ext = {}
    for col in ["ftk", "realization"]:
        q1, q3 = df[col].quantile([.25, .75])
        iqr = q3 - q1
        ext[col] = {"q1": float(q1), "q3": float(q3), "iqr": float(iqr),
                    "upper_1_5": float(q3 + 1.5 * iqr), "n_above_1_5": int((df[col] > q3 + 1.5 * iqr).sum()),
                    "upper_3_0": float(q3 + 3 * iqr), "n_above_3_0": int((df[col] > q3 + 3 * iqr).sum()),
                    "max": int(df[col].max())}
    profile["extreme_values_position_level"] = ext
    top = df.sort_values("realization", ascending=False).head(10)
    profile["top_realization_positions"] = top[["organization_id", "organization_name", "position_name",
                                                "grade", "ftk", "realization"]].to_dict("records")
    big = df[(df.realization >= 5) & (df.realization >= 3 * df.ftk.clip(lower=1))]
    issue("EXTREME_REALIZATION", "HIGH",
          "Realisasi jauh melebihi FTK pada level jabatan (≥5 orang dan ≥3× FTK). Perlu validasi: data error, pegawai 'parkir'/pool, atau kondisi bisnis valid (PRD §35).",
          len(big), True,
          "; ".join(big.organization_id + " " + big.position_name + f" ftk/real=" + big.ftk.astype(str) + "/" + big.realization.astype(str)))

    # ---------- jenjang ----------
    parsed = df.grade.apply(parse_grade)
    df["grade_code"] = parsed.str[0]
    df["grade_number"] = parsed.str[1]
    profile["grade_values"] = df.grade.value_counts(dropna=False).rename(index=str).to_dict()
    profile["grade_code_counts"] = df.grade_code.value_counts(dropna=False).rename(index=str).to_dict()
    nonstd = df[df.grade.notna() & df.grade_number.isna()]
    if len(nonstd):
        issue("NONSTANDARD_GRADE_LABEL", "MEDIUM",
              "Label jenjang tidak mengikuti format 'NAMA (KODE) - ANGKA' (mis. 'AM', 'VP'). Perlu mapping ke kelompok jenjang standar.",
              len(nonstd), True,
              "; ".join(sorted(nonstd.grade.unique())) + " | contoh: " + "; ".join(nonstd.position_name.head(5)))

    # ---------- whitespace tidak normal (tab, spasi ganda, spasi tepi) ----------
    ws_cols = ["organization_name", "parent_name", "position_name", "grade"]
    ws = df[ws_cols].apply(lambda c: c.fillna("").str.contains(r"\t|\s{2,}|^\s|\s$", regex=True)).any(axis=1)
    profile["rows_with_abnormal_whitespace"] = int(ws.sum())
    if ws.any():
        issue("ABNORMAL_WHITESPACE", "LOW", "Teks mengandung tab / spasi ganda / spasi tepi.", int(ws.sum()), False,
              "; ".join(df[ws].position_name.fillna("").head(5).str.replace("\t", "\\t")))

    # ---------- penanda '*)' pada nama jabatan ----------
    star = df[df.position_name.fillna("").str.contains(r"\*\)", regex=True)]
    profile["position_name_with_star_marker"] = int(len(star))
    if len(star):
        issue("POSITION_NAME_STAR_MARKER", "MEDIUM",
              "Nama jabatan berakhiran '*)' — kemungkinan penanda khusus (jabatan transisi/non-formasi). Arti penanda perlu dikonfirmasi.",
              len(star), True,
              f"{star.grade.isna().sum()} dari {len(star)} tanpa jenjang; FTK total={star.ftk.sum()}, realisasi total={star.realization.sum()}")

    # ---------- mapping organisasi ----------
    org_cols = [c for c in ["organization_id", "organization_name", "parent_name", "parent_organization_id",
                            "organization_level"] if c in df.columns]
    orgs = df[org_cols].drop_duplicates()
    per_id = orgs.groupby("organization_id").size()
    profile["organizations"] = int(df.organization_id.nunique())
    profile["organization_id_with_multiple_attributes"] = int((per_id > 1).sum())
    if (per_id > 1).any():
        issue("ORG_ID_INCONSISTENT", "BLOCKER", "Satu ID organisasi memiliki nama/parent/level berbeda.",
              int((per_id > 1).sum()), True)
    same_name = orgs.groupby("organization_name").organization_id.nunique()
    same_name = same_name[same_name > 1]
    profile["organization_names_shared_by_multiple_ids"] = same_name.to_dict()
    if len(same_name):
        has_pid = "parent_organization_id" in df.columns
        issue("ORG_NAME_NOT_UNIQUE", "LOW" if has_pid else "MEDIUM",
              "Beberapa ID organisasi memakai nama sama." + (" Tidak mengganggu hierarki karena tersedia ID Parent." if has_pid else
              " Karena 'Parent Organisasi' dicatat sebagai NAMA (bukan ID), resolusi parent bisa ambigu."),
              int(same_name.sum()), False, "; ".join(f"{k} ({v} ID)" for k, v in same_name.items()))

    hier = resolve_parents(orgs)
    hier.to_csv(OUT / "org_hierarchy_check.csv", index=False)
    profile["parent_resolution"] = hier.status.value_counts().to_dict()
    for status, sev, desc in [
        ("PARENT_NOT_IN_DATASET", "LOW", "Parent tidak ditemukan dalam dataset (termasuk root 'PT PLN (PERSERO) KANTOR PUSAT' yang memang di luar cakupan)."),
        ("RESOLVED_NAME_ONLY_LEVEL_MISMATCH", "MEDIUM", "Parent ditemukan tetapi level parent ≠ level anak − 1 (lompatan/inkonsistensi level)."),
        ("RESOLVED_ID_LEVEL_MISMATCH", "MEDIUM", "ID Parent valid tetapi level parent ≠ level anak − 1."),
        ("PARENT_ID_NAME_MISMATCH", "HIGH", "ID Parent tidak cocok dengan nama parent yang tercatat."),
        ("AMBIGUOUS", "HIGH", "Parent tidak dapat diresolusi secara unik."),
    ]:
        h = hier[hier.status == status]
        if len(h):
            issue(f"HIERARCHY_{status}", sev, desc, len(h), status != "PARENT_NOT_IN_DATASET" or len(h) > 1,
                  "; ".join(h.organization_id + " → " + h.parent_name))

    # organisasi yang tampak duplikat struktur lama vs baru (nama sama, level berbeda)
    legacy = orgs[orgs.organization_name.isin(same_name.index)].sort_values(["organization_name", "organization_level"])
    profile["same_name_org_detail"] = legacy.to_dict("records")

    # ---------- agregat per organisasi (jabatan langsung saja, TANPA roll-up) ----------
    agg = df.groupby("organization_id").agg(
        organization_name=("organization_name", "first"),
        organization_level=("organization_level", "first"),
        position_rows=("position_id", "size"),
        positions_ftk_gt0=("ftk", lambda s: int((s > 0).sum())),
        ftk=("ftk", "sum"),
        realization=("realization", "sum"),
        missing_grade=("grade", lambda s: int(s.isna().sum())),
    ).reset_index()
    agg["gap"] = agg.ftk - agg.realization
    agg.to_csv(OUT / "org_direct_aggregate.csv", index=False)
    profile["org_aggregate"] = {
        "position_rows_per_org": agg.position_rows.describe().round(3).to_dict(),
        "position_rows_per_org_counts": agg.position_rows.value_counts().sort_index().to_dict(),
        "ftk_per_org": agg.ftk.describe().round(3).to_dict(),
        "realization_per_org": agg.realization.describe().round(3).to_dict(),
        "orgs_ftk_0": int((agg.ftk == 0).sum()),
        "orgs_ftk_0_real_gt_0": int(((agg.ftk == 0) & (agg.realization > 0)).sum()),
        "orgs_ftk_0_real_0": int(((agg.ftk == 0) & (agg.realization == 0)).sum()),
        "orgs_with_1_position": int((agg.position_rows == 1).sum()),
        "orgs_with_ftk_le_2": int((agg.ftk <= 2).sum()),
        "orgs_by_level": agg.organization_level.value_counts().sort_index().to_dict(),
        "gap_sign": {"positive": int((agg.gap > 0).sum()), "zero": int((agg.gap == 0).sum()),
                     "negative": int((agg.gap < 0).sum())},
        "total_ftk": int(agg.ftk.sum()), "total_realization": int(agg.realization.sum()),
    }
    profile["levels"] = df.groupby("organization_level").agg(
        orgs=("organization_id", "nunique"), positions=("position_id", "size"),
        ftk=("ftk", "sum"), realization=("realization", "sum")).reset_index().to_dict("records")
    profile["ftk_realization_crosstab_position"] = {
        f"ftk={k}": {f"real={c}": int(v) for c, v in row.items()}
        for k, row in pd.crosstab(df.ftk, df.realization).iterrows()}
    issue("SMALL_ORGANIZATION_UNITS", "HIGH",
          "Unit organisasi kecil bila hanya memakai jabatan langsung (lihat median di kolom examples); jumlah = organisasi dengan FTK ≤ 2. Nilai rasio menjadi sangat diskret; perlu keputusan unit analisis (langsung vs roll-up sub-tree).",
          int((agg.ftk <= 2).sum()), True,
          f"median jabatan/org={agg.position_rows.median()}, median FTK/org={agg.ftk.median()}")

    # ---------- figures ----------
    plt.rcParams.update({"figure.dpi": 130, "font.size": 9})
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
    for a, col, title in [(ax[0], "ftk", "FTK per jabatan"), (ax[1], "realization", "Realisasi per jabatan")]:
        vc = df[col].value_counts().sort_index()
        a.bar(vc.index.astype(str), vc.values, color="#4C72B0")
        a.set_title(title); a.set_xlabel("nilai"); a.set_ylabel("jumlah jabatan")
    fig.tight_layout(); fig.savefig(FIG / "01_dist_position_ftk_realization.png"); plt.close(fig)

    fig, ax = plt.subplots(1, 3, figsize=(12, 3.2))
    ax[0].hist(agg.ftk, bins=range(0, int(agg.ftk.max()) + 2), color="#4C72B0"); ax[0].set_title("FTK per organisasi")
    ax[1].hist(agg.realization, bins=range(0, int(agg.realization.max()) + 2), color="#55A868"); ax[1].set_title("Realisasi per organisasi")
    ax[2].hist(agg.gap, bins=range(int(agg.gap.min()), int(agg.gap.max()) + 2), color="#C44E52"); ax[2].set_title("Gap (FTK−Realisasi) per organisasi")
    for a in ax: a.set_ylabel("jumlah organisasi")
    fig.tight_layout(); fig.savefig(FIG / "02_dist_org_ftk_realization_gap.png"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(4.8, 4.2))
    rng = np.random.default_rng(RANDOM_SEED)
    j = lambda s: s + rng.uniform(-.2, .2, len(s))
    ax.scatter(j(agg.ftk), j(agg.realization), s=10, alpha=.5)
    lim = max(agg.ftk.max(), agg.realization.max()) + 1
    ax.plot([0, lim], [0, lim], "k--", lw=.8, label="Realisasi = FTK")
    ax.set_xlabel("FTK (per organisasi)"); ax.set_ylabel("Realisasi (per organisasi)")
    ax.set_title("FTK vs Realisasi (jitter ±0.2)"); ax.legend()
    fig.tight_layout(); fig.savefig(FIG / "03_scatter_org_ftk_vs_realization.png"); plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(10, 3.4))
    vc = agg.position_rows.value_counts().sort_index()
    ax[0].bar(vc.index.astype(str), vc.values, color="#8172B2"); ax[0].set_title("Jumlah jabatan per organisasi")
    ax[0].set_xlabel("jabatan"); ax[0].set_ylabel("organisasi")
    vc = agg.organization_level.value_counts().sort_index()
    ax[1].bar(vc.index.astype(str), vc.values, color="#937860"); ax[1].set_title("Organisasi per level")
    ax[1].set_xlabel("level organisasi")
    fig.tight_layout(); fig.savefig(FIG / "04_positions_per_org_and_levels.png"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.6))
    gv = df.grade.fillna("<KOSONG>").value_counts().sort_values()
    ax.barh(gv.index, gv.values, color=["#C44E52" if (g == "<KOSONG>" or "(" not in g) else "#4C72B0" for g in gv.index])
    ax.set_title("Distribusi jenjang jabatan (merah = kosong / label non-standar)"); ax.set_xlabel("jumlah jabatan")
    fig.tight_layout(); fig.savefig(FIG / "05_grade_distribution.png"); plt.close(fig)

    pd.DataFrame(issues).to_csv(OUT / "issues.csv", index=False)
    profile["issues_summary"] = pd.DataFrame(issues)[["code", "severity", "affected_rows", "needs_user_decision"]].to_dict("records")
    (OUT / "profile.json").write_text(json.dumps(profile, indent=2, ensure_ascii=False, default=str))

    print(f"rows={n} orgs={profile['organizations']} issues={len(issues)}")
    for i in issues:
        print(f"[{i['severity']:7}] {i['code']:40} rows={i['affected_rows']:5} decision={i['needs_user_decision']}")


if __name__ == "__main__":
    main()
