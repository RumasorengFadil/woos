# Decision Log — Keputusan Metodologis

Setiap keputusan yang memengaruhi data, feature, model, atau interpretasi dicatat di sini, beserta alasan dan dampaknya. Dokumen ini menjadi dasar bagian *Methods* dan *Limitations* jurnal, dan menjawab pertanyaan reviewer "mengapa pilihan ini?".

Status: `PROPOSED` (usulan, menunggu konfirmasi) · `APPROVED` · `REJECTED` · `SUPERSEDED`.

| ID | Tahap | Topik | Status |
|---|---|---|---|
| D-000 | Setup | Layer ML Python terpisah dari aplikasi web PHP | APPROVED (ADR-001) |
| D-001 | S01 | Unit analisis: direct (utama) + roll-up (sensitivitas) | APPROVED |
| D-002 | S01 | Jabatan FTK=0 & Realisasi=0 | APPROVED — diterapkan S02 |
| D-003 | S01 | FTK=0 dengan Realisasi>0 (rasio tak terdefinisi) | APPROVED — diterapkan S02/S03 |
| D-004 | S01 | Jenjang kosong & label non-standar | APPROVED dengan **REVISI** (AM → GENERALIS, berbasis bukti S02) — revisi disetujui |
| D-005 | S01 | Jabatan bertanda `*)` dan unit struktur lama | APPROVED — diterapkan S02 (flag); arti `*)` masih terbuka |
| D-006 | S01 | Nilai realisasi ekstrem | APPROVED — outlier terkuat v1 hilang di v2 |
| D-007 | S01 | Orphan & inkonsistensi level hierarki | APPROVED → dilanjutkan oleh D-014 |
| D-008 | S01 | Tidak ada data historis → tanpa label volatility | APPROVED |
| D-009 | S01b | Redundansi `gap` & titik duplikat | APPROVED — diterapkan S03/S05 |
| D-010 | S01b | Tambahan protokol: Hopkins, baseline non-ML, batas 70·d | APPROVED — protokol §6 diperbarui |
| D-011 | S01c | Dataset v2 menggantikan v1 | APPROVED |
| D-012 | S01c | Populasi analisis = seluruh Kantor Pusat; DLMHC sebagai sub-analisis | APPROVED |
| D-013 | S01c | Jenjang `JE` (Junior Expert) → SPESIALIS | APPROVED |
| D-014 | S02 | Wadah organisasi tanpa jabatan & atribut direktorat | APPROVED |
| D-015 | S02 | Normalisasi whitespace & flag kemungkinan jabatan ganda | APPROVED |
| D-016 | S03 | Distribusi jenjang = proporsi jabatan aktif (model); komposisi FTK/realisasi (tampilan) | APPROVED |
| D-017 | S03 | Populasi model = organisasi dengan ≥ 1 jabatan aktif | APPROVED |
| D-018 | S03 | Kelompok jenjang input model: MAK+MA digabung, UNKNOWN dibuang | APPROVED |
| D-019 | S03 | Feature set F1 (A/B/C/R) & peran feature turunan PRD | SUPERSEDED oleh D-020 (F1 diarsipkan) |
| D-020 | S04 | Feature set F2: B tanpa avg_realization_per_position; C dengan GENERALIS sebagai referensi | APPROVED |
| D-021 | S04 | log1p tidak dipakai di grid utama | APPROVED |
| D-022 | S04 | StandardScaler utama, RobustScaler pembanding (perubahan bobot) | APPROVED |
| D-023 | S04 | Kontrol artefak wajib: Cramér's V cluster × level & × direktorat | APPROVED |
| D-024 | S04 | Outlier dipertahankan + uji pengaruh pada K-Means | APPROVED |
| D-025 | S05 | Varian pembanding titik kembar = vektor unik tanpa bobot (bukan berbobot) | APPROVED |
| D-026 | S05 | Hierarchical via scipy `linkage` + `fcluster`; grid eps DBSCAN dari kuantil k-distance positif | APPROVED |
| D-027 | S06 | Kriteria kelayakan (eligibility) run sebelum pemilihan | APPROVED |
| D-028 | S06 | Pemilihan multi-kriteria berbasis peringkat (6 kriteria, bobot sama) + uji sensitivitas bobot | APPROVED — hasil: EXP-DB-067 (diamandemen D-029) |
| D-029 | S06 | **Post-hoc:** keluarkan segmentasi yang setara aturan satu feature (ARI ≥ 0,90 vs kutub balance_index) → kandidat EXP-KM-067 | APPROVED — kandidat EXP-KM-067 |
| D-030 | S07 | Label bisnis 5 cluster EXP-KM-067 + penandaan anggota atipikal | APPROVED (2026-09-27) — model `APPROVED` |
| D-031 | S08 | Publikasi: model tervalidasi + model terbaik tiap algoritma (pembanding, tanpa label bisnis) | APPROVED |
| D-032 | S09 | Role aplikasi ADMIN & VIEWER | APPROVED |
| D-033 | S09 | Koordinat visual (PCA 2D) & figure statis dihasilkan pipeline, bukan dashboard | APPLIED |

