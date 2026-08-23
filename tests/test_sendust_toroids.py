from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from pe_claw_gui.libraries.magnetics.sendust_toroids import (
    filter_sendust_toroid_cores_by_permeability,
    list_sendust_toroid_cores,
    list_sendust_toroid_sizes,
)
from pe_claw_gui.models.ac_dc_reactor import AcDcReactorCandidate, AcDcReactorDesignRequest


def test_packaged_sendust_toroid_core_variants_include_al_and_geometry() -> None:
    cores = list_sendust_toroid_cores()

    assert len(cores) == 567
    assert len({core.part_number for core in cores}) == len(cores)
    assert all(core.al_nh_per_turn2 > 0.0 for core in cores)
    assert all(core.od_mm > core.id_mm > 0.0 for core in cores)
    assert all(core.ht_mm > 0.0 for core in cores)
    assert all(core.ae_cm2 > 0.0 for core in cores)
    assert all(core.le_cm > 0.0 for core in cores)
    assert all(core.ve_cm3 > 0.0 for core in cores)


def test_packaged_sendust_toroid_unique_sizes_are_available_from_small_to_large() -> None:
    sizes = list_sendust_toroid_sizes()

    assert len(sizes) == 61
    assert sizes[0].example_part == "MS-014014-8"
    assert sizes[0].od_mm == pytest.approx(3.556)
    assert sizes[0].id_mm == pytest.approx(1.778)
    assert sizes[-1].example_part == "MS-775014-2"
    assert sizes[-1].od_mm == pytest.approx(196.85)
    assert sizes[-1].id_mm == pytest.approx(146.05)
    assert all(size.permeabilities for size in sizes)


def test_sendust_toroid_core_unit_helpers_are_ready_for_turns_and_loss_calculation() -> None:
    core = next(item for item in list_sendust_toroid_cores() if item.part_number == "MS-014060-8")

    assert core.relative_permeability == pytest.approx(60.0)
    assert core.al_nh_per_turn2 == pytest.approx(13.0)
    assert core.al_h_per_turn2 == pytest.approx(13.0e-9)
    assert core.ae_m2 == pytest.approx(0.0137e-4)
    assert core.ve_m3 == pytest.approx(0.0107e-6)
    assert core.mean_length_per_turn_m == pytest.approx(math.pi * ((3.556 + 1.778) * 0.5e-3))
    assert core.window_area_mm2 == pytest.approx(math.pi * (1.778 * 0.5) ** 2)


def test_filter_sendust_toroid_cores_by_permeability_matches_material_family() -> None:
    cores = list_sendust_toroid_cores()

    ms60 = filter_sendust_toroid_cores_by_permeability(cores, 60.0)

    assert ms60
    assert all(core.relative_permeability == pytest.approx(60.0) for core in ms60)
    assert {core.part_number for core in ms60}.issubset({core.part_number for core in cores})


def test_ac_dc_reactor_models_preserve_low_frequency_selection_contract() -> None:
    request = AcDcReactorDesignRequest(
        topology_id="single_phase_diode_bridge_rectifier_dc_inductor_filter",
        display_name="Single-phase diode bridge rectifier with DC inductor filter",
        required_inductance_h=0.1,
        f_line_hz=50.0,
        ripple_frequency_hz=100.0,
        idc_a=5.0,
        i_rms_a=5.1,
        i_peak_a=7.5,
        i_valley_a=2.5,
        delta_i_pp_a=5.0,
        vdc_est_v=300.0,
        throughput_power_w=1500.0,
    )
    candidate = AcDcReactorCandidate(
        candidate_id="MS-520060-2_N900",
        core_part_number="MS-520060-2",
        material_id="ms_60",
        material_name="MS-60 Sendust",
        relative_permeability=60.0,
        turns=900,
        inductance_h=0.10044,
        effective_inductance_h=0.060264,
        al_dc_derating_factor=0.6,
        od_mm=132.5372,
        id_mm=78.5876,
        ht_mm=20.32,
        ae_cm2=5.35,
        le_cm=32.4,
        ve_cm3=173.0,
    )

    assert request.material_family == "sendust"
    assert request.core_shape == "toroid"
    assert candidate.effective_inductance_h < candidate.inductance_h
    assert candidate.al_dc_derating_factor == pytest.approx(0.6)
