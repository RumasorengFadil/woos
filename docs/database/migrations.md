# Migrations — WOOS

Runner: `ml/.venv/bin/python tools/migrate.py [--database=<nama>] [--create-db]`

- File `database/migrations/NNN_<deskripsi>.sql`, bernomor berurutan tanpa celah.
- Setiap file diterapkan sekali dalam satu transaksi, lalu dicatat di `woos.schema_migrations` beserta checksum SHA-256.
- **Jangan mengedit migration yang sudah diterapkan.** Runner menolak bila checksum berubah; perubahan dibuat sebagai migration baru.
- Statement dibuat idempotent (`IF NOT EXISTS`, `CREATE OR REPLACE VIEW`) sejauh praktis.

| No | File | Perubahan | Tabel/objek |
|---|---|---|---|
| 001 | `001_create_schema.sql` | Schema `woos`, pencatat migration | `schema_migrations` |
| 002 | `002_create_reference_tables.sql` | Versi dataset, master organisasi, feature organisasi | `dataset_version`, `organization`, `organization_feature` |
| 003 | `003_create_model_tables.sql` | Registri eksperimen, model, profil & hasil cluster + constraint validasi | `experiment`, `model`, `cluster_profile`, `cluster_result` |
| 004 | `004_create_dashboard_views.sql` | View baca dashboard | `v_validated_model`, `v_validated_organization`, `v_model_comparison` |
| 005 | `005_widen_experiment_calinski_harabasz.sql` | `calinski_harabasz` → DOUBLE PRECISION (nilai ekstrem pada run berartefak titik kembar) | `experiment` |
| 006 | `006_add_cluster_result_visual_coordinates.sql` | Koordinat PCA 2D per organisasi per model + explained variance (D-033) | `cluster_result.viz_x/viz_y`, `model.viz_explained_variance` |
| 007 | `007_create_auth_tables.sql` | Pengguna & percobaan login; `v_validated_organization` ditambah `viz_x/viz_y` | `app_user`, `auth_login_attempt`, view |

## Verifikasi manual

```bash
ml/.venv/bin/python tools/migrate.py            # → applied: nothing (up to date)
psql woos -c "select version, applied_at from woos.schema_migrations order by 1"
```
