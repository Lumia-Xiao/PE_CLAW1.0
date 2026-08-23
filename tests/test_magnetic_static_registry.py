from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.engines.magnetics.allow_profiles import get_default_allow_profile
from pe_claw_gui.libraries.magnetics.normalized_backend_loader import normalized_openmagnetics_to_engine_dataframes


def test_packaged_normalized_records_cover_representative_engine_fields() -> None:
    cores, materials, wires = normalized_openmagnetics_to_engine_dataframes()

    assert {"E 19/8/5", "E 42/21/15", "ETD 39/20/13", "PQ 40/40", "RM 14", "T 22/14/6.4", "U 93/76/30"}.intersection(
        set(str(item) for item in cores.index)
    )
    assert {"AF", "N87", "N97", "3C95", "PC47"}.intersection(set(str(item) for item in materials.index))
    assert wires.index.astype(str).str.contains("Litz", case=False).any()


def test_active_allow_profiles_remain_available_without_static_registry() -> None:
    for fs_hz in (10_000.0, 50_000.0, 300_000.0):
        active = get_default_allow_profile(fs_hz)

        assert active.band_name
        assert active.fs_min_hz <= fs_hz
        assert active.fs_max_hz > fs_hz
        assert active.b_allow_ratio_to_bsat_100c > 0.0
        assert active.j_allow_a_per_mm2 > 0.0
        assert active.fill_allow > 0.0