> **Catatan persetujuan (2026-09-27, kedelapan):** user menyetujui D-031 dan role ADMIN/VIEWER (D-032).
>
> **Catatan persetujuan (2026-09-27, ketujuh):** user menyetujui D-030 dan V1–V5 → EXP-KM-067 `APPROVED`.
>
> **Catatan persetujuan (2026-09-25, keenam):** user menyetujui D-029 → kandidat EXP-KM-067.
>
> **Catatan persetujuan (2026-09-25, kelima):** user menginstruksikan "lanjut ke tahap selanjutnya" → D-025, D-026 APPROVED.
>
> **Catatan persetujuan (2026-09-25, keempat):** user menyetujui D-020…D-024 ("setuju semua").
>
> **Catatan persetujuan (2026-09-25, ketiga):** user menyetujui D-016…D-019 ("setuju semua").
>
> **Catatan persetujuan (2026-09-25, kedua):** user menyatakan "setuju semua" untuk D-004 revisi dan D-011…D-015. Arti penanda `*)` (D-005) tetap *open question*; treatment flag tetap berlaku.
>
> **Catatan persetujuan (2026-09-25, pertama):** D-001…D-010 berstatus APPROVED karena user menginstruksikan "lanjut ke tahap berikutnya" tanpa koreksi atas rekomendasi. Pertanyaan domain yang belum dijawab tetap dicatat sebagai *open question* pada masing-masing keputusan. APPLIED berarti sudah diterapkan sebagai default yang dapat dibalik, tetapi belum dikonfirmasi eksplisit.

---

## D-000 — Layer ML Python

- **Konteks:** Blueprint arsitektur menetapkan PHP + PostgreSQL. PRD mensyaratkan K-Means, Hierarchical, DBSCAN, Silhouette, DBI, dendrogram.
- **Keputusan:** Eksperimen ML dijalankan di Python (`ml/`, scikit-learn, versi terkunci di `ml/requirements.txt`). Aplikasi web tetap PHP + PostgreSQL dan **hanya membaca** hasil yang sudah dipublish (PRD §19, §47).
- **Alasan:** Tidak ada implementasi algoritma & metrik tervalidasi yang setara di PHP; membangunnya sendiri menambah risiko kesalahan dan melemahkan reproducibility jurnal.

## D-001 — Unit analisis

- **Temuan:** median 3 jabatan & FTK 2 per organisasi; level 7–8 fulfillment 10–23 % sementara unit induknya >100 %; ORG-0258 memiliki 39 realisasi atas FTK 14.
- **Opsi:**
  - A. *Direct* — organisasi = jabatan yang tercatat langsung padanya (sesuai PRD §17 apa adanya). n = 379.
  - B. *Roll-up* — organisasi = dirinya + seluruh sub-unit. Unit induk menyerap sub-unit sehingga baris tidak independen (overlap).
  - C. *Direct* sebagai analisis utama + *roll-up* sebagai analisis sensitivitas.
