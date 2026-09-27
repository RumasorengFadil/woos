<?php
// Otorisasi terpusat: Role -> Permission (D-032). Halaman memanggil require_permission().
return [
    'roles' => [
        'VIEWER' => ['dashboard.view'],
        'ADMIN'  => ['dashboard.view', 'experiments.view', 'users.manage'],
    ],
    // Item menu: [permission, label, path]
    'menu' => [
        ['dashboard.view',   'Overview',            'modules/segmentation/index.php'],
        ['dashboard.view',   'Cluster Analysis',    'modules/segmentation/cluster.php'],
        ['dashboard.view',   'Model Comparison',    'modules/segmentation/comparison.php'],
        ['dashboard.view',   'Organisasi',          'modules/segmentation/organizations.php'],
        ['experiments.view', 'Registri Eksperimen', 'modules/admin/experiments.php'],
        ['users.manage',     'Pengguna',            'modules/admin/users.php'],
    ],
];
