<?php
// Model Comparison (PRD §51, §53–§55, §64, §69). Semua metrik dibaca dari registri eksperimen (tidak dihitung ulang).
require dirname(__DIR__, 2) . '/shared/bootstrap.php';
require_permission('dashboard.view');
require __DIR__ . '/repository.php';

$models = model_comparison();
$validated = array_values(array_filter($models, fn ($m) => $m['is_validated_model']))[0] ?? null;
$selectedId = $_GET['model'] ?? ($validated['experiment_id'] ?? null);
$selected = array_values(array_filter($models, fn ($m) => $m['experiment_id'] === $selectedId))[0] ?? $validated;
$algoName = ['KMEANS' => 'K-Means', 'HIERARCHICAL' => 'Hierarchical', 'DBSCAN' => 'DBSCAN'];
$points = $selected ? viz_points([], (int) $selected['model_id']) : [];
$curves = $validated ? metric_curves($validated['feature_set'], $validated['scaler']) : [];
$dbRuns = $validated ? dbscan_runs($validated['feature_set'], $validated['scaler']) : [];

$pageTitle = 'Model Comparison';
$activeMenu = 'modules/segmentation/comparison.php';
require APP_ROOT . '/shared/header.php';

$metricRows = [
    ['Silhouette ↑', 'silhouette', 3], ['Davies–Bouldin ↓', 'davies_bouldin', 3], ['Cluster Count', 'n_clusters', 0],
    ['Noise', 'noise_share', 'pct'], ['Stabilitas bootstrap (ARI) ↑', 'stability_ari', 3], ['Keseimbangan ukuran (entropi) ↑', 'size_entropy_norm', 3],
    ['Relevansi kondisi staffing (η²) ↑', 'workforce_eta2', 3], ["Cramér's V × level ↓", 'cramers_v_level', 3],
    ["Cramér's V × direktorat", 'cramers_v_directorate', 3], ['ARI vs tanda gap (baseline)', 'ari_vs_gap_sign', 3],
    ['ARI vs aturan kutub balance_index (D-029)', 'ari_vs_balance_poles', 3],
];
?>
<h1>Model Comparison</h1>
<p class="muted small">Model terbaik tiap algoritma dari 619 run eksperimen (Tahap 5–6). Hanya <strong>Validated Model</strong> yang dipakai halaman Overview, Cluster Analysis, dan Organisasi (PRD §45). Model pembanding tidak diberi label bisnis.</p>

<section class="card">
  <h2>Tabel perbandingan (PRD §55)</h2>
  <div class="table-wrap"><table>
    <thead><tr><th>Metric</th><?php foreach ($models as $m): ?><th class="num"><?= e($algoName[$m['model_name']]) ?><br>
      <?= $m['is_validated_model'] ? '<span class="badge badge-validated">Validated Model</span>' : '<span class="badge badge-exp">' . e($m['validation_status']) . '</span>' ?></th><?php endforeach; ?></tr></thead>
    <tbody>
      <tr><td>Experiment</td><?php foreach ($models as $m): ?><td class="num"><?= e($m['experiment_id']) ?></td><?php endforeach; ?></tr>
      <tr><td>Konfigurasi</td><?php foreach ($models as $m): ?><td class="num small">set <?= e($m['feature_set']) ?> · <?= e($m['scaler']) ?><br>
        <?= e(implode(', ', array_map(fn ($k, $v) => "$k=$v", array_keys($m['hyperparameters']), $m['hyperparameters']))) ?></td><?php endforeach; ?></tr>
      <?php foreach ($metricRows as [$label, $key, $dec]): ?>
      <tr><td><?= e($label) ?></td><?php foreach ($models as $m): ?><td class="num"><?= $dec === 'pct' ? fmt_pct($m[$key]) : ($dec === 0 ? fmt_int($m[$key]) : fmt_num($m[$key], $dec)) ?></td><?php endforeach; ?></tr>
      <?php endforeach; ?>
      <tr><td>Rank score (6 kriteria, D-028)</td><?php foreach ($models as $m): ?><td class="num"><?= fmt_num($m['rank_score'], 1) ?></td><?php endforeach; ?></tr>
      <tr><td>Rank score setelah D-029</td><?php foreach ($models as $m): ?><td class="num"><?= $m['rank_score_posthoc'] === null ? 'dikeluarkan (setara aturan)' : fmt_num($m['rank_score_posthoc'], 1) ?></td><?php endforeach; ?></tr>
    </tbody></table></div>
  <p class="muted small">Model dengan silhouette tertinggi (DBSCAN/Hierarchical) identik dengan aturan satu feature "balance_index = −1 / +1 / lainnya" (ARI ≈ 1), sehingga tidak dipilih (D-029). Rincian: dokumen riset Tahap 6.</p>
