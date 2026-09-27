# Eksperimen 01b — Dataset Adequacy Assessment

| Item | Nilai |
|---|---|
| ID tahap | `S01b-DA` |
| Tanggal | 2026-09-25 |
| Dataset | `DLMHC-2026-09-25-v1` — **SUPERSEDED oleh v2, lihat `01c_dataset_v2.md`** |
| Script | `ml/pipeline/s01b_dataset_adequacy.py` |
| Output | `ml/outputs/01b_dataset_adequacy/DLMHC-2026-09-25-v1/` |
| Status | SELESAI |
| Bagian jurnal | *Methods → Data adequacy*, *Limitations*, *Future work* |

> Pertanyaan: **apakah dataset cukup** untuk (a) menyelesaikan PRD 1.0 dan (b) menjadi dasar publikasi jurnal?
>
> *Update S02:* angka feature set C_grade diperbarui setelah revisi mapping jenjang AM → GENERALIS (D-004). Selisihnya kecil: vektor unik 107 → 105, Hopkins dedup 0,881 → 0,886.
>
> Feature di tahap ini **provisional**: dibuat hanya untuk mengukur kecukupan data, memakai asumsi sementara D-002, D-003, dan D-004 (VP→MM, AM→MD — kemudian direvisi menjadi AM→GENERALIS di S02). Feature final ditetapkan di Tahap 3.

---

## 1. Metode

1. **Cakupan field**: dataset dibandingkan dengan kebutuhan field PRD §13.1 (minimum), §15 (ideal), §89 (tambahan).
2. **Kecukupan ukuran sampel** terhadap jumlah feature *d*:
   - aturan minimum *n ≥ 2^d* (Formann, 1984);
   - rekomendasi segmentasi berbasis data *n ≥ 70·d* (Dolnicar, Grün, Leisch & Schmidt, 2014).
3. **Keragaman informasi**: jumlah vektor feature unik, porsi organisasi yang vektornya identik dengan organisasi lain, dan ukuran kelompok identik terbesar.
4. **Redundansi**: rank matriks feature dan pasangan korelasi |r| ≥ 0,9.
5. **Clustering tendency**: Hopkins statistic, 50 run, sampel 10 %. Nilai ≈ 0,5 berarti acak; > 0,75 berarti kecenderungan cluster kuat. Karena data diskret, banyak titik identik dengan jarak tetangga = 0, yang **menggelembungkan** nilai Hopkins. Karena itu dihitung juga Hopkins pada vektor unik saja. Sebagai kontrol sanity, data uniform acak berukuran sama menghasilkan H = 0,502.
6. Dua definisi unit dibandingkan: **direct** (jabatan yang tercatat langsung pada organisasi) dan **roll-up** (organisasi + seluruh sub-unit), terkait D-001.

Feature set provisional (mengacu PRD §80):

| Set | Feature |
|---|---|
| A_core | ftk, realization, gap, balance_index |
| A_core_nonredundant | ftk, realization, balance_index |
| B_structure | A_nonredundant + position_count, vacant_position_count, avg_realization_per_position |
| C_grade | B + pct_MAK, pct_MA, pct_MM, pct_MD, pct_SPESIALIS, pct_GENERALIS, pct_UNKNOWN |
| R_ratio_only | balance_index, vacant_share, avg_realization_per_position |

## 2. Hasil

### 2.1 Cakupan field PRD

| Field | Kebutuhan PRD | Status |
|---|---|---|
| ID/Nama/Level Organisasi | Wajib | ✅ Ada, lengkap |
| Parent Organisasi | Disarankan | ⚠️ Ada, tetapi berupa **nama** (374/379 dapat diresolusi tepat) |
| ID Jabatan, FTK, Realisasi | Wajib | ✅ Ada, lengkap |
| Nama Jabatan | Wajib | ⚠️ 1 kosong |
| Jenjang Jabatan | Wajib | ⚠️ 34 kosong, 2 label non-standar |
| Periode Data | Sangat disarankan | ⚠️ Ada, tetapi **hanya 1 periode** |
| Data historis multi-periode | Sangat direkomendasikan | ❌ Tidak ada |
| Status jabatan / status pegawai | Ideal | ❌ Tidak ada |
| Jenis organisasi / kategori jabatan | Opsional | ❌ Tidak ada |

**Semua field wajib tersedia.** Field ideal dan historis tidak tersedia.

