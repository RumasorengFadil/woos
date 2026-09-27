# Implementation Report — Tahap 3: Feature Engineering & Scaling

**Tanggal:** 2026-09-25
**Increment:** PRD §6–§12, §17, §23, §24, §79–§81 pada `KP-2026-09-25-v2`, feature version `F1`
**Temuan riset:** `docs/research/03_feature_engineering.md`

## Implementation Report

### Changed
- Script `s03_feature_engineering.py`:
  - agregasi jabatan bersih ke organisasi untuk dua definisi unit (direct, rollup);
  - seluruh feature PRD §6 dan feature turunan (balance_index, vacant_share, proporsi jenjang, komposisi FTK/realisasi per jenjang);
  - flag populasi model;
  - 4 feature set (A/B/C/R);
  - fit dan simpan StandardScaler & RobustScaler per unit × set;
  - `feature_schema.json` (kamus + set + versi);
  - validasi invarian (script berhenti bila ada yang gagal).
- Fungsi `build_matrix()` disediakan untuk Tahap 5 agar input model diambil dari definisi set yang sama.
- Decision log D-016…D-019; update D-010 (batas d dari n v2).

### Files
- `ml/pipeline/s03_feature_engineering.py` (baru)
- `tests/ml/test_s03_feature_engineering.py` (baru)
- `ml/outputs/03_feature_engineering/KP-2026-09-25-v2/` — `features_direct.csv`, `features_rollup.csv`, `feature_schema.json`, `feature_log.json`, `feature_descriptives_direct.csv`, `scaling_summary.csv`, `scalers/*.joblib` (16)
- Docs: `docs/research/03_feature_engineering.md` (baru), `decision_log.md`, `00_research_protocol.md`, `journal_outline.md`, `docs/research/README.md`, `docs/product/roadmap.md`, `AGENTS.md`, `README.md`

### Database
- No database changes.

### Tests
- `ml/.venv/bin/python -m pytest tests/ml`: PASS (23 passed: 18 Tahap 2 + 5 Tahap 3).
- Validasi internal s03: PASS (11 cek direct, 12 cek rollup).

### Manual Test
1. `ml/.venv/bin/python ml/pipeline/s03_feature_engineering.py` → `direct … 'model_population': 1280` dan `all_validation_passed: True`.
2. Buka `features_direct.csv`, cari ORG-0646 → ftk 14, realization 7, gap 7, fulfillment_ratio 0,5, balance_index −0,333, position_count 13.
3. Filter `in_model_population = 0` → 21 organisasi, semuanya `position_count = 0`.
4. `ls scalers/` → 16 file `.joblib`.

### Documentation
- Lihat Files.
