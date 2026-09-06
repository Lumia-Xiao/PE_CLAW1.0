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
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import run_efficiency_sweep
from pe_claw_gui.engines.devices.loss_evaluator import evaluate_switching_events
from pe_claw_gui.engines.devices.loss_evaluator import summarize_switching_event_energy
from pe_claw_gui.libraries.semiconductors.registry import build_default_semiconductor_registry
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


def test_vsi_switching_event_container_exposes_six_switch_schema() -> None:
    plugin = _plugin()
    candidate = plugin.synthesize(plugin.build_spec(MODULE.build_default_inputs()))
    waveform = plugin.generate_waveforms(candidate)
    metadata = waveform.metadata

    events = metadata["three_phase_vsi_switching_events"]
    schema = metadata["three_phase_vsi_switching_event_schema"]
    audit = metadata["three_phase_vsi_switching_event_audit"]

    assert events
    assert metadata["three_phase_vsi_switching_event_count"] == len(events)
    assert schema["topology"] == "three_phase_two_level_vsi"
    assert schema["switch_names"] == ["S1", "S2", "S3", "S4", "S5", "S6"]
    assert set(schema["field_names"]) == {
        "phase",
        "switch_name",
        "switch_index",
        "bridge_leg",
        "event_type",
        "event_time_s",
        "signed_current_A",
        "absolute_current_A",
        "blocking_voltage_V",
        "gate_before",
        "gate_after",
        "event_source",
        "current_source",
        "blocking_voltage_source",
    }
    assert schema["event_types"] == ["turn_on", "turn_off"]
    assert schema["time_interval"] == "[0, Tline)"
    assert audit["status"] == "populated"
    assert audit["event_count"] == len(events)
    assert audit["turn_on_count"] + audit["turn_off_count"] == len(events)
    assert audit["hard_turn_on_count"] + audit["soft_turn_on_count"] == audit["turn_on_count"]
    assert set(audit["switch_event_counts"]) == {"S1", "S2", "S3", "S4", "S5", "S6"}
    assert all(audit["switch_event_counts"][name] > 0 for name in ("S1", "S2", "S3", "S4", "S5", "S6"))
    assert audit["event_current_min_A"] < audit["event_current_max_A"]
    assert audit["event_blocking_voltage_min_V"] > 0.0
    assert audit["event_source"] == "actual_sampled_vsi_gate_edge"
    assert audit["current_source"] == "actual_phase_inductor_current_at_gate_edge"
    assert audit["blocking_voltage_source"] == "actual_dc_link_voltage_at_gate_edge"

    required_fields = set(schema["field_names"])
    assert all(required_fields <= set(event) for event in events)
    assert all(0.0 <= event["event_time_s"] < waveform.time_span_s for event in events)
    assert all(event["absolute_current_A"] == pytest.approx(abs(event["signed_current_A"])) for event in events)


def test_vsi_event_schema_documents_signed_current_and_voltage_contract() -> None:
    plugin = _plugin()
    candidate = plugin.synthesize(plugin.build_spec(MODULE.build_default_inputs()))
    waveform = plugin.generate_waveforms(candidate)
    schema = waveform.metadata["three_phase_vsi_switching_event_schema"]

    assert schema["signed_current_convention"] == "positive current from inverter bridge into AC phase"
    assert schema["blocking_voltage_convention"] == "absolute device blocking voltage in volts"
    assert schema["extraction_status"] == "actual_vsi_gate_edge_extraction_v1"


def test_vsi_events_use_complementary_six_switch_mapping_at_each_gate_edge() -> None:
    plugin = _plugin()
    candidate = plugin.synthesize(plugin.build_spec(MODULE.build_default_inputs()))
    waveform = plugin.generate_waveforms(candidate)
    events = waveform.metadata["three_phase_vsi_switching_events"]

    assert {event["switch_name"] for event in events} == {"S1", "S2", "S3", "S4", "S5", "S6"}
    for phase, upper_name, lower_name in (("a", "S1", "S2"), ("b", "S3", "S4"), ("c", "S5", "S6")):
        phase_events = [event for event in events if event["phase"] == phase]
        assert phase_events
        for event in phase_events:
            assert event["bridge_leg"] == phase.upper()
            paired = [
                other for other in phase_events
                if other["event_time_s"] == event["event_time_s"]
                and other["switch_name"] in {upper_name, lower_name}
                and other["switch_name"] != event["switch_name"]
            ]
            assert len(paired) == 1
            assert paired[0]["event_type"] != event["event_type"]
            assert paired[0]["gate_before"] == pytest.approx(1.0 - event["gate_before"])
            assert paired[0]["gate_after"] == pytest.approx(1.0 - event["gate_after"])


