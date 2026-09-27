<?php
// Membuat akun aplikasi dari CLI. Password dibaca dari STDIN (tidak muncul di riwayat shell).
// Pemakaian: php tools/create_user.php <username> "<nama lengkap>" <ADMIN|VIEWER>
if (PHP_SAPI !== 'cli') { exit(1); }
require dirname(__DIR__) . '/shared/bootstrap.php';
require APP_ROOT . '/modules/auth/auth_service.php';
[$_, $username, $fullName, $role] = array_pad($argv, 4, null);
if (!$username || !$fullName || !$role) {
    fwrite(STDERR, "Pemakaian: php tools/create_user.php <username> \"<nama>\" <ADMIN|VIEWER>  (password via STDIN)\n");
    exit(1);
}
fwrite(STDERR, "Password (min 12 karakter): ");
$password = rtrim((string) fgets(STDIN), "\r\n");
try {
    $id = create_user($username, $fullName, $password, strtoupper($role));
    echo "Dibuat user_id=$id ($username, " . strtoupper($role) . ")\n";
} catch (Throwable $ex) {
    fwrite(STDERR, 'Gagal: ' . $ex->getMessage() . "\n");
    exit(1);
}