- **Usulan:** **C**. A menjaga kesesuaian dengan PRD; B/C menguji apakah pola "induk overstaffed – anak understaffed" adalah artefak pencatatan. Dilaporkan sebagai robustness check di jurnal.
- **Butuh konfirmasi domain:** apakah pegawai di unit induk (mis. *Officer Legal* ORG-0258, 29 orang) sebenarnya ditempatkan di sub-unit?
- **Update S01c (v2):** realisasi jabatan tersebut di v2 = 6, dan pola "unit bawah kosong" tidak muncul pada populasi Kantor Pusat (L7 90 %, L8 79 %). Hipotesis pencatatan di induk melemah; roll-up tetap dipertahankan sebagai analisis sensitivitas.

## D-002 — Jabatan FTK=0 & Realisasi=0 (311 jabatan)

- **Usulan:** Baris dipertahankan (tidak memengaruhi total). `position_count` dihitung sebagai **jabatan aktif** (FTK>0 atau Realisasi>0); jumlah baris mentah disimpan sebagai `position_rows` untuk transparansi.
- **Alasan:** Jabatan tanpa formasi dan tanpa pegawai bukan beban kerja; memasukkannya membuat `avg_realization_per_position` bias ke bawah.

## D-003 — FTK=0 dengan Realisasi>0 (43 jabatan; 10 organisasi ber-FTK total 0 tetapi terisi)

- **Usulan:**
  - `fulfillment_ratio` & `staffing_ratio` (formula PRD) dihitung hanya bila FTK>0; bila FTK=0 → `NULL` + flag `ftk_zero = 1`. Nilai ini dipakai untuk **tampilan dashboard**.
  - Untuk **input model** ditambahkan feature rasio simetris terbatas `balance_index = (Realisasi − FTK) / (Realisasi + FTK)` ∈ [−1, 1] (0 bila keduanya 0). Terdefinisi di semua kasus dan tidak meledak pada FTK kecil.
- **Alasan:** PRD §8 mewajibkan treatment khusus FTK=0 tanpa pembagian langsung. Imputasi angka arbitrer (mis. 999 %) tidak dapat dijustifikasi.

## D-004 — Jenjang kosong (34) & label non-standar AM (12), VP (11)

- **Usulan:**
  - Kosong → `UNKNOWN` (PRD §22).
  - `VP` (Vice President) → `MM`; `AM` (Assistant Manager) → `MD` — **usulan berdasarkan nama jabatan, perlu konfirmasi**.
  - Kelompok feature distribusi jenjang mengikuti PRD §12: `MAK`, `MA`, `MM`, `MD`, `SPESIALIS` (SSP+SPC), `GENERALIS` (G1–G3), `UNKNOWN`.
- **REVISI (S02, 2026-09-25):** `AM` → **GENERALIS**, bukan MD. Bukti: dari 188 jabatan berjudul *ASSISTANT MANAGER* yang berlabel standar, 100 % berjenjang G3 (13/14). Nama jabatan yang sama bahkan muncul dengan label `AM` di satu unit dan `G3-14` di unit lain. `VP` → MM terkonfirmasi (276 jabatan *VICE PRESIDENT*, 99,6 % MM). Usulan awal berbasis semantik judul terbukti keliru; keputusan kini berbasis data (`preprocessing_log.json` → `nonstandard_grade_evidence`).

## D-005 — Jabatan `*)` (35) dan unit struktur lama

- **Temuan:** 31/35 tanpa jenjang, FTK 17, realisasi 0; banyak berada di unit L5 yang namanya juga ada di L6 (struktur baru).
- **Usulan:** Minta konfirmasi arti `*)`. Sementara: tetap disertakan (tidak ada dasar untuk membuang), diberi flag `is_marked_position`, dan diuji dampaknya di analisis sensitivitas.

## D-006 — Realisasi ekstrem

- **Usulan:** Tidak dihapus dan tidak di-capping. Diperlakukan sebagai observasi valid sampai terbukti error; dibandingkan StandardScaler vs RobustScaler, dan dicek apakah DBSCAN menandainya sebagai noise (PRD §35).

## D-007 — Orphan & inkonsistensi level

