"""Konfigurasi bersama pipeline ML WOOS (path, versi dataset, seed, mapping kolom)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUTS = ROOT / "ml" / "outputs"
RANDOM_SEED = 42

# Registri dataset. Satu dataset ACTIVE dipakai pipeline; versi lama disimpan untuk jejak audit.
DATASETS = {
    "v1": {"version": "DLMHC-2026-09-25-v1", "status": "SUPERSEDED",
           "file": ROOT / "data" / "raw" / "direktorat_legal_manajemen_human_capital.csv",
           "scope": "Direktorat Legal dan Manajemen Human Capital"},
    "v2": {"version": "KP-2026-09-25-v2", "status": "ACTIVE",
           "file": ROOT / "data" / "raw" / "kantor_pusat_semua_direktorat.csv",
           "scope": "PT PLN (Persero) Kantor Pusat — seluruh direktorat"},
}
ACTIVE_DATASET = "v2"


def dataset(key=None):
    """Dataset dari argumen CLI `--dataset=v1|v2`, argumen fungsi, atau ACTIVE_DATASET."""
    for arg in sys.argv[1:]:
        if arg.startswith("--dataset="):
            key = arg.split("=", 1)[1]
    return DATASETS[key or ACTIVE_DATASET]


# Nama kolom sumber -> nama kolom internal (snake_case, bahasa Inggris seperti PRD §17)
COLUMN_MAP = {
    "ID Organisasi": "organization_id",
    "Nama Organisasi": "organization_name",
    "Parent Organisasi": "parent_name",
    "ID Parent": "parent_organization_id",
    "Level Organisasi": "organization_level",
    "ID Jabatan": "position_id",
    "Nama Jabatan": "position_name",
    "Jenjang Jabatan": "grade",
    "FTK Jabatan": "ftk",
    "Realisasi Jabatan": "realization",
    "Periode Data": "period",
}

# Kelompok jenjang (PRD §12). VP->MM (D-004); AM->GENERALIS (D-004 revisi, bukti v2: jabatan
# "ASSISTANT MANAGER" berlabel standar 100% G3); JE->SPESIALIS (D-013).
GRADE_GROUP = {"MAK": "MAK", "MA": "MA", "MM": "MM", "VP": "MM", "MD": "MD", "AM": "GENERALIS",
               "SSP": "SPESIALIS", "SPC": "SPESIALIS", "JE": "SPESIALIS",
               "G1": "GENERALIS", "G2": "GENERALIS", "G3": "GENERALIS", None: "UNKNOWN"}
GRADE_GROUPS = ["MAK", "MA", "MM", "MD", "SPESIALIS", "GENERALIS", "UNKNOWN"]
