<?php
// Manajemen pengguna (ADMIN): daftar, tambah, aktif/nonaktif. Password tidak pernah ditampilkan.
require dirname(__DIR__, 2) . '/shared/bootstrap.php';
$me = require_permission('users.manage');
require APP_ROOT . '/modules/auth/auth_service.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    csrf_verify();
    try {
        if (($_POST['action'] ?? '') === 'create') {
            create_user(trim((string) $_POST['username']), trim((string) $_POST['full_name']), (string) $_POST['password'], (string) $_POST['role']);
            flash('Pengguna dibuat.', 'success');
        } elseif (($_POST['action'] ?? '') === 'toggle' && ctype_digit((string) $_POST['user_id'])) {
            if ((int) $_POST['user_id'] === (int) $me['user_id']) {
                throw new InvalidArgumentException('Tidak dapat menonaktifkan akun sendiri.');
            }
            db()->prepare('UPDATE app_user SET is_active = NOT is_active WHERE user_id = :id')->execute(['id' => (int) $_POST['user_id']]);
            flash('Status pengguna diperbarui.', 'success');
        }
    } catch (InvalidArgumentException $ex) {
        flash($ex->getMessage(), 'error');
    } catch (PDOException $ex) {
        flash(str_contains($ex->getMessage(), 'unique') ? 'Username sudah dipakai.' : 'Gagal menyimpan.', 'error');
    }
    redirect('modules/admin/users.php');
}
$users = db_all('SELECT user_id, username, full_name, role, is_active, created_at, last_login_at FROM app_user ORDER BY username');

$pageTitle = 'Pengguna';
$activeMenu = 'modules/admin/users.php';
require APP_ROOT . '/shared/header.php';
?>
<h1>Pengguna</h1>
<div class="card table-wrap"><table>
  <thead><tr><th>Username</th><th>Nama</th><th>Role</th><th>Status</th><th>Login terakhir</th><th></th></tr></thead><tbody>
  <?php foreach ($users as $u): ?>
    <tr><td><?= e($u['username']) ?></td><td><?= e($u['full_name']) ?></td><td><span class="badge"><?= e($u['role']) ?></span></td>
      <td><?= $u['is_active'] ? 'aktif' : 'nonaktif' ?></td><td class="small"><?= e($u['last_login_at'] ? date('d M Y H:i', strtotime($u['last_login_at'])) : '—') ?></td>
      <td><?php if ((int) $u['user_id'] !== (int) $me['user_id']): ?>
        <form method="post"><?= csrf_field() ?><input type="hidden" name="action" value="toggle"><input type="hidden" name="user_id" value="<?= (int) $u['user_id'] ?>">
          <button class="btn-link" type="submit"><?= $u['is_active'] ? 'Nonaktifkan' : 'Aktifkan' ?></button></form><?php endif; ?></td></tr>
  <?php endforeach; ?></tbody></table></div>
<section class="card section narrow">
  <h2>Tambah pengguna</h2>
  <form method="post" class="login form-stack">
    <?= csrf_field() ?><input type="hidden" name="action" value="create">
    <label>Username <input type="text" name="username" required pattern="[a-zA-Z0-9._\-]{3,60}"></label>
    <label>Nama lengkap <input type="text" name="full_name" required maxlength="120"></label>
    <label>Password awal (min. 12 karakter) <input type="password" name="password" required minlength="12" autocomplete="new-password"></label>
    <label>Role <select name="role"><option value="VIEWER">VIEWER</option><option value="ADMIN">ADMIN</option></select></label>
    <button type="submit">Simpan</button>
  </form>
</section>
<?php require APP_ROOT . '/shared/footer.php';
