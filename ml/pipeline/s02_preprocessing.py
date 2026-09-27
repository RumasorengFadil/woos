"""Tahap 2 — Preprocessing (PRD §22).

Menerapkan keputusan D-002..D-007 dan D-011..D-015 (docs/research/decision_log.md):
normalisasi teks, parsing & pemetaan jenjang, flag edge case, validasi duplikat &
nilai invalid, organization mapping (termasuk wadah organisasi tanpa jabatan),
job mapping, dan atribut direktorat.

Prinsip: TIDAK ada baris yang dihapus dan TIDAK ada nilai FTK/Realisasi yang diubah.
Semua treatment berupa kolom turunan atau flag, sehingga dapat diaudit dan dibalik.
Agregasi per organisasi (feature) adalah Tahap 3.

Output: ml/outputs/02_preprocessing/<dataset_version>/
    positions_clean.csv       1 baris = 1 jabatan (bersih + flag)
    organizations_clean.csv   master organisasi + hierarki + direktorat
    grade_mapping.csv         label jenjang mentah -> kode, angka, kelompok
    preprocessing_log.json    langkah, hitungan, hasil validasi

Jalankan:  ml/.venv/bin/python ml/pipeline/s02_preprocessing.py [--dataset=v2]
"""
import hashlib
import json
import re

import pandas as pd

from config import COLUMN_MAP, DATASETS, GRADE_GROUP, OUTPUTS, dataset
from s01_data_understanding import parse_grade

ROOT_LEVEL = 2
DIRECTORATE_LEVEL = 3
MARKER = re.compile(r"\*\)\s*$")


# ---------------------------------------------------------------- fungsi murni (diuji)

def normalize_text(value):
    """Tab / spasi ganda -> satu spasi, trim. NULL tetap NULL (D-015)."""
    if pd.isna(value):
        return value
    return re.sub(r"\s+", " ", str(value)).strip()


def map_grade(value):
    """Label jenjang -> (grade_code, grade_number, grade_group, mapping_rule)."""
    code, number = parse_grade(value)
    if code is None:
        return None, None, "UNKNOWN", "MISSING->UNKNOWN (PRD §22)"
    group = GRADE_GROUP.get(code)
    if group is None:
        return code, number, "UNKNOWN", "UNMAPPED->UNKNOWN"
    rule = "STANDARD" if number is not None else f"NONSTANDARD {code}->{group} (D-004 rev)"
    if code == "JE":
        rule = "JE->SPESIALIS (D-013)"
    return code, number, group, rule


def position_flags(ftk, realization):
    """Flag edge case jabatan (D-002, D-003). Tidak mengubah nilai."""
    return {
        "is_active": bool(ftk > 0 or realization > 0),
        "is_dormant": bool(ftk == 0 and realization == 0),
        "is_unbudgeted_filled": bool(ftk == 0 and realization > 0),
        "is_vacant": bool(ftk > 0 and realization == 0),
        "is_over_ftk": bool(realization > ftk),
        "is_extreme_realization": bool(realization >= 5 and realization >= 3 * max(ftk, 1)),
    }


def add_virtual_containers(orgs):
    """Tambahkan organisasi yang dirujuk sebagai parent tetapi tidak punya baris jabatan (D-014).

    Level = level anak - 1. Parent wadah hanya diisi bila dapat diinferensi tanpa ambigu:
    wadah level direktorat -> root Kantor Pusat (semua direktorat lain ber-parent root).
    """
    known = set(orgs.organization_id)
    missing = orgs[~orgs.parent_organization_id.isin(known)]
    root_ids = orgs.loc[orgs.organization_level == ROOT_LEVEL, "organization_id"].tolist()
    rows = []
    for pid, grp in missing.groupby("parent_organization_id"):
        level = int(grp.organization_level.iloc[0]) - 1
        if level < ROOT_LEVEL:  # parent root (PT PLN (Persero)) berada di luar cakupan dataset
            continue
        parent, status = None, "UNKNOWN"
        if level == DIRECTORATE_LEVEL and len(root_ids) == 1:
            parent, status = root_ids[0], "INFERRED_ROOT"
        rows.append({"organization_id": pid, "organization_name": grp.parent_name.iloc[0],
                     "parent_name": None, "parent_organization_id": parent,
                     "organization_level": level, "is_virtual_container": True,
                     "parent_status": status})
    out = orgs.assign(is_virtual_container=False, parent_status="DECLARED")
    out.loc[~out.parent_organization_id.isin(known | {r["organization_id"] for r in rows}), "parent_status"] = "OUT_OF_SCOPE"
    return pd.concat([out, pd.DataFrame(rows)], ignore_index=True)


