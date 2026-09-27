# Eksperimen 06 — Evaluasi, Perbandingan & Pemilihan Model

| Item | Nilai |
|---|---|
| ID tahap | `S06-EVAL` |
| Tanggal | 2026-09-25 |
| Dataset / feature / model version | `KP-2026-09-25-v2` / `F2` / `v1` |
| Script | `ml/pipeline/s06_evaluation.py` |
| Output | `ml/outputs/06_evaluation/KP-2026-09-25-v2/` |
| Test | `tests/ml/test_s06_evaluation.py` (7 test; total suite 42) |
| Status | **SELESAI — menunggu keputusan D-029 (pilihan kandidat untuk validasi bisnis)** |
| Bagian jurnal | *Methods → Model selection*; *Results → Model comparison*; *Discussion* |

## 1. Prosedur (ditetapkan sebelum peringkat dilihat)

1. **Kelayakan (D-027).** Varian `all`; 2–8 cluster; cluster terbesar < 95 %; cluster terkecil ≥ 2 %; noise ≤ 15 %; silhouette < 0,99.
2. **Enam kriteria (D-028).**
   - Silhouette ↑ dan Davies–Bouldin ↓.
   - **Stabilitas**: rata-rata ARI dari 50 subsample 80 % yang di-refit.
   - **Keseimbangan**: entropi ukuran cluster.
   - **Relevansi workforce**: rata-rata η² `balance_index` & `vacant_share`.
   - **Kontrol artefak**: Cramér's V × level ↓.
3. **Agregasi.** Rata-rata peringkat dengan bobot sama. Sensitivitasnya diuji pada 9 varian bobot.
4. **Pelaporan tambahan.**
   - Cramér's V × direktorat.
   - ARI terhadap baseline tanda gap (−/0/+).
   - Robustness model terbaik tiap algoritma: seed, rollup, tanpa 27 outlier, varian vektor unik.

## 2. Kelayakan (V01)

| Alasan penolakan | Run |
|---|---:|
| Varian `unique` (sensitivitas saja) | 207 |
| Cluster terkecil < 2 % | 144 |
| Jumlah cluster di luar 2–8 | 75 |
| Degenerate (cluster terbesar ≥ 95 %) | 45 |
| Noise > 15 % | 5 |
| **Layak** | **143** (DBSCAN 73, Hierarchical 38, K-Means 32) |

## 3. Hasil pemilihan menurut aturan pra-registrasi D-028

**Tabel perbandingan PRD §55: model terbaik per algoritma**

| Metric | K-Means | Hierarchical | DBSCAN |
|---|---:|---:|---:|
| Experiment | EXP-KM-067 | EXP-HC-044 | **EXP-DB-067** |
| Konfigurasi | set R / standard / K = 5 | set A / robust / ward, K = 3 | set A / robust / eps 1,046, min_samples 40 |
| Silhouette | 0,564 | 0,716 | **0,771** |
| Davies–Bouldin | 0,676 | 0,284 | **0,222** |
| Cluster Count | 5 | 3 | 3 |
| Noise | 0 % | 0 % | 4,8 % |
| Stabilitas (ARI) | 0,998 ± 0,003 | 1,000 ± 0,000 | 0,998 ± 0,004 |
| Keseimbangan (entropi) | **0,849** | 0,426 | 0,427 |
| Cluster terbesar | **42 %** | 87 % | 83 % |
| Workforce η² | **0,903** | 0,720 | 0,775 |
| Cramér's V level | 0,272 | 0,319 | 0,262 |
| Cramér's V direktorat | 0,278 | 0,333 | 0,280 |
| ARI vs tanda gap | 0,273 | 0,103 | 0,137 |
| Peringkat keseluruhan (dari 143) | 9 | 18 | **1** |
| Validation | EXPERIMENT | EXPERIMENT | **SELECTED_CANDIDATE (D-028)** |

