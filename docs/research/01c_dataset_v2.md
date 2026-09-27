# Eksperimen 01c — Dataset v2: Data Understanding, Adequacy & Rekonsiliasi

| Item | Nilai |
|---|---|
| ID tahap | `S01c-V2` |
| Tanggal | 2026-09-25 |
| Dataset aktif | `KP-2026-09-25-v2` (SHA-256 `29b39045…1f82`) menggantikan `DLMHC-2026-09-25-v1` |
| Script | `s01_data_understanding.py --dataset=v2`, `s01b_dataset_adequacy.py --dataset=v2`, `s01c_version_reconciliation.py` |
| Output | `ml/outputs/01_data_understanding/KP-2026-09-25-v2/`, `ml/outputs/01b_dataset_adequacy/KP-2026-09-25-v2/`, `ml/outputs/01c_version_reconciliation/` |
| Status | SELESAI |
| Bagian jurnal | *Methods → Data*, *Data adequacy*; *Limitations* |

Latar: S01b merekomendasikan data dari direktorat lain untuk memperbesar n dan keragaman (prioritas 2). User menyediakan dataset seluruh Direktorat Kantor Pusat. Metode identik dengan S01 dan S01b; script yang sama dijalankan pada v2.

---

## 1. Struktur v2

| Karakteristik | v1 (DLMHC) | **v2 (Kantor Pusat)** |
|---|---:|---:|
| Jabatan | 1.157 | **3.528** |
| Organisasi dengan jabatan | 379 | **1.301** |
| Direktorat (level 3) | 1 | 10 + Direktorat Utama (wadah, tanpa baris jabatan) |
| Level organisasi | 3–8 | 2–8 |
| Kolom | 10 | 11 (**+ ID Parent**) |
| Periode | 1 | 1 (`2026-09-25`) |
| Total FTK / Realisasi | 930 / 761 | 3.791 / 3.607 |
| Fulfillment agregat | 81,8 % | 95,1 % |

Kualitas dasar: 0 duplikat, 0 nilai negatif, 1 ID organisasi = 1 set atribut, ID jabatan unik global. Jenjang kosong 42 (1,2 %), nama jabatan kosong 5, 71 sel teks mengandung tab/spasi ganda.

### 1.1 Hierarki

Kolom ID Parent tersedia. Hasilnya: **1.292/1.301 parent valid**, tanpa ketidakcocokan nama dan tanpa lompatan level. 9 parent tidak ada di dataset:

- ORG-0001 *PT PLN (Persero)* adalah root di luar cakupan (wajar).
- **4 ID** (ORG-0013 *Direktorat Utama*, ORG-0226, ORG-1072, ORG-1074) persis sama dengan 4 celah pada urutan ID ORG-0002…ORG-1306. Interpretasinya: keempatnya **unit wadah tanpa jabatan**, sehingga tidak muncul di file berbasis jabatan. Treatment: D-014.

### 1.2 Pola per level

| Level | Org | FTK | Realisasi | Fulfillment |
|---:|---:|---:|---:|---:|
| 2 | 1 | 0 | 1 | — |
| 3 | 10 | 5 | 44 | 880 % |
| 4 | 77 | 100 | 120 | 120 % |
| 5 | 284 | 535 | 414 | 77 % |
| 6 | 625 | 2.072 | 2.082 | 100 % |
| 7 | 221 | 871 | 782 | 90 % |
| 8 | 83 | 208 | 164 | 79 % |

Pola "unit terbawah hampir kosong" di v1 (L7 = 23 %, L8 = 10 %) **tidak muncul** pada v2 secara keseluruhan. Ini melemahkan hipotesis bahwa pencatatan menumpuk di unit induk (D-001). Level 3 tetap anomali: jabatan *Senior Specialist <Direktorat>* ber-FTK 0 tetapi terisi 5–8 orang.

### 1.3 Edge case jabatan

