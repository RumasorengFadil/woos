<?php
// Guard bersama: autentikasi (session) + otorisasi (role_access.php). Dipanggil di awal setiap halaman.

function current_user(): ?array
{
    return $_SESSION['user'] ?? null;
}

function user_can(string $permission, ?array $user = null): bool
{
    $user ??= current_user();
    if (!$user) {
        return false;
    }
    return in_array($permission, config('rbac.roles.' . $user['role'], []), true);
}

function require_login(): array
{
    $user = current_user();
    $idle = config('auth.idle_timeout_seconds');
    if ($user && (time() - ($_SESSION['last_activity'] ?? 0)) > $idle) {
        session_unset();
        session_destroy();
        $user = null;
    }
    if (!$user) {
        if (str_contains($_SERVER['SCRIPT_NAME'] ?? '', '/api.php')) {
            http_response_code(401);
            header('Content-Type: application/json');
            exit(json_encode(['error' => 'unauthenticated']));
        }
        redirect('modules/auth/login.php');
    }
    $_SESSION['last_activity'] = time();
    return $user;
}

function require_permission(string $permission): array
{
    $user = require_login();
    if (!user_can($permission, $user)) {
        http_response_code(403);
        exit('Akses ditolak.');
    }
    return $user;
}
