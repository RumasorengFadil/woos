# Implementation Report — Tahap 2: Preprocessing

**Tanggal:** 2026-09-25
**Increment:** PRD §22 Preprocessing pada `KP-2026-09-25-v2`
**Temuan riset:** `docs/research/02_preprocessing.md`

## Implementation Report

### Changed
- Script `s02_preprocessing.py`:
  - normalisasi whitespace;
  - parsing & mapping jenjang (7 kelompok PRD §12);
  - flag jabatan: aktif, dormant, terisi tanpa formasi, kosong, melebihi FTK, ekstrem, bertanda `*)`, nama kosong, kemungkinan ganda;
  - cek duplikat & nilai invalid;
  - organization mapping dengan 4 wadah virtual dan atribut direktorat (beserta sumbernya);
  - job mapping;
  - bukti empiris untuk label jenjang non-standar;
  - 9 validasi otomatis (script berhenti bila ada yang gagal).
- Revisi mapping `AM` → GENERALIS di `config.py` berdasarkan bukti data (D-004 rev).
- Fondasi test: `tests/ml/` + pytest (ditambahkan ke `ml/requirements.txt`).

### Files
- `ml/pipeline/s02_preprocessing.py` (baru)
- `ml/pipeline/config.py` (mapping AM)
- `tests/ml/conftest.py`, `tests/ml/test_s02_preprocessing.py` (baru)
- `ml/requirements.txt` (+ pytest 8.3.3 dan dependensinya)
- `ml/outputs/02_preprocessing/KP-2026-09-25-v2/` — `positions_clean.csv`, `organizations_clean.csv`, `grade_mapping.csv`, `preprocessing_log.json`
- Docs: `docs/research/02_preprocessing.md` (baru), `decision_log.md` (D-004 rev, D-014, D-015; status D-001…D-010), `docs/product/roadmap.md`, `AGENTS.md`, `README.md`, `docs/architecture/overview.md`, `docs/architecture/blueprint_compliance.md`

### Database
- No database changes.

### Tests
- `ml/.venv/bin/python -m pytest tests/ml`: PASS (18 passed).
- Validasi internal `s02_preprocessing.py`: PASS (9/9: baris, ΣFTK, ΣRealisasi tetap; tanpa duplikat kunci; tanpa nilai invalid; setiap jabatan punya org; setiap parent deklaratif teresolusi; setiap org punya direktorat; `grade_group` tidak NULL).

### Manual Test
1. `ml/.venv/bin/python ml/pipeline/s02_preprocessing.py` → baris terakhir `validation: {... 'all_passed': True}`.
2. Buka `organizations_clean.csv`, filter `is_virtual_container = True` → 4 baris (ORG-0013, ORG-0226, ORG-1072, ORG-1074).
3. Buka `grade_mapping.csv` → baris `AM` bergrup GENERALIS dengan aturan `NONSTANDARD AM->GENERALIS (D-004 rev)`; baris kosong → UNKNOWN.
4. `positions_clean.csv`: jumlah `is_possible_duplicate_name = True` = 2 (ORG-0908).

### Documentation
- Lihat Files.
