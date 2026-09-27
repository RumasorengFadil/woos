-- 007 — Autentikasi aplikasi (blueprint: PHP session; role dari D-032).
CREATE TABLE IF NOT EXISTS woos.app_user (
    user_id        SERIAL       PRIMARY KEY,
    username       VARCHAR(60)  NOT NULL UNIQUE,
    full_name      VARCHAR(120) NOT NULL,
    password_hash  TEXT         NOT NULL,                 -- password_hash() PHP (bcrypt/argon2)
    role           VARCHAR(20)  NOT NULL CHECK (role IN ('ADMIN', 'VIEWER')),
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    last_login_at  TIMESTAMPTZ
);

-- Percobaan login untuk pembatasan brute force (per username & per IP).
CREATE TABLE IF NOT EXISTS woos.auth_login_attempt (
    attempt_id   BIGSERIAL    PRIMARY KEY,
    username     VARCHAR(60)  NOT NULL,
    ip_address   VARCHAR(45)  NOT NULL,
    succeeded    BOOLEAN      NOT NULL,
    attempted_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_login_attempt_recent ON woos.auth_login_attempt (username, attempted_at);
CREATE INDEX IF NOT EXISTS idx_login_attempt_ip ON woos.auth_login_attempt (ip_address, attempted_at);

-- View organisasi tervalidasi + koordinat visual (menggantikan definisi 004 dengan kolom tambahan).
CREATE OR REPLACE VIEW woos.v_validated_organization AS
SELECT r.model_id, r.experiment_id, r.dataset_version, r.period, r.organization_id,
       o.organization_name, o.parent_organization_id, p.organization_name AS parent_organization_name,
       o.organization_level, o.directorate_id, o.directorate_name,
       r.segmentation_status, r.cluster_id, r.cluster_code, r.cluster_label, r.cluster_distance, r.is_atypical_member,
       f.ftk, f.realization, f.gap, f.fulfillment_ratio, f.staffing_ratio, f.balance_index,
       f.position_count, f.vacant_position_count, f.vacant_share, f.avg_realization_per_position,
       f.unbudgeted_filled_count, f.grade_distribution, r.viz_x, r.viz_y
FROM woos.cluster_result r
JOIN woos.v_validated_model vm ON vm.model_id = r.model_id
JOIN woos.organization o ON o.dataset_version = r.dataset_version AND o.organization_id = r.organization_id
LEFT JOIN woos.organization p ON p.dataset_version = o.dataset_version AND p.organization_id = o.parent_organization_id
JOIN woos.organization_feature f ON f.dataset_version = r.dataset_version AND f.organization_id = r.organization_id
     AND f.feature_version = vm.feature_version AND f.unit_definition = 'direct';
