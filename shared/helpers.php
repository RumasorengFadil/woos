<?php
// Helper presentasi & keamanan yang dipakai lintas modul.

function config(string $path, mixed $default = null): mixed
{
    $node = $GLOBALS['config'];
    foreach (explode('.', $path) as $part) {
        if (!is_array($node) || !array_key_exists($part, $node)) {
            return $default;
        }
        $node = $node[$part];
    }
    return $node;
}

/** Escape HTML — WAJIB untuk setiap output data. */
function e(mixed $value): string
{
    return htmlspecialchars((string) ($value ?? ''), ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

/** URL relatif terhadap root aplikasi (berfungsi di subfolder MAMP maupun php -S). */
function url(string $path = '', array $query = []): string
{
    $script = str_replace('\\', '/', $_SERVER['SCRIPT_NAME'] ?? '/');
    $root = str_replace('\\', '/', APP_ROOT);
    $file = str_replace('\\', '/', realpath($_SERVER['SCRIPT_FILENAME'] ?? '') ?: '');
    $rel = $file !== '' && str_starts_with($file, $root) ? substr($file, strlen($root)) : $script;
    $base = rtrim(substr($script, 0, strlen($script) - strlen($rel)), '/');
    $q = $query ? '?' . http_build_query($query) : '';
    return $base . '/' . ltrim($path, '/') . $q;
}

function redirect(string $path, array $query = []): never
{
    header('Location: ' . url($path, $query));
    exit;
}

function fmt_int(mixed $v): string
{
    return $v === null ? '—' : number_format((float) $v, 0, ',', '.');
}

function fmt_num(mixed $v, int $dec = 2): string
{
    return $v === null ? '—' : number_format((float) $v, $dec, ',', '.');
}

function fmt_pct(mixed $ratio, int $dec = 1): string
{
    return $ratio === null ? '—' : number_format((float) $ratio * 100, $dec, ',', '.') . '%';
}

function fmt_signed(mixed $v): string
{
    if ($v === null) {
        return '—';
    }
    return ($v > 0 ? '+' : '') . number_format((float) $v, 0, ',', '.');
}

function csrf_token(): string
{
    if (empty($_SESSION['csrf'])) {
        $_SESSION['csrf'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf'];
}

function csrf_field(): string
{
    return '<input type="hidden" name="csrf" value="' . e(csrf_token()) . '">';
}

function csrf_verify(): void
{
    $sent = $_POST['csrf'] ?? '';
    if (!is_string($sent) || empty($_SESSION['csrf']) || !hash_equals($_SESSION['csrf'], $sent)) {
        http_response_code(400);
        exit('Permintaan tidak valid (CSRF).');
    }
}

function flash(?string $message = null, string $type = 'info'): ?array
{
    if ($message !== null) {
        $_SESSION['flash'] = ['message' => $message, 'type' => $type];
        return null;
    }
    $f = $_SESSION['flash'] ?? null;
    unset($_SESSION['flash']);
    return $f;
}

/** Data untuk chart disisipkan sebagai JSON non-eksekusi; dibaca assets/js/charts.js. */
function json_script(string $id, mixed $data): string
{
    $json = json_encode($data, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT | JSON_UNESCAPED_UNICODE);
    return '<script type="application/json" id="' . e($id) . '">' . $json . '</script>';
}

/** Class warna cluster (slot palet tetap per cluster_id; noise/tidak tersegmentasi = netral). */
function cluster_class(mixed $clusterId): string
{
    return $clusterId === null || (int) $clusterId < 0 ? 'c-noise' : 'c-' . ((int) $clusterId % 8);
}
