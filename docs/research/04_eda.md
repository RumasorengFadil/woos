# Eksperimen 04 — Exploratory Data Analysis

| Item | Nilai |
|---|---|
| ID tahap | `S04-EDA` |
| Tanggal | 2026-09-25 |
| Dataset / feature version | `KP-2026-09-25-v2` / `F1` (+ kandidat `F2`) |
| Script | `ml/pipeline/s04_eda.py` (gaya figure: `viz_style.py`) |
| Output | `ml/outputs/04_eda/KP-2026-09-25-v2/` — 15 figure + 15 tabel CSV + `eda_summary.json` |
| Test | `tests/ml/test_s04_eda.py` (5 test; total suite 28) |
| Status | **SELESAI — menunggu validasi usulan D-020…D-024** |
| Bagian jurnal | *Results → Data characteristics*; *Methods → justifikasi feature set & scaler* |

> Sesuai PRD §25, EDA **tidak** dipakai untuk menentukan cluster secara manual. Tujuannya memahami struktur data dan memutuskan desain eksperimen Tahap 5 berdasarkan bukti.
>
> Unit: *direct*, populasi model n = 1.280 organisasi.

## 1. Visualisasi minimum PRD §25

| PRD §25 | Figure | Temuan utama |
|---|---|---|
| Distribusi FTK | F01 | Median 3, maks 34, **skew 5,42** |
| Distribusi Realisasi | F01 | Median 3, maks 19, skew 1,04 |
| Distribusi Gap | F01, F03 | Median 0, rentang −8…34, skew 6,92; gap positif 379, nol 583, negatif 318 org |
| Distribusi Fulfillment | F01 | n = 1.228 (FTK > 0); median 1,00; rentang 0–6; skew 1,95 |
| Distribusi Staffing ratio | F01 | Identik fulfillment − 1 (bentuk distribusi sama) |
| FTK vs Realisasi | F02 | 83 kombinasi unik; 8 kombinasi terbanyak mencakup **60,9 %** org. 45,6 % tepat di diagonal (R = F), 29,6 % di bawah, 24,8 % di atas. Spearman 0,65 |
| Gap per organisasi | F03 | Gap terbesar di Direktorat Keuangan: 3 *Bidang Verifikasi* (gap 29–34; FTK 30–34, realisasi 0–1) dan *Bidang Pembayaran Terpusat 2* (25). Σ gap per direktorat: DLMHC +214; Direktorat Utama −60 |
| Korelasi feature | F04 | 4 pasangan \|ρ\| ≥ 0,7 (lihat §3) |
| Distribusi jenjang | F05 | GENERALIS 58,6 %, MD 24,7 %, MM 9,1 %, SPESIALIS 4,8 %, MA 2,1 %, UNKNOWN 0,6 %, MAK 0,1 % dari jabatan aktif; komposisi per direktorat relatif mirip |
| Missing value | F06 | Data mentah: jenjang 42, nama jabatan 5. Feature: fulfillment & staffing NULL pada 73 org (seluruhnya karena FTK = 0, D-003). **Input model tanpa NaN** |
| Outlier | F07 | Lihat §5 |

## 2. Clustering tendency (F13)

| Set F1 | Hopkins, semua titik | Hopkins, vektor unik (direct) | Hopkins, vektor unik (rollup) |
|---|---:|---:|---:|
| A | 0,994 | 0,829 | 0,975 |
| B | 0,990 | 0,905 | 0,988 |
| C | 0,985 | 0,914 | 0,974 |
| R | 0,988 | 0,862 | 0,909 |

Semua set di atas ambang 0,75, sehingga clustering layak dilakukan. Titik kembar tetap dominan (F12): pada set A, 98 % org berbagi vektor dan kelompok identik terbesar berisi 278 org; pada set C, 87,7 % org berbagi vektor dan kelompok terbesar 198 org.

## 3. Redundansi & multikolinearitas (F04, F15)

