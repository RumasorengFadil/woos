# AGENTS.md

## Project

WOOS (Workforce Organization Segmentation) adalah prototype penelitian + aplikasi untuk mengelompokkan unit organisasi Direktorat Legal dan Manajemen Human Capital berdasarkan FTK (formasi) dan realisasi tenaga kerja, menggunakan unsupervised learning (K-Means, Agglomerative Hierarchical, DBSCAN). Hasil model yang tervalidasi dipublish ke PostgreSQL dan ditampilkan oleh dashboard web PHP. Studi kasus ini juga disiapkan untuk publikasi jurnal.

## Product source of truth

`docs/product/PRD.md` adalah requirement resmi. Jangan ubah kecuali diminta user.
`docs/product/roadmap.md` melacak increment & progres. Jangan menampilkan rencana sebagai sudah diimplementasikan.
`docs/architecture/ARCHITECTURE_BLUEPRINT.md` adalah acuan arsitektur & konvensi engineering sampai PRD 1.0 selesai (salinan tetap, jangan diubah). Pemetaan aturan blueprint → WOOS ada di `docs/architecture/blueprint_compliance.md`; deviasi dicatat sebagai ADR di `docs/architecture/overview.md`.

Bangun secara incremental. Selesaikan dan validasi tahap saat ini sebelum mulai tahap berikutnya.

## Architecture

- `ml/` — pipeline eksperimen Python (ADR-001 di `docs/architecture/overview.md`). Script per tahap `ml/pipeline/sNN_<tahap>.py`, output ke `ml/outputs/NN_<tahap>/`.
- Dashboard — PHP native + PostgreSQL, modular monolith (`modules/auth`, `modules/segmentation`, `modules/admin`); query domain di `modules/segmentation/repository.php` (read-only). **Dashboard tidak boleh melakukan clustering atau rule klasifikasi sendiri**; hanya membaca hasil dengan `validation_status = APPROVED`.
- `data/raw/` read-only. Transformasi apa pun menghasilkan file baru di `ml/outputs/<NN_tahap>/<dataset_version>/`.
- Dataset diregistrasi di `ml/pipeline/config.py` (`DATASETS`, `ACTIVE_DATASET`). Preprocessing tidak menghapus baris dan tidak mengubah FTK/Realisasi; treatment berupa flag/kolom turunan.
- Fungsi murni pipeline diuji di `tests/ml/`.
- Keamanan web: CSP ketat tanpa `unsafe-inline` — **jangan pakai atribut `style=` atau `<script>` inline**; data chart via `json_script()`, warna cluster via `cluster_class()`. Setiap halaman memanggil `require_permission()`; output selalu lewat `e()`; POST wajib `csrf_field()`/`csrf_verify()`.
- Database: `docs/database/schema.md`. Perubahan struktur WAJIB lewat migration baru (jangan edit migration yang sudah diterapkan). Hanya `s08_publish.py` yang menulis ke DB; dashboard membaca view `v_*`.
- Figure statis memakai `ml/pipeline/viz_style.py` (palet dataviz: kategorikal urutan tetap, sequential biru, diverging biru–merah; scatter > 3 kategori → small multiples).

## Commands

```bash
# dataset aktif: KP-2026-09-25-v2 (config.ACTIVE_DATASET); tambahkan --dataset=v1 untuk versi lama
ml/.venv/bin/python ml/pipeline/s01_data_understanding.py
ml/.venv/bin/python ml/pipeline/s01b_dataset_adequacy.py
ml/.venv/bin/python ml/pipeline/s01c_version_reconciliation.py
ml/.venv/bin/python ml/pipeline/s02_preprocessing.py
ml/.venv/bin/python ml/pipeline/s03_feature_engineering.py
ml/.venv/bin/python ml/pipeline/s04_eda.py
ml/.venv/bin/python ml/pipeline/s05_experiments.py
ml/.venv/bin/python ml/pipeline/s06_evaluation.py
ml/.venv/bin/python ml/pipeline/s07_interpretation.py
ml/.venv/bin/python ml/pipeline/s07b_record_approval.py   # hanya setelah validasi bisnis
ml/.venv/bin/python tools/migrate.py --create-db
ml/.venv/bin/python ml/pipeline/s08_publish.py            # menolak model non-APPROVED
ml/.venv/bin/python -m pytest tests/ml

# dashboard (PHP 8.3+, pdo_pgsql)
php tools/create_user.php <username> "<nama>" <ADMIN|VIEWER>   # password via STDIN
php -S localhost:8090 -t . router.php
php tests/php/run.php
```

Setup venv: `python3 -m venv ml/.venv && ml/.venv/bin/pip install -r ml/requirements.txt`

## Documentation rules

- `docs/research/` = Research/Experiment Documentation (temuan, metode, keputusan — bahan jurnal).
- `docs/reports/YYYY/MM/DD/` = Implementation Report (format blueprint: Changed / Files / Database / Tests / Manual Test / Documentation).
- Keputusan metodologis wajib dicatat di `docs/research/decision_log.md` sebelum dieksekusi.
- Setiap angka di dokumen harus berasal dari output pipeline. Jangan laporkan test `PASS` bila tidak dijalankan.
- Label cluster diberikan setelah profiling, tidak pernah lewat rule `if gap > X`.
- Seed tetap: `RANDOM_SEED = 42` di `ml/pipeline/config.py`.
