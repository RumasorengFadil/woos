# Eksperimen 01 — Data Understanding

| Item | Nilai |
|---|---|
| ID tahap | `S01-DU` |
| Tanggal | 2026-09-25 |
| Dataset | `DLMHC-2026-09-25-v1` (SHA-256 `3d805a9d…b243`) — **SUPERSEDED oleh v2, lihat `01c_dataset_v2.md`** |
| Script | `ml/pipeline/s01_data_understanding.py` |
| Output | `ml/outputs/01_data_understanding/DLMHC-2026-09-25-v1/` |
| Status | SELESAI — keputusan D-001…D-008 APPROVED (lihat `decision_log.md`) |
| Bagian jurnal | *Methods → Data*, *Results → Data characteristics*, *Limitations* |

> Tahap ini **tidak mengubah data**. Semua angka dihitung dari file mentah. Keputusan cleaning ditunda ke Tahap 2 setelah divalidasi.

---

## 1. Tujuan

Memahami struktur, kelengkapan, dan karakter dataset FTK–Realisasi sebelum preprocessing, sesuai PRD §21, serta mengidentifikasi risiko metodologis yang dapat memengaruhi validitas clustering.

## 2. Metode

1. Profiling struktural: jumlah baris, kolom, tipe, nilai unik, missing value.
2. Pemeriksaan duplikat pada kunci `(periode, organisasi, ID jabatan)` dan `(periode, organisasi, nama jabatan)`.
3. Pemeriksaan nilai invalid (FTK/Realisasi < 0) dan edge case (FTK = 0, Realisasi = 0).
4. Deteksi nilai ekstrem dengan aturan IQR (Tukey, k = 1,5 dan 3,0) pada level jabatan, ditambah aturan domain: Realisasi ≥ 5 **dan** ≥ 3 × max(FTK, 1).
5. Parsing jenjang jabatan dengan pola `NAMA (KODE) - ANGKA`.
6. Validasi mapping organisasi: konsistensi atribut per ID, keunikan nama.
7. Resolusi hierarki. Karena `Parent Organisasi` dicatat sebagai **nama** (bukan ID), parent diresolusi dengan aturan: *nama sama* **dan** *level parent = level anak − 1*; fallback nama saja bila kandidat tunggal.
8. Agregasi sementara per organisasi (jabatan langsung, tanpa roll-up) hanya untuk memahami skala unit — **bukan** feature final.

## 3. Hasil

### 3.1 Struktur dataset

| Karakteristik | Nilai |
|---|---:|
| Baris (jabatan) | 1.157 |
| Kolom | 10 (sesuai dataset minimum PRD §13.1) |
| Organisasi (ID unik) | 379 |
| Nama organisasi unik | 373 |
| Level organisasi | 6 (level 3–8) |
| Jenjang (label unik) | 21 (+ kosong) |
| Periode | **1** (`2026-09-25`) |
| Total FTK | 930 |
| Total Realisasi | 761 |
| Fulfillment agregat | 81,8 % |

Organisasi per level: L3 = 1, L4 = 19, L5 = 90, L6 = 164, L7 = 65, L8 = 40.

### 3.2 Kelengkapan dan validitas

| Pemeriksaan | Hasil |
|---|---|
| Missing `Jenjang Jabatan` | 34 baris (2,9 %) |
| Missing `Nama Jabatan` | 1 baris |
| Missing kolom lain | 0 |
| Duplikat (baris penuh / kunci / nama jabatan per org) | 0 / 0 / 0 |
| `ID Jabatan` unik global | Ya |
| FTK < 0 atau Realisasi < 0 | 0 |
| Satu ID org → >1 nama/parent/level | 0 |

### 3.3 Distribusi FTK dan Realisasi (level jabatan)

| Kondisi | Jabatan |
|---|---:|
| FTK = 0 | 354 |
| — FTK = 0 & Realisasi = 0 | 311 |
| — FTK = 0 & Realisasi > 0 | 43 |
| FTK > 0 & Realisasi = 0 (jabatan kosong) | 313 |
| Realisasi = FTK | 688 |
| Realisasi < FTK | 326 |
| Realisasi > FTK | 143 |

FTK per jabatan bernilai 0–4 (Q1 = 0, Q3 = 1); Realisasi 0–29. Distribusi sangat diskret dan menumpuk pada 0–1 (Gambar 1).

Nilai ekstrem (aturan domain), 3 jabatan:

| Organisasi | Jabatan | FTK | Realisasi |
|---|---|---:|---:|
| ORG-0258 Bidang LBP Distribusi, Retail dan Niaga | Officer Legal | 2 | **29** |
| ORG-0001 Direktorat Legal dan MHC | Senior Specialist HCM | 2 | 8 |
| ORG-0259 Bidang LBP Keuangan dan MHC | Officer Legal | 1 | 7 |

### 3.4 Skala unit organisasi (jabatan langsung)

| Statistik | Jabatan/org | FTK/org | Realisasi/org |
|---|---:|---:|---:|
| Median | 3 | 2 | 2 |
| Rata-rata | 3,05 | 2,45 | 2,01 |
| Maks | 18 | 14 | 39 |

- 198 dari 379 organisasi (52 %) memiliki FTK ≤ 2; 33 organisasi hanya punya 1 jabatan.
- 23 organisasi ber-FTK total 0 (10 di antaranya tetap memiliki realisasi).
- Tanda gap: positif 139, nol 179, negatif 61.

### 3.5 Pola per level organisasi

