<?php
// Overview (PRD §49–§50, §57, §63, §67): ringkasan workforce + distribusi & visualisasi cluster model tervalidasi.
require dirname(__DIR__, 2) . '/shared/bootstrap.php';
require_permission('dashboard.view');
require __DIR__ . '/repository.php';

$model = validated_model();
$filters = read_filters($_GET);
$filters['dataset'] ??= $model['dataset_version'] ?? null;
$options = filter_options();
$sum = summary($filters);
$dist = cluster_distribution($filters);
$points = viz_points($filters);
$profiles = cluster_profiles();
$fulfillment = ($sum['ftk'] ?? 0) > 0 ? $sum['realization'] / $sum['ftk'] : null;
$metrics = $model ? json_decode($model['metrics'], true) : [];

$pageTitle = 'Overview';
$activeMenu = 'modules/segmentation/index.php';
require APP_ROOT . '/shared/header.php';
?>
<h1>Overview</h1>
<?php if ($model): ?>
<p class="muted small">
  Validated Model: <strong><?= e($model['model_name'] === 'KMEANS' ? 'K-Means' : $model['model_name']) ?> <?= e($model['model_version']) ?></strong>
  (<?= e($model['experiment_id']) ?>) <span class="badge badge-validated"><?= e($model['validation_status']) ?></span>
  · Dataset <?= e(date('d M Y', strtotime($model['period']))) ?> (<?= e($model['dataset_version']) ?>)
  · Training <?= e(date('d M Y', strtotime($model['trained_at']))) ?>
  · Disetujui <?= e($model['approved_on']) ?>
</p>
<?php else: ?>
<div class="alert alert-error">Belum ada model berstatus APPROVED yang dipublish.</div>
<?php endif; ?>

<?php $action = url('modules/segmentation/index.php'); require APP_ROOT . '/shared/components/filters.php'; ?>

<section class="grid grid-4" aria-label="Ringkasan workforce">
  <div class="card stat"><div class="label">Total FTK</div><div class="value"><?= fmt_int($sum['ftk']) ?></div><div class="sub"><?= fmt_int($sum['organizations']) ?> organisasi</div></div>
  <div class="card stat"><div class="label">Total Realisasi</div><div class="value"><?= fmt_int($sum['realization']) ?></div><div class="sub"><?= fmt_int($sum['positions']) ?> jabatan aktif</div></div>
  <div class="card stat"><div class="label">Total Gap (FTK − Realisasi)</div><div class="value"><?= fmt_signed($sum['gap']) ?></div><div class="sub"><?= fmt_int($sum['vacant_positions']) ?> jabatan kosong</div></div>
  <div class="card stat"><div class="label">Fulfillment Ratio</div><div class="value"><?= fmt_pct($fulfillment) ?></div><div class="sub">Σ realisasi ÷ Σ FTK</div></div>
</section>
<section class="grid grid-4 section" aria-label="Ringkasan model">
  <div class="card stat"><div class="label">Organisasi tersegmentasi</div><div class="value"><?= fmt_int($sum['segmented']) ?></div><div class="sub"><?= fmt_int($sum['not_segmented']) ?> tidak tersegmentasi (tanpa jabatan aktif)</div></div>
  <div class="card stat"><div class="label">Jumlah cluster</div><div class="value"><?= fmt_int($sum['clusters']) ?></div><div class="sub">noise: 0 (K-Means)</div></div>
  <div class="card stat"><div class="label">Anggota atipikal</div><div class="value"><?= fmt_int($sum['atypical']) ?></div><div class="sub">jarak ke centroid &gt; P95 cluster</div></div>
  <div class="card stat"><div class="label">Kualitas model</div><div class="value"><?= fmt_num($metrics['silhouette_score'] ?? null, 3) ?></div><div class="sub">Silhouette · stabilitas ARI <?= fmt_num($metrics['stability_ari'] ?? null, 3) ?></div></div>
</section>