- ORG-0375, ORG-0376 (parent *Sub Bidang Hukum Maluku*) dan ORG-0379 (parent *Sub Bidang Hukum Sulawesi Utara*) — parent tidak ada di dataset.
- ORG-0256 level 6 dengan parent level 6.
- **Usulan:** Tetap disertakan sebagai unit analisis; `parent_organization_id = NULL` + flag. Tidak memengaruhi analisis *direct*; pada *roll-up* mereka tidak tergabung ke induk.

## D-008 — Snapshot tunggal

- **Keputusan (mengikuti PRD §82, §90):** Tidak ada feature volatility; label cluster "Workforce Volatility Tinggi" tidak digunakan. Bila data historis tersedia kemudian, menjadi pekerjaan lanjutan.

## D-009 — Redundansi `gap` & titik duplikat

- **Temuan (S01b):** `gap = ftk − realization` membuat matriks feature rank-deficient. Pada feature inti hanya 38 vektor unik dari 379 organisasi; kelompok identik terbesar 67 org.
- **Usulan:**
  - `gap` tetap dihitung dan ditampilkan (dashboard, profil cluster), tetapi **tidak dimasukkan ke model bersama `ftk` dan `realization`**.
  - Eksperimen utama: clustering pada semua organisasi. Eksperimen pembanding: clustering pada vektor unik dengan `sample_weight` = jumlah org, lalu label dipetakan balik. Dua hasil ini dibandingkan.
- **Alasan:** PRD §79 meminta analisis redundansi. Duplikat masif mendistorsi DBSCAN (core point otomatis) dan dendrogram (ties pada jarak 0).

## D-010 — Tambahan protokol evaluasi

- **Usulan:** menambahkan ke `00_research_protocol.md` §6:
  - Hopkins statistic (semua titik + vektor unik) sebagai prasyarat clustering tendency;
  - feature set utama dibatasi d ≤ 5 (aturan n ≥ 70·d, Dolnicar et al., 2014); set lebih besar hanya sebagai pembanding;
  - baseline non-ML berbasis tanda gap, **hanya untuk riset**, untuk mengukur nilai tambah clustering (tidak dipakai di dashboard).
- **Alasan:** menjawab kritik reviewer yang dapat diprediksi, yaitu cluster yang trivial dan rasio sampel/feature.
- **Update S03:** dengan n = 1.280 (v2), batas 70·d menjadi d ≤ 18. Batas "d ≤ 5" (yang diturunkan dari n v1 = 379) tidak lagi mengikat. Semua feature set F1 (d = 3–11) memenuhi, sehingga set C dapat diperlakukan sebagai kandidat setara, bukan hanya pembanding.

## D-011 — Dataset v2 menggantikan v1

- **Konteks:** User menyediakan `kantor_pusat_semua_direktorat.csv` (v2). v2 memuat seluruh 1.157 jabatan v1 (ID jabatan sama), tetapi 23 nilai realisasi berbeda (semuanya turun, total −45) pada tanggal periode yang sama.
- **Keputusan:** v2 (`KP-2026-09-25-v2`) menjadi satu-satunya dataset aktif. v1 disimpan (SUPERSEDED) untuk jejak audit; output v1 tetap di folder versinya.
- **Alasan:** v2 adalah superset, memiliki ID Parent, dan menghilangkan outlier yang paling meragukan di v1. Menggabungkan keduanya akan menggandakan jabatan.
- **Open question:** apakah v2 memang ekstraksi terbaru/terkoreksi?

## D-012 — Populasi analisis

- **Keputusan:** Unit analisis = 1.301 organisasi Kantor Pusat yang memiliki jabatan (4 wadah dikecualikan). Analisis DLMHC (379 org) dipertahankan sebagai sub-analisis untuk kontinuitas dengan temuan v1 dan sebagai uji robustness.
- **Alasan:** Semua feature set memenuhi aturan 70·d hanya pada populasi gabungan (S01c §3). Clustering per direktorat tidak memadai (n direktorat terkecil = 47).
- **Dampak:** RQ ditambah analisis distribusi cluster antar-direktorat (lihat protokol).

## D-013 — `JUNIOR EXPERT (JE) - 15` → SPESIALIS