- Semua model terbaik **stabil** (ARI ≥ 0,998).
- **Tidak mencerminkan level atau direktorat**: Cramér's V 0,26–0,33, asosiasi lemah–sedang, sehingga kekhawatiran D-023 tidak terbukti untuk model-model ini.
- **Tidak mereplikasi tanda gap**: ARI 0,10–0,27. Silhouette baseline tanda gap hanya 0,12–0,32, di bawah semua model terbaik.
- **Sensitivitas bobot:** model teratas tetap dari keluarga DBSCAN set A/robust (DB-067 atau DB-066, yang praktis identik) pada 8 dari 9 varian. K-Means EXP-KM-067 menjadi teratas bila DBI dikeluarkan.

## 4. Diagnostik post-hoc: pemenang kuantitatif = aturan satu feature

Profil cluster memperlihatkan bahwa DB-067 dan HC-044 hanya memisahkan dua kutub `balance_index`:

| DB-067 | n | Median FTK | Median realisasi | Median balance_index | Pola |
|---|---:|---:|---:|---:|---|
| Cluster 2 | 108 | 2 | 0 | −1 | kosong total |
| Cluster 0 | 51 | 0 | 3 | +1 | terisi tanpa formasi |
| Cluster 1 | 1.060 (83 %) | 3 | 3 | 0 | semua lainnya |
| Noise | 61 | 3 | 1 | −0,5 | terisi sebagian |

**Uji:** ARI terhadap aturan satu feature "`balance_index` = −1 / = +1 / lainnya":

| Model | ARI (tanpa noise) |
|---|---:|
| DBSCAN EXP-DB-067 | **1,000** (identik) |
| Hierarchical EXP-HC-044 | 0,987 |
| K-Means EXP-KM-067 | 0,208 |

Sebanyak **49 dari 143 run layak** (46 DBSCAN, 3 Hierarchical) memiliki ARI ≥ 0,90 terhadap aturan tersebut.

**Interpretasi:**
- Silhouette dan DBI yang sangat baik pada run-run ini berasal dari dua kutub diskret `balance_index` (±1), yang terpisah jauh dari massa organisasi di sekitar 0.
- Segmentasi tersebut **tidak memberi informasi di luar ambang satu feature**, sehingga setara dengan klasifikasi rule-based. PRD §41 dan §47 secara eksplisit menyatakan pendekatan ini bukan tujuan sistem.
- Temuan ini tidak tertangkap oleh keenam kriteria D-028.

**Pemeringkatan ulang setelah run trivial dikeluarkan** (`eligible_runs_nontrivial_posthoc.csv`; usulan D-029):

| # | Run | Konfigurasi | Silhouette | DBI | Stabilitas | Entropi | Workforce η² | Skor |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | **EXP-KM-067** | K-Means, set R, standard, K = 5 | 0,564 | 0,676 | 0,998 | 0,849 | 0,903 | **23,7** |
| 2 | EXP-KM-069 | K-Means, set R, standard, K = 7 | 0,601 | 0,654 | 0,981 | 0,855 | 0,933 | 26,0 |
| 3 | EXP-DB-059 | DBSCAN, set A, robust, eps 0,587, ms 20 | 0,566 | 0,469 | 0,957 | 0,726 | 0,894 | 27,2 |
| 4 | EXP-DB-220 | DBSCAN, set R, standard, eps 0,489, ms 10 | 0,510 | 0,623 | 0,994 | 0,697 | 0,939 | 27,3 |

Hierarchical terbaik setelah pemeringkatan ulang: EXP-HC-195 (ward, set R, K = 7; skor 31,2).

## 5. Profil ringkas kandidat EXP-KM-067

Label bisnis belum diberikan; itu dilakukan di Tahap 7 (PRD §41).