def test_vsi_report_uses_event_energy_once_and_closes_loss_breakdown() -> None:
    plugin = _plugin()
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=MODULE.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=NO_DOWNSTREAM,
    )

    assert report.waveform is not None
    assert report.device is not None
    loss = report.device.design_point_losses["design_point:main_switch"]
    events = report.waveform.metadata["three_phase_vsi_switching_events"]
    device = build_default_semiconductor_registry().get_device(report.device.selected_devices["main_switch"])
    line_period_s = 1.0 / float(report.spec.metadata["f_line_hz"])
    event_losses = evaluate_switching_events(device, events, junction_temp_c=loss.tj_est_C)
    summary = summarize_switching_event_energy(
        event_losses,
        line_period_s=line_period_s,
        physical_position_count=6,
    )

    assert loss.mode == "three_phase_two_level_vsi_spwm_event_line_cycle_average"
    assert loss.p_sw_on_W == pytest.approx(summary["p_sw_on_W"])
    assert loss.p_sw_off_W == pytest.approx(summary["p_sw_off_W"])
    assert loss.p_rr_W == pytest.approx(summary["p_rr_W"])
    assert loss.p_total_W == pytest.approx(
        loss.p_cond_W + loss.p_sw_on_W + loss.p_sw_off_W + loss.p_rr_W + loss.p_eoss_W + loss.p_gate_W
    )
    assert any(
        "Three-phase VSI event-level switching loss" in note
        for note in loss.thermal_design_notes
    )
    assert any(item["soft_turn_on"] and item["eon_J"] == 0.0 for item in event_losses)
    assert any(item["event_type"] == "turn_on" and not item["soft_turn_on"] and item["eon_J"] > 0.0 for item in event_losses)


def test_vsi_sic_event_reverse_recovery_is_zero() -> None:
    plugin = _plugin()
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=MODULE.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=NO_DOWNSTREAM,
    )

    assert report.waveform is not None
    assert report.device is not None
    device = build_default_semiconductor_registry().get_device(report.device.selected_devices["main_switch"])
    event_losses = evaluate_switching_events(
        device,
        report.waveform.metadata["three_phase_vsi_switching_events"],
    )
    if "sic" in device.selection_device_type.casefold() or "sic" in device.part_number.casefold():
        assert all(item["reverse_recovery_J"] == 0.0 for item in event_losses)


def test_vsi_efficiency_sweep_refreshes_event_loss_audit_for_load_and_pf(tmp_path: Path) -> None:
    plugin = _plugin()
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=MODULE.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=NO_DOWNSTREAM,
    )
    assert report.device is not None
    selected_devices = dict(report.device.selected_devices)

    result = run_efficiency_sweep(
        report,
        plugin=plugin,
        load_points=(0.5, 1.0),
        output_dir=tmp_path,
    )

    assert len(result.points) == 2
    assert all(point.efficiency is not None for point in result.points)
    assert all(point.other_loss_w == 0.0 for point in result.points)
    assert all(point.switching_loss_audit["status"] == "available" for point in result.points)
    assert all(point.switching_loss_audit["event_count"] > 0 for point in result.points)
    assert all(
        set(point.switching_loss_audit["switch_event_counts"]) == {"S1", "S2", "S3", "S4", "S5", "S6"}
        for point in result.points
    )
    assert all(
        point.switching_loss_audit["hard_turn_on_count"] > 0
        and point.switching_loss_audit["soft_turn_on_count"] > 0
        for point in result.points
    )
    assert result.points[0].switching_loss_audit["signed_current_max_A"] < result.points[1].switching_loss_audit["signed_current_max_A"]
    assert result.points[0].semiconductor_loss_w != pytest.approx(result.points[1].semiconductor_loss_w)
    assert result.points[0].switching_loss_audit["event_source"] == "actual_sampled_vsi_gate_edge"
    assert result.points[0].switching_loss_audit["current_source"] == "actual_phase_inductor_current_at_gate_edge"
    assert result.points[0].switching_loss_audit["blocking_voltage_source"] == "actual_dc_link_voltage_at_gate_edge"
    assert len(result.pf_sweep_points) == 20
    assert all(point["switching_loss_audit"]["status"] == "available" for point in result.pf_sweep_points)
    assert all(point["switching_loss_audit"]["event_count"] > 0 for point in result.pf_sweep_points)
    assert len({point["switching_loss_audit"]["signed_current_max_A"] for point in result.pf_sweep_points}) > 1
    assert all(point["switching_loss_audit"]["sic_reverse_recovery_loss_W"] == 0.0 for point in result.pf_sweep_points)
    assert result.pf_sweep_points[0]["switching_loss_audit"]["formula"].startswith("Psw = sum")
    assert report.device.selected_devices == selected_devices


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
