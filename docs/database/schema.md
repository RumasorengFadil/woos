# Database Schema — WOOS

- Database: `woos` (PostgreSQL 14+; lokal: 17). Schema aplikasi: `woos`.
- Database `woos_test` dipakai integration test dan diisi otomatis.
- Sumber kebenaran struktur: `database/migrations/` (lihat `migrations.md`).
- Prinsip (PRD §19, §47, §95): tabel hasil model diisi **hanya** oleh pipeline ML (`ml/pipeline/s08_publish.py`). Dashboard hanya membaca, terutama lewat view `v_*`. Satu-satunya tulisan dari aplikasi web adalah `app_user` (ADMIN) dan `auth_login_attempt`.

## Diagram relasi

```
dataset_version 1─* organization 1─* organization_feature
      │                    │
      ├─* experiment 1─0..1 model 1─* cluster_profile
      │                          └─* cluster_result *─1 organization
```

## Tabel

| Tabel | Isi | Kunci | Diisi oleh |
|---|---|---|---|
| `schema_migrations` | Migration yang sudah diterapkan + checksum SHA-256 | `version` | `tools/migrate.py` |
| `dataset_version` | Versi dataset (file, SHA-256, cakupan, periode, status ACTIVE/SUPERSEDED) | `dataset_version` | s08 |
| `organization` | Master organisasi + hierarki + direktorat (termasuk 4 wadah virtual, D-014) | (`dataset_version`, `organization_id`) | s08 |
| `organization_feature` | Feature per organisasi (unit *direct*): FTK, realisasi, gap, rasio, jabatan, `grade_distribution` (JSONB), flag populasi | (`dataset_version`, `feature_version`, `organization_id`, `unit_definition`) | s08 |
| `experiment` | Registri **seluruh** run (619): hyperparameter, metrik internal, kelayakan (D-027), kriteria seleksi (D-028), `ari_vs_balance_poles` (D-029) | `experiment_id` | s08 |
| `model` | Model yang dipublish: 1 validated (`APPROVED`) + model pembanding (`EXPERIMENT`) — D-031 | `model_id`, `experiment_id` unik | s08 |
| `cluster_profile` | Profil per cluster (PRD §43); `is_business_label` = true hanya untuk model APPROVED | (`model_id`, `cluster_id`) | s08 |
| `cluster_result` | Hasil per organisasi (PRD §42): cluster, label, jarak ke centroid, flag atipikal, status segmentasi, koordinat visual `viz_x/viz_y` (006) | (`model_id`, `organization_id`) | s08 |
| `app_user` | Pengguna aplikasi: username, nama, `password_hash`, role (ADMIN/VIEWER), aktif, login terakhir (007) | `user_id`, `username` unik | `tools/create_user.php`, halaman Pengguna |
| `auth_login_attempt` | Riwayat percobaan login untuk pembatasan brute force (007) | `attempt_id` | `modules/auth` |

## Constraint penting

| Constraint | Aturan | Rujukan |
|---|---|---|
| `chk_validated_requires_approved` | `is_validated_model` hanya boleh true bila `validation_status = 'APPROVED'` | PRD §45 |
| `uq_model_validated_per_dataset` | Maksimal satu validated model per `dataset_version` | PRD §51, §64 |
| `chk_segmented_has_cluster` | `SEGMENTED` ⇔ `cluster_id` terisi; `NOT_SEGMENTED` tanpa cluster | D-017 |
| CHECK `validation_status` | EXPERIMENT, SELECTED_CANDIDATE, PENDING_BUSINESS_VALIDATION, APPROVED, REJECTED, RETIRED | PRD §45 |
| `fulfillment_ratio` / `staffing_ratio` NULL | NULL bila FTK = 0 (tidak ada pembagian nol) | PRD §8, D-003 |

## View untuk dashboard

| View | Dipakai untuk | Filter |
|---|---|---|
| `v_validated_model` | Info model (nama, versi, dataset, tanggal training; PRD §63) | APPROVED + validated |
| `v_validated_organization` | Overview, Cluster Analysis, Organization List/Detail | hasil model tervalidasi saja |
| `v_model_comparison` | Model Comparison (PRD §55) | semua model yang dipublish + penanda validated |

`model_id` adalah SERIAL dan berubah setiap publish ulang. Karena itu **gunakan `experiment_id`** atau view `v_validated_model` sebagai referensi yang stabil.

## Isi saat ini (KP-2026-09-25-v2)

| Objek | Baris |
|---|---:|
| organization | 1.305 (1.301 + 4 wadah) |
| organization_feature | 1.301 |
| experiment | 619 |
| model | 3 (EXP-KM-067 APPROVED/validated; EXP-HC-044, EXP-DB-067 EXPERIMENT) |
| v_validated_organization | 1.301 (1.280 SEGMENTED + 21 NOT_SEGMENTED) |
