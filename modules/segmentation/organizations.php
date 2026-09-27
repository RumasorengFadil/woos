<?php
// Organization List (PRD §58): search, sort, pagination, filter atas hasil model tervalidasi.
require dirname(__DIR__, 2) . '/shared/bootstrap.php';
require_permission('dashboard.view');
require __DIR__ . '/repository.php';

$model = validated_model();
$filters = read_filters($_GET);
$filters['dataset'] ??= $model['dataset_version'] ?? null;
$options = filter_options();
$sort = array_key_exists($_GET['sort'] ?? '', SORTABLE) ? $_GET['sort'] : 'name';
$dir = ($_GET['dir'] ?? 'asc') === 'desc' ? 'desc' : 'asc';
$size = (int) config('app.page_size');
$page = max(1, (int) ($_GET['page'] ?? 1));
$result = organizations($filters, $sort, $dir, $page, $size);
$pages = max(1, (int) ceil($result['total'] / $size));

function sort_link(string $key, string $label, array $filters, string $sort, string $dir): string
{
    $next = $sort === $key && $dir === 'asc' ? 'desc' : 'asc';
    $arrow = $sort === $key ? ($dir === 'asc' ? ' ▲' : ' ▼') : '';
    return '<a href="' . e(url('modules/segmentation/organizations.php', query_keep($filters, ['sort' => $key, 'dir' => $next]))) . '">'
        . e($label) . $arrow . '</a>';
}

$pageTitle = 'Organisasi';
$activeMenu = 'modules/segmentation/organizations.php';
require APP_ROOT . '/shared/header.php';
?>
<h1>Organisasi</h1>
<?php $action = url('modules/segmentation/organizations.php'); $withSearch = true; require APP_ROOT . '/shared/components/filters.php'; ?>
<p class="muted small"><?= fmt_int($result['total']) ?> organisasi · halaman <?= $page ?> dari <?= $pages ?></p>
<div class="card table-wrap">
<table>
  <thead><tr>
    <th><?= sort_link('name', 'Organisasi', $filters, $sort, $dir) ?></th><th>Direktorat</th>
    <th class="num"><?= sort_link('level', 'Level', $filters, $sort, $dir) ?></th>
    <th class="num"><?= sort_link('ftk', 'FTK', $filters, $sort, $dir) ?></th>
    <th class="num"><?= sort_link('realization', 'Realisasi', $filters, $sort, $dir) ?></th>
    <th class="num"><?= sort_link('gap', 'Gap', $filters, $sort, $dir) ?></th>
    <th class="num"><?= sort_link('fulfillment', 'Fulfillment', $filters, $sort, $dir) ?></th>
    <th class="num"><?= sort_link('vacant', 'Jabatan kosong', $filters, $sort, $dir) ?></th>
    <th><?= sort_link('cluster', 'Cluster', $filters, $sort, $dir) ?></th>
  </tr></thead>
  <tbody>
  <?php foreach ($result['rows'] as $r): ?>
    <tr>
      <td><a href="<?= e(url('modules/segmentation/organization.php', ['id' => $r['organization_id']])) ?>"><?= e($r['organization_name']) ?></a>
        <span class="muted small"><?= e($r['organization_id']) ?></span></td>
      <td class="small"><?= e(ucwords(strtolower(str_replace('DIREKTORAT ', '', (string) $r['directorate_name'])))) ?></td>
      <td class="num"><?= e($r['organization_level']) ?></td>
      <td class="num"><?= fmt_int($r['ftk']) ?></td><td class="num"><?= fmt_int($r['realization']) ?></td>
      <td class="num"><?= fmt_signed($r['gap']) ?></td><td class="num"><?= fmt_pct($r['fulfillment_ratio']) ?></td>
      <td class="num"><?= fmt_pct($r['vacant_share'], 0) ?></td>
      <td class="nowrap"><span class="swatch <?= cluster_class($r['cluster_id']) ?>"></span><?= e($r['cluster_label']) ?>
        <?= $r['is_atypical_member'] ? '<span class="badge" title="Jarak ke centroid > P95 cluster">atipikal</span>' : '' ?></td>
    </tr>
  <?php endforeach; ?>
  <?php if (!$result['rows']): ?><tr><td colspan="9" class="muted">Tidak ada organisasi sesuai filter.</td></tr><?php endif; ?>
  </tbody>
</table>
</div>
<nav class="pagination" aria-label="Halaman">
  <?php if ($page > 1): ?><a class="btn btn-secondary" href="<?= e(url('modules/segmentation/organizations.php', query_keep($filters, ['sort' => $sort, 'dir' => $dir, 'page' => $page - 1]))) ?>">← Sebelumnya</a><?php endif; ?>
  <span class="muted small">Halaman <?= $page ?> / <?= $pages ?></span>
  <?php if ($page < $pages): ?><a class="btn btn-secondary" href="<?= e(url('modules/segmentation/organizations.php', query_keep($filters, ['sort' => $sort, 'dir' => $dir, 'page' => $page + 1]))) ?>">Berikutnya →</a><?php endif; ?>
</nav>
<?php require APP_ROOT . '/shared/footer.php';