- **Alasan:** jalur *expert* (non-struktural). Angka jenjang 15 berada dalam rentang SPC (15–17). Hanya 8 jabatan, semuanya di Divisi Teknologi dan Enjinering.

## D-014 — Wadah organisasi tanpa jabatan & direktorat

- **Temuan:** 4 ID parent (ORG-0013, ORG-0226, ORG-1072, ORG-1074) tidak memiliki baris dan persis sama dengan 4 celah pada urutan ID.
- **Keputusan:**
  - Ditambahkan sebagai organisasi virtual (`is_virtual_container`), dengan level = level anak − 1.
  - Parent diisi hanya bila tidak ambigu: ORG-0013 → root ORG-0002 (`INFERRED_ROOT`); lainnya `UNKNOWN`.
  - Direktorat diturunkan dari leluhur level 3. Untuk rantai terputus: keanggotaan v1 (`FALLBACK_V1_MEMBERSHIP`) lalu konsensus anak (`CHILDREN_CONSENSUS`). Sumber selalu dicatat.
  - Wadah **bukan** unit clustering.
- **Alasan:** hierarki dan filter direktorat (PRD §61) membutuhkan pohon utuh; unit tanpa jabatan tidak memiliki data workforce.

## D-015 — Normalisasi teks & kemungkinan jabatan ganda

- Tab dan spasi ganda dinormalisasi (71 sel).
- Setelah normalisasi, ORG-0908 memiliki 2 jabatan bernama identik (ID 4000: FTK 1/R 1; ID 102466: FTK 1/R 0). Keduanya **tidak digabung atau dihapus**, hanya diberi flag `is_possible_duplicate_name`, karena ID jabatan berbeda dan bisa jadi formasi terpisah.

## D-016 — Representasi distribusi jenjang

- **Opsi:** proporsi berbobot FTK, proporsi berbobot realisasi, atau proporsi jumlah jabatan aktif.
- **Keputusan:** input model memakai **proporsi jabatan aktif** per kelompok jenjang (struktur jabatan). Hitungan FTK dan realisasi per kelompok (`ftk_<grup>`, `real_<grup>`) disimpan untuk tampilan komposisi tenaga kerja (PRD §60).
- **Alasan:**
  - Terdefinisi untuk semua organisasi dengan jabatan aktif; pembobotan realisasi tidak terdefinisi bila realisasi = 0 (8,8 % org).
  - Tidak "membocorkan" informasi tingkat pemenuhan ke feature jenjang, sehingga dimensi struktur dan dimensi staffing tetap terpisah.

## D-017 — Populasi model

- **Keputusan:** organisasi tanpa jabatan aktif (seluruh jabatan FTK = 0 & Realisasi = 0), yaitu 21 direct dan 18 rollup, tidak diikutkan dalam clustering. Di dashboard mereka ditampilkan sebagai "tidak tersegmentasi — tanpa jabatan aktif".
- **Alasan:** semua feature bernilai 0 sehingga tidak ada informasi workforce. Memasukkannya hanya membentuk cluster "nol" yang trivial.
- **Bukan rule-based clustering (PRD §41):** ini kriteria kelayakan data (*eligibility*), bukan pemberian label cluster.

## D-018 — Kelompok jenjang untuk input model

- **Keputusan:** `pct_MA_MAK` (MAK + MA), `pct_MM`, `pct_MD`, `pct_SPESIALIS`, `pct_GENERALIS`. `pct_UNKNOWN` tidak dipakai sebagai input.
- **Alasan:**
  - MAK hanya memiliki 4 jabatan aktif di seluruh Kantor Pusat. Sebagai feature tersendiri, 4 titik akan mendominasi jarak setelah standardisasi.
  - Tujuh proporsi berjumlah 1 (*compositional closure*), sehingga satu kategori harus dibuang agar tidak linear-dependen. UNKNOWN (19 jabatan aktif) adalah kategori kualitas data, bukan struktur.
- Tujuh kelompok asli tetap tersedia untuk tampilan (PRD §12).

## D-019 — Feature set F1

