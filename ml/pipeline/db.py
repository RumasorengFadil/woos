"""Koneksi PostgreSQL untuk pipeline. Konfigurasi dari .env (blueprint: config via .env)."""
import os
from pathlib import Path

from config import ROOT


def load_env(path=ROOT / ".env"):
    """Parser .env minimal (KEY=VALUE, komentar #, tanda kutip opsional). Variabel OS menang."""
    env = {}
    if Path(path).exists():
        for line in Path(path).read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    env.update({k: v for k, v in os.environ.items() if k.startswith(("DB_", "APP_"))})
    return env


def connect(database=None):
    import psycopg2

    env = load_env()
    return psycopg2.connect(host=env.get("DB_HOST", "127.0.0.1"), port=int(env.get("DB_PORT", 5432)),
                            dbname=database or env["DB_NAME"], user=env.get("DB_USER"),
                            password=env.get("DB_PASSWORD") or None)
