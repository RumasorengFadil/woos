# Instalasi & Menjalankan — WOOS

## Prasyarat
- Python 3.9+ dan PostgreSQL 14+ (lokal: 17).
- PHP 8.3+ dan Apache/MAMP untuk dashboard (Tahap 9).

## Langkah

```bash
cp .env.example .env                     # isi DB_USER / DB_PASSWORD
python3 -m venv ml/.venv && ml/.venv/bin/pip install -r ml/requirements.txt
ml/.venv/bin/python tools/migrate.py --create-db
```

## Pipeline end-to-end (dataset aktif: `KP-2026-09-25-v2`)

```bash
cd ml/pipeline
../.venv/bin/python s01_data_understanding.py
../.venv/bin/python s01b_dataset_adequacy.py
../.venv/bin/python s01c_version_reconciliation.py
../.venv/bin/python s02_preprocessing.py
../.venv/bin/python s03_feature_engineering.py
../.venv/bin/python s04_eda.py
../.venv/bin/python s05_experiments.py          # ±35 detik
../.venv/bin/python s06_evaluation.py           # ±2 menit (bootstrap)
../.venv/bin/python s07_interpretation.py
../.venv/bin/python s07b_record_approval.py     # HANYA setelah validasi bisnis (PRD §45)
../.venv/bin/python s08_publish.py              # menolak model yang belum APPROVED
```

Test: `ml/.venv/bin/python -m pytest tests/ml` (integration test memakai database `woos_test`).

## Dashboard (Tahap 9)

```bash
php -v                                              # PHP 8.3+ dengan pdo_pgsql
php tools/create_user.php admin "Nama Admin" ADMIN  # password via STDIN
php -S localhost:8090 -t . router.php               # server pengembangan → http://localhost:8090
```

- Apache/MAMP: arahkan document root ke folder proyek. `.htaccess` memblokir folder non-publik. PHP MAMP wajib memiliki `pdo_pgsql`.
- Figure riset untuk dashboard (`assets/figures/`) dihasilkan oleh `s08_publish.py`.
- Test PHP: `php tests/php/run.php` (unit + smoke HTTP + audit statis; memakai akun uji di `database/seeds/dev_users.local.json`).
