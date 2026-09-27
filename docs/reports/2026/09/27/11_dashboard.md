# Implementation Report — Tahap 9: Backend & Dashboard (PRD 1.0 selesai)

**Tanggal:** 2026-09-27
**Increment:** PRD §46–§70 — Website Dashboard Workforce Organization Segmentation (PHP native + PostgreSQL)

## Implementation Report

### Changed
- D-031, D-032 (role ADMIN/VIEWER) APPROVED; D-033 (visualisasi dihasilkan pipeline) APPLIED.
- Pipeline: `s08_publish.py` kini menghitung koordinat PCA 2D per model (Python) dan menyalin 6 figure riset ke `assets/figures/`. Validasi pasca-publish bertambah menjadi 10/10.
- Aplikasi web sesuai blueprint:
  - **Fondasi:** `config/` (app, database, auth, role_access), `shared/` (bootstrap, env, helpers, db PDO, auth_guard, layout, menu RBAC, komponen filter).
  - **Auth:** login/logout PHP session, `password_hash`, CSRF, regenerasi session, rate limit brute force, idle timeout.
  - **Segmentasi:** Overview, Cluster Analysis, Model Comparison, Organisasi (search/sort/pagination/filter), Organization Detail, API JSON read-only. Semua query ada di `repository.php` (read-only).
  - **Admin:** registri eksperimen dan manajemen pengguna.
  - **Front-end:** `charts.js` (SVG vanilla: bar, stacked 100 %, PCA small multiples dengan noise = X, line) dengan tooltip, legenda, tabel alternatif, dark mode, dan responsif hingga 375 px.
  - **Keamanan:** CSP ketat tanpa `unsafe-inline`, X-Frame-Options, nosniff; `.htaccess` + `router.php` memblokir folder non-publik.
- `tools/create_user.php` (CLI, password via STDIN); `composer.json` (deklarasi ekstensi, tanpa dependensi pihak ketiga).
- Masalah yang ditemukan dan diperbaiki saat verifikasi di browser:
  1. urutan bootstrap (`config()` dipanggil sebelum helpers dimuat);
  2. CSP memblokir seluruh atribut `style` inline, sehingga swatch/warna/lebar bar hilang → diganti class CSS + CSSOM;
  3. elemen bar inline tidak menerima `width`;
  4. teks chart terlalu kecil/tumpang tindih → chart responsif terhadap lebar kontainer;
  5. layout mobile: dropdown melebar, label terpotong, tabel tanpa scroll.

### Files
- Baru:
  - `index.php`, `router.php`, `.htaccess`, `composer.json`, `.claude/launch.json`
  - `config/{app,database,auth,role_access}.php`
  - `shared/{bootstrap,env,helpers,db,auth_guard,header,menu,footer}.php`, `shared/components/filters.php`
  - `modules/auth/{auth_service,login,login_submit,logout}.php`
  - `modules/segmentation/{repository,index,cluster,comparison,organizations,organization,api}.php`
  - `modules/admin/{experiments,users}.php`
  - `assets/css/app.css`, `assets/js/charts.js`
  - `tools/create_user.php`, `tests/php/run.php`
  - `database/migrations/006_add_cluster_result_visual_coordinates.sql`, `007_create_auth_tables.sql`
  - `database/seeds/dev_users.local.json` (akun uji lokal, gitignored)
  - Docs: `docs/features/segmentation/README.md`, `docs/security/{authentication,authorization}.md`, `docs/product/prd_acceptance.md`
- Diubah:
  - `ml/pipeline/s08_publish.py`, `.gitignore`
  - Docs: `docs/database/{schema,migrations}.md`, `docs/deployment/installation.md`, `docs/architecture/{overview,blueprint_compliance}.md`, `docs/product/roadmap.md`, `docs/README.md`, `docs/research/{decision_log,journal_outline}.md`, `AGENTS.md`, `README.md`

### Database
- Migration 006:
  - kolom `cluster_result.viz_x` / `cluster_result.viz_y`;
  - kolom `model.viz_explained_variance`.
- Migration 007:
  - tabel `app_user` dan `auth_login_attempt`;
  - view `v_validated_organization` diperbarui (tambah `viz_x/viz_y`).
- Diterapkan ke `woos` dan `woos_test`.

### Tests
- `php tests/php/run.php`: **PASS (41 passed)**.
  - 9 unit (escape, format, class cluster, whitelist filter, parameter terikat, RBAC).
  - 3 data (satu validated model APPROVED, summary = hasil pipeline, filter tidak mengubah model).
  - 4 audit statis (tanpa algoritma clustering, tanpa penetapan cluster di PHP/JS, repository read-only, tanpa style inline).
  - 25 smoke HTTP pada server terpisah:
    - redirect tamu, API 401, 5 path sensitif 403;
    - header keamanan, cookie HttpOnly/SameSite, CSRF login/logout;
    - semua halaman VIEWER 200, 404 organisasi tak dikenal, VIEWER → 403 admin, ADMIN → 200;
    - API summary, rate limit brute force.
- `ml/.venv/bin/python -m pytest tests/ml`: PASS (52 passed).
- Verifikasi visual di browser (desktop, mobile 375 px, dark mode): semua halaman, tooltip, noise DBSCAN (X merah), tanpa scroll horizontal. Tidak ada atribut style inline pada HTML maupun JS.

### Manual Test
1. `php -S localhost:8090 -t . router.php`, buka `http://localhost:8090` → diarahkan ke halaman login.
2. Login dengan akun VIEWER → Overview menampilkan "Validated Model: K-Means v1 (EXP-KM-067) APPROVED", Total FTK 3.791, Realisasi 3.607, Fulfillment 95,1 %.
3. Filter Cluster = "Understaffing Kritis (Belum Terisi)" di halaman Organisasi → 141 organisasi; urutkan Gap ▼ → teratas Bidang Verifikasi UID & UIW-1 (gap +34).
4. Model Comparison → pilih DBSCAN → panel "Noise" dengan penanda X merah.
5. Sebagai VIEWER buka `/modules/admin/users.php` → "Akses ditolak" (403); menu admin tidak tampil.
6. `/.env` dan `/ml/outputs/` → 403.

### Documentation
- Lihat Files. Acceptance criteria PRD §94: `docs/product/prd_acceptance.md` (30/30).
