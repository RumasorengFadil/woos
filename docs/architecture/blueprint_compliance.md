# Blueprint Compliance — WOOS terhadap ARCHITECTURE_BLUEPRINT.md

`ARCHITECTURE_BLUEPRINT.md` (di folder ini) adalah **acuan arsitektur & konvensi engineering WOOS sampai PRD 1.0 selesai**. Dokumen ini memetakan setiap aturan blueprint ke penerapannya di WOOS, beserta tahap penerapannya.

- Blueprint menentukan **HOW** (struktur, konvensi).
- `docs/product/PRD.md` menentukan **WHAT** (fitur, domain).
- Salinan blueprint: SHA-256 `a6578d3e…be2a`, disalin 2026-09-25 dari `pln_orbit_master/docs/`. **Jangan diubah**; deviasi dicatat sebagai ADR di `overview.md`.

## Klasifikasi CORE

| Aturan blueprint | Penerapan WOOS | Tahap | Status |
|---|---|---|---|
| Modular monolith, domain-oriented modules | `modules/segmentation/` (index, cluster, comparison, organizations, organization, api, repository), `modules/auth/`, `modules/admin/` | 9 | DONE |
| PostgreSQL | Database baru `woos`, schema `woos` (bukan skema ORBIT); `woos_test` untuk integration test | 8 | DONE |
| `.env` + config separation | `.env.example` + `.env` (gitignored), dibaca `ml/pipeline/db.py` dan `shared/env.php`; `config/app.php`, `database.php`, `auth.php`, `role_access.php` | 8 / 9 | DONE |
| Migration convention | `database/migrations/001…005_*.sql` + runner `tools/migrate.py` (checksum, transaksi) | 8 | DONE |
| Authentication (PHP session) | `modules/auth/` login/login_submit/logout + `auth_service.php`, `config/auth.php`, rate limit, CSRF | 9 | DONE |
| Authorization foundation | `config/role_access.php` (ADMIN/VIEWER, D-032) + `shared/auth_guard.php` | 9 | DONE |
| Documentation convention | `docs/` single source of truth: product, architecture, database, deployment, features, security, research, reports | 0–9 | DONE |
| Incremental development | Satu tahap PRD per increment, validasi user sebelum lanjut | 0 | DONE |
| Implementation Report | `docs/reports/YYYY/MM/DD/` format Changed/Files/Database/Tests/Manual Test/Documentation | 0 | DONE |
| Tidak membuat folder kosong | Folder dibuat saat mulai dipakai | 0 | DONE |
| Testing convention (`tests/`) | `tests/ml/` pytest (52) + `tests/php/run.php` (41: unit, smoke HTTP, audit statis) | 2–9 | DONE |

## Klasifikasi OPTIONAL — dipakai hanya jika PRD butuh

| Pola | Keputusan WOOS | Alasan |
|---|---|---|
| Automation / background job | **Dipakai terbatas**: pipeline ML `ml/` dijalankan manual (PRD §75), menulis hasil ke DB | PRD §74–75 |
| Upload storage | Tidak dipakai di PRD 1.0 | Dataset baru masuk lewat pipeline, bukan upload web (PRD §75 manual) |
| AI features / chatbot | Tidak dipakai | PRD §3.2 out of scope |
| Materialized views | Belum diputuskan | Dipertimbangkan bila query dashboard lambat |
| Complex RBAC | Tidak dipakai | PRD tidak mendefinisikan role kompleks |
| Legacy routing (`route_map.php`) | **Tidak dipakai** | Proyek baru, tidak ada URL lama |

## DOMAIN SPECIFIC ORBIT — tidak dibawa

Tabel, role, workflow, dan query ORBIT tidak disalin. Catatan: FTK tercantum sebagai *domain specific ORBIT*, tetapi di WOOS FTK **didefinisikan ulang oleh PRD WOOS** sebagai data input; tidak ada skema/query FTK ORBIT yang dipakai.

## Technical debt ORBIT — tidak diwarisi

| Debt ORBIT | Tindakan di WOOS |
|---|---|
| Tidak ada auth guard terpusat | **Diterapkan:** guard bersama `shared/auth_guard.php` (`require_login`, `require_permission`) |
| Menu tanpa RBAC | **Diterapkan:** `shared/menu.php` hanya menampilkan menu sesuai permission |
| PIN reset tanpa verifikasi | **Diterapkan:** tanpa reset mandiri; `password_hash` + rate limit login |

## Deviasi (Architecture Change Rule)

| ADR | Deviasi | Status |
|---|---|---|
| ADR-001 | Layer eksperimen ML Python di `ml/` di samping aplikasi PHP | Accepted |

## Struktur target saat PRD 1.0 selesai

```
woos/
├── config/                 app.php, database.php, database.example.php, auth.php, role_access.php
├── modules/
│   ├── auth/               login.php, login_submit.php, logout.php
│   └── segmentation/       index.php (overview), cluster.php, comparison.php, organization.php, api/*.php
├── shared/                 header.php, footer.php, menu.php, auth_guard.php, db.php
├── assets/                 css/, js/ (chart library lokal/CDN)
├── database/migrations/    001_create_users.sql, 002_create_model_tables.sql, …
├── ml/                     pipeline/, outputs/, requirements.txt   (ADR-001)
├── data/raw/
├── tests/                  php/ (dashboard), ml/ (pytest pipeline)
├── docs/                   product/, architecture/, database/, features/, security/, research/, reports/
├── .env.example, .gitignore, composer.json, AGENTS.md, CLAUDE.md, README.md
```

**Status 2026-09-27:** struktur target terpenuhi (`storage/` belum diperlukan karena tidak ada upload/log aplikasi). Pengecualian dari target: `config/database.example.php` tidak dibuat karena `.env.example` sudah menjadi template konfigurasi. Status aktual ada di `docs/product/roadmap.md`.
