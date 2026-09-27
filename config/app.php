<?php
// Konfigurasi aplikasi. Nilai lingkungan dibaca dari .env (shared/env.php).
return [
    'name'     => env('APP_NAME', 'WOOS — Workforce Organization Segmentation'),
    'env'      => env('APP_ENV', 'production'),
    'timezone' => 'Asia/Jakarta',
    'page_size' => 25,
];
