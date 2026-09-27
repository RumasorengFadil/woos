<?php
// Loader .env minimal (KEY=VALUE, # komentar, kutip opsional). Variabel lingkungan OS menang.
function load_env(string $path): void
{
    if (!is_file($path)) {
        return;
    }
    foreach (file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        $line = trim($line);
        if ($line === '' || $line[0] === '#' || !str_contains($line, '=')) {
            continue;
        }
        [$key, $value] = array_map('trim', explode('=', $line, 2));
        $value = trim($value, "\"'");
        if (getenv($key) === false) {
            $_ENV[$key] = $value;
        }
    }
}

function env(string $key, ?string $default = null): ?string
{
    $v = getenv($key);
    if ($v !== false) {
        return $v;
    }
    return $_ENV[$key] ?? $default;
}
