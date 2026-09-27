# Otorisasi — WOOS

Pola blueprint: **User → Role → Permission → Authorization Check**. Definisi terpusat ada di `config/role_access.php` (D-032).

| Role | Permission | Halaman |
|---|---|---|
| VIEWER | `dashboard.view` | Overview, Cluster Analysis, Model Comparison, Organisasi, Organization Detail, API |
| ADMIN | `dashboard.view`, `experiments.view`, `users.manage` | + Registri Eksperimen, Pengguna |

- Setiap halaman memanggil `require_permission('<permission>')` dari `shared/auth_guard.php` (guard bersama). Tanpa login → redirect ke login (API → 401 JSON); tanpa izin → 403.
- **Menu mengikuti RBAC**: tautan yang tidak diizinkan tidak ditampilkan. Ini memperbaiki technical debt ORBIT, yang menampilkan menu tanpa RBAC.
- ADMIN tidak dapat menonaktifkan akunnya sendiri.
- Tidak ada role yang dapat mengubah hasil model dari dashboard. Penulisan ke tabel model hanya dilakukan pipeline (`s08_publish.py`, gerbang `APPROVED`).
- Diuji di `tests/php/run.php`: VIEWER → 403 pada halaman admin, menu admin tersembunyi, ADMIN → 200.