def ancestors(org_id, parent_of):
    """Rantai [org, parent, ..., top]; berhenti bila parent tidak diketahui. Deteksi siklus."""
    chain, seen = [org_id], {org_id}
    while True:
        p = parent_of.get(chain[-1])
        if p is None or pd.isna(p) or p not in parent_of:
            return chain
        if p in seen:
            raise ValueError(f"Siklus hierarki pada {org_id}")
        chain.append(p)
        seen.add(p)


def assign_directorate(orgs, fallback=None):
    """Direktorat = leluhur ber-level 3. Root (level 2) -> dirinya sendiri.

    `fallback`: {organization_id: directorate_id} untuk rantai yang terputus (D-014),
    dengan sumber tercatat di kolom `directorate_source`.
    """
    fallback = fallback or {}
    parent_of = dict(zip(orgs.organization_id, orgs.parent_organization_id))
    level_of = dict(zip(orgs.organization_id, orgs.organization_level))
    res = []
    for o in orgs.organization_id:
        chain = ancestors(o, parent_of)
        hit = [c for c in chain if level_of[c] == DIRECTORATE_LEVEL]
        if hit:
            res.append((hit[0], "HIERARCHY", len(chain) - 1, chain[-1]))
        elif level_of[o] == ROOT_LEVEL:
            res.append((o, "ROOT", 0, o))
        elif o in fallback or chain[-1] in fallback:
            res.append((fallback.get(o, fallback.get(chain[-1])), "FALLBACK_V1_MEMBERSHIP", len(chain) - 1, chain[-1]))
        else:
            res.append((None, "UNRESOLVED", len(chain) - 1, chain[-1]))
    # Wadah tanpa jabatan dengan rantai terputus: pakai direktorat anak bila seluruh anak sepakat.
    idx = {o: i for i, o in enumerate(orgs.organization_id)}
    for i, (d, src, depth, top) in enumerate(res):
        if src != "UNRESOLVED":
            continue
        o = orgs.organization_id.iloc[i]
        child_dirs = {res[idx[c]][0] for c, p in parent_of.items() if p == o}
        if len(child_dirs) == 1 and None not in child_dirs:
            res[i] = (child_dirs.pop(), "CHILDREN_CONSENSUS", depth, top)
    out = orgs.copy()
    out["directorate_id"] = [r[0] for r in res]
    out["directorate_source"] = [r[1] for r in res]
    out["depth_to_top"] = [r[2] for r in res]
    out["top_ancestor_id"] = [r[3] for r in res]
    return out


# ---------------------------------------------------------------- pipeline

