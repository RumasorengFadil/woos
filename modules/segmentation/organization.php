<?php
// Organization Detail (PRD §59–§60, §70, §85): informasi, metrik, feature, cluster & penjelasan vs rata-rata cluster.
require dirname(__DIR__, 2) . '/shared/bootstrap.php';
require_permission('dashboard.view');
require __DIR__ . '/repository.php';

$id = (string) ($_GET['id'] ?? '');
$org = preg_match('/^ORG-\d{4}$/', $id) ? organization_detail($id) : null;
if (!$org) {
    http_response_code(404);
}
$pageTitle = $org ? $org['organization_name'] : 'Organisasi tidak ditemukan';
$activeMenu = 'modules/segmentation/organizations.php';
require APP_ROOT . '/shared/header.php';
if (!$org): ?>
  <h1>Organisasi tidak ditemukan</h1><p><a href="<?= e(url('modules/segmentation/organizations.php')) ?>">← Kembali ke daftar</a></p>
<?php require APP_ROOT . '/shared/footer.php'; exit; endif;
$p = $org['profile'];
$explain = [
    ['Gap', $org['gap'], $p['mean_gap'] ?? null, 'num'],
    ['Fulfillment', $org['fulfillment_ratio'], $p['median_fulfillment'] ?? null, 'pct'],
    ['Porsi jabatan kosong', $org['vacant_share'], $p['mean_vacant_share'] ?? null, 'pct'],
    ['Jabatan kosong', $org['vacant_position_count'], $p['mean_vacant_position'] ?? null, 'num'],
    ['Pegawai per jabatan', $org['avg_realization_per_position'], $p['mean_avg_realization_per_position'] ?? null, 'num'],
];
$gd = $org['grade_distribution'];
?>
<p class="small"><a href="<?= e(url('modules/segmentation/organizations.php')) ?>">← Daftar organisasi</a></p>
<h1><?= e($org['organization_name']) ?></h1>
<p class="muted small"><?= e($org['organization_id']) ?> · Level <?= e($org['organization_level']) ?> · <?= e(ucwords(strtolower((string) $org['directorate_name']))) ?>
  <?php if ($org['parent_organization_id']): ?> · Parent: <a href="<?= e(url('modules/segmentation/organization.php', ['id' => $org['parent_organization_id']])) ?>"><?= e($org['parent_organization_name'] ?? $org['parent_organization_id']) ?></a><?php endif; ?></p>

<section class="grid grid-4">
  <div class="card stat"><div class="label">FTK</div><div class="value"><?= fmt_int($org['ftk']) ?></div></div>
  <div class="card stat"><div class="label">Realisasi</div><div class="value"><?= fmt_int($org['realization']) ?></div></div>
  <div class="card stat"><div class="label">Gap</div><div class="value"><?= fmt_signed($org['gap']) ?></div></div>
  <div class="card stat"><div class="label">Fulfillment</div><div class="value"><?= fmt_pct($org['fulfillment_ratio']) ?></div><div class="sub"><?= $org['fulfillment_ratio'] === null ? 'FTK = 0 (tidak dibagi)' : '' ?></div></div>
</section>

<section class="grid grid-2 section">
  <div class="card cluster-card <?= cluster_class($org['cluster_id']) ?>">
    <h2>Cluster: <?= e($org['cluster_label']) ?> <?= $org['is_atypical_member'] ? '<span class="badge" title="Jarak ke centroid > P95 cluster">anggota atipikal</span>' : '' ?></h2>
    <?php if ($p): ?>
      <p class="small"><?= e($p['interpretation']) ?></p>
      <ul class="small"><?php foreach ($p['characteristics'] as $c): ?><li><?= e($c) ?></li><?php endforeach; ?></ul>
      <p class="muted small">Jarak ke centroid: <?= fmt_num($org['cluster_distance'], 3) ?> · Model <?= e($org['experiment_id']) ?> (Validated)</p>
    <?php else: ?>
      <p class="small">Organisasi ini tidak memiliki jabatan aktif (seluruh jabatan FTK = 0 dan realisasi = 0), sehingga tidak di-cluster (D-017).</p>
    <?php endif; ?>
    <?php if ($org['other_models']): ?>
      <p class="muted small">Model pembanding: <?php foreach ($org['other_models'] as $om): ?><?= e($om['model_name']) ?> → <?= e($om['cluster_label']) ?>; <?php endforeach; ?></p>
    <?php endif; ?>
  </div>
  <div class="card">
    <h2>Penjelasan: organisasi vs rata-rata cluster <span class="muted small">(PRD §85)</span></h2>
    <table><thead><tr><th>Feature</th><th class="num">Organisasi</th><th class="num">Cluster</th></tr></thead><tbody>
    <?php foreach ($explain as [$label, $v, $avg, $type]): ?>
      <tr><td><?= e($label) ?></td>
        <td class="num"><?= $type === 'pct' ? fmt_pct($v) : fmt_num($v) ?></td>
        <td class="num"><?= $type === 'pct' ? fmt_pct($avg) : fmt_num($avg) ?></td></tr>
    <?php endforeach; ?>
    </tbody></table>
    <p class="muted small">Fulfillment cluster = median; lainnya rata-rata.</p>
  </div>