- A = ftk, realization, balance_index
- B = A + position_count, vacant_position_count, avg_realization_per_position
- C = B + 5 proporsi jenjang
- R = balance_index, vacant_share, avg_realization_per_position (rasio saja, PRD §81)
- `gap`, `fulfillment_ratio`, `staffing_ratio` hanya untuk tampilan dan profil cluster (D-003, D-009).
- Perbandingan direct vs rollup memakai irisan populasi (1.280 org).

## D-020 — Feature set F2 (revisi D-019 berdasarkan EDA)

- **Bukti (S04 §3):** VIF maksimum F1 adalah B = 11,3 (realization, karena avg = realization/position_count) dan C = 75,9 (pct_MM, karena lima proporsi jenjang berjumlah ≈ 1; rata-rata 0,996).
- **Usulan:**
  - A = ftk, realization, balance_index (tetap)
  - **B = ftk, realization, balance_index, position_count, vacant_position_count** (avg_realization_per_position → tampilan saja)
  - **C = B + pct_MA_MAK, pct_MM, pct_MD, pct_SPESIALIS** (GENERALIS = kategori referensi)
  - R = balance_index, vacant_share, avg_realization_per_position (tetap; VIF 3,0)
- **Hasil:** VIF maksimum B 3,9 dan C 4,9; Hopkins dedup B 0,893 dan C 0,918. Feature version naik menjadi `F2`; F1 tetap tersimpan.

## D-021 — Tanpa log1p pada grid utama

- **Bukti (S04 §4):** log1p menurunkan skew (ftk 5,4 → −0,2), tetapi menaikkan VIF menjadi 10–35 karena hubungan rasio antar-feature menjadi hampir linear di ruang log.
- **Usulan:** tidak dipakai. Skew ditangani lewat pembanding RobustScaler dan analisis noise DBSCAN. Dilaporkan sebagai alternatif yang dipertimbangkan dan ditolak.

## D-022 — Peran scaler

- **Bukti (S04 §4):** RobustScaler melipatgandakan rentang balance_index (2,76×) dan mengecilkan feature jenjang ber-IQR 0 (0,15×).
- **Usulan:** StandardScaler = konfigurasi utama (default PRD §24). RobustScaler = pembanding, dan perbedaan hasilnya diinterpretasikan sebagai efek pembobotan feature.

## D-023 — Kontrol artefak level/direktorat

- **Bukti (S04 §6):** ε² level untuk proporsi jenjang 0,33–0,54, sedangkan ε² direktorat ≤ 0,15 untuk semua feature.
- **Usulan:** setiap model di Tahap 6 melaporkan Cramér's V (cluster × level, cluster × direktorat). Model dengan V_level tinggi diberi catatan "segmentasi struktural" pada kriteria *business interpretability* (PRD §38). Ini bukan filter otomatis; level tetap tidak menjadi input model.

## D-024 — Outlier

- **Bukti (S04 §5):** 27 outlier multivariat bersifat substantif, misalnya Bidang Verifikasi Keuangan (FTK 30–34, realisasi 0–1) dan *pool* Senior Specialist di unit direktorat.
- **Usulan:** tetap di populasi (konsisten D-006). Robustness: K-Means konfigurasi terpilih dijalankan ulang tanpa 27 outlier, lalu dibandingkan (ARI pada irisan).

## D-025 — Varian pembanding titik kembar

- **Konteks:** D-009 merencanakan clustering vektor unik dengan `sample_weight` = jumlah organisasi.
- **Temuan saat implementasi:** untuk K-Means dan DBSCAN, varian berbobot **setara matematis** dengan clustering pada data penuh. Fungsi objektif K-Means dan hitungan `min_samples` DBSCAN identik, sehingga varian ini tidak informatif. Hierarchical di scikit-learn/scipy tidak mendukung bobot.
- **Keputusan:** varian pembanding = vektor unik **tanpa bobot** (setiap profil dihitung sekali). Label dipetakan balik ke seluruh organisasi, dan metrik dihitung pada populasi penuh. Dijalankan untuk ketiga algoritma dengan StandardScaler.

## D-026 — Detail implementasi grid

