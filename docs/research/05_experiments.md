# Eksperimen 05 — K-Means, Hierarchical Clustering, DBSCAN

| Item | Nilai |
|---|---|
| ID tahap | `S05-EXP` |
| Tanggal | 2026-09-25 |
| Dataset / feature / model version | `KP-2026-09-25-v2` / `F2` / `v1` |
| Code version | `c4adf2d5834d` (SHA-256 12 karakter pertama dari `s05_experiments.py`) |
| Script | `ml/pipeline/s05_experiments.py` |
| Output | `ml/outputs/05_experiments/KP-2026-09-25-v2/` |
| Test | `tests/ml/test_s05_experiments.py` (6 test; total suite 35) |
| Status | **SELESAI — hasil eksperimen, belum ada pemilihan model** |
| Bagian jurnal | *Methods → Algorithms & hyperparameters*; *Results → Model experiments* |

> Tahap ini hanya **menjalankan dan mengukur**. Pemilihan model (PRD §38), stabilitas bootstrap, kontrol artefak level/direktorat (D-023), baseline non-ML (D-010), sensitivitas rollup (D-001), dan pengaruh outlier (D-024) dikerjakan di **Tahap 6**.

## 1. Desain eksperimen

Ketiga algoritma dijalankan pada dataset, feature set, dan scaler yang sama (PRD §26). Unit: *direct*, n = 1.280. Seed = 42.

| Faktor | Level |
|---|---|
| Feature set (F2, D-020) | A (3 feature), B (5), C (9), R (3) |
| Scaler (D-022) | StandardScaler (utama), RobustScaler (pembanding) |
| Varian data | `all` = seluruh organisasi; `unique` = vektor unik tanpa bobot, label dipetakan balik (D-025) — hanya StandardScaler |

| Algoritma | Grid | Catatan |
|---|---|---|
| K-Means (PRD §27–29) | K = 2…8; `n_init` = 20 | Elbow via *kneedle* |
| Agglomerative Hierarchical (PRD §30–32) | linkage ward / complete / average × K = 2…8 | scipy `linkage` + `fcluster(maxclust)`; satu pohon per konfigurasi; korelasi cophenetic |
| DBSCAN (PRD §33–36) | `min_samples` ∈ {5, 10, 20, 40}; `eps` = kuantil {0,50; 0,70; 0,80; 0,90; 0,95} dari k-distance positif + titik knee | Metrik internal dihitung tanpa noise |

Metrik per run:
- Silhouette (↑), Davies–Bouldin (↓), Calinski–Harabasz (↑);
- jumlah cluster, jumlah & % noise;
- ukuran setiap cluster, porsi cluster terkecil & terbesar, entropi ukuran ternormalisasi (1 = seimbang).

**Total 619 run:** K-Means 84, Hierarchical 252, DBSCAN 283. Rinciannya 412 run varian `all` dan 207 varian `unique`. Setiap run memiliki ID `EXP-KM/HC/DB-nnn` dan metadata PRD §44 (`experiments.json`). Label per organisasi per run tersimpan di `labels.csv.gz`.

## 2. Hasil K-Means (StandardScaler, varian `all`)

| Set | K | Silhouette | DBI | Cluster terkecil | Cluster terbesar |
|---|---:|---:|---:|---:|---:|
| A | 3 | 0,483 | 0,765 | 10,9 % | 51,3 % |
| A | 6 | 0,549 | 0,579 | 0,3 % | 41,2 % |
| B | 3 | 0,468 | 0,881 | 11,9 % | 53,8 % |
| B | 4 | 0,484 | 0,815 | 0,8 % | 54,1 % |
| C | 5 | 0,505 | 1,024 | 7,7 % | 56,8 % |
| C | 6 | 0,527 | 0,855 | 2,7 % | 56,8 % |
| R | 2 | 0,615 | 0,580 | 15,2 % | 84,8 % |
| R | 5 | 0,564 | 0,676 | 4,6 % | 42,0 % |

Tabel lengkap untuk K = 2…8 ada di `experiments.csv`.

- **Elbow** (E01): A = 5, B = 4, C = 5, R = 4 (StandardScaler); 3–4 (RobustScaler).
- Mulai K ≥ 4 pada set A/B, K-Means membentuk **cluster sangat kecil** (4–10 org, 0,3–0,8 %). Isinya organisasi ber-FTK sangat besar, yaitu tiga *Bidang Verifikasi* Keuangan dan satu *Bidang Pembayaran* (outlier S04 §5).
- **RobustScaler** menaikkan silhouette (A, K = 3: 0,708), tetapi dengan cluster dominan 83 %. Ini konsisten dengan S04 §4: `balance_index` mendominasi jarak, sehingga model terutama memisahkan "seimbang" vs "tidak seimbang".

## 3. Hasil Hierarchical

**Cophenetic correlation** (StandardScaler): average 0,89–0,92 > ward 0,52–0,79 ≈ complete 0,55–0,72. Dendrogram: E04.

| Linkage | Run degenerate (cluster terbesar ≥ 95 %) | Run dengan cluster < 1 % | Silhouette maks |
|---|---:|---:|---:|
| ward | 0 / 56 | 13 / 56 | 0,716 |
| complete | 11 / 56 | 51 / 56 | 0,840 |
| average | 29 / 56 | 56 / 56 | 0,840 |

