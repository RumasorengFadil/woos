# Research Protocol

Protokol ini ditulis **sebelum** modeling agar desain penelitian tidak disesuaikan setelah melihat hasil (menghindari *HARKing*). Perubahan protokol dicatat di `decision_log.md`.

## 1. Judul kerja

*Segmentasi Organisasi Berbasis Formasi dan Realisasi Tenaga Kerja: Studi Komparatif K-Means, Agglomerative Hierarchical Clustering, dan DBSCAN pada Direktorat Legal dan Manajemen Human Capital*

## 2. Latar masalah

Analisis FTK saat ini berbasis angka tunggal (FTK, realisasi, gap) per unit. Belum ada pendekatan yang secara otomatis mengelompokkan unit organisasi dengan karakteristik workforce serupa tanpa label yang ditentukan sebelumnya (PRD §1).

## 3. Pertanyaan penelitian

- **RQ1.** Apakah unit organisasi dapat dikelompokkan menjadi segmen yang terpisah secara statistik berdasarkan feature FTK, realisasi, struktur jabatan, dan komposisi jenjang?
- **RQ2.** Metode mana (K-Means, Hierarchical, DBSCAN) yang menghasilkan segmentasi paling valid dan dapat diinterpretasikan pada data workforce yang kecil, diskret, dan hierarkis?
- **RQ3.** Bagaimana pengaruh pilihan feature set (PRD §80) dan scaler (Standard vs Robust) terhadap kualitas dan stabilitas cluster?
- **RQ4.** Apa karakteristik bisnis masing-masing segmen, dan unit mana yang menjadi outlier/noise?
- **RQ5.** *(ditambahkan S01c, D-012)* Apakah komposisi segmen berbeda antar-direktorat, dan apakah segmen bukan sekadar cerminan direktorat atau level organisasi?

## 4. Desain

- Jenis: studi kasus kuantitatif, *unsupervised learning*, cross-sectional (1 snapshot).
- Kerangka proses: CRISP-DM (Business Understanding → Data Understanding → Data Preparation → Modeling → Evaluation → Deployment), dipetakan ke tahap PRD §20.
- Unit analisis: organisasi pada periode tertentu (PRD §17); lihat D-001.
- Populasi: 1.301 organisasi PT PLN (Persero) Kantor Pusat (11 direktorat termasuk Direktorat Utama), dataset `KP-2026-09-25-v2` (D-011, D-012). Sub-analisis: Direktorat Legal dan MHC (379 org).

## 5. Rencana tahapan

| Tahap | ID | Output riset |
|---|---|---|
| 1 Data Understanding | S01 | Profil data, isu kualitas |
| 1b Dataset Adequacy | S01b | Kecukupan data untuk PRD & jurnal |
| 1c Dataset v2 | S01c | Data understanding, adequacy & rekonsiliasi dataset Kantor Pusat |
| 2 Preprocessing | S02 | Dataset bersih + log transformasi |
| 3 Feature Engineering | S03 | Feature dataset (direct + rollup), kamus feature, feature set A/B/C/R, scaler |
| 4 EDA | S04 | Distribusi, korelasi, VIF, outlier, skewness, scaler, kontrol artefak level/direktorat, sub-analisis DLMHC |
| 5 Eksperimen model | S05 | 619 run: K-Means, Hierarchical (ward/complete/average), DBSCAN × feature set F2 (A/B/C/R) × scaler (Standard/Robust) + varian vektor unik |
| 6 Evaluasi & perbandingan | S06 | Kelayakan (D-027), 6 kriteria + agregasi peringkat (D-028), sensitivitas bobot, robustness, diagnostik rule-equivalence (D-029, post-hoc) |
| 7 Interpretasi & validasi | S07 | Profil cluster, label bisnis, validasi domain |
| 8 Publish hasil | S08 | Model result dataset (DB) |
| 9 Dashboard | S09 | Website (bukan bagian eksperimen, tetapi bukti deployment) |

## 6. Rencana evaluasi (ditetapkan di muka)

- **Internal validity:** Silhouette (↑), Davies–Bouldin (↓), Calinski–Harabasz (↑, pelengkap).
- **Stabilitas:** bootstrap resampling (mis. 100 iterasi) → Adjusted Rand Index antar-run; variasi seed untuk K-Means.
- **Balance:** proporsi cluster terkecil; entropi distribusi cluster.
- **DBSCAN:** % noise, jumlah cluster; metrik internal dihitung hanya pada non-noise dan dilaporkan bersama % noise.
- **Interpretability:** profil mean/median/std per feature per cluster; validasi domain oleh pakar HC.
- **Kontrol artefak:** uji apakah cluster hanya merefleksikan level organisasi atau direktorat (asosiasi cluster × level dan cluster × direktorat, mis. Cramér's V). *(S04: proporsi jenjang berasosiasi kuat dengan level, ε² 0,33–0,54 → wajib, D-023)*
- Pemilihan model memakai kombinasi kriteria PRD §38, bukan satu metrik (rincian: D-027, D-028).
- *(Amandemen post-hoc S06, D-029 usulan)* **Rule-equivalence check:** ARI segmentasi terhadap aturan satu feature (kutub balance_index); run dengan ARI ≥ 0,90 dianggap setara rule-based.
- *(Tambahan D-010)* **Clustering tendency:** Hopkins statistic pada semua titik dan pada vektor unik (hasil S01b: 0,81–0,88 pada vektor unik → layak di-cluster).
- *(Tambahan D-010, update S03)* **Rasio sampel/feature:** n ≥ 70·d. Dengan n = 1.280 berarti d ≤ 18; semua set F1 memenuhi.
- *(Tambahan D-010)* **Baseline non-ML (riset saja):** pengelompokan berdasarkan tanda gap (−/0/+), dibandingkan dengan hasil clustering (ARI) untuk mengukur nilai tambah ML.

## 7. Reproducibility

- Dataset aktif `KP-2026-09-25-v2` (SHA-256 `29b39045…1f82`); v1 `DLMHC-2026-09-25-v1` disimpan sebagai SUPERSEDED.
- `RANDOM_SEED = 42` (`ml/pipeline/config.py`).
- Dependensi terkunci di `ml/requirements.txt` (Python 3.9.6, scikit-learn 1.5.2, pandas 2.2.3, numpy 1.26.4, pytest 8.3.3).
- Unit test pipeline: `ml/.venv/bin/python -m pytest tests/ml`.
- Setiap eksperimen memiliki ID (`EXP-KM-xxx`, `EXP-HC-xxx`, `EXP-DB-xxx`) dan metadata (PRD §44, §71).
- Semua angka di dokumen riset berasal dari file output pipeline, bukan dihitung manual.
- **Code version:** repository git (commit awal `20086f4`, 2026-09-27). Registri eksperimen juga mencatat SHA-256 script (`code_version`, mis. `c4adf2d5834d` untuk `s05_experiments.py`). Untuk reproduksi: checkout commit → `pip install -r ml/requirements.txt` → jalankan pipeline sesuai `docs/deployment/installation.md`.

## 8. Etika & privasi

Dataset hanya berisi agregat jabatan (tanpa nama pegawai/NIP). Nama unit organisasi dapat dianonimkan pada naskah jurnal bila diwajibkan instansi (keputusan menunggu — lihat `journal_outline.md` §Catatan).
