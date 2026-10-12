from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import (  # noqa: E402
    build_default_inputs,
    build_spec,
    calculate_three_phase_three_level_t_type_inverter,
    synthesize,
)


def _default_estimates(**overrides: float | str) -> dict[str, object]:
    raw = build_default_inputs()
    raw.update({key: str(value) for key, value in overrides.items()})
    spec = build_spec(raw)
    return calculate_three_phase_three_level_t_type_inverter(
        vdc_nom_v=float(spec.metadata["vdc_nom_v"]),
        vac_ll_rms_v=float(spec.metadata["vac_ll_rms_v"]),
        f_line_hz=float(spec.metadata["f_line_hz"]),
        fsw_hz=float(spec.metadata["fsw_hz"]),
        pout_w=float(spec.metadata["pout_w"]),
        power_factor=float(spec.metadata["power_factor"]),
        power_factor_phase=str(spec.metadata["power_factor_phase"]),
        inductor_current_ripple_ratio=float(spec.metadata["inductor_current_ripple_ratio"]),
        dc_link_voltage_ripple_ratio=float(spec.metadata["dc_link_voltage_ripple_ratio"]),
    )


def test_b1_independent_scalar_reference_matches_contract() -> None:
    estimates = _default_estimates()
    assert estimates["vac_phase_rms_v"] == pytest.approx(230.94010767585033, rel=1e-12)
    assert estimates["i_phase_rms_a"] == pytest.approx(14.433756729740645, rel=1e-12)
    assert estimates["i_phase_peak_a"] == pytest.approx(20.412414523193153, rel=1e-12)
    assert estimates["delta_il_pp_a"] == pytest.approx(4.08248290463863, rel=1e-12)
    assert estimates["l_phase_h"] == pytest.approx(1.0716517624676405e-3, rel=1e-12)
    assert estimates["ceq_proxy_f"] == pytest.approx(40.81632653061225e-6, rel=1e-12)
    assert estimates["cbank_proxy_f"] == pytest.approx(81.6326530612245e-6, rel=1e-12)
    assert estimates["modulation_index_command"] == pytest.approx(0.9333455044846178, rel=1e-12)
    assert estimates["modulation_valid"] is True


@pytest.mark.parametrize(
    ("phase", "expected_l", "expected_m"),
    [
        ("lagging", 0.8573214099741122e-3, 0.9450504744502837),
        ("leading", 0.8573214099741122e-3, 0.9214918676931367),
    ],
)
def test_pf_phase_is_signed_in_the_voltage_drop_reference(phase: str, expected_l: float, expected_m: float) -> None:
    estimates = _default_estimates(power_factor="0.8", power_factor_phase=phase)
    assert estimates["power_factor_phase"] == phase
    assert estimates["power_factor_phase_angle_rad"] == pytest.approx(
        (1.0 if phase == "lagging" else -1.0) * math.acos(0.8), rel=1e-12
    )
    assert estimates["l_phase_h"] == pytest.approx(expected_l, rel=1e-12)
    assert estimates["modulation_index_command"] == pytest.approx(expected_m, rel=1e-12)
    assert estimates["i_phasor_imag_a"] < 0.0 if phase == "lagging" else estimates["i_phasor_imag_a"] > 0.0


def test_synthesize_maps_estimates_to_candidate_without_hardware_results() -> None:
    candidate = synthesize(build_spec(build_default_inputs()))
    assert candidate.topology_id == "three_phase_three_level_t_type_inverter"
    assert candidate.vin_min == candidate.vin_max == candidate.vin_nom == 700.0
    assert candidate.vout_target == 400.0
    assert candidate.iout == pytest.approx(14.433756729740645, rel=1e-12)
    assert candidate.inductance_h == pytest.approx(1.0716517624676405e-3, rel=1e-12)
    assert candidate.capacitance_f == pytest.approx(81.6326530612245e-6, rel=1e-12)
    assert candidate.metadata["t_type_design_estimates"]["model_scope"].endswith("balanced_split_bus")
    assert len(candidate.metadata["per_position_current_peak_estimate_a"]) == 12
    assert "semiconductor_selection_status" not in candidate.metadata
    assert all("selected" not in note.lower() for note in candidate.notes)


def test_low_bus_design_is_explicitly_unreachable_without_clipping() -> None:
    raw = build_default_inputs()
    raw["vdc_nom"] = "500"
    candidate = synthesize(build_spec(raw))
    assert candidate.feasible is False
    assert candidate.failure_reason is not None
    assert "m_command" in candidate.failure_reason
    assert candidate.metadata["modulation_index_command"] > 1.0
    assert math.isfinite(candidate.inductance_h)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"vdc_nom_v": 0.0},
        {"vac_ll_rms_v": 0.0},
        {"f_line_hz": 0.0},
        {"fsw_hz": 0.0},
        {"pout_w": 0.0},
        {"power_factor": 0.0},
        {"inductor_current_ripple_ratio": 0.0},
        {"dc_link_voltage_ripple_ratio": 0.0},
        {"power_factor_phase": "quadrature"},
    ],
)
def test_synthesis_rejects_invalid_direct_arguments(kwargs: dict[str, float | str]) -> None:
    base = {
        "vdc_nom_v": 700.0,
        "vac_ll_rms_v": 400.0,
        "f_line_hz": 50.0,
        "fsw_hz": 20_000.0,
        "pout_w": 10_000.0,
        "power_factor": 1.0,
        "power_factor_phase": "lagging",
        "inductor_current_ripple_ratio": 0.2,
        "dc_link_voltage_ripple_ratio": 0.05,
    }
    base.update(kwargs)
    with pytest.raises(ValueError):
        calculate_three_phase_three_level_t_type_inverter(**base)


def test_candidate_metadata_is_copy_owned_and_has_explicit_target_semantics() -> None:
    candidate = synthesize(build_spec(build_default_inputs()))
    estimates = candidate.metadata["t_type_design_estimates"]
    estimates["power_factor"] = 0.25
    repeat = synthesize(build_spec(build_default_inputs()))
    assert repeat.metadata["t_type_design_estimates"]["power_factor"] == 1.0
    assert "target" in repeat.metadata["inductor_ripple_design_target_definition"]
    assert repeat.metadata["t_type_capacitor_basis"].startswith("Q_proxy")