### 2.2 Ukuran sampel vs jumlah feature (unit direct, n = 379)

| Feature set | d | n ≥ 2^d | n ≥ 70·d | n/d |
|---|---:|:---:|:---:|---:|
| A_core | 4 | ✅ (16) | ✅ (280) | 94,8 |
| A_core_nonredundant | 3 | ✅ (8) | ✅ (210) | 126,3 |
| B_structure | 6 | ✅ (64) | ❌ (420) | 63,2 |
| C_grade | 13 | ❌ (8.192) | ❌ (910) | 29,2 |
| R_ratio_only | 3 | ✅ (8) | ✅ (210) | 126,3 |

n = 379 sudah memenuhi batas minimum PRD §78 (n ≥ ±30), tetapi **belum memenuhi rekomendasi 70·d untuk feature set B dan C**.

### 2.3 Keragaman informasi — temuan paling penting

| Unit | Feature set | Vektor unik | Org dengan vektor kembar | Kelompok kembar terbesar |
|---|---|---:|---:|---:|
| direct | A_core | **38** | 97,6 % | 67 |
| direct | B_structure | 66 | 93,1 % | 61 |
| direct | C_grade | 105 | 84,7 % | 32 |
| direct | R_ratio_only | 52 | 94,5 % | 99 |
| roll-up | A_core | 97 | 85,8 % | 54 |
| roll-up | B_structure | 140 | 74,9 % | 35 |
| roll-up | C_grade | 169 | 68,9 % | 22 |

Jumlah nilai berbeda per feature (direct): FTK 9, realisasi 10, gap 12, balance_index 22, fulfillment 21, jumlah jabatan 8, jabatan kosong 7.

Hanya **8 kombinasi (FTK, Realisasi) mencakup 65,4 % organisasi**:

| FTK | Realisasi | Organisasi |
|---:|---:|---:|
| 1 | 1 | 67 |
| 3 | 3 | 48 |
| 2 | 2 | 29 |
| 1 | 0 | 25 |
| 2 | 0 | 24 |
| 4 | 4 | 21 |
| 4 | 3 | 19 |
| 3 | 4 | 15 |

**Interpretasi.** Meskipun n = 379, pada feature inti (A_core) data sebenarnya hanya berisi **38 titik berbeda** dalam ruang feature. Akibatnya:

- risiko cluster **trivial**, yaitu hanya memisahkan "FTK = Realisasi", "Realisasi = 0", dan "Realisasi > FTK", hal yang sudah terlihat dari tanda gap tanpa ML;
- DBSCAN sensitif terhadap tumpukan titik identik (satu titik dengan 67 duplikat otomatis menjadi *core point*);
- dendrogram hierarchical memiliki banyak *ties* pada jarak 0.

Menambahkan feature struktur dan jenjang (set C) atau memakai roll-up menaikkan keragaman menjadi 105–169 vektor unik, tetapi set C melanggar aturan 70·d.

### 2.4 Redundansi

- A_core memiliki rank < d karena `gap = ftk − realization` merupakan kombinasi linear tepat (PRD §79). **Gap tidak boleh masuk model bersama FTK dan realisasi sekaligus.**
- Unit direct: tidak ada pasangan feature dengan |r| ≥ 0,9.
- Unit roll-up: FTK–realisasi r = 0,98, FTK–jumlah jabatan r ≈ 1,0. Ini karena unit induk memuat seluruh sub-unit, sehingga korelasi didominasi oleh ukuran unit, dan observasinya saling tumpang tindih (tidak independen).

### 2.5 Clustering tendency (Hopkins, StandardScaler, 50 run)

| Feature set | Direct, semua titik | Direct, vektor unik | Roll-up, vektor unik |
|---|---:|---:|---:|
| A_core | 0,992 | 0,862 | 0,962 |
| A_core_nonredundant | 0,989 | 0,829 | 0,970 |
| B_structure | 0,983 | 0,864 | 0,962 |
| C_grade | 0,976 | 0,886 | 0,936 |
| R_ratio_only | 0,980 | 0,806 | 0,827 |
| *Baseline uniform acak* | *0,502* | | |

- Nilai 0,98–0,99 pada "semua titik" **terinflasi oleh duplikat** dan tidak boleh dilaporkan sendirian.
- Setelah deduplikasi nilainya tetap 0,81–0,89 (direct), di atas ambang 0,75. Jadi **data memiliki kecukupan struktur untuk clustering**, bukan data acak.
- RobustScaler memberi nilai hampir identik dengan StandardScaler (selisih ≤ 0,01), lihat `feature_set_adequacy.csv`.

