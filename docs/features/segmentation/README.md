# Fitur: Workforce Organization Segmentation (dashboard)

Dokumen ini menggambarkan **perilaku yang benar-benar terimplementasi** (Tahap 9), bukan rencana.

## Prinsip

- Semua cluster, label, profil, metrik, dan koordinat visual **berasal dari pipeline ML** yang dipublish ke PostgreSQL (`s08_publish.py`).
- Dashboard hanya membaca view `v_validated_model`, `v_validated_organization`, `v_model_comparison`, serta tabel `cluster_profile`, `cluster_result`, dan `experiment` (PRD §47, §95).
- Filter hanya menyaring hasil yang sudah ada; tidak ada training ulang (PRD §62).
- Kepatuhan diverifikasi otomatis: test `audit statis` di `tests/php/run.php` memastikan tidak ada algoritma clustering, tidak ada penetapan cluster di PHP/JS, dan repository segmentasi read-only.

## Halaman

| Halaman | Path | Isi | PRD |
|---|---|---|---|
| Overview | `modules/segmentation/index.php` | Info Validated Model (model, versi, dataset, training, approval); 4 kartu utama (FTK, Realisasi, Gap, Fulfillment) + 4 kartu opsional (tersegmentasi, jumlah cluster, atipikal, kualitas model); distribusi cluster (bar + tabel); profil singkat; PCA 2D small multiples per cluster | §49–§50, §52, §57, §63, §67 |
| Cluster Analysis | `modules/segmentation/cluster.php` | Profile card per cluster (label, arketipe, rata-rata, karakteristik, interpretasi); distribusi feature per cluster (kuartil fulfillment, median/rata-rata jabatan kosong & pegawai/jabatan); komposisi cluster per direktorat (stacked + tabel); heatmap profil | §56, §68 |
| Model Comparison | `modules/segmentation/comparison.php` | Tabel PRD §55 untuk model terbaik tiap algoritma dengan penanda **Validated Model**; pemilih model (distribusi, profil, PCA; noise DBSCAN = X merah); Silhouette vs K & Elbow dari registri; tabel DBSCAN eps × min_samples × noise; dendrogram & figure riset | §51, §53–§55, §64, §69 |
| Organisasi | `modules/segmentation/organizations.php` | Tabel dengan search, sort (8 kolom), pagination (25), filter; badge atipikal | §58 |
| Organization Detail | `modules/segmentation/organization.php?id=` | Informasi (parent, level, direktorat); FTK/Realisasi/Gap/Fulfillment; cluster + interpretasi; **penjelasan organisasi vs rata-rata cluster**; feature; distribusi jenjang (proporsi + FTK/realisasi); sub-unit; cluster di model pembanding | §59–§60, §70, §85 |
| API | `modules/segmentation/api.php?resource=` | JSON read-only: `summary`, `clusters`, `organizations`, `organization&id=`, `comparison` (butuh login) | §46, §65 |
| Registri Eksperimen (ADMIN) | `modules/admin/experiments.php` | 619 run (varian `all`), filter algoritma/set/kelayakan, diurutkan menurut skor seleksi | §71–§72 |
| Pengguna (ADMIN) | `modules/admin/users.php` | Daftar, tambah, aktif/nonaktif pengguna | D-032 |

## Filter (PRD §61)

- Periode (`dataset_version` aktif), direktorat, level, cluster (termasuk "Tidak Tersegmentasi"), dan jenjang (organisasi yang memiliki jabatan aktif pada kelompok jenjang tersebut).
- Halaman Organisasi menambah pencarian nama dan filter "hanya anggota atipikal".
- Semua input divalidasi dengan whitelist/regex dan dikirim sebagai parameter terikat.

## Catatan tampilan

- Warna cluster mengikuti `cluster_id` (slot palet tetap, sama dengan figure riset). Ada dark mode; tata letak responsif hingga 375 px.
- Profil cluster (kartu, profil singkat) mewakili seluruh populasi model. Angka ringkasan dan distribusi mengikuti filter.
- Fulfillment `NULL` (FTK = 0) ditampilkan "—" (PRD §8).
