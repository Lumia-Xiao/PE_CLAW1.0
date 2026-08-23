from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.libraries.magnetics.normalized_backend_loader import normalized_openmagnetics_to_engine_dataframes
from pe_claw_gui.libraries.magnetics.normalized_inventory import build_normalized_openmagnetics_inventory


def test_normalized_magnetic_library_schema_loads_engine_dataframes() -> None:
    cores, materials, wires = normalized_openmagnetics_to_engine_dataframes()

    assert not cores.empty
    assert not materials.empty
    assert not wires.empty
    assert {"Ae", "Aw", "Ve", "le", "mlt", "gross_volume", "Ap"}.issubset(cores.columns)
    assert {"B_sat", "B_sat_100c", "steinmetz_ranges"}.issubset(materials.columns)
    assert {"d_strand", "bundle_copper_area", "outer_diameter"}.issubset(wires.columns)


def test_normalized_magnetic_library_inventory_reports_provenance_and_units() -> None:
    inventory = build_normalized_openmagnetics_inventory()

    assert inventory.core_shape_count == 890
    assert inventory.material_count == 411
    assert inventory.wire_count == 4352
    assert inventory.provenance_coverage_percent == 100.0
    assert inventory.unit_field_coverage_percent > 70.0
