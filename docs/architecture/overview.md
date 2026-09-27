# Architecture Overview — WOOS

WOOS (Workforce Organization Segmentation) mengikuti pemisahan tiga komponen PRD §19 dan konvensi [`ARCHITECTURE_BLUEPRINT.md`](ARCHITECTURE_BLUEPRINT.md) — acuan arsitektur sampai PRD 1.0 selesai. Pemetaan per aturan: [`blueprint_compliance.md`](blueprint_compliance.md).

```
┌──────────────────────────┐     ┌──────────────────────────┐     ┌──────────────────────────┐
│ MODEL EXPERIMENTATION    │ ──▶ │ MODEL RESULT             │ ──▶ │ WEBSITE DASHBOARD        │
│ ml/ (Python)             │     │ PostgreSQL (tabel hasil) │     │ modules/ (PHP native)    │
│ preprocessing, feature,  │     │ single source of truth   │     │ hanya membaca hasil      │
│ K-Means, HC, DBSCAN, eval│     │ validation_status        │     │ APPROVED                 │
└──────────────────────────┘     └──────────────────────────┘     └──────────────────────────┘
```

## Struktur saat ini (hanya yang sudah dipakai)

```
woos/
├── data/raw/                       dataset mentah (read-only)
├── ml/
│   ├── pipeline/                   script tahap: config.py, s01_…py, s02_…py, …
│   ├── outputs/<NN_tahap>/<dataset_version>/   output tiap tahap per versi dataset
│   ├── requirements.txt            dependensi terkunci
│   └── .venv/                      virtualenv lokal (tidak di-commit)
├── database/migrations/            001…005 SQL migration (Tahap 8)
├── tools/migrate.py                migration runner
├── tests/ml/                       pytest untuk fungsi pipeline (+ integration test PostgreSQL)
├── docs/
│   ├── product/                    PRD.md, roadmap.md
│   ├── architecture/               dokumen ini
│   ├── research/                   dokumentasi penelitian (untuk jurnal)
│   └── reports/YYYY/MM/DD/         implementation report
├── AGENTS.md, CLAUDE.md, README.md
```

Tahap 9 menambahkan aplikasi web:

```
├── config/        app.php, database.php, auth.php, role_access.php
├── modules/       auth/, segmentation/ (5 halaman + api.php + repository.php), admin/ (experiments, users)
├── shared/        bootstrap, env, helpers, db, auth_guard, header, menu, footer, components/filters.php
├── assets/        css/app.css, js/charts.js (SVG vanilla), figures/ (dari s08)
├── index.php, router.php (server dev), .htaccess (Apache), composer.json
└── tests/php/run.php
```

## ADR-001 — Layer ML Python (deviasi dari stack default blueprint)

- **Status:** Accepted (2026-09-25)
- **Konteks:** Stack default blueprint adalah PHP 8.3+ / PostgreSQL. PRD mewajibkan K-Means, Agglomerative Hierarchical, DBSCAN, Silhouette, Davies–Bouldin, dendrogram, scaler yang dapat disimpan, dan reproducibility.
- **Keputusan:** Pipeline eksperimen ditulis di Python 3.9 + scikit-learn di `ml/`. Aplikasi web tetap PHP native + PostgreSQL sesuai blueprint.
- **Batas tegas:** Python menulis hasil tervalidasi ke PostgreSQL (via migration-defined tables); PHP hanya membaca. Dashboard tidak menjalankan clustering, tidak membaca `.pkl` (PRD §47, §73).
- **Dampak:** dua runtime; dependensi Python dikunci di `ml/requirements.txt`.

## Keputusan yang ditunda

- Autentikasi/otorisasi: **selesai (Tahap 9)**. PHP session + role ADMIN/VIEWER (D-032); lihat `docs/security/`.
- Skema tabel hasil model: **selesai (Tahap 8)** — lihat `docs/database/schema.md`. Python (s08) menulis; PHP (Tahap 9) hanya membaca view `v_*`.
