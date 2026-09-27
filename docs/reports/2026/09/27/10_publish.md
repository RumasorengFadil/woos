# Implementation Report — Tahap 8: Publish Hasil Model ke Database

**Tanggal:** 2026-09-27
**Increment:** PRD §42–§45, §65, §73–§74. Model tervalidasi EXP-KM-067 dipublish ke PostgreSQL.

## Implementation Report

### Changed
- Validasi bisnis dicatat (D-030 APPROVED, V1–V5):
  - `s07b_record_approval.py` menulis `approval.json` dan mengubah status model menjadi `APPROVED`;
  - `s07_interpretation.py` kini mempertahankan status approval bila dijalankan ulang.
- Konfigurasi `.env.example` / `.env` (gitignored) dan helper koneksi `ml/pipeline/db.py`.
- Migration runner `tools/migrate.py`: berurutan, satu transaksi per file, checksum SHA-256, dan menolak migration yang diedit setelah diterapkan.
- Lima migration: schema, tabel referensi, tabel model, view dashboard, pelebaran kolom Calinski–Harabasz.
- Script `s08_publish.py`:
  - **gerbang APPROVED** (PRD §45);
  - publish idempotent dalam satu transaksi: dataset, organisasi, feature, 619 eksperimen, 3 model (1 validated + 2 pembanding, D-031), profil cluster, hasil per organisasi;
  - 9 validasi pasca-publish (gagal → rollback);
  - log publish.
- Dependensi baru: `psycopg2-binary 2.9.9` (driver PostgreSQL), dikunci di `ml/requirements.txt`.

### Files
- Baru:
  - `.env.example`; `.env` (lokal, tidak di-commit)
  - `ml/pipeline/db.py`, `ml/pipeline/s07b_record_approval.py`, `ml/pipeline/s08_publish.py`
  - `tools/migrate.py`
  - `database/migrations/001…005_*.sql`
  - `tests/ml/test_s08_publish.py`
  - `docs/database/schema.md`, `docs/database/migrations.md`, `docs/deployment/installation.md`
- Diubah: `ml/pipeline/s07_interpretation.py`, `ml/requirements.txt`, `docs/research/decision_log.md` (D-030 approved, D-031), `docs/architecture/blueprint_compliance.md`, `docs/architecture/overview.md`, `docs/README.md`, `docs/product/roadmap.md`, `docs/research/journal_outline.md`, `AGENTS.md`, `README.md`
- Output: `ml/outputs/07_interpretation/KP-2026-09-25-v2/model_artifacts/approval.json`, `ml/outputs/08_publish/publish_log_*.json`

### Database
- Database baru: `woos` (dan `woos_test` untuk integration test), schema `woos`.
- Tabel baru: `schema_migrations`, `dataset_version`, `organization`, `organization_feature`, `experiment`, `model`, `cluster_profile`, `cluster_result`.
- View baru: `v_validated_model`, `v_validated_organization`, `v_model_comparison`.
- Kolom diubah (005): `experiment.calinski_harabasz` → DOUBLE PRECISION.
- Dokumentasi: `docs/database/schema.md`, `docs/database/migrations.md`.

### Tests
- `ml/.venv/bin/python -m pytest tests/ml`: PASS (52 passed), termasuk integration test PostgreSQL:
  - migrate dua kali → "up to date";
  - publish dua kali → jumlah model tetap 3;
  - constraint `chk_validated_requires_approved` dan `uq_model_validated_per_dataset` menolak pelanggaran.
- Validasi pasca-publish di `woos`: PASS 9/9.

### Manual Test
1. `ml/.venv/bin/python tools/migrate.py` → `applied: nothing (up to date)`.
2. `psql woos -c "select experiment_id, validation_status, is_validated_model from woos.model"` → EXP-KM-067 APPROVED/t; EXP-HC-044 dan EXP-DB-067 EXPERIMENT/f.
3. `psql woos -c "select cluster_label, count(*) from woos.v_validated_organization group by 1"` → Relatif Stabil 537, Understaffing Parsial 388, Potensi Overstaffing 155, Understaffing Kritis 141, Terisi Tanpa Formasi 59, Tidak Tersegmentasi 21.
4. Uji gerbang: ubah sementara `validation_status` di `metrics.json` menjadi `PENDING_BUSINESS_VALIDATION`, jalankan `s08_publish.py` → harus berhenti dengan `PublishRefused`. Kembalikan dengan `s07b_record_approval.py`.

### Documentation
- Lihat Files.
