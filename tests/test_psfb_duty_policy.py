from __future__ import annotations

import math

import pytest

from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.pipeline.run_operating_point_refresh import run_operating_point_refresh
from pe_claw_gui.topologies.dc_dc.phase_shifted_full_bridge_diode_rectifier_isolated import input_schema
from pe_claw_gui.topologies.dc_dc.phase_shifted_full_bridge_diode_rectifier_isolated.synthesizer import synthesize
from pe_claw_gui.topologies.dc_dc.phase_shifted_full_bridge_diode_rectifier_isolated.stress import extract_stress
from pe_claw_gui.topologies.dc_dc.phase_shifted_full_bridge_diode_rectifier_isolated.waveform import generate_waveforms
from pe_claw_gui.topologies.dc_dc.phase_shifted_full_bridge_diode_rectifier_isolated.duty_policy import (
    assess_psfb_duty,
    calculate_psfb_duty,
)


COMMON = {
    "vout_v": 400.0,
    "diode_drop_total_v": 2.0,
    "turns_ratio_np_ns": 1.2599403578528827,
    "leakage_h": 2.2e-6,
    "iout_a": 5.0,
    "fs_hz": 100_000.0,
    "max_effective_duty": 0.78,
    "max_command_duty": 0.90,
}


def test_nominal_low_high_line_have_ordered_duty_and_auditable_scope() -> None:
    nominal = calculate_psfb_duty(vin_v=750.0, scope="design_point", **COMMON)
    low_line = calculate_psfb_duty(vin_v=650.0, scope="operating_point", **COMMON)
    high_line = calculate_psfb_duty(vin_v=850.0, scope="operating_point", **COMMON)

    assert nominal.scope == "design_point"
    assert low_line.scope == high_line.scope == "operating_point"
    for result in (nominal, low_line, high_line):
        assert 0.0 <= result.effective_duty <= result.command_duty <= 1.0
        assert math.isclose(
            result.duty_loss,
            result.command_duty - result.effective_duty,
            rel_tol=1e-12,
            abs_tol=1e-12,
        )
        assert result.within_physical_range
        assert result.duty_loss_consistent
        assert result.within_configured_limits
        assert result.status == "pass"
        assert result.failure_reason is None


def test_light_and_very_light_load_reduce_duty_loss() -> None:
    light = calculate_psfb_duty(
        vin_v=750.0,
        scope="operating_point",
        **{**COMMON, "iout_a": 1.0},
    )
    very_light = calculate_psfb_duty(
        vin_v=750.0,
        scope="operating_point",
        **{**COMMON, "iout_a": 0.5},
    )

    assert light.duty_loss < calculate_psfb_duty(vin_v=750.0, scope="operating_point", **COMMON).duty_loss
    assert very_light.duty_loss < light.duty_loss


def test_configured_limit_failure_is_explicit_and_not_clamped() -> None:
    result = calculate_psfb_duty(
        vin_v=600.0,
        scope="operating_point",
        **{**COMMON, "max_effective_duty": 0.70, "max_command_duty": 0.75},
    )

    assert result.effective_duty > result.max_effective_duty
    assert result.command_duty > result.max_command_duty
    assert result.status == "configured_boundary_failure"
    assert result.failure_reason == "configured_duty_limit_exceeded"
    assert not result.feasible


def test_illegal_duty_order_is_explicitly_rejected() -> None:
    result = assess_psfb_duty(
        effective_duty=0.80,
        duty_loss=0.05,
        command_duty=0.70,
        max_effective_duty=0.90,
        max_command_duty=0.95,
        scope="operating_point",
    )

    assert not result.within_physical_range
    assert result.status == "physical_boundary_failure"
    assert "duty_order_or_physical_range_violation" in (result.failure_reason or "")
    assert not result.feasible


def test_invalid_calculation_input_is_rejected() -> None:
    with pytest.raises(ValueError, match="vin_v must be finite and positive"):
        calculate_psfb_duty(vin_v=0.0, scope="operating_point", **COMMON)


