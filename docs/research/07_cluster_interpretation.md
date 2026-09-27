# Eksperimen 07 — Interpretasi Cluster, Profiling & Validasi

| Item | Nilai |
|---|---|
| ID tahap | `S07-INT` |
| Tanggal | 2026-09-25 |
| Model | **EXP-KM-067**: K-Means, K = 5, feature set R (`balance_index`, `vacant_share`, `avg_realization_per_position`), StandardScaler, seed 42 |
| Script | `ml/pipeline/s07_interpretation.py` |
| Output | `ml/outputs/07_interpretation/KP-2026-09-25-v2/` (+ `model_artifacts/`) |
| Test | `tests/ml/test_s07_interpretation.py` (5 test; total suite 47) |
| Status | **SELESAI — menunggu validasi bisnis (D-030)**; `validation_status = PENDING_BUSINESS_VALIDATION` |
| Bagian jurnal | *Results → Cluster profiles*; *Discussion → implikasi manajerial* |

Alur PRD §41/§83: **Cluster → Profiling → Domain Validation → Business Label**. Label di dokumen ini masih **usulan** dan diberikan per `cluster_id` setelah membaca profil. Label bukan aturan klasifikasi. Script memverifikasi "tanda tangan" profil setiap cluster, sehingga label tidak tertukar bila model dijalankan ulang (test `test_signatures_detect_swapped_cluster_ids`).

## 1. Reproduksibilitas

- Refit (seed 42, `n_init` 20) **identik 100 %** dengan label EXP-KM-067 di registri Tahap 5 (ARI = 1,000).
- Artefak PRD §73 (`model_artifacts/`): `model.joblib`, `scaler.joblib`, `feature_schema.json`, `metrics.json`, `cluster_profile.json`.

## 2. Profil cluster (populasi model n = 1.280)

| ID | Label usulan | Arketipe PRD §40 | n (%) | FTK | Realisasi | Gap | Fulfillment | Jabatan kosong | Pegawai / jabatan |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | **Terisi Tanpa Formasi** | Potensi overstaffing (struktural) | 59 (4,6 %) | 0,15 | 2,97 | −2,81 | —¹ | 0 % | 1,57 |
| 1 | **Understaffing Parsial** | Understaffing | 388 (30,3 %) | 3,55 | 3,09 | +0,46 | 87,5 % | 37 % | 1,00 |
| 2 | **Relatif Stabil** | Relatif stabil | 537 (42,0 %) | 2,14 | 2,29 | −0,15 | 107,1 % | 0,1 % | 1,13 |
| 3 | **Understaffing Kritis (Belum Terisi)** | Understaffing | 141 (11,0 %) | 3,59 | 0,27 | +3,32 | 5,5 % | 94 % | 0,06 |
| 4 | **Potensi Overstaffing** | Potensi overstaffing | 155 (12,1 %) | 4,83 | 6,24 | −1,41 | 145,4 % | 5,7 % | 2,47 |

Nilai adalah rata-rata cluster. ¹ 50 dari 59 org ber-FTK 0, sehingga fulfillment tidak terdefinisi (D-003). Rata-rata 366,7 % hanya dihitung dari 9 org.

Statistik lengkap (mean/median/min/max/std) untuk 17 feature ada di `cluster_profile_stats.csv`. Heatmap profil relatif ada di P01.

**Karakteristik otomatis** (z-relatif terhadap populasi, |z| ≥ 0,5):

| ID | Karakteristik |
|---:|---|
| 0 | Fulfillment tinggi (+5,0 SD) · jabatan terisi tanpa formasi tinggi (+3,4) · keseimbangan R-F tinggi (+2,5) · gap rendah (−1,3) |
| 1 | Jumlah jabatan tinggi (+0,6) · jabatan kosong tinggi (+0,6) |
| 2 | Porsi jabatan kosong rendah (−0,7) · jabatan kosong rendah (−0,7) |
| 3 | Porsi jabatan kosong tinggi (+2,3) · keseimbangan R-F rendah (−2,2) · jabatan kosong tinggi (+1,8) · fulfillment rendah (−1,7) |
| 4 | Pegawai per jabatan tinggi (+1,8) · realisasi tinggi (+1,6) · fulfillment tinggi (+0,9) · FTK tinggi (+0,8) |

Cluster 1 dan 2 berbeda "halus" dari rata-rata populasi (|z| ≤ 0,7), karena keduanya adalah mayoritas (72 %). Perbedaan utamanya adalah porsi jabatan kosong: 37 % vs 0 %.

## 3. Organisasi representatif (terdekat ke centroid)

| ID | Contoh | FTK / R | Catatan |
|---:|---|---|---|
| 0 | Sub Bidang Verifikasi Pusat Penunjang 2; Bagian Pembayaran UID 1 (Keuangan) | 0 / 3 | 5 contoh teratas semuanya unit verifikasi/pembayaran Keuangan |
| 1 | Bagian HCBP Layanan UID Aceh (DLMHC); Sub Bidang Operasi Pembangkitan IPP Sulawesi (Pembangkitan) | 4 / 3 | 1 dari 3 jabatan kosong |
| 2 | Sub Bidang Kesekretariatan Dewan Komisaris (Utama); Bidang Pengamanan Pendapatan (Retail) | 5 / 5; 1 / 1 | seimbang |
| 3 | Sub Bidang Kontrak Sumut, Sumsel, Sulawesi Selatan (DLMHC) | 1 / 0 | unit legal regional belum terisi |
| 4 | Sub Bidang Aneka Energi IPP, Bio Energi, Energi Hidro (MP-EBT) | 5 / 7 | ±2,3 pegawai per jabatan |

