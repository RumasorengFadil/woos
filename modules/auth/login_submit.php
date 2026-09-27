<?php
require dirname(__DIR__, 2) . '/shared/bootstrap.php';
require __DIR__ . '/auth_service.php';
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    redirect('modules/auth/login.php');
}
csrf_verify();
$result = attempt_login((string) ($_POST['username'] ?? ''), (string) ($_POST['password'] ?? ''), $_SERVER['REMOTE_ADDR'] ?? 'unknown');
if (!$result['ok']) {
    flash($result['error'], 'error');
    redirect('modules/auth/login.php');
}
session_regenerate_id(true);
$_SESSION['user'] = $result['user'];
$_SESSION['last_activity'] = time();
unset($_SESSION['csrf']);
redirect('modules/segmentation/index.php');
