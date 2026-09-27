<?php
// Cluster Analysis (PRD §56, §68): profile card per cluster, rata-rata feature, distribusi feature, komposisi direktorat.
require dirname(__DIR__, 2) . '/shared/bootstrap.php';
require_permission('dashboard.view');
require __DIR__ . '/repository.php';

$model = validated_model();
$filters = read_filters($_GET);
$filters['dataset'] ??= $model['dataset_version'] ?? null;
$options = filter_options();
$profiles = cluster_profiles();
$stats = array_column(cluster_feature_stats($filters), null, 'cluster_id');
$byDir = cluster_by_directorate($filters);
$focus = isset($_GET['id']) && ctype_digit((string) $_GET['id']) ? (int) $_GET['id'] : null;

$pageTitle = 'Cluster Analysis';
$activeMenu = 'modules/segmentation/cluster.php';
require APP_ROOT . '/shared/header.php';
?>
<h1>Cluster Analysis</h1>
<p class="muted small">Profil & label berasal dari model tervalidasi <?= e($model['experiment_id'] ?? '—') ?>. Label diberikan setelah profiling dan validasi bisnis (PRD §41, §45) — bukan aturan ambang.</p>
<?php $action = url('modules/segmentation/cluster.php'); require APP_ROOT . '/shared/components/filters.php'; ?>

<section class="grid grid-5">
<?php foreach ($profiles as $p): $s = $stats[$p['cluster_id']] ?? null; ?>
  <article class="card cluster-card <?= cluster_class($p['cluster_id']) ?><?= $focus === (int) $p['cluster_id'] ? ' is-focus' : '' ?>" id="cluster-<?= (int) $p['cluster_id'] ?>">
    <h3><?= e(mb_strtoupper($p['cluster_label'])) ?></h3>
    <p class="muted small"><?= e($p['prd_archetype']) ?></p>
    <dl class="kv small">
      <dt>Organisasi</dt><dd><?= fmt_int($p['organization_count']) ?> (<?= fmt_pct($p['organization_share'], 0) ?>)<?= $s && (int) $s['n'] !== (int) $p['organization_count'] ? ' · ' . fmt_int($s['n']) . ' sesuai filter' : '' ?></dd>
      <dt>Rata-rata FTK</dt><dd><?= fmt_num($p['mean_ftk']) ?></dd>
      <dt>Rata-rata realisasi</dt><dd><?= fmt_num($p['mean_realization']) ?></dd>
      <dt>Rata-rata gap</dt><dd><?= fmt_num($p['mean_gap']) ?></dd>
      <dt>Fulfillment (median)</dt><dd><?= fmt_pct($p['median_fulfillment']) ?></dd>
      <dt>Jabatan kosong</dt><dd><?= fmt_pct($p['mean_vacant_share'], 0) ?> (<?= fmt_num($p['mean_vacant_position']) ?> jabatan)</dd>
      <dt>Pegawai/jabatan</dt><dd><?= fmt_num($p['mean_avg_realization_per_position']) ?></dd>
    </dl>
    <strong class="small">Karakteristik</strong>
    <ul class="small"><?php foreach ($p['characteristics'] as $c): ?><li><?= e($c) ?></li><?php endforeach; ?></ul>
    <p class="small"><?= e($p['interpretation']) ?></p>
    <a class="small" href="<?= e(url('modules/segmentation/organizations.php', query_keep($filters, ['cluster' => $p['cluster_code']]))) ?>">Lihat organisasi →</a>
  </article>
<?php endforeach; ?>
</section>

