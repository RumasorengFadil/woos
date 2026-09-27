# Autentikasi — WOOS

| Aspek | Implementasi |
|---|---|
| Mekanisme | PHP session (blueprint), cookie `WOOSSESSID`: `HttpOnly`, `SameSite=Lax`, `Secure` otomatis bila HTTPS |
| Penyimpanan password | `password_hash(PASSWORD_DEFAULT)`; rehash otomatis bila algoritma default berubah; minimal 12 karakter |
| Login | `modules/auth/login.php` → `login_submit.php` (POST + CSRF); `session_regenerate_id(true)` setelah sukses; pesan gagal generik |
| Brute force | `woos.auth_login_attempt`: blokir sementara bila ≥ 5 gagal per username atau ≥ 20 gagal per IP dalam 15 menit (`config/auth.php`) |
| Idle timeout | 2 jam (`idle_timeout_seconds`) |
| Logout | `modules/auth/logout.php`, hanya POST + CSRF |
| Pembuatan akun | `php tools/create_user.php <username> "<nama>" <ADMIN|VIEWER>`; password dibaca dari STDIN. Atau halaman Pengguna (ADMIN) |
| Reset password | Tidak ada fitur reset mandiri (technical debt ORBIT tidak diwarisi). ADMIN membuat ulang/menonaktifkan akun |

## Header keamanan (`shared/bootstrap.php`)

- `Content-Security-Policy`: `default-src 'self'`; **tanpa `unsafe-inline`** untuk script maupun style. Data chart dikirim sebagai `<script type="application/json">` (non-eksekusi), dan warna/ukuran dinamis diatur lewat class atau CSSOM.
- `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`.

## Akses file

`.htaccess` (Apache) dan `router.php` (server dev) menolak akses ke `config/`, `shared/`, `database/`, `ml/`, `data/`, `tools/`, `tests/`, `docs/`, `storage/`, dan file tersembunyi (`.env`). Semua path ini diuji otomatis.

## Akun uji lokal

`database/seeds/dev_users.local.json` (gitignored) berisi akun uji `admin.dev` / `viewer.dev` dengan password acak. File ini dipakai test smoke dan **tidak boleh dipakai di produksi**.
