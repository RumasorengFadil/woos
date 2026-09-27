# Eksperimen 03 — Feature Engineering & Feature Scaling

| Item | Nilai |
|---|---|
| ID tahap | `S03-FE` |
| Tanggal | 2026-09-25 |
| Dataset / feature version | `KP-2026-09-25-v2` / `F1` |
| Script | `ml/pipeline/s03_feature_engineering.py` |
| Output | `ml/outputs/03_feature_engineering/KP-2026-09-25-v2/` |
| Test | `tests/ml/test_s03_feature_engineering.py` (5 test; total suite 23) |
| Status | **SELESAI — menunggu validasi** |
| Bagian jurnal | *Methods → Feature engineering, Feature scaling* |

## 1. Unit analisis & populasi

1 baris = 1 organisasi + 1 periode (PRD §17). Unit didefinisikan dengan dua cara (D-001):

| Unit | Definisi | Organisasi | Populasi model | Peran |
|---|---|---:|---:|---|
| **direct** | jabatan yang tercatat langsung pada organisasi | 1.301 | **1.280** | analisis utama |
| rollup | organisasi + seluruh sub-unit (termasuk yang melewati wadah virtual) | 1.301 | 1.283 | analisis sensitivitas |

- **Populasi model (D-017):** organisasi yang memiliki ≥ 1 jabatan aktif dan bukan wadah virtual.
- 21 organisasi *direct* dikecualikan karena seluruh jabatannya FTK = 0 dan Realisasi = 0. Sebanyak 13 di antaranya ada di DLMHC dan sebagian besar merupakan unit struktur lama, misalnya ORG-0224/0225 L5 yang namanya kembar dengan unit L6.
- Tiga unit hanya masuk populasi *rollup* (ORG-0011 Direktorat TEK, ORG-0320, ORG-0328) karena sub-unitnya memiliki jabatan aktif.
- Perbandingan direct vs rollup di Tahap 6 memakai **irisan 1.280 organisasi**.

## 2. Kamus feature

| Feature | Formula | Peran | Rujukan |
|---|---|---|---|
| `ftk` | Σ FTK jabatan | model + tampilan | PRD §6 |
| `realization` | Σ realisasi jabatan | model + tampilan | PRD §6 |
| `gap` | ftk − realization | tampilan | PRD §7; **bukan input model** (D-009) |
| `fulfillment_ratio` | realization / ftk; NULL bila ftk = 0 | tampilan | PRD §8; D-003 |
| `staffing_ratio` | (realization − ftk) / ftk; NULL bila ftk = 0 | tampilan | PRD §9; identik fulfillment − 1 |
| `balance_index` | (realization − ftk) / (realization + ftk), 0 bila keduanya 0; ∈ [−1, 1] | model | D-003 |
| `position_count` | jumlah jabatan aktif (FTK > 0 atau Realisasi > 0) | model + tampilan | PRD §6; D-002 |
| `vacant_position_count` | jabatan FTK > 0 & Realisasi = 0 | model + tampilan | PRD §10 |
| `avg_realization_per_position` | realization / position_count | model + tampilan | PRD §11 |
| `vacant_share` | vacant_position_count / position_count | model (set R) | PRD §81 |
| `pct_MA_MAK`, `pct_MM`, `pct_MD`, `pct_SPESIALIS`, `pct_GENERALIS` | proporsi jabatan aktif per kelompok jenjang | model (set C) | PRD §12; D-016, D-018 |
| `pct_<7 kelompok>` | proporsi jabatan aktif (MAK, MA, MM, MD, SPESIALIS, GENERALIS, UNKNOWN) | tampilan | PRD §12 |
| `ftk_<kelompok>`, `real_<kelompok>` | Σ FTK / Σ realisasi per kelompok jenjang | tampilan (komposisi tenaga kerja, PRD §60) | D-016 |
| `position_rows`, `dormant_position_count`, `unbudgeted_filled_count`, `marked_position_count`, `extreme_position_count` | hitungan jabatan per kondisi | tampilan / sensitivitas | D-002, D-003, D-005, D-006 |
| `ftk_zero`, `has_active_positions`, `in_model_population` | flag | kontrol | D-003, D-017 |

Kamus lengkap dalam format mesin: `feature_schema.json` (PRD §73).

**Hubungan matematis yang ditangani (PRD §79):**

- `gap` = ftk − realization, sehingga linear-dependen dengan ftk dan realization.
- `staffing_ratio` = fulfillment − 1, sehingga identik secara informasi.
- `balance_index` = (f − 1)/(f + 1) untuk ftk > 0, yaitu transformasi monoton dari fulfillment yang terbatas dan terdefinisi pula saat ftk = 0.
- Tujuh proporsi jenjang berjumlah 1 (*closure*), sehingga satu kategori harus dibuang dari input model (D-018).

## 3. Feature set (PRD §80–§81)

