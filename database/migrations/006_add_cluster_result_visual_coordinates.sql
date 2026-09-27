-- 006 — Koordinat visualisasi PCA 2D per organisasi per model (D-033). Dihitung pipeline, hanya untuk tampilan.
ALTER TABLE woos.cluster_result ADD COLUMN IF NOT EXISTS viz_x NUMERIC(10, 4);
ALTER TABLE woos.cluster_result ADD COLUMN IF NOT EXISTS viz_y NUMERIC(10, 4);
ALTER TABLE woos.model ADD COLUMN IF NOT EXISTS viz_explained_variance JSONB;
