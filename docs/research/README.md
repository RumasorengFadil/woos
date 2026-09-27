# Research / Experiment Documentation

Folder ini adalah **catatan penelitian** — apa yang diteliti, bagaimana, hasilnya, dan mengapa keputusan diambil. Ditulis agar dapat langsung diolah menjadi naskah jurnal.

Berbeda dengan `docs/reports/` yang berisi **Implementation Report** (apa yang dibangun di kode, file apa yang berubah, bagaimana diuji).

| Pertanyaan | Lihat di |
|---|---|
| "Apa yang ditemukan dari data/model?" | `docs/research/` |
| "Apa yang diubah di kode dan bagaimana mengujinya?" | `docs/reports/YYYY/MM/DD/` |

## Isi

| File | Fungsi |
|---|---|
| `00_research_protocol.md` | RQ, desain, rencana evaluasi, reproducibility (ditulis sebelum modeling) |
| `dataset_card.md` | Deskripsi formal dataset |
| `decision_log.md` | Semua keputusan metodologis + alasan + status |
| `journal_outline.md` | Peta dokumen → bagian naskah IMRaD |
| `01_data_understanding.md` | Tahap 1 |
| `01b_dataset_adequacy.md` | Tahap 1b — kecukupan dataset (v1) |
| `01c_dataset_v2.md` | Tahap 1c — dataset v2: understanding, adequacy, rekonsiliasi |
| `02_preprocessing.md` | Tahap 2 — preprocessing |
| `03_feature_engineering.md` | Tahap 3 — feature engineering & scaling |
| `04_eda.md` | Tahap 4 — EDA |
| `05_experiments.md` | Tahap 5 — eksperimen K-Means, Hierarchical, DBSCAN |
| `06_evaluation.md` | Tahap 6 — evaluasi, perbandingan & pemilihan model |
| `07_cluster_interpretation.md` | Tahap 7 — profiling, label usulan, validasi bisnis |
| Registri eksperimen | Metadata seluruh run (`EXP-KM/HC/DB-nnn`, PRD §44/§71) di `ml/outputs/05_experiments/<dataset>/experiments.json`; label per run di `labels.csv.gz` |

## Aturan

1. Setiap angka harus dapat ditelusuri ke file output di `ml/outputs/`.
2. Keputusan yang mengubah data/feature/model wajib masuk `decision_log.md` sebelum dieksekusi.
3. Hasil negatif (mis. metrik rendah, cluster tidak bermakna) tetap dicatat — ini bahan diskusi jurnal.
4. Label bisnis cluster hanya diberikan setelah profiling (PRD §41).