| Set | Feature | d | 70·d ≤ n? | Rank | Vektor unik (direct / rollup) |
|---|---|---:|:---:|---:|---:|
| **A** — inti | ftk, realization, balance_index | 3 | ✅ | 3 | 83 / 263 |
| **B** — + struktur | A + position_count, vacant_position_count, avg_realization_per_position | 6 | ✅ | 6 | 191 / 507 |
| **C** — + jenjang | B + pct_MA_MAK, pct_MM, pct_MD, pct_SPESIALIS, pct_GENERALIS | 11 | ✅ (770 ≤ 1.280) | 11 | 281 / 581 |
| **R** — rasio saja | balance_index, vacant_share, avg_realization_per_position | 3 | ✅ | 3 | 162 / 468 |

Semua matriks memiliki **rank penuh**, jadi tidak ada lagi dependensi linear, dan tidak memiliki nilai NaN.

## 4. Statistik deskriptif feature model (direct, n = 1.280)

| Feature | Mean | SD | Median | Maks | Nilai unik | % nol |
|---|---:|---:|---:|---:|---:|---:|
| ftk | 2,96 | 2,43 | 3 | 34 | 18 | 4,1 |
| realization | 2,82 | 2,10 | 3 | 19 | 13 | 8,8 |
| balance_index | −0,06 | 0,39 | 0 | 1 | 45 | 45,6 |
| position_count | 2,38 | 1,07 | 3 | 13 | 9 | 0 |
| vacant_position_count | 0,60 | 0,89 | 0 | 11 | 9 | 56,3 |
| avg_realization_per_position | 1,16 | 0,71 | 1 | 8 | 33 | 8,8 |
| vacant_share | 0,22 | 0,31 | 0 | 1 | 13 | 56,3 |
| pct_MA_MAK | 0,04 | 0,16 | 0 | 1 | 6 | 94,7 |
| pct_MM | 0,19 | 0,38 | 0 | 1 | 9 | 78,4 |
| pct_MD | 0,24 | 0,26 | 0,33 | 1 | 11 | 42,5 |
| pct_SPESIALIS | 0,05 | 0,15 | 0 | 1 | 9 | 90,0 |
| pct_GENERALIS | 0,48 | 0,36 | 0,67 | 1 | 12 | 32,1 |

Catatan awal untuk EDA (Tahap 4), tanpa analisis lanjutan di tahap ini:

- **Korelasi Spearman tinggi** (|ρ| ≥ 0,7):
  - vacant_position_count–vacant_share 0,97 (tidak pernah berada dalam set yang sama);
  - realization–avg_realization_per_position 0,85;
  - ftk–position_count 0,80;
  - balance_index–avg_realization_per_position 0,75.
- **Risiko artefak level (protokol §6):** komposisi jenjang berasosiasi kuat dengan level organisasi. Spearman terhadap level: pct_GENERALIS +0,57, pct_MM −0,49, pct_MA_MAK −0,38. Rata-rata pct_MM paling tinggi di L5 (0,61) karena unit bidang dipimpin VP. Set C berpotensi mengelompokkan berdasarkan level. Ini diuji di Tahap 4 dan Tahap 6.
- Feature jenjang sangat jarang (sparse): pct_MA_MAK 94,7 % nol, pct_SPESIALIS 90 % nol.

## 5. Feature scaling (PRD §24)

- Scaler di-*fit* pada populasi model, per unit × set: 2 unit × 4 set × 2 scaler = **16 artefak** (`scalers/*.joblib`). Setiap artefak menyimpan daftar feature, versi dataset, dan versi feature.
- **StandardScaler** adalah default; **RobustScaler** adalah alternatif (PRD §24).
- Keterbatasan RobustScaler: IQR = 0 pada pct_MA_MAK, pct_MM, dan pct_SPESIALIS. Scikit-learn memakai skala 1 untuk kasus ini, sehingga ketiga feature tersebut tidak ter-skala sementara feature lain dibagi IQR-nya. Bobot relatifnya menjadi berbeda dari StandardScaler, dan perbedaan ini dilaporkan sebagai bagian perbandingan scaler.
- Center/scale setiap feature: `scaling_summary.csv`.

## 6. Validasi (semua PASS)

| Cek | direct | rollup |
|---|:---:|:---:|
| gap = ftk − realization | ✅ | ✅ |
| fulfillment NULL ⇔ ftk = 0 | ✅ | ✅ |
| staffing = fulfillment − 1 | ✅ | ✅ |
| balance_index ∈ [−1, 1] | ✅ | ✅ |
| jabatan kosong ≤ jabatan aktif ≤ baris jabatan | ✅ | ✅ |
| Σ proporsi jenjang = 1 (jabatan aktif > 0), = 0 bila tidak ada | ✅ | ✅ |
| Σ FTK/realisasi per jenjang = total | ✅ | ✅ |
| Total FTK & realisasi = total Tahap 2 | ✅ | — |
| Roll-up seluruh puncak pohon mencakup semua FTK | — | ✅ |
| Roll-up ≥ direct untuk setiap organisasi | — | ✅ |
