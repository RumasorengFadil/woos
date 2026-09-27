-- 004 — View baca dashboard. Dashboard hanya membaca view/tabel ini; tidak ada clustering di aplikasi (PRD §47).

CREATE OR REPLACE VIEW woos.v_validated_model AS
SELECT m.*
FROM woos.model m
WHERE m.is_validated_model AND m.validation_status = 'APPROVED';

-- Hasil model tervalidasi + feature + master organisasi (Overview, Organization List/Detail).
CREATE OR REPLACE VIEW woos.v_validated_organization AS
SELECT r.model_id, r.experiment_id, r.dataset_version, r.period, r.organization_id,
       o.organization_name, o.parent_organization_id, p.organization_name AS parent_organization_name,
       o.organization_level, o.directorate_id, o.directorate_name,
       r.segmentation_status, r.cluster_id, r.cluster_code, r.cluster_label, r.cluster_distance, r.is_atypical_member,
       f.ftk, f.realization, f.gap, f.fulfillment_ratio, f.staffing_ratio, f.balance_index,
       f.position_count, f.vacant_position_count, f.vacant_share, f.avg_realization_per_position,
       f.unbudgeted_filled_count, f.grade_distribution
FROM woos.cluster_result r
JOIN woos.v_validated_model vm ON vm.model_id = r.model_id
JOIN woos.organization o ON o.dataset_version = r.dataset_version AND o.organization_id = r.organization_id
LEFT JOIN woos.organization p ON p.dataset_version = o.dataset_version AND p.organization_id = o.parent_organization_id
JOIN woos.organization_feature f ON f.dataset_version = r.dataset_version AND f.organization_id = r.organization_id
     AND f.feature_version = vm.feature_version AND f.unit_definition = 'direct';

-- Tabel perbandingan model terbaik tiap algoritma (PRD §55): metrik dari eksperimen, bukan dihitung dashboard.
CREATE OR REPLACE VIEW woos.v_model_comparison AS
SELECT m.model_id, m.experiment_id, m.model_name, m.dataset_version, m.validation_status, m.is_validated_model,
       e.feature_set, e.scaler, e.hyperparameters, e.n_clusters, e.noise_count, e.noise_share,
       e.silhouette, e.davies_bouldin, e.stability_ari, e.size_entropy_norm, e.workforce_eta2,
       e.cramers_v_level, e.cramers_v_directorate, e.ari_vs_gap_sign, e.ari_vs_balance_poles,
       e.rank_score, e.rank_score_posthoc
FROM woos.model m
JOIN woos.experiment e ON e.experiment_id = m.experiment_id;