- **Temuan utama:** silhouette tertinggi di seluruh eksperimen hierarchical (0,84) dicapai average/complete linkage dengan K = 2, yaitu **99,7 % org dalam satu cluster dan 4 org dalam cluster lain**. Dendrogram average memperlihatkan *chaining*: outlier dikupas satu per satu. Ini ilustrasi empiris PRD §38, bahwa silhouette tertinggi tidak otomatis menjadi model terbaik. Korelasi cophenetic yang tinggi pada average linkage juga mencerminkan struktur rantai ini, bukan segmentasi yang bermakna.
- **Ward** berperilaku paling mirip K-Means (pola silhouette vs K sejajar, E02) dan tidak pernah degenerate.

## 4. Hasil DBSCAN

- Dari 283 run: 188 varian `all`. Sebanyak 27 run menghasilkan hanya 1 cluster dan 32 run degenerate. Jumlah cluster bervariasi dari 1 sampai 44 (E06).
- **Artefak titik kembar:**
  - Pada eps kecil, misalnya EXP-DB-001 (set A, eps = 0,05, min_samples = 5), DBSCAN menghasilkan **38 cluster dengan silhouette = 1,000 dan DBI = 0**.
  - Setiap "cluster" hanyalah kelompok organisasi dengan vektor feature identik (kelompok kembar ≥ 5 org).
  - Silhouette sempurna ini artefak data diskret, bukan segmentasi (S04 §2, F12).
- Pada eps sedang dengan min_samples besar, DBSCAN konvergen ke pola **1 cluster besar + 1–3 cluster kecil + noise 2–10 %**. Contohnya EXP-DB-019 (A, eps 0,82, min_samples 40): 2 cluster, noise 6,9 %, silhouette 0,549.
- **Noise vs outlier multivariat S04** (27 org, Mahalanobis set B):
  - EXP-DB-083 (set B): noise 139 org, mencakup 25 dari 27 outlier;
  - EXP-DB-019 (set A): noise 88 org, mencakup 22 dari 27;
  - EXP-DB-279 (set R/robust): noise 92 org, mencakup 13 dari 27.

  Noise DBSCAN menangkap sebagian besar outlier ekstrem, tetapi juga memuat banyak organisasi di wilayah berkepadatan rendah. Noise tidak diperlakukan sebagai error (PRD §35); analisis anggotanya dilakukan di Tahap 6/7.

## 5. Varian `unique` (pengaruh titik kembar)

- Clustering pada vektor unik (83–281 titik) lalu label dipetakan balik. Rata-rata perbedaan silhouette `unique − all` pada 112 konfigurasi yang dapat dipasangkan: **−0,047** (K-Means −0,103, Hierarchical −0,028). DBSCAN tidak dipasangkan karena grid eps dihitung terpisah.
- Varian `unique` cenderung memisahkan outlier (misalnya K-Means set A, K = 2: 99,7 % / 0,3 %). Tanpa bobot, 4 profil ekstrem mendapat pengaruh relatif lebih besar terhadap centroid.
- **Interpretasi:** sebagian kohesi cluster pada varian `all` berasal dari tumpukan organisasi identik. Metrik internal harus dibaca dengan catatan ini (D-009).

## 6. Pratinjau deskriptif (bukan pemilihan model)

Dengan batas deskriptif cluster terkecil ≥ 5 %, cluster terbesar < 95 %, dan noise ≤ 10 %, **48 dari 412 run** varian `all` memenuhi syarat. Silhouette tertinggi per algoritma dalam kelompok ini:

| Algoritma | Run | Set / scaler | K / param | Silhouette | DBI | Terkecil / terbesar |
|---|---|---|---|---:|---:|---|
| K-Means | EXP-KM-016 | A / robust | K = 3 | 0,708 | 0,397 | 5,2 % / 83,4 % |
| HC ward | EXP-HC-043 | A / robust | K = 2 | 0,706 | 0,329 | 9,0 % / 91,0 % |
| HC complete | EXP-HC-050 | A / robust | K = 2 | 0,706 | 0,329 | 9,0 % / 91,0 % |
| DBSCAN | EXP-DB-279 | R / robust | eps 1,37, ms 40 | 0,733 | 0,199 | 9,0 % / 83,8 % (noise 7,2 %) |

Pola yang terlihat: konfigurasi dengan metrik tertinggi cenderung **segmentasi kasar 2–3 cluster dengan cluster dominan 83–91 %**. Segmentasi yang lebih terperinci (K = 4–6, StandardScaler) memiliki silhouette 0,46–0,55. Menimbang metrik, keseimbangan, stabilitas, dan interpretabilitas (PRD §38) adalah pekerjaan Tahap 6.

## 7. Figure

| Figure | Isi |
|---|---|
| E01 | Elbow K-Means per set (Standard & Robust) |
| E02 / E03 | Silhouette & DBI vs K: K-Means, HC ward/complete/average (Standard / Robust) |
| E04 | Dendrogram 3 linkage × 4 set (30 merge terakhir) + cophenetic r |
| E05 | Kurva k-distance DBSCAN per min_samples |
| E06 | DBSCAN: jumlah cluster vs % noise (garis mengikuti eps naik) |

## 8. Implikasi untuk Tahap 6

1. Pemilihan tidak boleh berbasis silhouette saja. Konfigurasi degenerate (cluster terbesar ≥ 95 %) dan silhouette DBSCAN = 1 karena duplikat harus dikeluarkan secara eksplisit.
2. Perlu kriteria keseimbangan minimum, uji stabilitas bootstrap (ARI), dan Cramér's V terhadap level/direktorat (D-023).
3. Perbandingan StandardScaler vs RobustScaler harus dibaca sebagai perbandingan pembobotan: Robust ≈ segmentasi berbasis `balance_index`.
4. Baseline tanda gap (−/0/+) diperlukan untuk menguji apakah segmentasi 2–3 cluster dengan metrik tertinggi sekadar mereplikasi tanda gap.
