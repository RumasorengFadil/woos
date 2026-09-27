# WOOS — Workforce Organization Segmentation

Segmentasi unit organisasi berdasarkan FTK dan realisasi tenaga kerja menggunakan K-Means, Hierarchical Clustering, dan DBSCAN, dengan dashboard web yang hanya membaca hasil model tervalidasi.

- Requirement: `docs/product/PRD.md`
- Progres: `docs/product/roadmap.md` · Acceptance PRD 1.0: `docs/product/prd_acceptance.md`
- Instalasi: `docs/deployment/installation.md`
- Arsitektur: `docs/architecture/overview.md` (acuan: `docs/architecture/ARCHITECTURE_BLUEPRINT.md`)
- Penelitian: `docs/research/`
- Implementation report: `docs/reports/`

## Setup ML

```bash
python3 -m venv ml/.venv
ml/.venv/bin/pip install -r ml/requirements.txt
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
