<?php
// Menu mengikuti RBAC: hanya menampilkan tautan yang boleh diakses (memperbaiki technical debt ORBIT).
$active = $activeMenu ?? '';
?>
<nav class="menu" aria-label="Navigasi utama">
  <?php foreach (config('rbac.menu') as [$perm, $label, $path]): ?>
    <?php if (user_can($perm)): ?>
      <a href="<?= e(url($path)) ?>" class="<?= $active === $path ? 'active' : '' ?>"><?= e($label) ?></a>
    <?php endif; ?>
  <?php endforeach; ?>
</nav>