def main():
    ds = dataset()
    OUT = OUTPUTS / "02_preprocessing" / ds["version"]
    OUT.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(ds["file"])
    df = raw.rename(columns=COLUMN_MAP)
    log = {"dataset_version": ds["version"], "source_sha256": hashlib.sha256(ds["file"].read_bytes()).hexdigest(),
           "steps": [], "validation": {}}

    def step(name, decision, **counts):
        log["steps"].append({"step": name, "decision": decision, **counts})

    n0, ftk0, real0 = len(df), int(df.ftk.sum()), int(df.realization.sum())

    # 1. Normalisasi teks
    changed = 0
    for col in ["organization_name", "parent_name", "position_name", "grade"]:
        new = df[col].map(normalize_text)
        changed += int((new.fillna("") != df[col].fillna("")).sum())
        df[col] = new
    step("normalize_whitespace", "D-015", cells_changed=changed)

    # 2. Missing value
    df["is_position_name_missing"] = df.position_name.isna()
    step("missing_position_name", "Dibiarkan NULL + flag (bukan feature model)",
         rows=int(df.is_position_name_missing.sum()))

    # 3. Jenjang
    g = df.grade.map(map_grade)
    df["grade_code"] = g.str[0]
    df["grade_number"] = g.str[1].astype("Int64")
    df["grade_group"] = g.str[2]
    df["grade_mapping_rule"] = g.str[3]
    step("grade_mapping", "PRD §12, §22; D-004; D-013",
         unknown=int((df.grade_group == "UNKNOWN").sum()),
         nonstandard_mapped=int(df.grade_mapping_rule.str.startswith("NONSTANDARD").sum()),
         je_mapped=int((df.grade_code == "JE").sum()))
    gm = (df.groupby(["grade", "grade_code", "grade_number", "grade_group", "grade_mapping_rule"], dropna=False)
          .size().rename("positions").reset_index())
    gm.to_csv(OUT / "grade_mapping.csv", index=False)

    # 4. Penanda '*)'
    df["is_marked_position"] = df.position_name.fillna("").str.contains(MARKER)
    step("marked_position_flag", "D-005", rows=int(df.is_marked_position.sum()))

    # 5. Flag FTK/Realisasi
    flags = pd.DataFrame([position_flags(f, r) for f, r in zip(df.ftk, df.realization)], index=df.index)
    df = pd.concat([df, flags], axis=1)
    step("position_flags", "D-002, D-003, D-006", **{k: int(flags[k].sum()) for k in flags.columns})

    # 5b. Kemungkinan jabatan ganda: nama identik (setelah normalisasi) dalam satu organisasi
    named = df.position_name.notna()
    df["is_possible_duplicate_name"] = named & df.duplicated(["period", "organization_id", "position_name"], keep=False)
    step("possible_duplicate_name_flag", "D-015 (tidak dihapus, hanya flag)",
         rows=int(df.is_possible_duplicate_name.sum()))

    # 5c. Bukti empiris mapping label non-standar: jenjang mayoritas jabatan berjudul sama
    evidence = {}
    for label, prefix in [("AM", "ASSISTANT MANAGER"), ("VP", "VICE PRESIDENT")]:
        titled = df[df.position_name.fillna("").str.startswith(prefix) & df.grade_number.notna()]
        evidence[label] = {"title_prefix": prefix, "standard_labeled_positions": int(len(titled)),
                           "grade_group_share": titled.grade_group.value_counts(normalize=True).round(3).to_dict()}
    step("nonstandard_grade_evidence", "D-004 (revisi)", evidence=evidence)

    # 6. Duplikat (PRD §22: periode + organisasi + jabatan)
    dup = int(df.duplicated(["period", "organization_id", "position_id"]).sum())
    dup_name = int(df.dropna(subset=["position_name"]).duplicated(["period", "organization_id", "position_name"]).sum())
    step("duplicate_check", "PRD §22", duplicate_key=dup, duplicate_org_position_name=dup_name, removed=0)

    # 7. Nilai invalid
    inv = int(((df.ftk < 0) | (df.realization < 0)).sum())
    step("invalid_value_check", "PRD §22 (FTK<0 / Realisasi<0 = invalid)", invalid_rows=inv, removed=0)

    # 8. Organization mapping
    org_cols = ["organization_id", "organization_name", "parent_name", "parent_organization_id", "organization_level"]
    orgs = df[org_cols].drop_duplicates()
    consistent = bool(orgs.organization_id.is_unique)
    orgs = add_virtual_containers(orgs)
    v1_members = {}
    if "v1" in DATASETS and ds["version"] != DATASETS["v1"]["version"]:
        v1 = pd.read_csv(DATASETS["v1"]["file"]).rename(columns=COLUMN_MAP)
        v1_ids = set(v1.position_id)
        dl = df.loc[df.position_id.isin(v1_ids), "organization_id"].unique()
        dl_dir = orgs.loc[(orgs.organization_level == DIRECTORATE_LEVEL) &
                          orgs.organization_id.isin(dl), "organization_id"].tolist()
        if len(dl_dir) == 1:
            v1_members = {o: dl_dir[0] for o in dl}
    orgs = assign_directorate(orgs, fallback=v1_members)
    names = orgs.set_index("organization_id").organization_name
    orgs["directorate_name"] = orgs.directorate_id.map(names)
    counts = df.groupby("organization_id").agg(position_rows=("position_id", "size"))
    orgs = orgs.merge(counts, left_on="organization_id", right_index=True, how="left")
    orgs["position_rows"] = orgs.position_rows.fillna(0).astype(int)
    orgs["has_positions"] = orgs.position_rows > 0
    kids = orgs.groupby("parent_organization_id").size()
    orgs["n_children"] = orgs.organization_id.map(kids).fillna(0).astype(int)
    orgs["is_leaf"] = orgs.n_children == 0
    orgs["is_name_shared"] = orgs.organization_name.map(orgs.organization_name.value_counts()) > 1
    orgs = orgs.sort_values("organization_id").reset_index(drop=True)
    step("organization_mapping", "PRD §22; D-007; D-014",
         org_id_attributes_consistent=consistent,
         organizations_with_positions=int(orgs.has_positions.sum()),
         virtual_containers_added=int(orgs.is_virtual_container.sum()),
         parent_status=orgs.parent_status.value_counts().to_dict(),
         directorate_source=orgs.directorate_source.value_counts().to_dict())

    # 9. Job mapping (PRD §22: satu kode jabatan -> referensi konsisten)
    job_unique = bool(df.position_id.is_unique)
    name_grade = df.dropna(subset=["position_name"]).groupby("position_name").grade_group.nunique()
    step("job_mapping", "PRD §22", position_id_unique=job_unique,
         position_names_with_multiple_grade_groups=int((name_grade > 1).sum()))

    # 10. Output jabatan
    df = df.merge(orgs[["organization_id", "directorate_id", "directorate_name"]], on="organization_id", how="left")
    cols = ["period", "position_id", "organization_id", "directorate_id", "directorate_name",
            "organization_level", "position_name", "grade", "grade_code", "grade_number", "grade_group",
            "grade_mapping_rule", "ftk", "realization", "is_active", "is_dormant", "is_unbudgeted_filled",
            "is_vacant", "is_over_ftk", "is_extreme_realization", "is_marked_position", "is_position_name_missing",
            "is_possible_duplicate_name"]
    df[cols].to_csv(OUT / "positions_clean.csv", index=False)
    orgs.to_csv(OUT / "organizations_clean.csv", index=False)

    # 11. Validasi
    v = log["validation"]
    v["rows_preserved"] = len(df) == n0
    v["ftk_sum_preserved"] = int(df.ftk.sum()) == ftk0
    v["realization_sum_preserved"] = int(df.realization.sum()) == real0
    v["no_duplicate_key"] = dup == 0
    v["no_invalid_value"] = inv == 0
    v["every_position_has_org"] = bool(df.organization_id.isin(orgs.organization_id).all())
    v["every_declared_parent_resolvable"] = bool(
        orgs.loc[orgs.parent_status == "DECLARED", "parent_organization_id"].isin(orgs.organization_id).all())
    v["every_org_has_directorate"] = bool(orgs.directorate_id.notna().all())
    v["grade_group_never_null"] = bool(df.grade_group.notna().all())
    v["all_passed"] = all(v.values())
    log["summary"] = {"positions": len(df), "organizations_total": len(orgs),
                      "organizations_with_positions": int(orgs.has_positions.sum()),
                      "ftk": ftk0, "realization": real0,
                      "directorates": orgs[orgs.has_positions].groupby("directorate_name").size().to_dict()}
    (OUT / "preprocessing_log.json").write_text(json.dumps(log, indent=2, ensure_ascii=False, default=str))

    for s in log["steps"]:
        print(s)
    print("validation:", v)
    if not v["all_passed"]:
        raise SystemExit("VALIDASI GAGAL")


if __name__ == "__main__":
    main()