<section class="card section">
  <h2>Distribusi feature per cluster <span class="muted small">(sesuai filter)</span></h2>
  <div class="table-wrap"><table>
    <thead><tr><th>Cluster</th><th class="num">n</th><th class="num">Fulfillment Q1</th><th class="num">Median</th><th class="num">Q3</th>
      <th class="num">Jabatan kosong (median / rata-rata)</th><th class="num">Pegawai/jabatan (median / rata-rata)</th><th class="num">Rata-rata gap</th></tr></thead>
    <tbody>
    <?php foreach ($profiles as $p): $s = $stats[$p['cluster_id']] ?? null; if (!$s) { continue; } ?>
      <tr><td class="nowrap"><span class="swatch <?= cluster_class($p['cluster_id']) ?>"></span><?= e($p['cluster_label']) ?></td>
        <td class="num"><?= fmt_int($s['n']) ?></td><td class="num"><?= fmt_pct($s['ful_q1']) ?></td><td class="num"><?= fmt_pct($s['ful_med']) ?></td>
        <td class="num"><?= fmt_pct($s['ful_q3']) ?></td><td class="num"><?= fmt_pct($s['vac_med'], 0) ?> / <?= fmt_pct($s['vac_mean'], 0) ?></td>
        <td class="num"><?= fmt_num($s['arp_med']) ?> / <?= fmt_num($s['arp_mean']) ?></td><td class="num"><?= fmt_num($s['gap_mean']) ?></td></tr>
    <?php endforeach; ?>
    </tbody></table></div>
  <p class="muted small">Fulfillment hanya untuk organisasi ber-FTK &gt; 0 (FTK = 0 tidak dibagi, PRD §8).</p>
</section>

<section class="card section">
  <h2>Komposisi cluster per direktorat</h2>
  <?php
  $rows = [];
  $order = array_map(fn ($p) => $p['cluster_code'], $profiles);
  $ids = array_column($profiles, 'cluster_id', 'cluster_code');
  $labels = array_column($profiles, 'cluster_label', 'cluster_code');
  foreach ($byDir as $r) {
      $key = $r['directorate_id'] ?? '—';
      $rows[$key]['label'] ??= ucwords(strtolower(str_replace('DIREKTORAT ', '', $r['directorate_name'] ?? '—')));
      $rows[$key]['counts'][$r['cluster_code']] = (int) $r['n'];
  }
  $data = [];
  foreach ($rows as $row) {
      $parts = [];
      foreach ($order as $code) {
          $parts[] = ['cluster' => (int) $ids[$code], 'label' => $labels[$code], 'value' => $row['counts'][$code] ?? 0];
      }
      $parts[] = ['cluster' => -1, 'label' => 'Tidak Tersegmentasi', 'value' => $row['counts']['NOT_SEGMENTED'] ?? 0];
      $data[] = ['label' => $row['label'], 'parts' => $parts];
  }
  $legend = array_map(fn ($p) => ['cluster' => (int) $p['cluster_id'], 'label' => $p['cluster_label']], $profiles);
  $legend[] = ['cluster' => -1, 'label' => 'Tidak Tersegmentasi'];
  echo json_script('dir-data', ['rows' => $data, 'labelWidth' => 300, 'legend' => $legend, 'title' => 'Komposisi cluster per direktorat']);
  ?>
  <div class="chart" data-chart="stack" data-source="dir-data"></div>
  <details><summary>Tampilkan sebagai tabel</summary>
    <div class="table-wrap"><table><thead><tr><th>Direktorat</th><?php foreach ($profiles as $p): ?><th class="num"><?= e($p['cluster_label']) ?></th><?php endforeach; ?><th class="num">Tidak Tersegmentasi</th></tr></thead><tbody>
    <?php foreach ($rows as $row): ?><tr><td><?= e($row['label']) ?></td><?php foreach ($order as $code): ?><td class="num"><?= fmt_int($row['counts'][$code] ?? 0) ?></td><?php endforeach; ?><td class="num"><?= fmt_int($row['counts']['NOT_SEGMENTED'] ?? 0) ?></td></tr><?php endforeach; ?>
    </tbody></table></div>
  </details>
</section>

<section class="card section">
  <h2>Profil relatif (figure riset)</h2>
  <figure><img src="<?= e(url('assets/figures/P01_cluster_profile_heatmap.png')) ?>" alt="Heatmap z-score rata-rata cluster relatif terhadap populasi" loading="lazy">
    <figcaption>Rata-rata feature per cluster dalam satuan standar deviasi populasi (dihasilkan pipeline Tahap 7).</figcaption></figure>
</section>
<?php require APP_ROOT . '/shared/footer.php';
