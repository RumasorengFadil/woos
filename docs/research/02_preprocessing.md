# Eksperimen 02 — Preprocessing

| Item | Nilai |
|---|---|
| ID tahap | `S02-PP` |
| Tanggal | 2026-09-25 |
| Dataset | `KP-2026-09-25-v2` |
| Script | `ml/pipeline/s02_preprocessing.py` |
| Output | `ml/outputs/02_preprocessing/KP-2026-09-25-v2/` |
| Test | `tests/ml/test_s02_preprocessing.py` (18 test) |
| Status | **SELESAI — menunggu validasi** |
| Bagian jurnal | *Methods → Data preparation* |

## 1. Prinsip

1. **Tidak ada baris yang dihapus dan tidak ada nilai FTK/Realisasi yang diubah.** Semua treatment berupa kolom turunan atau flag, sehingga setiap keputusan dapat dibalik atau diuji sensitivitasnya pada tahap berikut tanpa mengulang preprocessing.
2. Imputasi hanya dilakukan bila ada justifikasi (PRD §22): jenjang kosong menjadi `UNKNOWN`. Nama jabatan kosong dibiarkan NULL karena bukan feature model.
3. Setiap langkah mencatat jumlah baris terdampak di `preprocessing_log.json`.

## 2. Langkah dan hasil

| # | Langkah | Keputusan | Hasil |
|---|---|---|---|
| 1 | Normalisasi whitespace (tab/spasi ganda/tepi → satu spasi) | D-015 | 71 sel diubah |
| 2 | Nama jabatan kosong → tetap NULL + `is_position_name_missing` | PRD §22 | 5 jabatan |
| 3 | Parsing jenjang → `grade_code`, `grade_number`, `grade_group` | PRD §12, D-004 rev, D-013 | UNKNOWN 42; non-standar dipetakan 24 (12 VP→MM, 12 AM→GENERALIS); JE→SPESIALIS 8 |
| 4 | Flag jabatan bertanda `*)` | D-005 | 42 |
| 5 | Flag FTK/Realisasi: aktif, dormant, terisi tanpa formasi, kosong, melebihi FTK, ekstrem | D-002, D-003, D-006 | 3.042 / 486 / 172 / 763 / 605 / 13 |
| 5b | Flag kemungkinan jabatan ganda (nama identik setelah normalisasi, dalam org yang sama) | D-015 | 2 jabatan (1 pasang, ORG-0908) |
| 6 | Cek duplikat (periode + org + ID jabatan) | PRD §22 | 0, tidak ada yang dihapus |
| 7 | Cek nilai invalid (FTK/Realisasi < 0) | PRD §22 | 0 |
| 8 | Organization mapping: tambah 4 wadah virtual, validasi parent, atribut direktorat | D-007, D-014 | 1.301 org + 4 wadah; direktorat terisi 100 % |
| 9 | Job mapping: ID jabatan unik; konsistensi nama jabatan ↔ kelompok jenjang | PRD §22 | ID unik; 3 nama jabatan dengan >1 kelompok jenjang |

### 2.1 Bukti empiris untuk label non-standar (revisi D-004)

| Label | Pembanding | Jabatan berlabel standar | Kelompok jenjang |
|---|---|---:|---|
| `AM` | Judul diawali *ASSISTANT MANAGER* | 188 | **GENERALIS 100 %** (G3-13/14) |
| `VP` | Judul diawali *VICE PRESIDENT* | 276 | **MM 99,6 %** |

Usulan awal AM → MD (berdasarkan semantik judul) **dibantah oleh data**. Contohnya, *Assistant Manager Kontrak Banten* ber-label `AM` di ORG-1021, sedangkan jabatan bernama sama di ORG-1224 berjenjang *G3-14*. Mapping direvisi menjadi AM → GENERALIS.

Setelah revisi, inkonsistensi nama ↔ kelompok jenjang turun dari 13 menjadi 3 nama jabatan (*Officer Legal*, *Senior Specialist Legal*, *Vice President Harmonisasi dan Monitoring Kebijakan*). Ketiganya dibiarkan sesuai data sumber.

### 2.2 Wadah organisasi & direktorat

