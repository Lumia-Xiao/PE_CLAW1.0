from __future__ import annotations

from importlib import import_module
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.app.topology_forms.single_phase_full_bridge_inverter_form import (
    SinglePhaseFullBridgeInverterForm,
)
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.pipeline.run_operating_point_refresh import run_operating_point_refresh
from pe_claw_gui.topologies.base.registry import build_default_registry


TOPOLOGY_ID = "single_phase_full_bridge_inverter"
MODULE = import_module("pe_claw_gui.topologies.dc_ac.single_phase_full_bridge_inverter")
NO_DOWNSTREAM = PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False)


def _plugin():
    return build_default_registry().get_plugin(TOPOLOGY_ID)


def _candidate(raw_input: dict[str, str] | None = None):
    plugin = _plugin()
    raw = raw_input or MODULE.build_default_inputs()
    return plugin, plugin.synthesize(plugin.build_spec(raw))


def test_default_inputs_build_ccm_spec_and_candidate_contract() -> None:
    plugin, candidate = _candidate()
    spec = plugin.build_spec(MODULE.build_default_inputs())

    assert spec.topology_id == TOPOLOGY_ID
    assert spec.metadata["conduction_mode"] == "ccm"
    assert spec.metadata["modulation"] == "unipolar_spwm"
    assert spec.metadata["dc_link_capacitor_basis"] == "single-phase twice-line-frequency energy balance"
    assert candidate.mode_capable == "ccm_unipolar_spwm_first_pass"
    assert candidate.feasible is True
    assert candidate.metadata["cdc_required_f"] > 0.0
    assert candidate.metadata["output_inductance_h"] > 0.0


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("conduction_mode", "invalid", "CCM or TCM"),
        ("power_factor", "0", "range"),
        ("vdc_nom", "0", "positive"),
        ("pout_w", "not-a-number", "valid numbers"),
    ],
)
def test_invalid_design_inputs_are_rejected(field: str, value: str, message: str) -> None:
    raw = MODULE.build_default_inputs()
    raw[field] = value

    with pytest.raises(ValueError, match=message):
        _plugin().build_spec(raw)


def test_tcm_schema_and_candidate_preserve_first_pass_boundary() -> None:
    raw = MODULE.build_default_inputs()
    raw["conduction_mode"] = "TCM"
    raw["fsw_min_hz"] = "60000"
    raw["fsw_max_hz"] = "250000"
    raw["tcm_valley_current_target_a"] = "-2"

    plugin, candidate = _candidate(raw)
    spec = plugin.build_spec(raw)
    waveform = plugin.generate_waveforms(candidate)

    assert spec.metadata["conduction_mode"] == "tcm"
    assert candidate.mode_capable == "tcm_triangular_current_first_pass"
    assert candidate.metadata["tcm_valley_current_target_a"] == -2.0
    assert candidate.metadata["tcm_fsw_min_actual_hz"] >= 60000.0
    assert candidate.metadata["tcm_fsw_max_actual_hz"] <= 250000.0
    assert waveform.mode == "tcm triangular-current envelope"
    assert waveform.metadata["single_phase_inverter_tcm_envelope"]
    assert waveform.notes and any("not modeled" in note for note in waveform.notes)


def test_ccm_waveform_contains_refined_gates_and_required_signals() -> None:
    plugin, candidate = _candidate()
    waveform = plugin.generate_waveforms(candidate)
    refined = waveform.metadata["single_phase_inverter_refined_waveforms"]

    assert len(waveform.time_s) == len(waveform.switch_node_voltage_v)
    assert len(waveform.time_s) == len(waveform.inductor_current_a)
    assert len(waveform.time_s) == len(waveform.output_voltage_v)
    assert waveform.operating_vin_v == pytest.approx(400.0)
    assert waveform.operating_vout_v > 0.0
    assert waveform.metadata["refined_bridge_voltage_levels_v"] == [-400.0, 0.0, 400.0]
    assert refined["gate_s1"] and refined["gate_s2"]
    assert refined["gate_s3"] and refined["gate_s4"]
    assert len(refined["gate_s1"]) == len(refined["v_ab_pwm_v"])
    assert waveform.metadata["single_phase_inverter_branch_currents"]["semantics"] == (
        "complete_mosfet_with_antiparallel_diode_branch_current"
    )


def test_stress_uses_single_phase_ac_current_peak_and_rms() -> None:
    plugin, candidate = _candidate()
    waveform = plugin.generate_waveforms(candidate)
    stress = plugin.extract_stress(candidate, waveform)

    assert stress.switch.voltage_max_v == pytest.approx(400.0)
    assert stress.switch.current_peak_a == pytest.approx(candidate.metadata["iac_peak_a"])
    assert stress.switch.current_rms_a == pytest.approx(candidate.metadata["iac_rms_a"])
    assert stress.rectifier == stress.switch
    assert any("sinusoidal AC current" in note for note in stress.notes)


def test_full_pipeline_generates_waveform_and_topology_specific_report() -> None:
    plugin = _plugin()
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=MODULE.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=NO_DOWNSTREAM,
    )

    assert report.spec.topology_id == TOPOLOGY_ID
    assert report.candidate is not None
    assert report.waveform is not None
    assert report.stress is not None
    assert report.topology_result is not None
    assert any("full-bridge inverter" in line for line in report.topology_result.summary_lines)
    assert all("buck" not in line.lower() and "boost" not in line.lower() for line in report.topology_result.summary_lines)


def test_operating_refresh_changes_load_and_pf_but_reuses_selected_switch() -> None:
    plugin = _plugin()
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=MODULE.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=NO_DOWNSTREAM,
    )
    assert report.device is not None
    selected_device = dict(report.device.selected_devices)

    refreshed = run_operating_point_refresh(
        report,
        plugin,
        OperatingPoint(vin_v=400.0, load_ratio=0.5, power_factor=0.8),
        pipeline_options=NO_DOWNSTREAM,
    )

    assert refreshed.waveform is not None
    assert refreshed.waveform.load_ratio == pytest.approx(0.5)
    assert refreshed.waveform.metadata["operating_power_factor"] == pytest.approx(0.8)
    assert refreshed.waveform.metadata["operating_iac_rms_a"] < report.waveform.metadata["operating_iac_rms_a"]
    assert refreshed.candidate is report.candidate
    assert refreshed.device is not None
    assert refreshed.device.selected_devices == selected_device


def test_form_exposes_ccm_tcm_and_operating_point_fields() -> None:
    assert SinglePhaseFullBridgeInverterForm.topology_id == TOPOLOGY_ID
    assert SinglePhaseFullBridgeInverterForm.implemented is True
    assert SinglePhaseFullBridgeInverterForm.common_design_fields[0].choices == ("CCM", "TCM")
    assert {field.key for field in SinglePhaseFullBridgeInverterForm.ccm_design_fields} == {
        "fsw_hz",
        "inductor_current_ripple_ratio",
    }
    assert {field.key for field in SinglePhaseFullBridgeInverterForm.tcm_design_fields} == {
        "fsw_min_hz",
        "fsw_max_hz",
        "tcm_valley_current_target_a",
    }
    assert {field.key for field in SinglePhaseFullBridgeInverterForm.design_fields} >= {
        "conduction_mode",
        "vdc_nom",
        "vac_rms",
        "pout_w",
        "ambient_temp_c",
        "target_junction_temp_c",
    }
