# Implementation Report — Tahap 0 (Setup) & Tahap 1 (Data Understanding)

**Tanggal:** 2026-09-25
**Increment:** Setup repositori + PRD §21 Data Understanding
**Temuan riset:** lihat `docs/research/01_data_understanding.md` (report ini hanya mencatat implementasi)

## Implementation Report

### Changed
- Inisialisasi struktur proyek sesuai blueprint (hanya folder yang dipakai).
- Dataset mentah disalin ke `data/raw/` dan diberi versi `DLMHC-2026-09-25-v1` + SHA-256.
- PRD disalin ke `docs/product/PRD.md` sebagai product source of truth.
- Virtualenv Python + dependensi ML terkunci (ADR-001).
- Script Tahap 1: profiling, deteksi isu kualitas data, resolusi hierarki berbasis nama+level, 5 figure.
- Dokumentasi penelitian terpisah di `docs/research/`.

### Files
- `ml/pipeline/config.py` — path, versi dataset, seed, mapping kolom
- `ml/pipeline/s01_data_understanding.py` — script Tahap 1
- `ml/requirements.txt` — dependensi terkunci
- `ml/outputs/01_data_understanding/` — `profile.json`, `issues.csv`, `org_hierarchy_check.csv`, `org_direct_aggregate.csv`, `figures/01…05.png`
- `data/raw/direktorat_legal_manajemen_human_capital.csv`
- `docs/product/PRD.md`, `docs/product/roadmap.md`
- `docs/architecture/overview.md` (ADR-001)
- `docs/research/README.md`, `00_research_protocol.md`, `dataset_card.md`, `decision_log.md`, `journal_outline.md`, `01_data_understanding.md`
- `README.md`, `AGENTS.md`, `CLAUDE.md`, `.gitignore`, `docs/README.md`

### Database
- No database changes.

### Tests
- Script Tahap 1 dijalankan end-to-end: PASS (exit 0, 12 isu terdeteksi, semua output tertulis).
- Unit test otomatis: NOT TESTED (belum ada logika transformasi; test dimulai Tahap 2 untuk fungsi preprocessing & feature).

### Manual Test
1. `ml/.venv/bin/python ml/pipeline/s01_data_understanding.py` — harus mencetak `rows=1157 orgs=379 issues=12`.
2. `shasum -a 256 data/raw/*.csv` — harus `3d805a9d…b243` (sama dengan `profile.json`).
3. Buka `ml/outputs/01_data_understanding/issues.csv` — 12 baris isu, kolom `needs_user_decision`.
4. Buka `org_hierarchy_check.csv` — 374 `RESOLVED_NAME_LEVEL`, 4 `PARENT_NOT_IN_DATASET`, 1 `RESOLVED_NAME_ONLY_LEVEL_MISMATCH`.

### Documentation
- Dibuat: seluruh file di `docs/` di atas.
- `roadmap.md`: Tahap 1 = DONE – AWAITING VALIDATION.

### Blocking
- Tahap 2 menunggu keputusan D-001…D-007 (`docs/research/decision_log.md`).
