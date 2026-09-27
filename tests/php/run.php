<?php
// Test runner PHP tanpa dependensi (unit + smoke HTTP + audit statis). Jalankan: php tests/php/run.php
// Smoke test menjalankan server `php -S` sendiri di port acak dan memakai akun uji dari database/seeds/dev_users.local.json.
declare(strict_types=1);
require dirname(__DIR__, 2) . '/shared/bootstrap.php';
require APP_ROOT . '/modules/segmentation/repository.php';

$pass = 0; $fail = [];
function check(string $name, bool $cond): void { global $pass, $fail; $cond ? $pass++ : $fail[] = $name; echo ($cond ? '  ok   ' : '  FAIL ') . $name . "\n"; }

echo "== unit\n";
check('e() escape HTML', e('<b a="1">&') === '&lt;b a=&quot;1&quot;&gt;&amp;');
check('fmt_pct', fmt_pct(0.951) === '95,1%' && fmt_pct(null) === '—');
check('fmt_signed', fmt_signed(184) === '+184' && fmt_signed(-6) === '-6');
check('cluster_class slot tetap', cluster_class(0) === 'c-0' && cluster_class(4) === 'c-4' && cluster_class(null) === 'c-noise' && cluster_class(-1) === 'c-noise');
$f = read_filters(['directorate' => "ORG-0005'; DROP", 'level' => '6', 'cluster' => 'VACANT', 'grade' => 'XX', 'q' => '  hukum ', 'sort' => 'x']);
check('read_filters whitelist', $f['directorate'] === null && $f['level'] === 6 && $f['cluster'] === 'VACANT' && $f['grade'] === null && $f['search'] === 'hukum');
[$w, $p] = filter_sql($f);
check('filter_sql memakai parameter terikat', str_contains($w, ':level') && str_contains($w, ':search') && $p['search'] === '%hukum%' && !str_contains($w, 'hukum'));
check('RBAC viewer', user_can('dashboard.view', ['role' => 'VIEWER']) && !user_can('users.manage', ['role' => 'VIEWER']) && !user_can('experiments.view', ['role' => 'VIEWER']));
check('RBAC admin', user_can('users.manage', ['role' => 'ADMIN']) && user_can('experiments.view', ['role' => 'ADMIN']));
check('RBAC role tak dikenal', !user_can('dashboard.view', ['role' => 'X']));

echo "== data (view model tervalidasi)\n";
$m = validated_model();
check('ada tepat satu validated model APPROVED', $m !== null && $m['validation_status'] === 'APPROVED' && $m['experiment_id'] === 'EXP-KM-067');
$s = summary(read_filters([]));
check('summary = hasil pipeline (1280 segmented, FTK 3791)', (int) $s['segmented'] === 1280 && (int) $s['ftk'] === 3791 && (int) $s['not_segmented'] === 21);
$flt = summary(read_filters(['cluster' => 'VACANT']));
check('filter cluster tidak mengubah model (141 org)', (int) $flt['organizations'] === 141);

echo "== audit statis (PRD §47: dashboard tanpa clustering / rule klasifikasi)\n";
$code = '';
foreach (['modules', 'shared', 'assets/js'] as $dir) {
    foreach (new RecursiveIteratorIterator(new RecursiveDirectoryIterator(APP_ROOT . "/$dir")) as $file) {
        if ($file->isFile() && preg_match('/\.(php|js)$/', $file->getFilename())) { $code .= file_get_contents($file->getPathname()); }
    }
}
check('tidak ada algoritma clustering di aplikasi', !preg_match('/\b(kmeans|k_means|dbscan|linkage|centroid\s*=|euclid)\s*\(/i', $code));
// Penetapan nilai cluster di PHP (array key) atau JS (properti). Kondisi SQL "cluster_code = :cluster" adalah baca, bukan penetapan.
check('tidak ada penetapan cluster di aplikasi', !preg_match('/\[[\'"]cluster_(id|code|label)[\'"]\]\s*=(?![=>])|\.cluster_(id|code|label)\s*=(?!=|\s*:)/', $code));   // "= :param" = kondisi SQL
$repo = file_get_contents(APP_ROOT . '/modules/segmentation/repository.php');
check('repository segmentasi read-only', !preg_match('/\b(INSERT|UPDATE|DELETE|TRUNCATE|ALTER|DROP)\b/i', $repo));
check('tidak ada atribut style inline (CSP)', !preg_match('/\sstyle="/', $code));

echo "== smoke HTTP\n";
$port = random_int(18000, 18999);
$proc = proc_open([PHP_BINARY, '-S', "127.0.0.1:$port", '-t', APP_ROOT, APP_ROOT . '/router.php'], [1 => ['file', '/dev/null', 'w'], 2 => ['file', '/dev/null', 'w']], $pipes);
usleep(600000);
$base = "http://127.0.0.1:$port";
function http(string $method, string $path, array $data = [], ?string &$jar = null): array {
    global $base;
    $ch = curl_init($base . $path);
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_HEADER => true, CURLOPT_FOLLOWLOCATION => false,
        CURLOPT_COOKIEFILE => $jar, CURLOPT_COOKIEJAR => $jar, CURLOPT_CUSTOMREQUEST => $method]);
    if ($method === 'POST') { curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($data)); }
    $raw = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    $hs = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
    curl_close($ch);
    return ['code' => $code, 'headers' => substr($raw, 0, $hs), 'body' => substr($raw, $hs)];
}
function login(string $user, string $pw): string {
    $jar = tempnam(sys_get_temp_dir(), 'woos');
    $page = http('GET', '/modules/auth/login.php', [], $jar);
    preg_match('/name="csrf" value="([a-f0-9]+)"/', $page['body'], $mm);
    http('POST', '/modules/auth/login_submit.php', ['csrf' => $mm[1] ?? '', 'username' => $user, 'password' => $pw], $jar);
    return $jar;
}
$creds = array_column(json_decode(file_get_contents(APP_ROOT . '/database/seeds/dev_users.local.json'), true)['users'], null, 'username');
$anon = tempnam(sys_get_temp_dir(), 'woos');

