<?php
require dirname(__DIR__, 2) . '/shared/bootstrap.php';
if (current_user()) {
    redirect('modules/segmentation/index.php');
}
$pageTitle = 'Masuk';
require APP_ROOT . '/shared/header.php';
?>
<section class="card login">
  <h1>Masuk</h1>
  <p class="muted small">Dashboard hasil segmentasi organisasi berbasis Machine Learning.</p>
  <form method="post" action="<?= e(url('modules/auth/login_submit.php')) ?>">
    <?= csrf_field() ?>
    <label>Username <input type="text" name="username" autocomplete="username" required maxlength="60"></label>
    <label>Password <input type="password" name="password" autocomplete="current-password" required></label>
    <button type="submit">Masuk</button>
  </form>
</section>
<?php require APP_ROOT . '/shared/footer.php';
