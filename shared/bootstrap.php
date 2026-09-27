<?php
// Bootstrap setiap request: env, config, session aman, header keamanan, helper.
declare(strict_types=1);

define('APP_ROOT', dirname(__DIR__));
require_once APP_ROOT . '/shared/env.php';
load_env(APP_ROOT . '/.env');

$GLOBALS['config'] = [
    'app'   => require APP_ROOT . '/config/app.php',
    'db'    => require APP_ROOT . '/config/database.php',
    'auth'  => require APP_ROOT . '/config/auth.php',
    'rbac'  => require APP_ROOT . '/config/role_access.php',
];
require_once APP_ROOT . '/shared/helpers.php';
require_once APP_ROOT . '/shared/db.php';
date_default_timezone_set(config('app.timezone'));
require_once APP_ROOT . '/shared/auth_guard.php';

if (PHP_SAPI !== 'cli') {
    header('X-Content-Type-Options: nosniff');
    header('X-Frame-Options: DENY');
    header('Referrer-Policy: same-origin');
    header("Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'; form-action 'self'");
    session_name(config('auth.session_name'));
    session_set_cookie_params([
        'lifetime' => 0, 'path' => '/', 'httponly' => true, 'samesite' => 'Lax',
        'secure' => (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off'),
    ]);
    session_start();
}