- Hierarchical: `scipy.cluster.hierarchy.linkage` (euclidean) + `fcluster(criterion="maxclust")`, setara dengan `AgglomerativeClustering`. Satu pohon per konfigurasi dipakai untuk dendrogram dan untuk semua K, sehingga konsisten. Ditambah korelasi cophenetic.
- DBSCAN eps: kuantil {0,50…0,95} dari jarak ke tetangga ke-(min_samples − 1) yang **positif**, ditambah titik knee kurva k-distance; batas bawah 0,05. Jarak 0 dikecualikan karena titik kembar membuat banyak k-distance = 0, dan `eps` wajib > 0.

## D-027 — Kriteria kelayakan run (ditetapkan sebelum pemilihan)

Sebuah run eksperimen menjadi kandidat pemilihan hanya bila memenuhi seluruh syarat berikut:
1. Varian `all`, yaitu clustering pada seluruh populasi. Varian `unique` hanya untuk analisis sensitivitas.
2. Jumlah cluster (tanpa noise) 2–8, sama dengan rentang K PRD §28. Ini mengeluarkan fragmentasi DBSCAN hingga 44 cluster.
3. Cluster terbesar < 95 %, sehingga bukan partisi degenerate (S05 §3).
4. Cluster terkecil ≥ 2 % populasi (≥ 26 org), sehingga setiap segmen cukup besar untuk diprofilkan dan dilaporkan ke bisnis. Kelompok yang lebih kecil ditangani sebagai outlier/noise.
5. Noise ≤ 15 % (DBSCAN).
6. Silhouette < 0,99, untuk mengeluarkan artefak kelompok organisasi identik (S05 §4).

## D-028 — Pemilihan multi-kriteria (PRD §38)

- **Enam kriteria** dihitung untuk setiap run yang layak:
  1. Silhouette (↑)
  2. Davies–Bouldin (↓)
  3. **Stabilitas**: rata-rata ARI 50 bootstrap subsample 80 %, refit dengan hyperparameter sama (↑)
  4. **Keseimbangan**: entropi ukuran cluster ternormalisasi (↑)
  5. **Relevansi workforce**: rata-rata η² `balance_index` dan `vacant_share` antar-cluster, yaitu seberapa jauh segmen membedakan kondisi staffing (PRD §1) (↑)
  6. **Kontrol artefak**: Cramér's V (bias-corrected) cluster × level organisasi (↓, D-023)
- **Agregasi:** peringkat per kriteria (1 = terbaik), lalu dirata-ratakan dengan bobot sama. Skor terendah = kandidat terpilih.
- **Sensitivitas:** peringkat diulang dengan (a) menghapus satu kriteria bergantian dan (b) hanya memakai silhouette + DBI. Hasilnya dilaporkan apakah model terpilih berubah.
- **Pelaporan saja (bukan kriteria):** Cramér's V × direktorat, ARI terhadap baseline tanda gap (D-010), silhouette baseline.
- **Status:** model terpilih = `SELECTED_CANDIDATE`. Status `APPROVED` baru diberikan setelah profiling & validasi bisnis di Tahap 7 (PRD §45).

## D-029 — Kontrol kesetaraan dengan aturan satu feature (post-hoc)

- **Status:** APPROVED oleh user (2026-09-25). Diusulkan **setelah** melihat hasil D-028 dan dilaporkan sebagai amandemen post-hoc, bukan bagian protokol awal.
- **Temuan (S06 §4):** kandidat D-028, EXP-DB-067, identik (ARI 1,000 tanpa noise) dengan aturan "`balance_index` = −1 / = +1 / lainnya". Sebanyak 49 dari 143 run layak memiliki ARI ≥ 0,90 terhadap aturan ini. Metrik tinggi mereka berasal dari dua kutub diskret ±1.
- **Usulan:** run dengan ARI (tanpa noise) ≥ 0,90 terhadap aturan tersebut dikeluarkan dari pemilihan, karena setara klasifikasi rule-based (PRD §41, §47). Enam kriteria D-028 lalu diterapkan ulang pada 94 run tersisa.
- **Hasil bila disetujui:** kandidat = **EXP-KM-067** (K-Means, set R = balance_index, vacant_share, avg_realization_per_position; StandardScaler; K = 5). Kandidat ini unggul jelas atas #2 (skor 23,7 vs 26,0).
- **Alternatif bila ditolak:** kandidat tetap EXP-DB-067 (3 segmen: kosong total / terisi tanpa formasi / lainnya 83 %).
- **Pelaporan jurnal:** kedua hasil dilaporkan, dan amandemen ditandai jelas sebagai post-hoc beserta alasannya.