</section>

<section class="card section">
  <h2>Hasil per model</h2>
  <form class="filters" method="get">
    <label>Model
      <select name="model">
        <?php foreach ($models as $m): ?><option value="<?= e($m['experiment_id']) ?>" <?= $selected && $m['experiment_id'] === $selected['experiment_id'] ? 'selected' : '' ?>>
          <?= e($algoName[$m['model_name']]) ?> · <?= e($m['experiment_id']) ?><?= $m['is_validated_model'] ? ' (Validated)' : '' ?></option><?php endforeach; ?>
      </select></label>
    <button type="submit">Tampilkan</button>
  </form>
  <?php if ($selected): ?>
  <div class="grid grid-2">
    <div>
      <h3>Distribusi cluster</h3>
      <?php
      $total = array_sum(array_column($selected['clusters'], 'organization_count')) ?: 1;
      $items = array_map(fn ($c) => ['label' => $c['cluster_label'], 'value' => (int) $c['organization_count'], 'cluster' => (int) $c['cluster_id'],
          'valueLabel' => fmt_int($c['organization_count']) . ' (' . fmt_pct($c['organization_count'] / $total, 0) . ')',
          'tip' => sprintf('median fulfillment %s · jabatan kosong %s', fmt_pct($c['median_fulfillment']), fmt_pct($c['mean_vacant_share'], 0))], $selected['clusters']);
      echo json_script('cmp-dist', ['items' => $items, 'labelWidth' => 220]);
      ?>
      <div class="chart" data-chart="bar" data-source="cmp-dist"></div>
    </div>
    <div>
      <h3>Profil ringkas</h3>
      <div class="table-wrap"><table><thead><tr><th>Cluster</th><th class="num">n</th><th class="num">FTK</th><th class="num">Realisasi</th><th class="num">Fulfillment</th><th class="num">Kosong</th></tr></thead><tbody>
      <?php foreach ($selected['clusters'] as $c): ?><tr><td><?= e($c['cluster_label']) ?></td><td class="num"><?= fmt_int($c['organization_count']) ?></td><td class="num"><?= fmt_num($c['mean_ftk']) ?></td><td class="num"><?= fmt_num($c['mean_realization']) ?></td><td class="num"><?= fmt_pct($c['median_fulfillment']) ?></td><td class="num"><?= fmt_pct($c['mean_vacant_share'], 0) ?></td></tr><?php endforeach; ?>
      </tbody></table></div>
    </div>
  </div>
  <h3 class="section">Visualisasi (PCA 2D)<?= $selected['model_name'] === 'DBSCAN' ? ' — noise ditandai X merah' : '' ?></h3>
  <?php
  $groups = array_map(fn ($c) => ['id' => (int) $c['cluster_id'], 'label' => $c['cluster_label']], $selected['clusters']);
  $pts = array_map(fn ($r) => ['x' => (float) $r['x'], 'y' => (float) $r['y'], 'c' => (int) $r['c'], 'name' => $r['name'], 'label' => $r['label']], $points);
  echo json_script('cmp-pca', ['points' => $pts, 'groups' => $groups, 'columns' => 5]);
  ?>
  <div class="chart" data-chart="multiples" data-source="cmp-pca"></div>
  <?php endif; ?>
</section>

