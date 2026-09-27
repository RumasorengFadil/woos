# Implementation Report — Tahap 5: Eksperimen Model

**Tanggal:** 2026-09-25
**Increment:** PRD §26–§36, §44, §71–§72 pada `KP-2026-09-25-v2` / `F2` / model `v1`
**Temuan riset:** `docs/research/05_experiments.md`

## Implementation Report

### Changed
- Feature set F2 diterapkan di `s03_feature_engineering.py` (D-020), dengan `FEATURE_VERSION = "F2"`.
  - `FEATURE_SETS_F1` dipertahankan dan dipakai `s04_eda.py` agar EDA tetap reproducible; EDA dijalankan ulang dan PASS.
  - Artefak F1 (scaler, schema, log, scaling summary) dipindah ke `ml/outputs/03_feature_engineering/KP-2026-09-25-v2/archive_F1/`.
- Script `s05_experiments.py`:
  - 619 run: K-Means 84, Hierarchical 252, DBSCAN 283 = 4 feature set × 2 scaler, ditambah varian vektor unik;
  - metrik internal per run;
  - registri eksperimen dengan metadata PRD §44 (ID, model/version, timestamp, dataset/feature/code version, features, scaler, hyperparameter, seed, metrik, noise, `validation_status = EXPERIMENT`);
  - label per run, elbow (kneedle), cophenetic, k-distance;
  - 7 figure (E01…E06; E02/E03 per scaler).
- Decision log: D-020…D-024 APPROVED; D-025, D-026 (detail implementasi) APPLIED.

### Files
- `ml/pipeline/s05_experiments.py` (baru); `ml/pipeline/s03_feature_engineering.py`, `ml/pipeline/s04_eda.py` (diubah)
- `tests/ml/test_s05_experiments.py` (baru); `tests/ml/test_s03_feature_engineering.py` (+1 test F2)
- `ml/outputs/03_feature_engineering/KP-2026-09-25-v2/` (F2) + `archive_F1/`
- `ml/outputs/05_experiments/KP-2026-09-25-v2/` — `experiments.json`, `experiments.csv`, `labels.csv.gz`, `elbow.csv`, `cophenetic.csv`, `kdistance.csv`, `experiment_summary.json`, `figures/E01…E06`
- Docs: `docs/research/05_experiments.md` (baru), `decision_log.md`, `00_research_protocol.md`, `journal_outline.md`, `docs/research/README.md`, `docs/product/roadmap.md`, `AGENTS.md`, `README.md`

### Database
- No database changes. Model belum dipublish; semua run berstatus `EXPERIMENT` (PRD §45).

### Tests
- `ml/.venv/bin/python -m pytest tests/ml`: PASS (35 passed).
- `s03_feature_engineering.py` (F2): PASS, semua validasi; rank penuh di semua set.
- `s04_eda.py` dijalankan ulang setelah perubahan import: PASS.
- `s05_experiments.py` end-to-end: PASS (±33 detik).

### Manual Test
1. `ml/.venv/bin/python ml/pipeline/s05_experiments.py` → `"runs": 619`, `code_version` tercetak.
2. `experiments.csv`: filter `experiment_id = EXP-KM-002` → set A, standard, K = 3, silhouette 0,4827.
3. `experiments.csv`: filter `EXP-DB-001` → 38 cluster, silhouette 1,0 (artefak titik kembar, lihat dokumen riset §4).
4. `labels.csv.gz`: 1.280 baris × 619 kolom run.

### Documentation
- Lihat Files.
