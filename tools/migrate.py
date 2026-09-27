"""Migration runner WOOS: menerapkan database/migrations/NNN_*.sql berurutan, sekali saja.

- Setiap file dicatat di woos.schema_migrations beserta checksum SHA-256.
- File yang sudah diterapkan tetapi isinya berubah -> error (buat migration baru, jangan edit).
- Setiap migration berjalan dalam satu transaksi.

Jalankan:  ml/.venv/bin/python tools/migrate.py [--database=woos_test] [--create-db]
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml" / "pipeline"))
from db import connect, load_env  # noqa: E402

MIGRATIONS = ROOT / "database" / "migrations"
PATTERN = re.compile(r"^(\d{3})_[a-z0-9_]+\.sql$")


def migration_files(folder=MIGRATIONS):
    files = sorted(p for p in folder.iterdir() if PATTERN.match(p.name))
    numbers = [int(PATTERN.match(p.name).group(1)) for p in files]
    if numbers != list(range(1, len(numbers) + 1)):
        raise SystemExit(f"Nomor migration tidak berurutan: {numbers}")
    return files


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_database(name):
    conn = connect("postgres")
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
        if not cur.fetchone():
            cur.execute(f'CREATE DATABASE "{name}"')
            print(f"created database {name}")
    conn.close()


def migrate(database=None):
    conn = connect(database)
    applied = {}
    with conn, conn.cursor() as cur:
        cur.execute("SELECT to_regclass('woos.schema_migrations')")
        if cur.fetchone()[0]:
            cur.execute("SELECT version, checksum FROM woos.schema_migrations")
            applied = dict(cur.fetchall())
    done = []
    for path in migration_files():
        version, digest = path.stem, checksum(path)
        if version in applied:
            if applied[version] != digest:
                raise SystemExit(f"{path.name} sudah diterapkan tetapi isinya berubah. Buat migration baru.")
            continue
        with conn, conn.cursor() as cur:
            cur.execute(path.read_text())
            cur.execute("INSERT INTO woos.schema_migrations (version, checksum) VALUES (%s, %s)", (version, digest))
        done.append(path.name)
    conn.close()
    return done


if __name__ == "__main__":
    db = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--database=")), None)
    if "--create-db" in sys.argv:
        create_database(db or load_env()["DB_NAME"])
    applied = migrate(db)
    print("applied:", applied or "nothing (up to date)")