Korelasi Spearman |ρ| ≥ 0,7:

| Pasangan | ρ | Keterangan |
|---|---:|---|
| vacant_position_count – vacant_share | 0,97 | tidak pernah dalam set yang sama |
| realization – avg_realization_per_position | 0,85 | avg = realization / position_count |
| ftk – position_count | 0,80 | ukuran unit |
| balance_index – avg_realization_per_position | 0,75 | |

**VIF maksimum** (StandardScaler):

| Set | F1 (mentah) | F1 log1p | **F2 (usulan, mentah)** | F2 log1p |
|---|---:|---:|---:|---:|
| A | 2,3 | 9,8 | 2,3 | 9,8 |
| B | **11,3** (realization) | 34,8 | **3,9** | 11,1 |
| C | **75,9** (pct_MM) | 78,4 | **4,9** | 11,7 |
| R | 3,0 | 3,3 | 3,0 | 3,3 |

Temuan:

1. **Set C F1 multikolinear berat.** Pembuangan `pct_UNKNOWN` (D-018) tidak cukup, karena UNKNOWN hanya 0,6 % sehingga lima proporsi yang tersisa hampir selalu berjumlah 1 (rata-rata 0,996). Solusi: jadikan GENERALIS kategori referensi (dibuang dari input), dengan hasil VIF ≤ 4,9.
2. **Set B F1:** `avg_realization_per_position` ≈ realization / position_count. Mengeluarkannya dari input model menurunkan VIF dari 11,3 menjadi 3,9. Nilainya tetap dipakai untuk tampilan dan profil cluster (PRD §11).
3. Hopkins set F2 tetap tinggi: B 0,893; C 0,918.

## 4. Transformasi & scaling (F10, F11)

**Skewness** feature hitungan, dari mentah menjadi log1p: ftk 5,42 → −0,16; vacant_position_count 3,09 → 0,86; avg_realization 1,83 → −0,28; realization 1,04 → −0,32; position_count 1,05 → −0,30.

**Dilema log1p:** log1p menormalkan distribusi, tetapi hubungan rasio (avg = R/P, balance_index ≈ fungsi dari log R − log F) menjadi hampir linear di ruang log. Akibatnya VIF naik menjadi 10–35 (tabel §3). Karena itu log1p **tidak** dipakai di grid utama dan hanya dicatat sebagai alternatif yang dipertimbangkan (D-021).

**StandardScaler vs RobustScaler pada set C** (`scaler_comparison_setC.csv`): kedua scaler **mengubah bobot relatif feature**, bukan hanya meredam outlier.

| Feature | Rentang Robust / Rentang Standard |
|---|---:|
| balance_index | **2,76×** (IQR hanya 0,14) |
| avg_realization_per_position | 2,14× |
| pct_SPESIALIS, pct_MA_MAK | 0,15–0,16× (IQR = 0, tidak ter-skala) |
| position_count | 0,54× |

Artinya RobustScaler praktis membuat model didominasi oleh `balance_index` dan mengecilkan feature jenjang. Hal ini dicatat sebagai interpretasi perbandingan scaler di Tahap 6 (D-022).

## 5. Outlier (F07)

- Univariat |z| > 3: pct_SPESIALIS 74 org, pct_MA_MAK 27, avg_realization 18, vacant_position_count 15, ftk 8, position_count 8, realization 7. Tidak ada pada balance_index, vacant_share, pct_MM, pct_MD, pct_GENERALIS.
- Multivariat (Mahalanobis², set B, χ² 0,999 = 22,46): **27 organisasi**. Teratas:

| Organisasi | Direktorat | FTK | Realisasi | Pola |
|---|---|---:|---:|---|
| Bidang Verifikasi UID & UIW-1 | Keuangan | 34 | 0 | formasi besar, hampir kosong |
| Bidang Verifikasi UIP, UIT, Penunjang | Keuangan | 34 | 1 | idem |
| Direktorat Legal dan MHC (unit direktorat) | DLMHC | 2 | 8 | *pool* Senior Specialist tanpa formasi |
| Bidang Verifikasi UID | Keuangan | 30 | 1 | formasi besar, hampir kosong |
| Bidang LBP Distribusi, Retail dan Niaga | DLMHC | 14 | 7 | 11 dari 13 jabatan kosong |

Pola outlier bersifat **substantif** (unit baru yang belum terisi dan *pool* tingkat direktorat), bukan kesalahan data. Karena itu outlier dipertahankan (D-006, D-024) dan menjadi objek analisis noise DBSCAN (PRD §35).

## 6. Kontrol artefak: level & direktorat (F08, F09)

Effect size Kruskal–Wallis ε² (0 = tanpa efek):

| Feature | ε² level | ε² direktorat |
|---|---:|---:|
| pct_MA_MAK | **0,544** | 0,011 |
| pct_GENERALIS | **0,502** | 0,030 |
| pct_MM | **0,379** | 0,021 |
| pct_MD | **0,331** | 0,007 |
| position_count | 0,306 | 0,017 |
| ftk | 0,305 | 0,041 |
| realization | 0,207 | 0,104 |
| pct_SPESIALIS | 0,154 | 0,041 |
| avg_realization_per_position | 0,093 | **0,153** |
| vacant_position_count | 0,086 | 0,072 |
| vacant_share | 0,085 | 0,093 |
| balance_index | **0,055** | 0,064 |

Temuan:

1. **Komposisi jenjang hampir sepenuhnya ditentukan level organisasi.** Unit bidang (L5) dipimpin VP (MM), unit terbawah didominasi Generalis. Clustering dengan set C berisiko besar hanya merekonstruksi level. PCA set C (F09) memperlihatkan L3–L4 menempati wilayah terpisah.
2. Feature ukuran (ftk, position_count) berasosiasi sedang dengan level.
3. **Feature kondisi staffing** (balance_index, vacant_share) hampir bebas dari level maupun direktorat. Feature inilah yang paling mewakili "kondisi workforce" menurut PRD §1.
4. Tidak ada feature yang didominasi direktorat (ε² ≤ 0,15). Segmentasi tidak akan sekadar mencerminkan direktorat.

PCA (visual saja): dua komponen pertama set B menjelaskan 82,5 % varians; set C 54,3 %.

## 7. Sub-analisis DLMHC vs direktorat lain (F14)

| Feature | Mean DLMHC | Mean lainnya | Rank-biserial | p (Mann–Whitney) |
|---|---:|---:|---:|---:|
| balance_index | −0,21 | 0,00 | 0,24 | < 0,001 |
| vacant_share | 0,37 | 0,16 | −0,32 | < 0,001 |
| avg_realization_per_position | 0,83 | 1,29 | 0,39 | < 0,001 |
| position_count | 2,30 | 2,41 | 0,09 | 0,007 |

DLMHC lebih *understaffed* dengan efek kecil-sedang. Ini konsisten dengan fulfillment agregat DLMHC sebesar 77 % dibanding 87–110 % di direktorat lain.

## 8. Implikasi untuk desain Tahap 5 (usulan)

| Usulan | Isi | Bukti |
|---|---|---|
| D-020 | Feature set **F2**: B tanpa avg_realization_per_position; C memakai GENERALIS sebagai referensi. A & R tetap | §3 |
| D-021 | log1p **tidak** dipakai di grid utama | §4 |
| D-022 | StandardScaler = utama; RobustScaler = pembanding, diinterpretasikan sebagai perubahan bobot | §4 |
| D-023 | Kontrol artefak wajib di Tahap 6: Cramér's V cluster × level dan cluster × direktorat untuk setiap model | §6 |
| D-024 | Outlier dipertahankan; uji pengaruhnya pada K-Means (dengan/tanpa 27 outlier multivariat) sebagai robustness | §5 |
