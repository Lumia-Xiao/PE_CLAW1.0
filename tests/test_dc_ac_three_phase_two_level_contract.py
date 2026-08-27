from __future__ import annotations

from importlib import import_module
import inspect
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.app.topology_forms.three_phase_two_level_voltage_source_inverter_form import (
    ThreePhaseTwoLevelVoltageSourceInverterForm,
)
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.pipeline.run_operating_point_refresh import run_operating_point_refresh
from pe_claw_gui.topologies.base.registry import build_default_registry


TOPOLOGY_ID = "three_phase_two_level_voltage_source_inverter"
MODULE = import_module("pe_claw_gui.topologies.dc_ac.three_phase_two_level_voltage_source_inverter")
NO_DOWNSTREAM = PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False)


def _plugin():
    return build_default_registry().get_plugin(TOPOLOGY_ID)


def test_default_three_phase_inputs_preserve_vsi_design_contract() -> None:
    plugin = _plugin()
    spec = plugin.build_spec(MODULE.build_default_inputs())
    candidate = plugin.synthesize(spec)

    assert spec.topology_id == TOPOLOGY_ID
    assert spec.metadata["vac_ll_rms_v"] == pytest.approx(400.0)
    assert spec.metadata["conduction_mode"] == "ccm"
    assert spec.metadata["modulation"] == "spwm"
    assert candidate.mode_capable == "ccm_three_phase_two_level_spwm_first_pass"
    assert candidate.metadata["phase_count"] == 3
    assert candidate.metadata["switch_position_count"] == 6
    assert candidate.metadata["vac_phase_rms_v"] == pytest.approx(400.0 / 3**0.5)
    assert candidate.metadata["i_phase_rms_a"] > 0.0
    assert candidate.metadata["l_phase_h"] > 0.0


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("vdc_nom", "0", "positive"),
        ("vac_ll_rms", "0", "positive"),
        ("fsw_hz", "not-a-number", "valid numbers"),
        ("power_factor", "1.1", "range"),
    ],
)
def test_invalid_three_phase_inputs_are_rejected(field: str, value: str, message: str) -> None:
    raw = MODULE.build_default_inputs()
    raw[field] = value

    with pytest.raises(ValueError, match=message):
        _plugin().build_spec(raw)


def test_spwm_waveform_contains_three_phase_voltage_current_and_gate_metadata() -> None:
    plugin = _plugin()
    candidate = plugin.synthesize(plugin.build_spec(MODULE.build_default_inputs()))
    waveform = plugin.generate_waveforms(candidate)
    details = waveform.metadata["three_phase_two_level_spwm_waveforms"]

    assert waveform.mode == "three-phase two-level SPWM first-pass preview"
    assert len(waveform.time_s) == 38_401
    assert len(details["time_s"]) == len(details["vab_pwm_v"])
    assert details["gate_a_high"] and details["gate_b_high"] and details["gate_c_high"]
    assert details["va_phase_v"] and details["vb_phase_v"] and details["vc_phase_v"]
    assert details["vab_pwm_v"] and details["vbc_pwm_v"] and details["vca_pwm_v"]
    assert details["ia_a"] and details["ib_a"] and details["ic_a"]
    assert len(details["dc_link_bus_current_pwm_a"]) == len(details["time_s"])
    assert waveform.metadata["line_line_voltage_phase_shift_deg"] == pytest.approx(30.0)
    assert waveform.metadata["phase_current_reference"].startswith("ia aligned to va_phase")
    assert waveform.metadata["dc_link_capacitor_current_pwm_a"]
    assert waveform.metadata["three_phase_vsi_branch_currents"]["q1"]["rms_current_a"] > 0.0


def test_stress_uses_waveform_backed_phase_current_and_six_switch_branch_contract() -> None:
    plugin = _plugin()
    candidate = plugin.synthesize(plugin.build_spec(MODULE.build_default_inputs()))
    waveform = plugin.generate_waveforms(candidate)
    stress = plugin.extract_stress(candidate, waveform)

    assert stress.switch.voltage_max_v == pytest.approx(700.0)
    assert stress.switch.current_peak_a == pytest.approx(waveform.metadata["phase_current_peak_abs_a"])
    assert stress.switch.current_rms_a == pytest.approx(waveform.metadata["phase_current_total_rms_a"])
    assert stress.rectifier == stress.switch
    assert any("Q1-Q6" in note for note in stress.notes)
    assert set(waveform.metadata["three_phase_vsi_branch_currents"]) >= {"q1", "q2", "q3", "q4", "q5", "q6"}


def test_full_pipeline_returns_three_phase_specific_report() -> None:
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
    assert report.device is not None
    assert any("Three-phase two-level SPWM" in line for line in report.topology_result.summary_lines)
    assert any("per phase" in line for line in report.topology_result.summary_lines)
    assert all("buck" not in line.lower() and "boost" not in line.lower() for line in report.topology_result.summary_lines)


def test_operating_refresh_updates_load_and_pf_without_redesigning_candidate_or_switch() -> None:
    plugin = _plugin()
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=MODULE.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=NO_DOWNSTREAM,
    )
    assert report.waveform is not None
    assert report.device is not None
    selected_devices = dict(report.device.selected_devices)

    refreshed = run_operating_point_refresh(
        report,
        plugin,
        OperatingPoint(vin_v=700.0, load_ratio=0.5, power_factor=0.8),
        pipeline_options=NO_DOWNSTREAM,
    )

    assert refreshed.waveform is not None
    assert refreshed.waveform.load_ratio == pytest.approx(0.5)
    assert refreshed.waveform.metadata["operating_power_factor"] == pytest.approx(0.8)
    assert refreshed.waveform.metadata["operating_i_phase_rms_a"] < report.waveform.metadata["operating_i_phase_rms_a"]
    assert refreshed.candidate is report.candidate
    assert refreshed.device is not None
    assert refreshed.device.selected_devices == selected_devices


def test_form_exposes_three_phase_design_and_operating_point_controls() -> None:
    form = ThreePhaseTwoLevelVoltageSourceInverterForm
    assert form.topology_id == TOPOLOGY_ID
    assert form.implemented is True
    assert [field.key for field in form.design_fields] == [
        "vdc_nom",
        "vac_ll_rms",
        "f_line_hz",
        "fsw_hz",
        "pout_w",
        "power_factor",
        "inductor_current_ripple_ratio",
        "dc_link_voltage_ripple_ratio",
        "ambient_temp_c",
        "target_junction_temp_c",
    ]
    form_source = inspect.getsource(form)
    assert '"load_ratio": tk.StringVar' in form_source
    assert '"power_factor": tk.StringVar' in form_source