<section class="grid grid-2 section">
  <div class="card">
    <h2>Distribusi cluster</h2>
    <?php
    $total = array_sum(array_column($dist, 'n')) ?: 1;
    $items = array_map(fn ($d) => [
        'label' => $d['cluster_label'], 'value' => (int) $d['n'], 'cluster' => $d['cluster_id'] === null ? -1 : (int) $d['cluster_id'],
        'valueLabel' => fmt_int($d['n']) . ' (' . fmt_pct($d['n'] / $total, 0) . ')',
        'tip' => sprintf('%s org · FTK %s · realisasi %s · gap %s', fmt_int($d['n']), fmt_int($d['ftk']), fmt_int($d['realization']), fmt_signed($d['gap'])),
    ], $dist);
    echo json_script('dist-data', ['items' => $items, 'labelWidth' => 250, 'title' => 'Distribusi cluster']);
    ?>
    <div class="chart" data-chart="bar" data-source="dist-data"></div>
    <details><summary>Tampilkan sebagai tabel</summary>
      <table><thead><tr><th>Cluster</th><th class="num">Organisasi</th><th class="num">FTK</th><th class="num">Realisasi</th><th class="num">Gap</th></tr></thead><tbody>
      <?php foreach ($dist as $d): ?><tr><td><?= e($d['cluster_label']) ?></td><td class="num"><?= fmt_int($d['n']) ?></td><td class="num"><?= fmt_int($d['ftk']) ?></td><td class="num"><?= fmt_int($d['realization']) ?></td><td class="num"><?= fmt_signed($d['gap']) ?></td></tr><?php endforeach; ?>
      </tbody></table>
    </details>
  </div>
  <div class="card">
    <h2>Profil singkat</h2>
    <div class="table-wrap"><table><thead><tr><th>Cluster</th><th class="num">Fulfillment</th><th class="num">Jabatan kosong</th><th class="num">Pegawai/jabatan</th></tr></thead><tbody>
    <?php foreach ($profiles as $p): ?>
      <tr><td class="nowrap"><span class="swatch <?= cluster_class($p['cluster_id']) ?>"></span><a href="<?= e(url('modules/segmentation/cluster.php', ['id' => $p['cluster_id']])) ?>"><?= e($p['cluster_label']) ?></a></td>
      <td class="num"><?= fmt_pct($p['median_fulfillment']) ?></td><td class="num"><?= fmt_pct($p['mean_vacant_share'], 0) ?></td><td class="num"><?= fmt_num($p['mean_avg_realization_per_position']) ?></td></tr>
    <?php endforeach; ?>
    </tbody></table></div>
    <p class="muted small">Fulfillment = median per cluster (hanya organisasi ber-FTK &gt; 0; untuk <em>Terisi Tanpa Formasi</em> sebagian besar organisasi ber-FTK 0 sehingga nilainya berasal dari sedikit organisasi). Kolom lain rata-rata. Profil dihitung pipeline untuk seluruh populasi model (tidak terpengaruh filter).</p>
  </div>
</section>

<section class="card section">
  <h2>Visualisasi cluster (PCA 2D)</h2>
  <p class="muted small">Satu panel per cluster: titik berwarna = anggota cluster, abu-abu = organisasi lain. PCA hanya untuk visualisasi (PRD §52); model memakai 3 feature asli. Arahkan kursor ke titik untuk nama organisasi.</p>
  <?php
  $groups = array_map(fn ($p) => ['id' => (int) $p['cluster_id'], 'label' => $p['cluster_label']], $profiles);
  $pts = array_map(fn ($r) => ['x' => (float) $r['x'], 'y' => (float) $r['y'], 'c' => (int) $r['c'], 'name' => $r['name'], 'label' => $r['label']], $points);
  echo json_script('pca-data', ['points' => $pts, 'groups' => $groups, 'columns' => 5, 'title' => 'PCA per cluster']);
  ?>
  <div class="chart" data-chart="multiples" data-source="pca-data"></div>
</section>
<?php require APP_ROOT . '/shared/footer.php';