def test_low_line_waveform_uses_operating_command_duty_for_primary_current() -> None:
    spec = input_schema.build_spec(input_schema.build_default_inputs())
    candidate = synthesize(spec)
    waveform = generate_waveforms(candidate, OperatingPoint(vin_v=650.0, load_ratio=1.0))
    psfb_waveforms = waveform.metadata["psfb_waveforms"]
    policy = psfb_waveforms["duty_policy"]
    primary_model = psfb_waveforms["primary_current_model"]

    assert policy["scope"] == "operating_point"
    assert policy["status"] == "pass"
    assert policy["effective_duty"] > candidate.metadata["psfb"]["effective_duty_nom"]
    assert policy["command_duty"] > policy["effective_duty"]
    assert primary_model["power_transfer_duration_per_half_cycle_s"] == pytest.approx(
        policy["effective_duty"] / (2.0 * candidate.fs_hz)
    )
    assert primary_model["commutation_duration_per_half_cycle_s"] == pytest.approx(
        policy["duty_loss"] / (2.0 * candidate.fs_hz)
    )
    assert psfb_waveforms["command_duty"] != candidate.metadata["psfb"]["command_duty_nom"]

    stress = extract_stress(candidate, waveform_set=waveform)
    assert any("Operating-point waveform metadata" in note for note in stress.notes)
    assert stress.switch.current_rms_a == pytest.approx(
        psfb_waveforms["primary_current_model"]["switches"][
            psfb_waveforms["primary_current_model"]["worst_switch_rms_position"]
        ]["branch_current_rms_a"]
    )


def test_waveform_operating_frequency_is_reflected_in_duty_loss_and_period() -> None:
    spec = input_schema.build_spec(input_schema.build_default_inputs())
    candidate = synthesize(spec)
    waveform = generate_waveforms(
        candidate,
        OperatingPoint(vin_v=750.0, load_ratio=0.2, switching_frequency_hz=200_000.0),
    )
    policy = waveform.metadata["psfb_waveforms"]["duty_policy"]
    assert policy["duty_loss"] == pytest.approx(
        candidate.metadata["psfb"]["duty_loss_nom"] * 0.2 * 2.0
    )
    assert waveform.switching_period_s == pytest.approx(1.0 / 200_000.0)


def test_operating_point_refresh_reuses_candidate_and_updates_psfb_report() -> None:
    from pe_claw_gui.topologies.dc_dc.phase_shifted_full_bridge_diode_rectifier_isolated import PLUGIN

    raw_input = input_schema.build_default_inputs()
    baseline = run_full_pipeline(
        PLUGIN,
        raw_input,
        operating_point=OperatingPoint(vin_v=750.0, load_ratio=1.0),
        include_waveforms=True,
        pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
    )
    baseline_candidate = baseline.candidate
    baseline_devices = dict(baseline.device.selected_devices)
    refreshed = run_operating_point_refresh(
        baseline,
        PLUGIN,
        OperatingPoint(vin_v=650.0, load_ratio=1.0),
        pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
    )
    policy = refreshed.waveform.metadata["psfb_waveforms"]["duty_policy"]

    assert refreshed.candidate.topology_id == baseline_candidate.topology_id
    assert refreshed.candidate.inductance_h == pytest.approx(baseline_candidate.inductance_h)
    assert refreshed.candidate.capacitance_f == pytest.approx(baseline_candidate.capacitance_f)
    assert refreshed.candidate.fs_hz == pytest.approx(baseline_candidate.fs_hz)
    assert refreshed.device.selected_devices == baseline_devices
    assert policy["scope"] == "operating_point"
    assert policy["status"] == "pass"
    assert policy["effective_duty"] == pytest.approx(0.78)
    assert policy["command_duty"] > policy["effective_duty"]
    assert policy["command_duty"] == pytest.approx(
        policy["effective_duty"] + policy["duty_loss"]
    )
    assert refreshed.stress.switch.current_rms_a == pytest.approx(
        refreshed.waveform.metadata["psfb_waveforms"]["primary_current_model"]["switches"][
            refreshed.waveform.metadata["psfb_waveforms"]["primary_current_model"]["worst_switch_rms_position"]
        ]["branch_current_rms_a"]
    )
