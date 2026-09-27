# Implementation Report — Tahap 1c: Revalidasi dengan Dataset v2

**Tanggal:** 2026-09-25
**Increment:** Integrasi dataset Kantor Pusat (v2), Tahap 1/1b dijalankan ulang, rekonsiliasi v1–v2
**Temuan riset:** `docs/research/01c_dataset_v2.md`

## Implementation Report

### Changed
- Registri dataset berversi di `config.py` (`DATASETS`, `ACTIVE_DATASET = "v2"`, argumen CLI `--dataset=`). Mapping kolom ditambah `ID Parent`, dan `GRADE_GROUP` dipindah ke config.
- `s01_data_understanding.py`:
  - resolusi parent memakai `ID Parent` bila tersedia (validasi nama & level); fallback nama+level untuk v1;
  - deteksi whitespace abnormal;
  - output per versi dataset.
- `s01b_dataset_adequacy.py`: output per versi, cakupan field membaca kolom `ID Parent`, baseline Hopkins memakai n aktual.
- Script baru `s01c_version_reconciliation.py` (pencocokan berdasarkan ID jabatan).
- Output v1 lama dipindah ke subfolder `DLMHC-2026-09-25-v1/`. Hasil v1 direproduksi identik; hanya C_grade berubah kecil setelah revisi D-004 (dicatat di `01b_dataset_adequacy.md`).

### Files
- `data/raw/kantor_pusat_semua_direktorat.csv` (baru, SHA-256 `29b39045…1f82`)
- `ml/pipeline/config.py`, `s01_data_understanding.py`, `s01b_dataset_adequacy.py` (diubah)
- `ml/pipeline/s01c_version_reconciliation.py` (baru)
- `ml/outputs/01_data_understanding/{DLMHC-2026-09-25-v1,KP-2026-09-25-v2}/`, `ml/outputs/01b_dataset_adequacy/{…}/`, `ml/outputs/01c_version_reconciliation/`
- Docs: `docs/research/01c_dataset_v2.md` (baru), `dataset_card.md`, `decision_log.md` (D-011…D-013), `00_research_protocol.md` (populasi, RQ5), `journal_outline.md`, `01_data_understanding.md`, `01b_dataset_adequacy.md` (path & status)

### Database
- No database changes.

### Tests
- `s01` & `s01b` pada v1: PASS, angka identik dengan run sebelumnya (38 vektor unik, Hopkins dedup A_core 0,862).
- `s01` & `s01b` & `s01c` pada v2: PASS (exit 0).
- Unit test otomatis untuk s01/s01b: NOT TESTED (fungsi `parse_grade` diuji via test Tahap 2).

### Manual Test
1. `ml/.venv/bin/python ml/pipeline/s01_data_understanding.py` → `rows=3528 orgs=1301 issues=12`.
2. `ml/.venv/bin/python ml/pipeline/s01c_version_reconciliation.py` → `v1_positions_found_in_v2: 1157`, `realization_changed_positions: 23`, `realization_delta: -45`.
3. `ml/.venv/bin/python ml/pipeline/s01_data_understanding.py --dataset=v1` → `rows=1157 orgs=379`.

### Documentation
- Lihat Files.