| Kondisi | Jabatan |
|---|---:|
| FTK = 0 & Realisasi = 0 | 486 |
| FTK = 0 & Realisasi > 0 | 172 (Direktorat Keuangan saja 78) |
| FTK > 0 & Realisasi = 0 | 763 |
| Realisasi > FTK | 605 |
| Nilai ekstrem (≥ 5 dan ≥ 3× max(FTK, 1)) | 13, maksimum 9 orang |
| Nama jabatan bertanda `*)` | 42 (35 di DLMHC) |
| Label jenjang baru `JUNIOR EXPERT (JE) - 15` | 8 |

## 2. Rekonsiliasi v1 vs v2

Pencocokan menggunakan `ID Jabatan`, yang stabil antar-versi.

| Hasil | Nilai |
|---|---|
| Jabatan v1 yang ada di v2 | 1.157 / 1.157 |
| Perbedaan nama org/parent/level/jabatan/jenjang/FTK/periode | 0 |
| **Perbedaan realisasi** | **23 jabatan, semuanya turun** (22 × −1, 1 × −23) |
| Total realisasi jabatan yang sama | 761 → 716 (−45) |
| ID organisasi | Dinomori ulang (pemetaan 1:1) |

Kasus terbesar: *Officer Legal* pada *Bidang LBP Distribusi, Retail dan Niaga* turun dari 29 menjadi 6. Outlier terkuat v1 (D-006) dengan demikian **hilang di v2**. Perubahan lainnya adalah jabatan manajerial yang realisasinya 1 → 0.

**Interpretasi:** v2 konsisten sebagai ekstraksi yang lebih baru atau sudah dikoreksi, dengan tanggal periode yang sama. Karena itu v2 dipakai sebagai satu-satunya dataset aktif (D-011). Rincian: `ml/outputs/01c_version_reconciliation/changed_positions.csv`.

> Catatan untuk jurnal: perbedaan dua ekstraksi pada tanggal periode yang sama adalah bukti bahwa *snapshot* HRIS dapat berubah retroaktif. Hal ini dicatat sebagai ancaman validitas (*measurement reliability*).

## 3. Adequacy v2 (metode identik S01b)

| Feature set | d | 70·d | v1 memenuhi? | **v2 memenuhi?** | Vektor unik v1 → v2 | Hopkins dedup v1 → v2 |
|---|---:|---:|:---:|:---:|---:|---:|
| A_core | 4 | 280 | ✅ | ✅ | 38 → 84 | 0,862 → 0,872 |
| A_core_nonredundant | 3 | 210 | ✅ | ✅ | 38 → 84 | 0,829 → 0,828 |
| B_structure | 6 | 420 | ❌ | **✅** | 66 → 192 | 0,864 → 0,904 |
| C_grade | 13 | 910 | ❌ | **✅** | 105 → 288 | 0,886 → 0,930 |
| R_ratio_only | 3 | 210 | ✅ | ✅ | 52 → 163 | 0,806 → 0,859 |

(Unit direct. Hopkins data acak = 0,50. Nilai v1 C_grade sudah memakai mapping jenjang revisi D-004.)

- **Semua feature set kini memenuhi aturan 70·d** (Dolnicar et al., 2014).
- Keragaman vektor naik 2,2–2,9 kali, dan clustering tendency tetap kuat (0,83–0,93).
- **Titik kembar tetap dominan:** 87–98 % organisasi berbagi vektor dengan organisasi lain; kelompok identik terbesar berisi 278 org pada A_core. Mitigasi D-009 tetap berlaku.
- Per direktorat, n berkisar 47–379. Clustering per direktorat **tidak memadai** untuk d ≥ 1 bila mengikuti 70·d pada direktorat terkecil. Karena itu clustering dilakukan pada populasi gabungan, lalu distribusi cluster dibandingkan antar-direktorat.

## 4. Verdict v2

| Tujuan | v1 | **v2** |
|---|---|---|
| PRD 1.0 | Cukup bersyarat | **Cukup** |
| Jurnal | Cukup untuk studi kasus, lemah untuk generalisasi | **Cukup untuk studi kasus multi-direktorat.** Keterbatasan yang tersisa: satu snapshot, satu perusahaan, titik kembar |

Rekomendasi data yang masih terbuka: **multi-periode** (prioritas 1), status jabatan, dan arti tanda `*)`.
