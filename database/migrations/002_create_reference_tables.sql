-- 002 — Versi dataset, master organisasi, feature organisasi (PRD §17, §59–§60, §72).

CREATE TABLE IF NOT EXISTS woos.dataset_version (
    dataset_version   VARCHAR(40) PRIMARY KEY,
    source_file       TEXT        NOT NULL,
    source_sha256     CHAR(64)    NOT NULL,
    scope             TEXT        NOT NULL,
    period            DATE        NOT NULL,
    status            VARCHAR(20) NOT NULL CHECK (status IN ('ACTIVE', 'SUPERSEDED')),
    position_rows     INTEGER     NOT NULL CHECK (position_rows >= 0),
    organization_rows INTEGER     NOT NULL CHECK (organization_rows >= 0),
    published_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS woos.organization (
    dataset_version        VARCHAR(40) NOT NULL REFERENCES woos.dataset_version (dataset_version),
    organization_id        VARCHAR(20) NOT NULL,
    organization_name      TEXT        NOT NULL,
    parent_organization_id VARCHAR(20),
    parent_status          VARCHAR(20) NOT NULL,
    organization_level     SMALLINT    NOT NULL,
    directorate_id         VARCHAR(20),
    directorate_name       TEXT,
    directorate_source     VARCHAR(30),
    is_virtual_container   BOOLEAN     NOT NULL DEFAULT FALSE,
    is_leaf                BOOLEAN     NOT NULL,
    n_children             INTEGER     NOT NULL DEFAULT 0,
    PRIMARY KEY (dataset_version, organization_id)
);
CREATE INDEX IF NOT EXISTS idx_organization_directorate ON woos.organization (dataset_version, directorate_id);
CREATE INDEX IF NOT EXISTS idx_organization_parent ON woos.organization (dataset_version, parent_organization_id);

-- Feature per organisasi hasil pipeline (unit direct). Dashboard membaca nilai ini, tidak menghitung sendiri.
CREATE TABLE IF NOT EXISTS woos.organization_feature (
    dataset_version              VARCHAR(40) NOT NULL,
    feature_version              VARCHAR(10) NOT NULL,
    organization_id              VARCHAR(20) NOT NULL,
    unit_definition              VARCHAR(10) NOT NULL CHECK (unit_definition IN ('direct', 'rollup')),
    ftk                          INTEGER     NOT NULL,
    realization                  INTEGER     NOT NULL,
    gap                          INTEGER     NOT NULL,
    fulfillment_ratio            NUMERIC(10, 4),            -- NULL bila FTK = 0 (D-003)
    staffing_ratio               NUMERIC(10, 4),            -- NULL bila FTK = 0 (D-003)
    balance_index                NUMERIC(8, 4) NOT NULL,
    position_rows                INTEGER     NOT NULL,
    position_count               INTEGER     NOT NULL,
    dormant_position_count       INTEGER     NOT NULL,
    vacant_position_count        INTEGER     NOT NULL,
    vacant_share                 NUMERIC(8, 4) NOT NULL,
    avg_realization_per_position NUMERIC(10, 4) NOT NULL,
    unbudgeted_filled_count      INTEGER     NOT NULL,
    marked_position_count        INTEGER     NOT NULL,
    extreme_position_count       INTEGER     NOT NULL,
    grade_distribution           JSONB       NOT NULL,      -- pct_/ftk_/real_ per kelompok jenjang (PRD §12, §60)
    in_model_population          BOOLEAN     NOT NULL,
    PRIMARY KEY (dataset_version, feature_version, organization_id, unit_definition),
    FOREIGN KEY (dataset_version, organization_id) REFERENCES woos.organization (dataset_version, organization_id)
);
