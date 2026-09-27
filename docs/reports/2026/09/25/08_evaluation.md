# Implementation Report — Tahap 6: Evaluasi & Pemilihan Model

**Tanggal:** 2026-09-25
**Increment:** PRD §36–§38, §45, §55 pada 619 run Tahap 5
**Temuan riset:** `docs/research/06_evaluation.md`

## Implementation Report

### Changed
- Kriteria kelayakan (D-027) dan pemilihan multi-kriteria (D-028) dicatat di decision log **sebelum** script dijalankan.
- Script `s06_evaluation.py`:
  - filter kelayakan;
  - stabilitas bootstrap: 50 × subsample 80 % per run layak, 143 run;
  - η² relevansi workforce, Cramér's V (bias-corrected) × level/direktorat, ARI vs baseline tanda gap;
  - agregasi peringkat + 9 varian sensitivitas bobot;
  - tabel perbandingan PRD §55;
  - robustness model terbaik tiap algoritma (seed, rollup, tanpa outlier, varian unik);
  - profil ringkas finalis;
  - diagnostik post-hoc kesetaraan dengan aturan satu feature (D-029) + pemeringkatan ulang;
  - 5 figure.
- Status kandidat: `SELECTED_CANDIDATE` sesuai D-028. Belum ada model `APPROVED` (menunggu Tahap 7, PRD §45).

### Files
- `ml/pipeline/s06_evaluation.py` (baru)
- `tests/ml/test_s06_evaluation.py` (baru, 7 test)
- `ml/outputs/06_evaluation/KP-2026-09-25-v2/` — `eligible_runs.csv`, `eligible_runs_nontrivial_posthoc.csv`, `model_comparison.csv`, `selection.json`, `selection_posthoc_D029.json`, `rank_sensitivity.csv`, `robustness.json`, `baseline.csv`, `finalist_cluster_profiles.csv`, `selected_labels.csv`, `figures/V01…V05`
- Docs: `docs/research/06_evaluation.md` (baru), `decision_log.md` (D-025…D-029), `00_research_protocol.md`, `journal_outline.md`, `docs/research/README.md`, `docs/product/roadmap.md`, `AGENTS.md`, `README.md`

### Database
- No database changes.

### Tests
- `ml/.venv/bin/python -m pytest tests/ml`: PASS (42 passed).
- `s06_evaluation.py` end-to-end: PASS (±2 menit, didominasi bootstrap).

### Manual Test
1. `ml/.venv/bin/python ml/pipeline/s06_evaluation.py` → funnel mencetak `ELIGIBLE 143`.
2. `model_comparison.csv` → kolom DBSCAN = EXP-DB-067, Validation = SELECTED_CANDIDATE.
3. `selection_posthoc_D029.json` → `n_trivial: 49`, `top_posthoc.experiment_id: EXP-KM-067`.
4. `robustness.json` → K-Means `seed_stability_ari_min: 1.0`.

### Documentation
- Lihat Files.