| Cluster | n | % | Median FTK | Median realisasi | Median balance | Median vacant_share | Median jabatan | % gap > 0 | % gap < 0 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 59 | 4,6 | 0 | 3 | +1,00 | 0 | 2 | 0 | 100 |
| 1 | 388 | 30,3 | 4 | 3 | 0,00 | 0,33 | 3 | 49 | 16 |
| 2 | 537 | 42,0 | 1 | 1 | 0,00 | 0 | 1 | 6 | 18 |
| 3 | 141 | 11,0 | 3 | 0 | −1,00 | 1,00 | 2 | 100 | 0 |
| 4 | 155 | 12,1 | 5 | 6 | +0,11 | 0 | 3 | 11 | 66 |

K-Means memecah cluster "lainnya" (83 %) milik DB-067 menjadi tiga segmen yang berbeda secara substantif:
- cluster 1: kekosongan parsial;
- cluster 2: unit kecil yang seimbang;
- cluster 4: unit lebih besar dengan realisasi melebihi formasi.

Crosstab DB-067 × KM-067 ada di `selected_labels.csv`.

## 6. Robustness model terbaik

| Uji | K-Means KM-067 | Hierarchical HC-044 | DBSCAN DB-067 |
|---|---:|---:|---:|
| Stabilitas seed (10 seed, ARI min) | 1,000 | — | — |
| Rollup vs direct (ARI, 1.280 org) | 0,500 | 0,062 | 0,586 |
| Tanpa 27 outlier multivariat (ARI) | 0,845 | 1,000 | 1,000 |
| Varian vektor unik (ARI) | 0,464 (EXP-KM-074) | — | — |

- **Rollup** (D-001): segmentasi berubah cukup besar (ARI 0,50–0,59). Hasil segmentasi bergantung pada definisi unit (jabatan langsung vs sub-tree), sehingga harus dilaporkan sebagai keterbatasan. Unit *direct* tetap analisis utama.
- **Outlier:** K-Means cukup robust (0,845). Pada DBSCAN/HC, outlier sudah menjadi noise atau berada di cluster besar, sehingga tidak berpengaruh.
- **Titik kembar** (D-009/D-025): K-Means berubah cukup besar tanpa bobot duplikat (0,464). Kohesi cluster sebagian ditopang oleh banyaknya organisasi dengan profil identik; ini sifat data, bukan kesalahan model.
- Kesepakatan antar-model: DBSCAN–Hierarchical 0,82 (sama-sama pola kutub); K-Means–DBSCAN 0,27; K-Means–Hierarchical 0,21.

## 7. Kesimpulan untuk jurnal (draft)

1. Pada data workforce yang diskret dan kaya titik kembar, **kriteria internal klasik (Silhouette, DBI) secara sistematis memenangkan partisi yang setara dengan ambang satu feature**. Seleksi berbasis metrik saja, bahkan multi-kriteria dengan stabilitas, dapat berujung pada "ML yang mereplikasi rule".
2. Uji kesetaraan dengan aturan sederhana (ARI terhadap *rule baseline*) diusulkan sebagai langkah wajib dalam protokol pemilihan clustering workforce.
3. Setelah kontrol ini diterapkan, **K-Means (set rasio R, StandardScaler, K = 5)** memberikan segmentasi yang stabil (ARI 0,998), seimbang (cluster terbesar 42 %), paling relevan terhadap kondisi staffing (η² 0,90), dan tidak mencerminkan level/direktorat (V ≈ 0,27).

## 8. Figure & tabel

| Output | Isi |
|---|---|
| V01 | Funnel kelayakan |
| V02 | Silhouette vs stabilitas (143 run layak) |
| V03 | Peringkat per kriteria, 12 run teratas |
| V04 | Model terbaik per algoritma, 6 kriteria |
| V05 | PCA 2D model terpilih D-028 (visual saja) |
| `eligible_runs.csv` | 143 run + semua kriteria + peringkat |
| `eligible_runs_nontrivial_posthoc.csv` | 94 run setelah diagnostik D-029 |
| `model_comparison.csv` | Tabel PRD §55 |
| `rank_sensitivity.csv`, `robustness.json`, `baseline.csv`, `finalist_cluster_profiles.csv`, `selected_labels.csv` | detail |
