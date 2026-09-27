# Dataset Card — FTK & Realisasi PT PLN (Persero) Kantor Pusat

Format mengikuti gagasan *Datasheets for Datasets* (Gebru et al.) agar mudah diringkas menjadi subbab *Data* pada jurnal.

## Versi

| Versi | Status | File | Cakupan | Jabatan / Org |
|---|---|---|---|---|
| `KP-2026-09-25-v2` | **ACTIVE** | `data/raw/kantor_pusat_semua_direktorat.csv` (SHA-256 `29b39045161d7cf126b167fcaa29b752196a81d086cb8397c1c7717c78ef1f82`) | Seluruh direktorat Kantor Pusat, level 2–8 | 3.528 / 1.301 (+4 wadah tanpa jabatan) |
| `DLMHC-2026-09-25-v1` | SUPERSEDED (D-011) | `data/raw/direktorat_legal_manajemen_human_capital.csv` | Direktorat Legal dan MHC | 1.157 / 379 |

v2 memuat seluruh jabatan v1; 23 nilai realisasi berbeda (lihat `01c_dataset_v2.md` §2). Kolom v2 = kolom v1 + `ID Parent`.

## Detail v1 (historis)

| Item | Nilai |
|---|---|
| Versi | `DLMHC-2026-09-25-v1` |
| File | `data/raw/direktorat_legal_manajemen_human_capital.csv` |
| SHA-256 | `3d805a9d32368cece82a10705a131cfc24cd969a422bd4be0b844f336234b243` |
| Cakupan | Direktorat Legal dan Manajemen Human Capital beserta seluruh unit di bawahnya |
| Periode | 1 snapshot, `2026-09-25` |
| Granularitas | 1 baris = 1 jabatan pada 1 organisasi |
| Ukuran | 1.157 jabatan, 379 organisasi, level 3–8 |
| Data personal | Tidak ada (agregat jumlah pegawai per jabatan) |

## Kolom

| Kolom sumber | Nama internal | Tipe | Keterangan |
|---|---|---|---|
| ID Organisasi | `organization_id` | string | Unik & konsisten |
| Nama Organisasi | `organization_name` | string | Tidak unik (v1: 5 nama; v2: 16 nama dipakai >1 ID) |
| Parent Organisasi | `parent_name` | string | **Nama** parent |
| ID Parent (v2) | `parent_organization_id` | string | ID parent; 1.292/1.301 valid, 5 ID tidak ada (root + 4 wadah) |
| Level Organisasi | `organization_level` | int | 2 (Kantor Pusat) / 3 (direktorat) – 8 |
| ID Jabatan | `position_id` | int | Unik global |
| Nama Jabatan | `position_name` | string | kosong v1 1 / v2 5; bertanda `*)` v1 35 / v2 42; v2: 71 sel ber-tab/spasi ganda |
| Jenjang Jabatan | `grade` | string | Format `NAMA (KODE) - ANGKA`; kosong v1 34 / v2 42; label `AM`/`VP` non-standar; v2 menambah `JE` |
| FTK Jabatan | `ftk` | int | v1: 0–4; v2: 0–17 |
| Realisasi Jabatan | `realization` | int | v1: 0–29; v2: 0–9 |
| Periode Data | `period` | date | Satu nilai |

## Keterbatasan diketahui

Lihat `01_data_understanding.md` §3–§5, `01c_dataset_v2.md`, dan `decision_log.md`.