Gambar: `figures/01_hopkins_by_feature_set.png`.

## 3. Verdict

### 3.1 Untuk PRD 1.0 → **CUKUP (bersyarat)**

PRD 1.0 berada pada **Kondisi A — Hanya Satu Periode** (PRD §90).

| Kebutuhan PRD | Terpenuhi? |
|---|---|
| Semua field wajib §13.1 | ✅ |
| Semua feature §6 dapat dihitung | ✅ (fulfillment/staffing ratio tak terdefinisi untuk 23 org ber-FTK 0 → D-003) |
| n ≥ ±30 (§78) | ✅ 379 |
| K-Means, Hierarchical, DBSCAN dapat dijalankan | ✅ |
| Semua acceptance criteria §94 | ✅ dapat dicapai (volatility tidak termasuk acceptance criteria) |
| Filter periode (§61) | ⚠️ tersedia tetapi hanya 1 nilai |
| Filter organisasi, jenjang, level, parent | ✅ |
| Label "Workforce Volatility" (§16) | ❌ tidak dapat (D-008) |

Syaratnya: keputusan D-001 s.d. D-009 disetujui.

### 3.2 Untuk publikasi jurnal → **CUKUP untuk studi kasus, LEMAH untuk klaim generalisasi**

Kekuatan:

- data riil organisasi, lengkap pada field wajib, tanpa duplikat dan tanpa nilai invalid;
- clustering tendency terbukti (Hopkins dedup > 0,75);
- n memenuhi aturan 70·d untuk feature set kecil (A, R).

Kelemahan yang kemungkinan besar dipersoalkan reviewer:

1. **Keragaman efektif rendah**: 38 vektor unik pada feature inti; 65 % org berada di 8 kombinasi.
2. **Satu direktorat, satu snapshot** → generalisasi dan stabilitas temporal tidak dapat diuji.
3. **Validitas konstruk realisasi**: pegawai kemungkinan tercatat di unit induk (D-001).
4. Feature set lengkap (C) melampaui rasio sampel/feature yang direkomendasikan.

## 4. Rekomendasi

### 4.1 Data tambahan (diurutkan dari dampak terbesar)

| Prioritas | Data | Dampak |
|---|---|---|
| 1 | **Snapshot multi-periode** dengan format sama (idealnya ≥ 12 bulan) | Membuka feature volatility (PRD §16), uji stabilitas cluster antar-waktu, memperbesar n menjadi org × periode |
| 2 | **Direktorat lain** dengan format sama | Memperbesar n dan keragaman; menguji apakah segmen konsisten lintas direktorat (generalisasi) |
| 3 | **Unit penempatan aktual pegawai** (atau konfirmasi pencatatan di unit induk) | Menyelesaikan D-001; memperkuat validitas konstruk |
| 4 | **Status jabatan** (aktif / transisi / dihapus) dan arti penanda `*)` | Menyelesaikan D-005; memisahkan struktur lama dan baru |
| 5 | **ID parent** (bukan nama) | Menghilangkan resolusi hierarki berbasis nama |

### 4.2 Mitigasi bila data tambahan tidak tersedia

Mitigasi ini akan dimasukkan ke desain Tahap 3–6:

1. Gap tidak dipakai bersama FTK dan realisasi dalam satu model (redundansi linear).
2. Feature set utama dibatasi agar memenuhi 70·d (d ≤ 5); set C diuji sebagai eksperimen pembanding, dengan keterbatasan dilaporkan eksplisit.
3. Titik duplikat ditangani secara eksplisit: eksperimen pembanding memakai clustering pada vektor unik dengan `sample_weight` (didukung K-Means dan DBSCAN di scikit-learn), lalu label dipetakan kembali ke semua organisasi.
4. Analisis sensitivitas direct vs roll-up (D-001).
5. Uji stabilitas bootstrap (ARI) sesuai protokol §6.
6. **Baseline non-ML untuk riset saja**: pengelompokan sederhana berdasarkan tanda gap dibandingkan dengan hasil clustering, untuk menjawab "apakah ML menemukan sesuatu di luar tanda gap?". Baseline ini **tidak** dipakai di dashboard (PRD §41, §47).
7. Hopkins selalu dilaporkan dalam dua versi (semua titik dan vektor unik).