</section>

<section class="grid grid-2 section">
  <div class="card">
    <h2>Feature</h2>
    <dl class="kv">
      <dt>Jumlah jabatan aktif</dt><dd><?= fmt_int($org['position_count']) ?></dd>
      <dt>Jabatan kosong</dt><dd><?= fmt_int($org['vacant_position_count']) ?> (<?= fmt_pct($org['vacant_share'], 0) ?>)</dd>
      <dt>Rata-rata realisasi/jabatan</dt><dd><?= fmt_num($org['avg_realization_per_position']) ?></dd>
      <dt>Staffing ratio</dt><dd><?= $org['staffing_ratio'] === null ? '—' : fmt_pct($org['staffing_ratio']) ?></dd>
      <dt>Balance index</dt><dd><?= fmt_num($org['balance_index'], 3) ?></dd>
      <dt>Jabatan terisi tanpa formasi</dt><dd><?= fmt_int($org['unbudgeted_filled_count']) ?></dd>
    </dl>
  </div>
  <div class="card">
    <h2>Distribusi jenjang <span class="muted small">(PRD §60)</span></h2>
    <?php $maxPct = max(array_values($gd['pct'])) ?: 1; foreach (GRADE_GROUPS as $g): $v = $gd['pct'][$g] ?? 0; if ($v <= 0 && ($gd['realization'][$g] ?? 0) <= 0) { continue; } ?>
      <div class="bar-row"><span><?= e($g) ?></span><span class="bar-track"><span class="bar-fill" data-width="<?= e(round(100 * $v / $maxPct, 1)) ?>"></span></span><span class="num"><?= fmt_pct($v, 0) ?></span></div>
    <?php endforeach; ?>
    <p class="muted small">Proporsi jabatan aktif per kelompok jenjang (D-016).</p>
    <table class="small"><thead><tr><th>Jenjang</th><th class="num">FTK</th><th class="num">Realisasi</th></tr></thead><tbody>
    <?php foreach (GRADE_GROUPS as $g): if (($gd['ftk'][$g] ?? 0) + ($gd['realization'][$g] ?? 0) === 0) { continue; } ?>
      <tr><td><?= e($g) ?></td><td class="num"><?= fmt_int($gd['ftk'][$g]) ?></td><td class="num"><?= fmt_int($gd['realization'][$g]) ?></td></tr>
    <?php endforeach; ?></tbody></table>
  </div>
</section>

<?php if ($org['children']): ?>
<section class="card section">
  <h2>Sub-unit (<?= count($org['children']) ?>)</h2>
  <div class="table-wrap"><table><thead><tr><th>Organisasi</th><th class="num">FTK</th><th class="num">Realisasi</th><th>Cluster</th></tr></thead><tbody>
  <?php foreach ($org['children'] as $c): ?><tr><td><a href="<?= e(url('modules/segmentation/organization.php', ['id' => $c['organization_id']])) ?>"><?= e($c['organization_name']) ?></a></td>
    <td class="num"><?= fmt_int($c['ftk']) ?></td><td class="num"><?= fmt_int($c['realization']) ?></td><td><?= e($c['cluster_label']) ?></td></tr><?php endforeach; ?>
  </tbody></table></div>
</section>
<?php endif; ?>
<?php require APP_ROOT . '/shared/footer.php';
