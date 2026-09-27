import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from s08_publish import PublishRefused, assert_publishable, clean, generic_label

ROOT = Path(__file__).resolve().parents[2]
PY = str(ROOT / "ml" / ".venv" / "bin" / "python")
sys.path.insert(0, str(ROOT / "tools"))


def test_publish_gate_requires_approved_and_matching_approval():
    ok = {"experiment_id": "EXP-KM-067", "validation_status": "APPROVED"}
    assert assert_publishable(ok, {"experiment_id": "EXP-KM-067"})
    with pytest.raises(PublishRefused):
        assert_publishable({**ok, "validation_status": "PENDING_BUSINESS_VALIDATION"}, {"experiment_id": "EXP-KM-067"})
    with pytest.raises(PublishRefused):
        assert_publishable(ok, None)
    with pytest.raises(PublishRefused):
        assert_publishable(ok, {"experiment_id": "EXP-KM-001"})


def test_clean_converts_numpy_and_non_finite():
    assert clean(np.int64(3)) == 3 and isinstance(clean(np.int64(3)), int)
    assert clean(np.float64(np.nan)) is None and clean(float("inf")) is None
    assert clean(np.bool_(True)) is True and clean("x") == "x"


def test_generic_label_for_comparison_models():
    assert generic_label(-1) == ("NOISE", "Noise") and generic_label(2) == ("C2", "Cluster 2")


def test_migration_files_are_sequential():
    from migrate import migration_files
    names = [p.name for p in migration_files()]
    assert names[0].startswith("001_") and all(n[:3] == f"{i + 1:03d}" for i, n in enumerate(names))


# ---------------------------------------------------------------- integration (PostgreSQL lokal)

def _db_available():
    try:
        from db import connect
        connect("postgres").close()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _db_available(), reason="PostgreSQL tidak tersedia")
def test_migrate_and_publish_into_test_database():
    from db import connect
    run = lambda *a: subprocess.run([PY, *a], cwd=ROOT, capture_output=True, text=True)  # noqa: E731
    r1 = run("tools/migrate.py", "--database=woos_test", "--create-db")
    assert r1.returncode == 0, r1.stderr
    r2 = run("tools/migrate.py", "--database=woos_test")
    assert "up to date" in r2.stdout                          # idempotent
    for _ in range(2):                                         # publish idempotent
        p = run("ml/pipeline/s08_publish.py", "--database=woos_test")
        assert p.returncode == 0, p.stderr[-2000:]
        assert all(json.loads(p.stdout)["checks"].values())
    conn = connect("woos_test")
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM woos.model")
        assert cur.fetchone()[0] == 3                          # tidak bertambah setelah publish ulang
        cur.execute("SELECT cluster_label, count(*) FROM woos.v_validated_organization GROUP BY 1")
        counts = dict(cur.fetchall())
        assert counts["Relatif Stabil"] == 537 and counts["Tidak Tersegmentasi"] == 21
    # constraint: model non-APPROVED tidak boleh menjadi validated model
    import psycopg2
    with pytest.raises(psycopg2.errors.CheckViolation):
        with conn, conn.cursor() as cur:
            cur.execute("UPDATE woos.model SET is_validated_model = true WHERE validation_status = 'EXPERIMENT'")
    # constraint: maksimal satu validated model per dataset
    with pytest.raises(psycopg2.errors.UniqueViolation):
        with conn, conn.cursor() as cur:
            cur.execute("UPDATE woos.model SET validation_status = 'APPROVED' WHERE validation_status = 'EXPERIMENT'")
            cur.execute("UPDATE woos.model SET is_validated_model = true WHERE NOT is_validated_model")
    conn.close()
