<?php
// Router untuk server pengembangan PHP (php -S). Di Apache digantikan .htaccess.
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
if (preg_match('#^/(config|shared|database|ml|data|tools|tests|docs|storage)(/|$)#', $path) || preg_match('#/\.#', $path)) {
    http_response_code(403);
    exit('Forbidden');
}
if ($path === '/' ) {
    require __DIR__ . '/index.php';
    return true;
}
return false; // file statis & skrip PHP dilayani langsung
