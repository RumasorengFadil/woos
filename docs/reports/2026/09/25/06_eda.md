# Implementation Report — Tahap 4: Exploratory Data Analysis

**Tanggal:** 2026-09-25
**Increment:** PRD §25 EDA + analisis tambahan protokol §6 pada `KP-2026-09-25-v2` / `F1`
**Temuan riset:** `docs/research/04_eda.md`

## Implementation Report

### Changed
- Script `s04_eda.py`:
  - 15 figure: 7 visualisasi minimum PRD §25 dan 8 figure tambahan (level, PCA, scaler, skewness, titik kembar, Hopkins F1, DLMHC vs lainnya, VIF kandidat F2);
  - tabel statistik: korelasi Spearman/Pearson, VIF, ε² level/direktorat, outlier univariat & multivariat (Mahalanobis), skewness, PCA, perbandingan scaler, ringkasan direktorat, kombinasi FTK–realisasi, gap per organisasi, evaluasi kandidat feature set F2.
- Modul gaya figure `viz_style.py`:
  - palet dataviz divalidasi dengan `validate_palette.js` (light: semua PASS; WARN kontras 3 slot diimbangi legenda + tabel CSV);
  - scatter dengan > 3 kategori dibuat sebagai small multiples.
- Decision log: D-016…D-019 APPROVED; usulan D-020…D-024.
- Tidak ada perubahan pada feature Tahap 3. Usulan F2 baru diterapkan setelah disetujui.

### Files
- `ml/pipeline/s04_eda.py`, `ml/pipeline/viz_style.py` (baru)
- `tests/ml/test_s04_eda.py` (baru)
- `ml/outputs/04_eda/KP-2026-09-25-v2/` — `figures/F01…F15.png`, `eda_summary.json`, `correlation_spearman.csv`, `correlation_pearson.csv`, `vif_by_feature_set.csv`, `feature_set_candidates_vif.csv`, `association_level_directorate.csv`, `outliers_univariate.csv`, `outliers_multivariate_setB.csv`, `skewness.csv`, `pca_explained_variance.csv`, `scaler_comparison_setC.csv`, `hopkins_F1.csv`, `grade_distribution_by_directorate.csv`, `gap_per_organization.csv`, `ftk_realization_combinations.csv`, `summary_by_directorate.csv`
- Docs: `docs/research/04_eda.md` (baru), `decision_log.md`, `00_research_protocol.md`, `journal_outline.md`, `docs/research/README.md`, `docs/product/roadmap.md`, `AGENTS.md`, `README.md`

### Database
- No database changes.

### Tests
- `ml/.venv/bin/python -m pytest tests/ml`: PASS (28 passed).
- `s04_eda.py` end-to-end: PASS (exit 0).
- Pemeriksaan visual F03, F05, F09: label yang bertabrakan (judul/legenda F05, label F03) sudah diperbaiki dan dirender ulang.

### Manual Test
1. `ml/.venv/bin/python ml/pipeline/s04_eda.py` → berakhir tanpa error; `figures/` berisi 15 PNG.
2. `feature_set_candidates_vif.csv` → baris `F1,C,raw` max_vif 75,89; baris `F2,C,raw` max_vif 4,88.
3. `outliers_multivariate_setB.csv` → 27 baris; teratas ORG-0138 (FTK 34, realisasi 0).
4. `association_level_directorate.csv` → `pct_MA_MAK` epsilon2_level 0,544.

### Documentation
- Lihat Files.