Daftar lengkap: `representative_organizations.csv`. Penjelasan per organisasi, yaitu nilai organisasi vs rata-rata cluster (PRD §85), ada di `organization_results.csv` (kolom `cluster_avg_*`).

## 4. Anggota atipikal & outlier

- **45 anggota atipikal** (jarak ke centroid > P95 cluster masing-masing): C0 3, C1 20, C2 13, C3 1, C4 8. Semuanya diberi flag `is_atypical_member`.
- **Temuan penting:** unit tingkat direktorat (L3) dengan *pool* Senior Specialist tanpa/minim formasi masuk C4 atau C0 dengan jarak sangat jauh. Contohnya ORG-0005 Direktorat Legal dan MHC (FTK 2, R 8; jarak 7,8) dan ORG-0007 Direktorat MP-EBT (FTK 0, R 6). Pola ini berbeda dari unit operasional biasa → **pertanyaan validasi V3**.
- ORG-0646 (Bidang LBP Distribusi, Retail dan Niaga; FTK 14, R 7, 85 % jabatan kosong) masuk C3 sebagai anggota atipikal. Unit ini berada di perbatasan antara understaffing kritis dan parsial.
- 27 outlier multivariat EDA tersebar di C4 (13), C3 (11), C0 (2), dan C1 (1). K-Means tidak memiliki noise, sehingga outlier terserap ke cluster terdekat. Flag atipikal menjadi mekanisme untuk menandainya.
- **21 organisasi tidak tersegmentasi** (tanpa jabatan aktif, D-017). Di `organization_results.csv` mereka berlabel `NOT_SEGMENTED`.

## 5. Distribusi (P02, P05)

**Per direktorat** (% organisasi; `cluster_by_directorate.csv`):
- **DLMHC:** Understaffing Kritis 23,5 % dan Understaffing Parsial 37,4 %, dibanding direktorat lain 6,0 % dan 27,5 %. Konsisten dengan fulfillment agregat 77 % (S04 §7).
- **Direktorat Utama:** Potensi Overstaffing 31 % (79 org), tertinggi dari semua direktorat.
- **Keuangan:** Terisi Tanpa Formasi 25 % (37 org), yaitu unit verifikasi/pembayaran dengan jabatan tanpa formasi.
- Retail dan Niaga: Understaffing Kritis 24 %.

**Per level:** Understaffing Kritis meningkat di level bawah; di L8, 33 dari 82 org (40 %) masuk cluster ini. Cramér's V cluster × level = 0,27, jadi asosiasinya lemah–sedang dan segmen tidak sekadar mencerminkan level.

## 6. Interpretasi manajerial (draft *Discussion*)

1. 42 % unit berada pada kondisi **seimbang** dan tidak memerlukan intervensi formasi.
2. **Kekurangan pegawai muncul dalam dua bentuk berbeda** yang menuntut respons berbeda:
   - parsial (30 %): pengisian jabatan tertentu;
   - kritis/belum terisi (11 %): pembentukan/pengisian unit, sering unit baru atau regional.
   Analisis gap tunggal tidak membedakan keduanya.
3. **Kelebihan pegawai juga muncul dalam dua bentuk:**
   - kelebihan di atas formasi (12 %; banyak di Direktorat Utama);
   - pegawai pada jabatan tanpa formasi (5 %; terkonsentrasi di Keuangan).
   Bentuk kedua adalah isu **penataan formasi**, bukan jumlah pegawai.
4. Label *Workforce Volatility* tidak digunakan (data 1 periode, D-008).

## 7. Validasi bisnis (PRD §45) — pertanyaan untuk pakar domain

| No | Pertanyaan | Opsi |
|---|---|---|
| V1 | Apakah kelima label usulan tepat untuk konteks HC PLN? | Setuju / ubah nama label tertentu |
| V2 | Apakah label "Relatif Stabil" dapat dipakai, mengingat hanya berbasis 1 snapshot? Alternatif: "Seimbang (Terpenuhi)" | Pilih salah satu |
| V3 | Unit tingkat direktorat dengan *pool* Senior Specialist (mis. ORG-0005, ORG-0007) masuk "Potensi Overstaffing" / "Terisi Tanpa Formasi". Apakah wajar, atau perlu ditandai khusus di dashboard? | Wajar / tandai sebagai atipikal (sudah ada flag) |
| V4 | Apakah contoh organisasi representatif di §3 sesuai pengetahuan lapangan? | Ya / sebutkan yang janggal |
| V5 | Apakah "Terisi Tanpa Formasi" di Keuangan (unit verifikasi/pembayaran) sesuai kondisi sebenarnya? Misalnya formasi belum ditetapkan atau data belum diperbarui | Ya / catatan |

Setelah V1–V5 dijawab, status model menjadi `APPROVED` (D-030) dan hasilnya dipublish di Tahap 8.

## 8. Figure

| Figure | Isi |
|---|---|
| P01 | Heatmap z-relatif profil cluster |
| P02 | Ukuran cluster & komposisi per direktorat |
| P03 | Distribusi fulfillment, porsi kosong, pegawai/jabatan, gap per cluster |
| P04 | PCA 2D set R per cluster (visual saja) |
| P05 | Komposisi cluster per level |