| Level | Org | FTK | Realisasi | Fulfillment |
|---:|---:|---:|---:|---:|
| 3 | 1 | 2 | 8 | 400 % |
| 4 | 19 | 20 | 26 | 130 % |
| 5 | 90 | 163 | 175 | 107 % |
| 6 | 164 | 516 | 509 | 99 % |
| 7 | 65 | 151 | 35 | **23 %** |
| 8 | 40 | 78 | 8 | **10 %** |

**Temuan penting:** realisasi terkonsentrasi di level 3–6, sedangkan level 7–8 hampir kosong. Contoh: ORG-0258 mempunyai 39 realisasi atas FTK 14, sementara 16 sub-unitnya (level 7) hanya terisi 17 dari FTK 29. Pola ini konsisten dengan dua penjelasan yang **belum dapat dibedakan dari data**: (a) understaffing nyata pada unit terbawah, atau (b) pegawai tercatat pada unit induk (pool/penempatan belum di-breakdown).

### 3.6 Jenjang jabatan

Kode jenjang: G3 = 341, G2 = 269, MD = 197, SPC = 181, MM = 53, SSP = 48, MA = 8, MAK = 2, G1 = 1; label non-standar `AM` = 12 dan `VP` = 11; kosong = 34 (Gambar 5).

- 35 nama jabatan berakhiran `*)`; 31 di antaranya tanpa jenjang, total FTK 17, total realisasi 0.
- Jabatan tanpa jenjang terkonsentrasi di 15 organisasi (ORG-0105 s.d. ORG-0110, ORG-0256, ORG-0264–0266, ORG-0277, ORG-0296, ORG-0303–0305).

### 3.7 Hierarki

| Status resolusi parent | Org |
|---|---:|
| Tepat (nama + level) | 374 |
| Parent di luar dataset | 4 (1 root `PT PLN (PERSERO) KANTOR PUSAT` + 3 orphan: ORG-0375, ORG-0376, ORG-0379) |
| Level tidak konsisten | 1 (ORG-0256, level 6 dengan parent level 6) |
| Ambigu | 0 |

5 nama organisasi dipakai oleh >1 ID (total 11 ID):

- Tiga pasang berbeda level (ORG-0105 L5 vs ORG-0272 L6; ORG-0106 L5 vs ORG-0258 L6; ORG-0256 L6 vs ORG-0338 L7). Dua pasang pertama berada di bawah *Sub Direktorat Hukum dan Kebijakan* (struktur lama) vs *Divisi …* (struktur baru), mengindikasikan **koeksistensi struktur lama dan baru**. Unit-unit L5 lama tersebut sebagian besar berisi jabatan `*)` tanpa jenjang.
- *Bagian HCBP Strategi UIT Jawa Bagian Timur dan Bali* muncul 3× (ORG-0194/0195/0196) dengan parent berbeda, dua di antaranya *Sub Bidang HCBP Kantor Pusat 1/2* — kemungkinan kesalahan penamaan (nama unit tersalin).
- *Sub Bidang Legal* (ORG-0305/0308) berada di bawah dua parent berbeda pada level yang sama — tampak wajar.

### 3.8 Gambar

| No | File | Isi |
|---|---|---|
| 1 | `figures/01_dist_position_ftk_realization.png` | Distribusi FTK & realisasi per jabatan |
| 2 | `figures/02_dist_org_ftk_realization_gap.png` | Distribusi FTK, realisasi, gap per organisasi |
| 3 | `figures/03_scatter_org_ftk_vs_realization.png` | FTK vs realisasi per organisasi (jitter) |
| 4 | `figures/04_positions_per_org_and_levels.png` | Jabatan per organisasi & organisasi per level |
| 5 | `figures/05_grade_distribution.png` | Distribusi jenjang |

## 4. Interpretasi untuk desain penelitian

1. **Tidak ada dimensi temporal** → label *Workforce Volatility* tidak dapat digunakan (PRD §82, §90). Penelitian diposisikan sebagai **segmentasi cross-sectional**.
2. **Unit kecil dan diskret** → rasio (fulfillment, staffing ratio) akan mengambil sedikit nilai unik, sehingga jarak Euclidean berpotensi menghasilkan cluster yang mencerminkan "grid" nilai diskret, bukan pola substantif. Ini alasan kuat untuk menguji (a) roll-up hierarki dan/atau (b) feature rasio yang terbatas (*bounded*).
3. **FTK = 0 dengan realisasi > 0** → formula PRD §8–9 tidak terdefinisi; dibutuhkan treatment eksplisit.
4. **Heterogenitas level** → level 7–8 berperilaku sangat berbeda dari level 3–6. Ada risiko clustering hanya "menemukan ulang" level organisasi. Perlu dicek di EDA dan dilaporkan.
5. **Outlier kuat** (ORG-0258) → mendukung eksperimen RobustScaler (PRD §24) dan relevan untuk analisis noise DBSCAN.

## 5. Ancaman validitas (draft untuk bagian *Limitations*)

- *Construct validity*: realisasi mungkin tercatat pada unit induk, bukan unit penempatan aktual.
- *Internal validity*: koeksistensi struktur lama/baru dapat menggandakan unit.
- *External validity*: satu direktorat, satu snapshot.
- *Statistical conclusion validity*: nilai sangat diskret dan unit kecil.

## 6. Keputusan data yang menunggu validasi

Dicatat di `decision_log.md` (D-001 s.d. D-008). Tahap 2 (Preprocessing) tidak dijalankan sebelum keputusan ini dikonfirmasi.
