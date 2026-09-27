# Journal Outline (IMRaD) — Peta Dokumen → Naskah

Dokumen ini memetakan setiap dokumen riset ke bagian naskah jurnal. Diperbarui setiap tahap selesai. Kolom **Status** menunjukkan apakah bahan untuk bagian tersebut sudah tersedia.

| Bagian naskah | Sumber bahan | Status |
|---|---|---|
| Abstract | Ringkasan S01c, S06, S07 | Siap disusun (seluruh bahan tersedia) |
| 1. Introduction — latar, gap, kontribusi | `00_research_protocol.md` §1–3, PRD §1–2 | Draft |
| 2. Related Work — clustering workforce/HR analytics, K-Means/HC/DBSCAN | Belum ada (butuh studi literatur) | Belum |
| 3.1 Methods — Data | `dataset_card.md`, `01_data_understanding.md` | **Tersedia** |
| 3.1b Methods — Data adequacy & clustering tendency | `01b_dataset_adequacy.md`, `01c_dataset_v2.md` §3 | **Tersedia** |
| 3.1c Methods — Versi data & rekonsiliasi | `01c_dataset_v2.md` §2 | **Tersedia** |
| 3.2 Methods — Preprocessing | `02_preprocessing.md` | **Tersedia** |
| 3.3 Methods — Feature engineering & scaling | `03_feature_engineering.md`, `04_eda.md` §3–§4 (justifikasi F2, scaler, log1p) | **Tersedia** |
| 3.4 Methods — Algoritma & hyperparameter | `05_experiments.md` §1, D-025, D-026 | **Tersedia** |
| 3.5 Methods — Evaluasi | `00_research_protocol.md` §6 | Draft |
| 4.1 Results — Karakteristik data (EDA) | `01c_dataset_v2.md` §1, `02_preprocessing.md` §2.2, `04_eda.md` §1–§7 | **Tersedia** |
| 4.2 Results — Eksperimen model | `05_experiments.md` §2–§6 | **Tersedia** |
| 4.3 Results — Perbandingan & pemilihan model | `06_evaluation.md` §2–§6 | **Tersedia** |
| 4.4 Results — Profil cluster | `07_cluster_interpretation.md` §2–§5 | **Tersedia** (label menunggu validasi) |
| 5. Discussion — implikasi manajerial, perbandingan metode | `06_evaluation.md` §7 (metodologis); `07_cluster_interpretation.md` §6 (manajerial) | **Draft** |
| 6. Limitations | `01_data_understanding.md` §5, `01b_dataset_adequacy.md` §3.2, `01c_dataset_v2.md` §2 (reliabilitas snapshot) & §4 | Draft |
| 7. Conclusion & future work | PRD §93, `01b_dataset_adequacy.md` §4.1 | Draft |
| 5b. Implementasi sistem (opsional, jurnal terapan/SI) | `docs/architecture/overview.md`, `docs/database/schema.md`, `docs/features/segmentation/README.md`, `docs/product/prd_acceptance.md` | **Tersedia** |
| Lampiran — reproducibility | `00_research_protocol.md` §7; registri eksperimen di DB `woos.experiment` (619 run) & `ml/outputs/05_experiments/`; `docs/deployment/installation.md` (pipeline end-to-end) | **Tersedia** |

## Kontribusi yang berpotensi diklaim (hipotesis awal, diverifikasi setelah S06)

1. Studi komparatif tiga metode clustering pada data workforce riil multi-direktorat (1.301 unit) yang diskret dan hierarkis.
2. Treatment eksplisit untuk FTK = 0 (rasio simetris terbatas `balance_index`) sebagai alternatif rasio fulfillment klasik, serta penanganan hubungan matematis antar-feature workforce (gap, staffing ratio, closure komposisi jenjang).
3. Analisis sensitivitas unit analisis (direct vs roll-up hierarki).
4. Arsitektur yang memisahkan eksperimen ML dari dashboard (single source of truth).
5. Pemetaan jenjang non-standar berbasis bukti empiris (bukan asumsi semantik) — contoh D-004.
8. Protokol pemilihan dengan *rule-equivalence check*: pemenang multi-kriteria (DBSCAN) ternyata identik dengan ambang satu feature (ARI 1,00); setelah kontrol, K-Means set rasio K = 5 terpilih (S06 §4, D-029).
7. Bukti empiris bahwa metrik internal (Silhouette) menyesatkan pada data workforce diskret: linkage average/complete dan DBSCAN eps kecil mencapai silhouette 0,84–1,00 lewat partisi degenerate atau kelompok organisasi identik.
6. Bukti bahwa komposisi jenjang merepresentasikan level organisasi (ε² hingga 0,54), sehingga segmentasi *workforce condition* dan segmentasi struktural perlu dibedakan.

## Referensi yang sudah dipakai

- Dolnicar, S., Grün, B., Leisch, F., & Schmidt, K. (2014). Required sample sizes for data-driven market segmentation analyses in tourism. *Journal of Travel Research*, 53(3), 296–306.
- Formann, A. K. (1984). *Die Latent-Class-Analyse*. Beltz.
- Gebru, T. et al. (2021). Datasheets for datasets. *Communications of the ACM*, 64(12), 86–92.
- Hopkins, B., & Skellam, J. G. (1954). A new method for determining the type of distribution of plant individuals. *Annals of Botany*, 18(2), 213–227.

> Detail sitasi wajib diverifikasi ulang ke sumber aslinya sebelum naskah dikirim.

## Catatan

- Nama unit organisasi perlu dikonfirmasi apakah boleh ditampilkan di naskah atau harus dianonimkan.
- Target jurnal (Sinta/Scopus, bahasa) belum ditentukan — memengaruhi format.
