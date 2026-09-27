<?php
// Autentikasi: PHP session (blueprint). Role/permission ada di role_access.php.
return [
    'session_name'          => 'WOOSSESSID',
    'idle_timeout_seconds'  => 60 * 60 * 2,
    'max_failed_per_user'   => 5,      // dalam jendela di bawah
    'max_failed_per_ip'     => 20,
    'lockout_window_minutes' => 15,
];