## D-030 — Label bisnis cluster (PRD §41, §45)

- **Status:** APPROVED oleh user pada 2026-09-27 ("setuju semua"). V1–V5 disetujui; V2: label "Relatif Stabil" dipertahankan. Tercatat di `model_artifacts/approval.json` (script `s07b_record_approval.py`).
- **Usulan** (diberikan per `cluster_id` setelah profiling; diverifikasi terhadap tanda tangan profil):

| ID | Kode | Label | Arketipe PRD |
|---:|---|---|---|
| 0 | UNBUDGETED | Terisi Tanpa Formasi | Potensi overstaffing (struktural) |
| 1 | PARTIAL_UNDER | Understaffing Parsial | Understaffing |
| 2 | STABLE | Relatif Stabil | Relatif stabil |
| 3 | VACANT | Understaffing Kritis (Belum Terisi) | Understaffing |
| 4 | OVER | Potensi Overstaffing | Potensi overstaffing |
| — | NOT_SEGMENTED | Tidak Tersegmentasi | — (D-017) |

- Anggota dengan jarak ke centroid > P95 cluster diberi flag `is_atypical_member` (45 org) untuk ditampilkan di dashboard. Label cluster mereka tidak diubah.
- Setelah validasi: `validation_status` EXP-KM-067 berubah dari `PENDING_BUSINESS_VALIDATION` menjadi `APPROVED`, dan model boleh dipublish (PRD §45).

## D-031 — Cakupan publikasi ke database (PRD §45, §51, §55, §64)

- **Konteks:**
  - PRD §45 menyatakan dashboard hanya memakai model `APPROVED`.
  - PRD §51/§64 meminta dashboard tetap dapat **membandingkan** K-Means, Hierarchical, dan DBSCAN, dengan penanda *Validated Model*.
- **Keputusan:**
  - Dipublish: (a) model tervalidasi EXP-KM-067 (`APPROVED`, `is_validated_model = true`), beserta profil cluster berlabel bisnis dan hasil per organisasi; (b) model terbaik tiap algoritma lain (EXP-HC-044, EXP-DB-067) berstatus `EXPERIMENT`, hanya untuk konteks *Model Comparison*. Label cluster keduanya generik ("Cluster n" / "Noise"), tanpa label bisnis.
  - Registri seluruh 619 eksperimen dipublish untuk transparansi metrik (PRD §55, §71).
  - Constraint database memastikan **maksimal satu model tervalidasi per dataset**, dan hanya model `APPROVED` yang boleh menjadi validated model.
- **Alasan:** memenuhi PRD §51 tanpa melanggar §45. Pandangan utama dashboard (overview, profil, organisasi) hanya membaca view yang difilter `APPROVED`.

## D-032 — Role aplikasi

- PRD tidak mendefinisikan role. Role yang disetujui user:
  - `VIEWER`: seluruh halaman dashboard (baca saja);
  - `ADMIN`: VIEWER + registri eksperimen + manajemen user.
- Pola blueprint: User → Role → Permission (`config/role_access.php`) → cek otorisasi di setiap halaman melalui guard bersama.

## D-033 — Visualisasi dihasilkan pipeline

- PRD §47 melarang dashboard melakukan clustering sendiri; PRD §52 menyatakan PCA hanya untuk visualisasi.
- **Keputusan:**
  - koordinat PCA 2D per organisasi per model dihitung `s08_publish.py` (Python) dan disimpan di `cluster_result.viz_x/viz_y` (migration 006);
  - dendrogram, elbow, dan figure riset lain yang tidak dapat direkonstruksi dari tabel disalin pipeline ke `assets/figures/`.
- Dashboard hanya menggambar ulang data yang sudah tersimpan.
