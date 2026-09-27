<?php
/** Bar filter (PRD §61–§62): hanya memfilter hasil yang sudah ada — tidak memicu training ulang.
 * @var array $filters  @var array $options  @var string $action  @var bool $withSearch
 */
$withSearch = $withSearch ?? false;
?>
<form class="filters" method="get" action="<?= e($action) ?>">
  <label>Periode
    <select name="dataset">
      <?php foreach (periods() as $p): ?>
        <option value="<?= e($p['dataset_version']) ?>" <?= $filters['dataset'] === $p['dataset_version'] ? 'selected' : '' ?>>
          <?= e(date('d M Y', strtotime($p['period']))) ?></option>
      <?php endforeach; ?>
    </select>
  </label>
  <label>Direktorat
    <select name="directorate"><option value="">Semua</option>
      <?php foreach ($options['directorates'] as $d): ?>
        <option value="<?= e($d['directorate_id']) ?>" <?= $filters['directorate'] === $d['directorate_id'] ? 'selected' : '' ?>><?= e(ucwords(strtolower($d['directorate_name']))) ?></option>
      <?php endforeach; ?>
    </select>
  </label>
  <label>Level
    <select name="level"><option value="">Semua</option>
      <?php foreach ($options['levels'] as $l): ?>
        <option value="<?= e($l) ?>" <?= $filters['level'] === (int) $l ? 'selected' : '' ?>>Level <?= e($l) ?></option>
      <?php endforeach; ?>
    </select>
  </label>
  <label>Cluster
    <select name="cluster"><option value="">Semua</option>
      <?php foreach ($options['clusters'] as $c): ?>
        <option value="<?= e($c['cluster_code']) ?>" <?= $filters['cluster'] === $c['cluster_code'] ? 'selected' : '' ?>><?= e($c['cluster_label']) ?></option>
      <?php endforeach; ?>
      <option value="NOT_SEGMENTED" <?= $filters['cluster'] === 'NOT_SEGMENTED' ? 'selected' : '' ?>>Tidak Tersegmentasi</option>
    </select>
  </label>
  <label>Jenjang (memiliki jabatan aktif)
    <select name="grade"><option value="">Semua</option>
      <?php foreach ($options['grades'] as $g): ?>
        <option value="<?= e($g) ?>" <?= $filters['grade'] === $g ? 'selected' : '' ?>><?= e($g) ?></option>
      <?php endforeach; ?>
    </select>
  </label>
  <?php if ($withSearch): ?>
  <label>Cari organisasi <input type="search" name="q" value="<?= e($filters['search']) ?>" maxlength="80"></label>
  <label class="check"><input type="checkbox" name="atypical" value="1" <?= $filters['atypical'] ? 'checked' : '' ?>> Hanya anggota atipikal</label>
  <?php endif; ?>
  <button type="submit">Terapkan</button>
  <a class="btn btn-secondary" href="<?= e($action) ?>">Reset</a>
</form>
