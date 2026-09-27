<?php
/** @var string $pageTitle  @var string $activeMenu */
$user = current_user();
$flash = flash();
?><!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= e($pageTitle ?? 'WOOS') ?> · WOOS</title>
<link rel="stylesheet" href="<?= e(url('assets/css/app.css')) ?>">
</head>
<body>
<header class="topbar">
  <a class="brand" href="<?= e(url('modules/segmentation/index.php')) ?>">
    <span class="brand-mark" aria-hidden="true"></span>
    <span>Workforce Organization Segmentation</span>
  </a>
  <?php if ($user): ?>
  <div class="userbox">
    <span><?= e($user['full_name']) ?> · <span class="badge"><?= e($user['role']) ?></span></span>
    <form method="post" action="<?= e(url('modules/auth/logout.php')) ?>"><?= csrf_field() ?><button class="btn-link" type="submit">Keluar</button></form>
  </div>
  <?php endif; ?>
</header>
<?php if ($user) { require APP_ROOT . '/shared/menu.php'; } ?>
<main class="container">
<?php if ($flash): ?><div class="alert alert-<?= e($flash['type']) ?>"><?= e($flash['message']) ?></div><?php endif; ?>
