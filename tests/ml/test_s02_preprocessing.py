import pandas as pd
import pytest

from s01_data_understanding import parse_grade
from s02_preprocessing import (add_virtual_containers, ancestors, assign_directorate, map_grade,
                               normalize_text, position_flags)


def test_normalize_text_collapses_tabs_and_spaces():
    assert normalize_text("OFFICER\tVERIFIKASI") == "OFFICER VERIFIKASI"
    assert normalize_text("  A   B ") == "A B"
    assert pd.isna(normalize_text(None))


@pytest.mark.parametrize("label, expected", [
    ("MANAJEMEN DASAR (MD) - 16", ("MD", 16)),
    ("GENERALIST 1 (G1) - 08", ("G1", 8)),
    ("JUNIOR EXPERT (JE) - 15", ("JE", 15)),
    ("VP", ("VP", None)),
    (None, (None, None)),
])
def test_parse_grade(label, expected):
    assert parse_grade(label) == expected


@pytest.mark.parametrize("label, group", [
    ("MANAJEMEN ATAS KHUSUS (MAK) - 25", "MAK"),
    ("SENIOR SPECIALIST (SSP) - 18", "SPESIALIS"),
    ("GENERALIST 3 (G3) - 14", "GENERALIS"),
    ("VP", "MM"),
    ("AM", "GENERALIS"),
    ("JUNIOR EXPERT (JE) - 15", "SPESIALIS"),
    (None, "UNKNOWN"),
    ("LABEL ASING", "UNKNOWN"),
])
def test_map_grade_group(label, group):
    assert map_grade(label)[2] == group


def test_position_flags_edge_cases():
    assert position_flags(0, 0)["is_dormant"] and not position_flags(0, 0)["is_active"]
    assert position_flags(0, 2)["is_unbudgeted_filled"]
    assert position_flags(3, 0)["is_vacant"]
    assert position_flags(1, 5)["is_extreme_realization"]
    assert not position_flags(4, 9)["is_extreme_realization"]  # 9 < 3*4
    assert position_flags(0, 5)["is_extreme_realization"]      # FTK 0 -> dibanding 3*1


def _orgs():
    return pd.DataFrame([
        ("R", "ROOT", "PLN", "X", 2),
        ("D1", "DIR 1", "ROOT", "R", 3),
        ("U1", "DIV A", "DIR UTAMA", "D0", 4),   # parent D0 tidak punya baris jabatan
        ("S1", "SUB A", "DIV A", "U1", 5),
        ("B1", "BIDANG B", "DIR 1", "D1", 4),
        ("O1", "ORPHAN", "WADAH", "W1", 6),     # parent W1 (level 5) tidak ada
    ], columns=["organization_id", "organization_name", "parent_name", "parent_organization_id",
                "organization_level"])


def test_virtual_containers_added_with_inferred_level_and_parent():
    o = add_virtual_containers(_orgs()).set_index("organization_id")
    assert o.loc["D0", "is_virtual_container"] and o.loc["D0", "organization_level"] == 3
    assert o.loc["D0", "parent_organization_id"] == "R" and o.loc["D0", "parent_status"] == "INFERRED_ROOT"
    assert o.loc["W1", "organization_level"] == 5 and o.loc["W1", "parent_status"] == "UNKNOWN"
    assert o.loc["R", "parent_status"] == "OUT_OF_SCOPE"
    assert "X" not in o.index  # parent root di luar cakupan tidak dibuat


def test_assign_directorate_hierarchy_root_fallback_and_consensus():
    o = assign_directorate(add_virtual_containers(_orgs()), fallback={"O1": "D1"}).set_index("organization_id")
    assert o.loc["S1", "directorate_id"] == "D0" and o.loc["S1", "directorate_source"] == "HIERARCHY"
    assert o.loc["B1", "directorate_id"] == "D1"
    assert o.loc["R", "directorate_source"] == "ROOT"
    assert o.loc["O1", "directorate_source"] == "FALLBACK_V1_MEMBERSHIP"
    assert o.loc["W1", "directorate_id"] == "D1" and o.loc["W1", "directorate_source"] == "CHILDREN_CONSENSUS"


def test_ancestors_detects_cycle():
    with pytest.raises(ValueError):
        ancestors("A", {"A": "B", "B": "A"})
