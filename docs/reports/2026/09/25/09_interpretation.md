# Implementation Report — Tahap 7: Interpretasi, Profiling & Validasi

**Tanggal:** 2026-09-25
**Increment:** PRD §39–§45, §73, §85 untuk model kandidat EXP-KM-067
**Temuan riset:** `docs/research/07_cluster_interpretation.md`

## Implementation Report

### Changed
- D-029 dicatat sebagai APPROVED.
- Script `s07_interpretation.py`:
  - refit model final dan verifikasi identik dengan registri Tahap 5 (script berhenti bila tidak identik);
  - profil statistik per cluster (PRD §39) + z-relatif + kalimat karakteristik otomatis;
  - label usulan per `cluster_id` dengan verifikasi tanda tangan profil (script berhenti bila cluster tertukar);
  - dataset profil cluster (PRD §43);
  - hasil per organisasi (PRD §42): `cluster_id`, `cluster_label`, `cluster_distance`, flag atipikal, rata-rata cluster untuk penjelasan (PRD §85), dan 21 org `NOT_SEGMENTED`;
  - organisasi representatif & atipikal; crosstab direktorat/level; sub-analisis DLMHC;
  - artefak model PRD §73 dengan `validation_status = PENDING_BUSINESS_VALIDATION`;
  - 5 figure.
- Bug yang ditemukan dan diperbaiki saat verifikasi output: kalimat karakteristik memuat "+nan SD" (reindex setelah filter) dan kapitalisasi "Ftk".

### Files
- `ml/pipeline/s07_interpretation.py` (baru)
- `tests/ml/test_s07_interpretation.py` (baru, 5 test)
- `ml/outputs/07_interpretation/KP-2026-09-25-v2/`:
  - `cluster_profile_stats.csv`, `cluster_relative_z.csv`, `cluster_profile.csv`
  - `organization_results.csv`, `representative_organizations.csv`, `atypical_members.csv`
  - `cluster_by_directorate.csv`, `cluster_by_level.csv`, `cluster_dlmhc_vs_other.csv`
  - `interpretation_summary.json`, `figures/P01…P05`
  - `model_artifacts/{model.joblib, scaler.joblib, feature_schema.json, metrics.json, cluster_profile.json}`
- Docs: `docs/research/07_cluster_interpretation.md` (baru), `decision_log.md` (D-029 approved, D-030), `journal_outline.md`, `docs/research/README.md`, `docs/product/roadmap.md`, `AGENTS.md`, `README.md`

### Database
- No database changes. Publish ke database dilakukan di Tahap 8, setelah D-030 disetujui.

### Tests
- `ml/.venv/bin/python -m pytest tests/ml`: PASS (47 passed).
- `s07_interpretation.py` end-to-end: PASS. Refit ARI = 1,0; semua tanda tangan cluster cocok.

### Manual Test
1. `ml/.venv/bin/python ml/pipeline/s07_interpretation.py` → `"refit_ari": 1.0`, ukuran cluster {0: 59, 1: 388, 2: 537, 3: 141, 4: 155}.
2. `organization_results.csv` → 1.301 baris (1.280 tersegmentasi + 21 `NOT_SEGMENTED`).
3. Cari ORG-0005 → `cluster_label = Potensi Overstaffing`, `is_atypical_member = True`.
4. `model_artifacts/metrics.json` → `validation_status: PENDING_BUSINESS_VALIDATION`.

### Documentation
- Lihat Files.
