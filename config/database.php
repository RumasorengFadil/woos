<?php
return [
    'host'     => env('DB_HOST', '127.0.0.1'),
    'port'     => (int) env('DB_PORT', '5432'),
    'dbname'   => env('DB_NAME', 'woos'),
    'user'     => env('DB_USER', ''),
    'password' => env('DB_PASSWORD', ''),
    'schema'   => env('DB_SCHEMA', 'woos'),
];