$r = http('GET', '/modules/segmentation/index.php', [], $anon);
check('tamu diarahkan ke login', $r['code'] === 302 && str_contains($r['headers'], 'login.php'));
$r = http('GET', '/modules/segmentation/api.php?resource=summary', [], $anon);
check('API tanpa login -> 401 JSON', $r['code'] === 401 && str_contains($r['body'], 'unauthenticated'));
foreach (['/.env', '/config/database.php', '/ml/outputs/', '/database/seeds/dev_users.local.json', '/data/raw/'] as $path) {
    check("path sensitif diblokir: $path", http('GET', $path, [], $anon)['code'] === 403);
}
$fresh = tempnam(sys_get_temp_dir(), 'woos');
$r = http('GET', '/modules/auth/login.php', [], $fresh);
check('header keamanan (CSP, X-Frame-Options, nosniff)', str_contains($r['headers'], 'Content-Security-Policy') && str_contains($r['headers'], 'X-Frame-Options: DENY') && str_contains($r['headers'], 'nosniff'));
check('cookie session HttpOnly + SameSite', (bool) preg_match('/Set-Cookie: WOOSSESSID=[^\r\n]*HttpOnly[^\r\n]*SameSite=Lax/i', $r['headers']));
$r = http('POST', '/modules/auth/login_submit.php', ['username' => 'viewer.dev', 'password' => 'x'], $anon);
check('login tanpa CSRF ditolak', $r['code'] === 400);

$viewer = login('viewer.dev', $creds['viewer.dev']['password']);
$r = http('GET', '/modules/segmentation/index.php', [], $viewer);
check('viewer: Overview 200 + Validated Model', $r['code'] === 200 && str_contains($r['body'], 'EXP-KM-067') && str_contains($r['body'], 'APPROVED'));
check('viewer: menu admin tersembunyi', !str_contains($r['body'], 'Registri Eksperimen'));
foreach (['cluster.php', 'comparison.php', 'organizations.php?q=hukum&sort=gap&dir=desc', 'organization.php?id=ORG-0646'] as $pg) {
    check("viewer: $pg 200", http('GET', "/modules/segmentation/$pg", [], $viewer)['code'] === 200);
}
check('viewer: organisasi tidak dikenal 404', http('GET', '/modules/segmentation/organization.php?id=ORG-9999', [], $viewer)['code'] === 404);
check('viewer: registri eksperimen 403', http('GET', '/modules/admin/experiments.php', [], $viewer)['code'] === 403);
check('viewer: manajemen user 403', http('GET', '/modules/admin/users.php', [], $viewer)['code'] === 403);
$api = json_decode(http('GET', '/modules/segmentation/api.php?resource=summary', [], $viewer)['body'], true);
check('API summary = hasil pipeline', (int) ($api['data']['summary']['segmented'] ?? 0) === 1280 && ($api['data']['model']['experiment_id'] ?? '') === 'EXP-KM-067');
check('API resource tak dikenal 400', http('GET', '/modules/segmentation/api.php?resource=x', [], $viewer)['code'] === 400);
check('logout tanpa CSRF ditolak', http('POST', '/modules/auth/logout.php', [], $viewer)['code'] === 400);

$admin = login('admin.dev', $creds['admin.dev']['password']);
$r = http('GET', '/modules/admin/experiments.php', [], $admin);
check('admin: registri eksperimen 200', $r['code'] === 200 && str_contains($r['body'], 'EXP-KM-067'));
check('admin: manajemen user 200', http('GET', '/modules/admin/users.php', [], $admin)['code'] === 200);

$probe = 'throttle.test.' . bin2hex(random_bytes(3));
$jar = tempnam(sys_get_temp_dir(), 'woos');
for ($i = 0; $i < 6; $i++) {
    $pg = http('GET', '/modules/auth/login.php', [], $jar);
    preg_match('/name="csrf" value="([a-f0-9]+)"/', $pg['body'], $mm);
    http('POST', '/modules/auth/login_submit.php', ['csrf' => $mm[1], 'username' => $probe, 'password' => 'wrong-password'], $jar);
}
$pg = http('GET', '/modules/auth/login.php', [], $jar);
check('brute force: dibatasi setelah 5 kegagalan', str_contains($pg['body'], 'Terlalu banyak percobaan'));

proc_terminate($proc);
db()->prepare("DELETE FROM auth_login_attempt WHERE username LIKE 'throttle.test.%'")->execute();   // bersihkan jejak test

echo "\n$pass passed, " . count($fail) . " failed\n";
exit($fail ? 1 : 0);
