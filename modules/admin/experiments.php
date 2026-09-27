<?php
// Registri eksperimen (ADMIN): seluruh 619 run beserta metrik & kelayakan — transparansi riset (PRD §71–§72).
require dirname(__DIR__, 2) . '/shared/bootstrap.php';
require_permission('experiments.view');

$algo = in_array($_GET['algo'] ?? '', ['KMEANS', 'HIERARCHICAL', 'DBSCAN'], true) ? $_GET['algo'] : null;
$set = in_array($_GET['set'] ?? '', ['A', 'B', 'C', 'R'], true) ? $_GET['set'] : null;
$eligibleOnly = !empty($_GET['eligible']);
$where = ["variant = 'all'"];
$p = [];
if ($algo) { $where[] = 'model_name = :a'; $p['a'] = $algo; }
if ($set) { $where[] = 'feature_set = :s'; $p['s'] = $set; }
if ($eligibleOnly) { $where[] = 'eligible'; }
$rows = db_all('SELECT experiment_id, model_name, feature_set, scaler, hyperparameters, n_clusters, noise_share, silhouette, davies_bouldin,
                       stability_ari, size_entropy_norm, ari_vs_balance_poles, eligible, rejection_reason, rank_score, rank_score_posthoc, validation_status
                FROM experiment WHERE ' . implode(' AND ', $where) . ' ORDER BY rank_score_posthoc NULLS LAST, rank_score NULLS LAST, experiment_id', $p);
$totals = db_one("SELECT count(*) AS runs, count(*) FILTER (WHERE eligible) AS eligible, max(code_version) AS code_version FROM experiment");

$pageTitle = 'Registri Eksperimen';
$activeMenu = 'modules/admin/experiments.php';
require APP_ROOT . '/shared/header.php';
?>
<h1>Registri Eksperimen</h1>
<p class="muted small"><?= fmt_int($totals['runs']) ?> run tercatat (termasuk varian unik) · <?= fmt_int($totals['eligible']) ?> layak (D-027) · code version <?= e($totals['code_version']) ?>. Diurutkan menurut skor pemilihan (D-028/D-029).</p>
<form class="filters" method="get">
  <label>Algoritma <select name="algo"><option value="">Semua</option><?php foreach (['KMEANS', 'HIERARCHICAL', 'DBSCAN'] as $a): ?><option <?= $algo === $a ? 'selected' : '' ?>><?= e($a) ?></option><?php endforeach; ?></select></label>
  <label>Feature set <select name="set"><option value="">Semua</option><?php foreach (['A', 'B', 'C', 'R'] as $s): ?><option <?= $set === $s ? 'selected' : '' ?>><?= e($s) ?></option><?php endforeach; ?></select></label>
  <label class="check"><input type="checkbox" name="eligible" value="1" <?= $eligibleOnly ? 'checked' : '' ?>> Hanya layak</label>
  <button type="submit">Terapkan</button>
</form>
<div class="card table-wrap"><table>
  <thead><tr><th>Run</th><th>Algoritma</th><th>Set/scaler</th><th>Parameter</th><th class="num">Cluster</th><th class="num">Noise</th><th class="num">Silhouette</th><th class="num">DBI</th>
    <th class="num">Stabilitas</th><th class="num">Entropi</th><th class="num">ARI aturan</th><th>Kelayakan</th><th class="num">Skor</th><th>Status</th></tr></thead>
  <tbody>
  <?php foreach ($rows as $r): $h = json_decode($r['hyperparameters'], true); unset($h['n_init']); ?>
    <tr><td><?= e($r['experiment_id']) ?></td><td><?= e($r['model_name']) ?></td><td><?= e($r['feature_set']) ?>/<?= e($r['scaler']) ?></td>
      <td class="small"><?= e(implode(', ', array_map(fn ($k, $v) => "$k=$v", array_keys($h), $h))) ?></td>
      <td class="num"><?= fmt_int($r['n_clusters']) ?></td><td class="num"><?= fmt_pct($r['noise_share']) ?></td>
      <td class="num"><?= fmt_num($r['silhouette'], 3) ?></td><td class="num"><?= fmt_num($r['davies_bouldin'], 3) ?></td>
      <td class="num"><?= fmt_num($r['stability_ari'], 3) ?></td><td class="num"><?= fmt_num($r['size_entropy_norm'], 3) ?></td>
      <td class="num"><?= fmt_num($r['ari_vs_balance_poles'], 3) ?></td>
      <td class="small"><?= $r['eligible'] ? 'layak' : e($r['rejection_reason']) ?></td>
      <td class="num"><?= fmt_num($r['rank_score_posthoc'] ?? $r['rank_score'], 1) ?></td>
      <td><?= $r['validation_status'] === 'APPROVED' ? '<span class="badge badge-validated">APPROVED</span>' : '<span class="badge badge-exp">' . e($r['validation_status']) . '</span>' ?></td></tr>
  <?php endforeach; ?>
  </tbody></table></div>
<?php require APP_ROOT . '/shared/footer.php';
