<?php
// Logika autentikasi (terpisah dari otorisasi). Password disimpan sebagai password_hash().

function login_is_throttled(string $username, string $ip): bool
{
    $window = (int) config('auth.lockout_window_minutes');
    $byUser = (int) db_value("SELECT count(*) FROM auth_login_attempt WHERE lower(username) = lower(:u) AND NOT succeeded
                              AND attempted_at > now() - make_interval(mins => :w)", ['u' => $username, 'w' => $window]);
    $byIp = (int) db_value("SELECT count(*) FROM auth_login_attempt WHERE ip_address = :ip AND NOT succeeded
                            AND attempted_at > now() - make_interval(mins => :w)", ['ip' => $ip, 'w' => $window]);
    return $byUser >= config('auth.max_failed_per_user') || $byIp >= config('auth.max_failed_per_ip');
}

function record_login_attempt(string $username, string $ip, bool $ok): void
{
    db()->prepare('INSERT INTO auth_login_attempt (username, ip_address, succeeded) VALUES (:u, :ip, :ok)')
        ->execute(['u' => mb_substr($username, 0, 60), 'ip' => $ip, 'ok' => $ok ? 'true' : 'false']);
}

/** @return array{ok: bool, user?: array, error?: string} */
function attempt_login(string $username, string $password, string $ip): array
{
    $username = trim($username);
    if ($username === '' || $password === '') {
        return ['ok' => false, 'error' => 'Username dan password wajib diisi.'];
    }
    if (login_is_throttled($username, $ip)) {
        return ['ok' => false, 'error' => 'Terlalu banyak percobaan gagal. Coba lagi dalam beberapa menit.'];
    }
    $user = db_one('SELECT user_id, username, full_name, password_hash, role, is_active FROM app_user WHERE lower(username) = lower(:u)',
                   ['u' => $username]);
    $valid = $user && $user['is_active'] && password_verify($password, $user['password_hash']);
    record_login_attempt($username, $ip, (bool) $valid);
    if (!$valid) {
        return ['ok' => false, 'error' => 'Username atau password salah.'];   // pesan generik
    }
    if (password_needs_rehash($user['password_hash'], PASSWORD_DEFAULT)) {
        db()->prepare('UPDATE app_user SET password_hash = :h WHERE user_id = :id')
            ->execute(['h' => password_hash($password, PASSWORD_DEFAULT), 'id' => $user['user_id']]);
    }
    db()->prepare('UPDATE app_user SET last_login_at = now() WHERE user_id = :id')->execute(['id' => $user['user_id']]);
    unset($user['password_hash']);
    return ['ok' => true, 'user' => $user];
}

function create_user(string $username, string $fullName, string $password, string $role): int
{
    if (!preg_match('/^[a-zA-Z0-9._-]{3,60}$/', $username)) {
        throw new InvalidArgumentException('Username 3–60 karakter: huruf, angka, titik, garis bawah, strip.');
    }
    if (!array_key_exists($role, config('rbac.roles'))) {
        throw new InvalidArgumentException('Role tidak dikenal.');
    }
    if (strlen($password) < 12) {
        throw new InvalidArgumentException('Password minimal 12 karakter.');
    }
    $st = db()->prepare('INSERT INTO app_user (username, full_name, password_hash, role) VALUES (:u, :n, :h, :r) RETURNING user_id');
    $st->execute(['u' => $username, 'n' => $fullName, 'h' => password_hash($password, PASSWORD_DEFAULT), 'r' => $role]);
    return (int) $st->fetchColumn();
}
