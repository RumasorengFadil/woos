<?php
require __DIR__ . '/shared/bootstrap.php';
redirect(current_user() ? 'modules/segmentation/index.php' : 'modules/auth/login.php');
