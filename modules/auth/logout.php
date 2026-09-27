<?php
require dirname(__DIR__, 2) . '/shared/bootstrap.php';
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    exit('Gunakan tombol Keluar.');
}
csrf_verify();
$_SESSION = [];
session_destroy();
session_start();
flash('Anda telah keluar.', 'success');
redirect('modules/auth/login.php');
