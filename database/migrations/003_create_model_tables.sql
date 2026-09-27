-- 003 — Registri eksperimen, model, profil cluster, hasil cluster (PRD §42–§45, §71).

CREATE TABLE IF NOT EXISTS woos.experiment (
    experiment_id          VARCHAR(20) PRIMARY KEY,
    model_name             VARCHAR(20) NOT NULL CHECK (model_name IN ('KMEANS', 'HIERARCHICAL', 'DBSCAN')),
    model_version          VARCHAR(10) NOT NULL,
    dataset_version        VARCHAR(40) NOT NULL REFERENCES woos.dataset_version (dataset_version),
    feature_version        VARCHAR(10) NOT NULL,
    unit_definition        VARCHAR(10) NOT NULL,
    feature_set            VARCHAR(5)  NOT NULL,
    features_used          JSONB       NOT NULL,
    scaler                 VARCHAR(20) NOT NULL,
    variant                VARCHAR(10) NOT NULL,
    hyperparameters        JSONB       NOT NULL,
    random_seed            INTEGER     NOT NULL,
    code_version           VARCHAR(20) NOT NULL,
    training_timestamp     TIMESTAMPTZ NOT NULL,
    n_samples              INTEGER     NOT NULL,
    n_clusters             INTEGER     NOT NULL,
    noise_count            INTEGER     NOT NULL,
    noise_share            NUMERIC(6, 4) NOT NULL,
    silhouette             NUMERIC(8, 4),
    davies_bouldin         NUMERIC(10, 4),
    calinski_harabasz      NUMERIC(14, 2),
    min_cluster_share      NUMERIC(6, 4),
    max_cluster_share      NUMERIC(6, 4),
    size_entropy_norm      NUMERIC(6, 4),
    cluster_sizes          JSONB,
    inertia                NUMERIC(14, 4),
    eligible               BOOLEAN     NOT NULL,           -- D-027
    rejection_reason       VARCHAR(40),
    stability_ari          NUMERIC(6, 4),                   -- D-028 (hanya run layak)
    workforce_eta2         NUMERIC(6, 4),
    cramers_v_level        NUMERIC(6, 4),
    cramers_v_directorate  NUMERIC(6, 4),
    ari_vs_gap_sign        NUMERIC(6, 4),
    ari_vs_balance_poles   NUMERIC(6, 4),                   -- D-029
    rank_score             NUMERIC(8, 3),
    rank_score_posthoc     NUMERIC(8, 3),
    validation_status      VARCHAR(30) NOT NULL DEFAULT 'EXPERIMENT'
);
CREATE INDEX IF NOT EXISTS idx_experiment_model ON woos.experiment (dataset_version, model_name, eligible);

CREATE TABLE IF NOT EXISTS woos.model (
    model_id            SERIAL      PRIMARY KEY,
    experiment_id       VARCHAR(20) NOT NULL UNIQUE REFERENCES woos.experiment (experiment_id),
    model_name          VARCHAR(20) NOT NULL,
    model_version       VARCHAR(10) NOT NULL,
    dataset_version     VARCHAR(40) NOT NULL REFERENCES woos.dataset_version (dataset_version),
    feature_version     VARCHAR(10) NOT NULL,
    features_used       JSONB       NOT NULL,
    scaler              VARCHAR(20) NOT NULL,
    hyperparameters     JSONB       NOT NULL,
    metrics             JSONB       NOT NULL,
    validation_status   VARCHAR(30) NOT NULL CHECK (validation_status IN
                        ('EXPERIMENT', 'SELECTED_CANDIDATE', 'PENDING_BUSINESS_VALIDATION', 'APPROVED', 'REJECTED', 'RETIRED')),
    is_validated_model  BOOLEAN     NOT NULL DEFAULT FALSE,
    selection_decisions JSONB       NOT NULL DEFAULT '[]'::jsonb,
    approved_by         TEXT,
    approved_on         DATE,
    trained_at          TIMESTAMPTZ NOT NULL,
    published_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_validated_requires_approved CHECK (NOT is_validated_model OR validation_status = 'APPROVED')
);
-- Maksimal satu Validated Model per dataset (PRD §51, §64).
CREATE UNIQUE INDEX IF NOT EXISTS uq_model_validated_per_dataset
    ON woos.model (dataset_version) WHERE is_validated_model;

CREATE TABLE IF NOT EXISTS woos.cluster_profile (
    model_id                          INTEGER     NOT NULL REFERENCES woos.model (model_id) ON DELETE CASCADE,
    cluster_id                        INTEGER     NOT NULL,          -- -1 = noise (DBSCAN)
    cluster_code                      VARCHAR(30) NOT NULL,
    cluster_label                     TEXT        NOT NULL,
    prd_archetype                     TEXT,
    is_business_label                 BOOLEAN     NOT NULL,          -- true hanya untuk model APPROVED
    organization_count                INTEGER     NOT NULL,
    organization_share                NUMERIC(6, 4) NOT NULL,
    mean_ftk                          NUMERIC(10, 3),
    mean_realization                  NUMERIC(10, 3),
    mean_gap                          NUMERIC(10, 3),
    mean_fulfillment                  NUMERIC(10, 4),
    median_fulfillment                NUMERIC(10, 4),
    mean_staffing_ratio               NUMERIC(10, 4),
    mean_position_count               NUMERIC(10, 3),
    mean_vacant_position              NUMERIC(10, 3),
    mean_vacant_share                 NUMERIC(8, 4),
    mean_avg_realization_per_position NUMERIC(10, 3),
    sum_ftk                           INTEGER,
    sum_realization                   INTEGER,
    sum_gap                           INTEGER,
    characteristics                   JSONB       NOT NULL DEFAULT '[]'::jsonb,
    interpretation                    TEXT,
    centroid                          JSONB,
    PRIMARY KEY (model_id, cluster_id)
);

CREATE TABLE IF NOT EXISTS woos.cluster_result (
    model_id            INTEGER     NOT NULL REFERENCES woos.model (model_id) ON DELETE CASCADE,
    experiment_id       VARCHAR(20) NOT NULL,
    dataset_version     VARCHAR(40) NOT NULL,
    period              DATE        NOT NULL,
    organization_id     VARCHAR(20) NOT NULL,
    segmentation_status VARCHAR(20) NOT NULL CHECK (segmentation_status IN ('SEGMENTED', 'NOT_SEGMENTED')),
    cluster_id          INTEGER,
    cluster_code        VARCHAR(30) NOT NULL,
    cluster_label       TEXT        NOT NULL,
    cluster_distance    NUMERIC(10, 4),
    is_atypical_member  BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (model_id, organization_id),
    FOREIGN KEY (dataset_version, organization_id) REFERENCES woos.organization (dataset_version, organization_id),
    CONSTRAINT chk_segmented_has_cluster CHECK ((segmentation_status = 'SEGMENTED') = (cluster_id IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS idx_cluster_result_cluster ON woos.cluster_result (model_id, cluster_id);
