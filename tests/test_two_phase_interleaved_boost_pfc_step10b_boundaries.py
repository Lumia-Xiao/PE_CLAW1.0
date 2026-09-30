from __future__ import annotations

from math import isclose, sqrt

import pytest

from pe_claw_gui.topologies.ac_dc.single_phase_interleaved_boost_pfc_diode_bridge import (
    build_default_inputs,
    build_spec,
    synthesize,
)


def _candidate(raw: dict[str, str] | None = None):
    inputs = build_default_inputs()
    if raw:
        inputs.update(raw)
    spec = build_spec(inputs)
    return spec, synthesize(spec)


def test_step10b_records_all_line_condition_current_and_ripple_metrics() -> None:
    spec, candidate = _candidate()
    metadata = candidate.metadata
    metrics = metadata["line_condition_metrics"]

    assert set(metrics) == {"nominal", "low_line", "high_line"}
    assert metrics["low_line"]["input_current_rms_a"] > metrics["nominal"]["input_current_rms_a"] > metrics["high_line"]["input_current_rms_a"]
    for condition, expected_vac in (("nominal", 230.0), ("low_line", 180.0), ("high_line", 265.0)):
        row = metrics[condition]
        assert row["vac_rms_v"] == pytest.approx(expected_vac)
        assert row["vac_peak_v"] == pytest.approx(expected_vac * sqrt(2.0))
        assert row["phase_current_share"] == pytest.approx(0.5)
        assert row["phase_current_peak_a"] == pytest.approx(row["input_current_peak_a"] / 2.0)
        assert row["phase_current_rms_a"] == pytest.approx(row["input_current_rms_a"] / 2.0, rel=2e-3)
        assert row["phase_current_average_a"] < row["phase_current_rms_a"]
        assert row["phase_ripple_allowed_pp_a"] > 0.0
        assert row["phase_ripple_actual_pp_max_a"] > 0.0
        assert row["line_cycle_point_count"] == 181

    assert metrics["low_line"]["phase_current_rms_with_switching_ripple_a"] > metrics["low_line"]["phase_current_rms_a"]
    assert metadata["line_condition_metrics"]["low_line"]["phase_ripple_actual_pp_max_a"] == pytest.approx(
        metadata["inductor_ripple_worst_case_a"]
    )
    assert isclose(
        metadata["phase_current_rms_a"]["phase_1"],
        metrics["nominal"]["phase_current_rms_a"],
        rel_tol=2e-3,
    )
    assert spec.metadata["phase_count"] == 2


def test_step10b_records_separate_current_and_voltage_design_boundaries() -> None:
    _, candidate = _candidate()
    basis = candidate.metadata["design_boundary_basis"]

    assert basis["inductor"] == {
        "current_design_basis": "low_line_phase_current_envelope_and_allowed_ripple",
        "voltage_design_basis": "low_line_rectified_line_cycle_volt_second",
        "line_condition": "low_line",
    }
    assert basis["power_devices"]["current_line_condition"] == "low_line"
    assert basis["power_devices"]["voltage_line_condition"] == "high_line"
    assert basis["input_bridge"]["current_line_condition"] == "low_line"
    assert basis["input_bridge"]["voltage_line_condition"] == "high_line"
    assert "low_line" in basis["power_devices"]["current_design_basis"]
    assert "high_line" in basis["power_devices"]["voltage_design_basis"]