<?php if ($validated): ?>
<section class="grid grid-2 section">
  <div class="card">
    <h2>Silhouette vs K <span class="muted small">(set <?= e($validated['feature_set']) ?>, <?= e($validated['scaler']) ?>)</span></h2>
    <?php
    $series = [];
    foreach ($curves as $c) {
        $name = $c['model_name'] === 'KMEANS' ? 'K-Means' : 'HC ' . $c['linkage'];
        $series[$name]['name'] = $name;
        $series[$name]['points'][] = ['x' => (int) $c['k'], 'y' => $c['silhouette'] === null ? null : (float) $c['silhouette'],
            'mark' => $c['model_name'] === 'KMEANS' && (int) $c['k'] === (int) $validated['hyperparameters']['n_clusters'],
            'note' => 'DBI ' . fmt_num($c['davies_bouldin'], 3)];
    }
    uksort($series, fn ($a, $b) => ($a === 'K-Means' ? '0' : $a) <=> ($b === 'K-Means' ? '0' : $b));   // model terpilih = slot 1
    $series = array_values($series);
    foreach ($series as $i => &$s) { $s['highlight'] = $s['name'] === 'K-Means'; }
    echo json_script('sil-data', ['series' => $series, 'xLabel' => 'K', 'yLabel' => 'Silhouette', 'highlight' => true,
        'legend' => array_map(fn ($s, $i) => ['label' => $s['name'], 'slot' => $i + 1], $series, array_keys($series))]);
    ?>
    <div class="chart" data-chart="line" data-source="sil-data"></div>
    <p class="muted small">Lingkaran besar = K model tervalidasi.</p>
  </div>
  <div class="card">
    <h2>Elbow K-Means <span class="muted small">(inertia, set <?= e($validated['feature_set']) ?>)</span></h2>
    <?php
    $elbow = array_values(array_filter($curves, fn ($c) => $c['model_name'] === 'KMEANS'));
    echo json_script('elbow-data', ['series' => [['name' => 'K-Means', 'points' => array_map(fn ($c) => ['x' => (int) $c['k'], 'y' => (float) $c['inertia'],
        'mark' => (int) $c['k'] === (int) $validated['hyperparameters']['n_clusters']], $elbow)]], 'xLabel' => 'K', 'yLabel' => 'Inertia']);
    ?>
    <div class="chart" data-chart="line" data-source="elbow-data"></div>
  </div>
</section>

<section class="card section">
  <h2>DBSCAN: jumlah cluster & noise per konfigurasi <span class="muted small">(set <?= e($validated['feature_set']) ?>, <?= e($validated['scaler']) ?>)</span></h2>
  <div class="table-wrap"><table><thead><tr><th>Experiment</th><th class="num">min_samples</th><th class="num">eps</th><th class="num">Cluster</th><th class="num">Noise</th><th class="num">Silhouette</th><th>Layak (D-027)</th></tr></thead><tbody>
  <?php foreach ($dbRuns as $r): ?><tr><td><?= e($r['experiment_id']) ?></td><td class="num"><?= e($r['min_samples']) ?></td><td class="num"><?= fmt_num($r['eps'], 3) ?></td><td class="num"><?= fmt_int($r['n_clusters']) ?></td><td class="num"><?= fmt_pct($r['noise_share']) ?></td><td class="num"><?= fmt_num($r['silhouette'], 3) ?></td><td><?= $r['eligible'] ? 'ya' : 'tidak' ?></td></tr><?php endforeach; ?>
  </tbody></table></div>
</section>
<?php endif; ?>

<section class="grid grid-2 section">
  <figure class="card"><h2>Dendrogram (Hierarchical)</h2><img src="<?= e(url('assets/figures/E04_dendrograms.png')) ?>" alt="Dendrogram ward, complete, average untuk 4 feature set" loading="lazy">
    <figcaption>30 merge terakhir per linkage × feature set (PRD §31, §53). Figure riset Tahap 5.</figcaption></figure>
  <figure class="card"><h2>Kualitas vs stabilitas</h2><img src="<?= e(url('assets/figures/V02_silhouette_vs_stability.png')) ?>" alt="Scatter silhouette vs stabilitas 143 run layak" loading="lazy">
    <figcaption>143 run layak (Tahap 6). Kandidat berdasarkan D-028 dilingkari.</figcaption></figure>
  <figure class="card"><h2>Elbow semua feature set</h2><img src="<?= e(url('assets/figures/E01_kmeans_elbow.png')) ?>" alt="Elbow K-Means per feature set" loading="lazy"></figure>
  <figure class="card"><h2>DBSCAN noise vs cluster (semua set)</h2><img src="<?= e(url('assets/figures/E06_dbscan_noise_vs_clusters.png')) ?>" alt="DBSCAN noise vs jumlah cluster" loading="lazy"></figure>
</section>
<?php require APP_ROOT . '/shared/footer.php';