| ID | Nama | Level (inferensi) | Parent | Direktorat | Sumber |
|---|---|---:|---|---|---|
| ORG-0013 | Direktorat Utama | 3 | ORG-0002 (inferensi: seluruh direktorat ber-parent root) | dirinya sendiri | HIERARCHY |
| ORG-0226 | Bidang Regulasi Internal | 5 | tidak diketahui | DLMHC | CHILDREN_CONSENSUS |
| ORG-1072 | Sub Bidang Hukum Maluku | 7 | tidak diketahui | DLMHC | CHILDREN_CONSENSUS |
| ORG-1074 | Sub Bidang Hukum Sulawesi Utara | 7 | tidak diketahui | DLMHC | CHILDREN_CONSENSUS |

4 organisasi di bawah wadah terputus (ORG-0644, ORG-1259, ORG-1260, ORG-1263) diberi direktorat DLMHC berdasarkan keanggotaan di dataset v1 (`FALLBACK_V1_MEMBERSHIP`). Wadah **tidak** menjadi unit analisis clustering karena tidak memiliki jabatan. Wadah hanya dipakai untuk hierarki, roll-up, dan filter.

Distribusi organisasi (yang memiliki jabatan) per direktorat:

| Direktorat | Org | FTK | Realisasi | Fulfillment |
|---|---:|---:|---:|---:|
| Legal dan Manajemen Human Capital | 379 | 930 | 716 | 77,0 % |
| Direktorat Utama (SPI, Sekper, DIVTI, PMO) | 255 | 906 | 966 | 106,6 % |
| Keuangan | 147 | 471 | 456 | 96,8 % |
| Manajemen Proyek dan EBT | 110 | 347 | 358 | 103,2 % |
| Retail dan Niaga | 72 | 171 | 149 | 87,1 % |
| Manajemen Risiko | 64 | 206 | 219 | 106,3 % |
| Teknologi, Engineering dan Keberlanjutan | 59 | 161 | 147 | 91,3 % |
| Transmisi dan Perencanaan Sistem | 57 | 167 | 160 | 95,8 % |
| Perencanaan Korporat dan Pengembangan Bisnis | 56 | 161 | 146 | 90,7 % |
| Distribusi | 54 | 144 | 159 | 110,4 % |
| Manajemen Pembangkitan | 47 | 127 | 130 | 102,4 % |
| Kantor Pusat (root) | 1 | 0 | 1 | — |

## 3. Validasi (semua PASS)

Validasi yang dijalankan:
- jumlah baris tetap;
- ΣFTK dan ΣRealisasi tetap;
- tidak ada duplikat kunci;
- tidak ada nilai invalid;
- setiap jabatan memiliki organisasi;
- setiap parent yang dideklarasikan dapat diresolusi;
- setiap organisasi memiliki direktorat;
- `grade_group` tidak pernah NULL.

## 4. Output

| File | Isi |
|---|---|
| `positions_clean.csv` | 3.528 jabatan: nilai asli + jenjang terparsing + 9 flag + direktorat |
| `organizations_clean.csv` | 1.305 org (1.301 + 4 wadah): parent tervalidasi, status parent, direktorat + sumbernya, jumlah anak, leaf, wadah |
| `grade_mapping.csv` | Tabel label jenjang → kode/angka/kelompok/aturan |
| `preprocessing_log.json` | Langkah, hitungan, bukti mapping, hasil validasi |

## 5. Implikasi untuk Tahap 3 (Feature Engineering)

- Feature `position_count` memakai `is_active` (D-002). `vacant_position_count` memakai `is_vacant`.
- `fulfillment_ratio`/`staffing_ratio` bernilai NULL untuk org ber-FTK 0 (73 org). Model memakai `balance_index` (D-003).
- Distribusi jenjang dibentuk dari `grade_group` (7 kelompok termasuk UNKNOWN).
- Flag `is_marked_position` dan `is_extreme_realization` tersedia untuk analisis sensitivitas.
- `directorate_name` tersedia untuk filter dashboard dan uji "apakah cluster hanya mencerminkan direktorat/level" (kontrol artefak, protokol §6).
