-- 001 — Schema aplikasi WOOS + pencatat migration.
CREATE SCHEMA IF NOT EXISTS woos;

CREATE TABLE IF NOT EXISTS woos.schema_migrations (
    version     VARCHAR(64) PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    checksum    CHAR(64)    NOT NULL
);
