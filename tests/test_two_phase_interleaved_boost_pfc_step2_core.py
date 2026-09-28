from __future__ import annotations

from math import isclose, sqrt

import pytest

from pe_claw_gui.topologies.ac_dc.single_phase_interleaved_boost_pfc_diode_bridge import (
    build_default_inputs,
    build_spec,
    synthesize,
)
from pe_claw_gui.topologies.ac_dc.single_phase_interleaved_boost_pfc_diode_bridge.interleaving import (
    calculate_interleaved_ripple,
    interleaved_cancellation_factor,
)
from pe_claw_gui.topologies.ac_dc.single_phase_interleaved_boost_pfc_diode_bridge.line_cycle import (
    sample_interleaved_boost_pfc_line_cycle,
)


def _candidate(raw: dict[str, str] | None = None):
    inputs = build_default_inputs()
    if raw:
        inputs.update(raw)
    spec = build_spec(inputs)
    return spec, synthesize(spec)


def test_step2_input_schema_reuses_boost_fields_without_efficiency_or_phase_inputs() -> None:
    defaults = build_default_inputs()

    assert "sizing_efficiency_assumption" not in defaults
    assert "phase_count" not in defaults
    assert "phase_shift_deg" not in defaults
    assert defaults["input_inductance_h"] == "0.0001"

    spec = build_spec(defaults)
    assert spec.topology_id == "single_phase_interleaved_boost_pfc_diode_bridge"
    assert spec.metadata["contract_version"] == "two_phase_interleaved_boost_pfc_contract_v1"
    assert spec.metadata["phase_count"] == 2
    assert spec.metadata["phase_shift_deg"] == 180.0
    assert spec.metadata["input_inductance_role"] == "per_phase_series_input_inductance"
    assert "sizing_efficiency_assumption" not in spec.metadata


def test_line_cycle_has_zero_crossing_peak_and_ideal_equal_phase_current() -> None:
    line_cycle = sample_interleaved_boost_pfc_line_cycle(
        vac_rms_v=230.0,
        vdc_target_v=400.0,
        input_current_rms_a=10.0,
        ripple_current_ratio=0.3,
    )

    assert line_cycle.point_count == 181
    assert line_cycle.total_input_current_a[0] == pytest.approx(0.0)
    assert line_cycle.total_input_current_a[-1] == pytest.approx(0.0)
    assert line_cycle.total_input_current_a[90] == pytest.approx(sqrt(2.0) * 10.0)
    assert line_cycle.phase_current_a[90] == pytest.approx(sqrt(2.0) * 10.0 / 2.0)
    assert line_cycle.phase_current_a[90] * 2.0 == pytest.approx(line_cycle.total_input_current_a[90])
    assert line_cycle.delta_i_allowed_a[90] == pytest.approx(sqrt(2.0) * 10.0 / 2.0 * 0.3)
    assert 0.0 <= min(line_cycle.duty) <= max(line_cycle.duty) <= 1.0


def test_180_degree_interleaving_cancels_identical_ripple_at_half_duty() -> None:
    assert interleaved_cancellation_factor(0.5) == pytest.approx(0.0)
    assert interleaved_cancellation_factor(0.25) == pytest.approx(0.5)
    result = calculate_interleaved_ripple(
        duty=[0.25, 0.5, 0.75],
        phase_ripple_pp_a=[4.0, 4.0, 4.0],
    )
    assert result.cancellation_factor == pytest.approx([0.5, 0.0, 0.5])
    assert result.aggregate_ripple_pp_a == pytest.approx([2.0, 0.0, 2.0])


def test_step2_synthesis_reports_per_phase_and_aggregate_quantities() -> None:
    spec, candidate = _candidate()
    metadata = candidate.metadata

    expected_input_rms = spec.pout / (
        float(spec.metadata["vac_rms_v"]) * float(spec.metadata["power_factor_target"])
    )
    assert candidate.feasible is True
    assert candidate.ccm_valid is True
    assert metadata["electrical_input_current_rms_a"] == pytest.approx(expected_input_rms)
    assert metadata["phase_current_rms_a"] == pytest.approx(
        {"phase_1": expected_input_rms / 2.0, "phase_2": expected_input_rms / 2.0}
    )
    assert candidate.inductance_h == pytest.approx(metadata["phase_total_series_inductance_h"]["phase_1"])
    assert metadata["phase_boost_inductance_h"]["phase_1"] + float(metadata["input_inductance_h"]) == pytest.approx(
        candidate.inductance_h
    )
    assert metadata["phase_line_cycle"]["phase_1"]["phase_current_a"] == metadata["phase_line_cycle"]["phase_2"]["phase_current_a"]
    assert metadata["interleaved_ripple"]["phase_shift_deg"] == 180.0
    assert metadata["formula_basis"]["phase_inductance"]["unit"] == "H"


def test_low_line_sizes_inductor_and_high_line_sets_bus_feasibility() -> None:
    _, candidate = _candidate()
    metadata = candidate.metadata
    assert metadata["inductor_design_line"] == "low_line"
    assert metadata["low_line_line_cycle"]["v_rectified_v"][90] == pytest.approx(180.0 * sqrt(2.0))
    assert metadata["high_line_line_cycle"]["v_rectified_v"][90] == pytest.approx(265.0 * sqrt(2.0))
    assert metadata["vdc_feasibility_passed"] is True

    _, below_high_line = _candidate({"vdc_target_v": "375"})
    assert below_high_line.feasible is False
    assert below_high_line.ccm_valid is False
    assert below_high_line.failure_reason == "interleaved_boost_pfc_dc_bus_below_high_line_peak"
    assert isclose(float(below_high_line.metadata["required_min_vdc_v"]), 1.02 * 265.0 * sqrt(2.0))
