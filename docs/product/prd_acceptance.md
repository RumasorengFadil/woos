# PRD 1.0 — Acceptance Criteria (§94) & Bukti

Status per 2026-09-27. Setiap butir menunjuk ke bukti yang dapat diperiksa, sesuai aturan "never represent planned functionality as implemented".

| # | Kriteria PRD §94 | Status | Bukti |
|---:|---|:---:|---|
| 1 | Dataset FTK dan Realisasi telah dipahami | ✅ | `docs/research/01_data_understanding.md`, `01b_dataset_adequacy.md`, `01c_dataset_v2.md` |
| 2 | Data preprocessing tersedia | ✅ | `ml/pipeline/s02_preprocessing.py`; `docs/research/02_preprocessing.md` |
| 3 | Feature engineering terdokumentasi | ✅ | `s03_feature_engineering.py`, `feature_schema.json`; `docs/research/03_feature_engineering.md` |
| 4 | Semua feature utama telah dievaluasi | ✅ | EDA korelasi/VIF/ε² (`04_eda.md` §3, §6); revisi F2 (D-020) |
| 5 | EDA tersedia | ✅ | `s04_eda.py`, 15 figure; `docs/research/04_eda.md` |
| 6 | K-Means telah diuji | ✅ | 84 run (`experiments.json`, `woos.experiment`) |
| 7 | Hierarchical Clustering telah diuji | ✅ | 252 run (ward/complete/average) |
| 8 | DBSCAN telah diuji | ✅ | 283 run |
| 9 | Elbow Method tersedia | ✅ | Figure E01; chart Elbow di Model Comparison |
| 10 | Dendrogram tersedia | ✅ | Figure E04; ditampilkan di Model Comparison |
| 11 | DBSCAN noise analysis tersedia | ✅ | `05_experiments.md` §4 (noise vs outlier); E06; tabel & PCA noise (X merah) di dashboard |
| 12 | Silhouette Score tersedia | ✅ | Setiap run + dashboard |
| 13 | Davies-Bouldin Index tersedia | ✅ | Setiap run + dashboard |
| 14 | Model comparison tersedia | ✅ | `06_evaluation.md`; `v_model_comparison`; halaman Model Comparison |
| 15 | Model final tervalidasi | ✅ | EXP-KM-067 `APPROVED` (D-030, `approval.json`) |
| 16 | Setiap cluster memiliki profil | ✅ | `cluster_profile_stats.csv`, `woos.cluster_profile` |
| 17 | Setiap cluster memiliki interpretasi bisnis | ✅ | `07_cluster_interpretation.md`; label & interpretasi disetujui user |
| 18 | Model result disimpan | ✅ | PostgreSQL `woos` (`cluster_result`, `model`, `experiment`, …); artefak `model_artifacts/` |
| 19 | Dashboard membaca hasil model yang sama | ✅ | View `v_validated_*`; test "summary = hasil pipeline" |
| 20 | Dashboard tidak menggunakan rule clustering independen | ✅ | Audit statis otomatis di `tests/php/run.php` |
| 21 | Summary FTK tersedia | ✅ | Overview |
| 22 | Summary Realisasi tersedia | ✅ | Overview |
| 23 | Summary Gap tersedia | ✅ | Overview |
| 24 | Fulfillment Ratio tersedia | ✅ | Overview, list, detail |
| 25 | Visualisasi cluster tersedia | ✅ | PCA 2D small multiples (Overview, Comparison) |
| 26 | Perbandingan model tersedia | ✅ | Model Comparison |
| 27 | Cluster profile tersedia | ✅ | Cluster Analysis |
| 28 | Organization list tersedia | ✅ | Organisasi (search/sort/pagination/filter) |
| 29 | Organization detail tersedia | ✅ | Organization Detail + penjelasan PRD §85 |
| 30 | Filter tersedia jika field terkait ada | ✅ | Periode, direktorat, level, cluster, jenjang (+ cari, atipikal) |

## Di luar cakupan PRD 1.0 / keterbatasan yang diketahui

- **Workforce Volatility** tidak tersedia karena data hanya 1 periode (PRD §82, §90; D-008). Filter periode sudah siap untuk data multi-periode.
- Retraining terjadwal dan upload dataset lewat web belum tersedia (PRD §75: manual untuk prototype).
- Out of scope PRD §3.2 tidak dikerjakan.
