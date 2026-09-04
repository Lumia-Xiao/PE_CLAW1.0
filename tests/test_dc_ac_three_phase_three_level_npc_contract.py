from __future__ import annotations

from importlib import import_module
import inspect
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.app.topology_forms.three_phase_three_level_npc_inverter_form import (
    ThreePhaseThreeLevelNPCInverterForm,
)
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.pipeline.run_operating_point_refresh import run_operating_point_refresh
from pe_claw_gui.engines.devices.loss_evaluator import (
    evaluate_npc_switching_event_energy,
    evaluate_npc_switching_events,
)
from pe_claw_gui.libraries.semiconductors.registry import build_default_semiconductor_registry
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter.waveform import (
    _integrate_phase_current_by_cycle,
)


TOPOLOGY_ID = "three_phase_three_level_npc_inverter"
MODULE = import_module("pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter")
NO_DOWNSTREAM = PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False)


def _plugin():
    return build_default_registry().get_plugin(TOPOLOGY_ID)


def test_default_npc_inputs_preserve_three_level_split_link_contract() -> None:
    plugin = _plugin()
    spec = plugin.build_spec(MODULE.build_default_inputs())
    candidate = plugin.synthesize(spec)

    assert spec.topology_id == TOPOLOGY_ID
    assert spec.metadata["vac_ll_rms_v"] == pytest.approx(400.0)
    assert spec.metadata["conduction_mode"] == "ccm"
    assert spec.metadata["modulation_scheme"] == "phase_disposition_level_shifted_spwm_first_pass"
    assert spec.metadata["topology_level_count"] == 3
    assert candidate.mode_capable == "ccm_three_phase_three_level_npc_lspwm_first_pass"
    assert candidate.metadata["phase_count"] == 3
    assert candidate.metadata["switch_position_count"] == 12
    assert candidate.metadata["clamp_diode_count"] == 6
    assert candidate.metadata["dc_link_split_capacitor_count"] == 2
    assert candidate.metadata["npc_half_bus_voltage_v"] == pytest.approx(350.0)
    assert candidate.metadata["dc_link_series_equivalent_capacitance_f"] > 0.0


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("vdc_nom", "0", "positive"),
        ("vac_ll_rms", "0", "positive"),
        ("fsw_hz", "not-a-number", "valid numbers"),
        ("power_factor", "1.1", "range"),
    ],
)
def test_invalid_npc_inputs_are_rejected(field: str, value: str, message: str) -> None:
    raw = MODULE.build_default_inputs()
    raw[field] = value

    with pytest.raises(ValueError, match=message):
        _plugin().build_spec(raw)


def test_npc_waveform_contains_pd_spwm_three_level_signals_and_split_link_data() -> None:
    plugin = _plugin()
    candidate = plugin.synthesize(plugin.build_spec(MODULE.build_default_inputs()))
    waveform = plugin.generate_waveforms(candidate)
    details = waveform.metadata["three_phase_npc_pd_spwm_waveforms"]

    assert waveform.mode == "three-phase three-level NPC PD-SPWM first-pass preview"
    assert len(waveform.time_s) == 9_601
    assert len(details["time_s"]) == len(details["vab_pwm_v"])
    assert all(details[key] for key in ("carrier_lower", "carrier_upper", "mod_a", "mod_b", "mod_c"))
    assert all(details[key] for key in ("phase_state_a", "phase_state_b", "phase_state_c"))
    assert all(details[key] for key in ("gate_a_s1", "gate_a_s2", "gate_a_s3", "gate_a_s4"))
    assert all(details[key] for key in ("gate_b_s1", "gate_b_s2", "gate_b_s3", "gate_b_s4"))
    assert all(details[key] for key in ("gate_c_s1", "gate_c_s2", "gate_c_s3", "gate_c_s4"))
    assert all(details[key] for key in ("va_phase_neutral_pwm_v", "vb_phase_neutral_pwm_v", "vc_phase_neutral_pwm_v"))
    assert all(details[key] for key in ("upper_dc_link_capacitor_current_pwm_a", "lower_dc_link_capacitor_current_pwm_a"))
    assert waveform.metadata["upper_dc_link_capacitor_current_rms_pwm_a"] > 0.0
    assert waveform.metadata["lower_dc_link_capacitor_current_rms_pwm_a"] > 0.0
    assert waveform.metadata["npc_neutral_point_current_rms_a"] > 0.0
    assert waveform.metadata["line_line_voltage_phase_shift_deg"] == pytest.approx(30.0)
    assert waveform.metadata["phase_current_integration_method"].startswith("continuous_")
    assert waveform.metadata["phase_current_periodic_correction_applied"] is True
    assert len(waveform.metadata["phase_current_periodic_correction_a"]) == 3


def test_npc_waveform_extracts_interpolated_events_for_all_switch_positions() -> None:
    plugin = _plugin()
    candidate = plugin.synthesize(plugin.build_spec(MODULE.build_default_inputs()))
    waveform = plugin.generate_waveforms(candidate)
    events = waveform.metadata["three_phase_npc_switching_events"]

    assert events
    assert waveform.metadata["three_phase_npc_switching_event_count"] == len(events)
    assert {(event["phase"], event["switch_index"]) for event in events} == {
        (phase, switch_index) for phase in ("a", "b", "c") for switch_index in range(1, 5)
    }
    assert {event["event_type"] for event in events} == {"turn_on", "turn_off"}
    assert all(0.0 <= event["event_time_s"] <= waveform.time_span_s for event in events)
    assert all(event["absolute_current_A"] == pytest.approx(abs(event["signed_current_A"])) for event in events)
    assert all(event["blocking_voltage_V"] > 0.0 for event in events)
    assert len({round(event["signed_current_A"], 9) for event in events}) > 10


def test_npc_event_energy_uses_polarity_and_actual_current() -> None:
    device = build_default_semiconductor_registry().get_device("IPZA60R037CM8")
    soft_on = evaluate_npc_switching_event_energy(
        device,
        {
            "event_type": "turn_on",
            "signed_current_A": -8.0,
            "blocking_voltage_V": 350.0,
        },
    )
    low_current_on = evaluate_npc_switching_event_energy(
        device,
        {
            "event_type": "turn_on",
            "signed_current_A": 2.0,
            "blocking_voltage_V": 350.0,
        },
    )
    high_current_on = evaluate_npc_switching_event_energy(
        device,
        {
            "event_type": "turn_on",
            "signed_current_A": 8.0,
            "blocking_voltage_V": 350.0,
        },
    )
    turn_off = evaluate_npc_switching_event_energy(
        device,
        {
            "event_type": "turn_off",
            "signed_current_A": 8.0,
            "blocking_voltage_V": 350.0,
        },
    )

    assert soft_on["soft_turn_on"] is True
    assert soft_on["eon_J"] == pytest.approx(0.0)
    assert low_current_on["soft_turn_on"] is False
    assert low_current_on["eon_J"] >= 0.0
    assert high_current_on["eon_J"] != pytest.approx(low_current_on["eon_J"])
    assert turn_off["eoff_J"] >= 0.0


def test_npc_event_energy_sets_sic_reverse_recovery_to_zero() -> None:
    device = build_default_semiconductor_registry().get_device("SCS304AG")
    result = evaluate_npc_switching_event_energy(
        device,
        {
            "event_type": "turn_off",
            "signed_current_A": 12.0,
            "blocking_voltage_V": 350.0,
        },
    )

    assert result["reverse_recovery_J"] == pytest.approx(0.0)


def test_npc_phase_current_integrates_continuously_across_pwm_boundaries() -> None:
    time_s = [index * 0.1 for index in range(9)]
    voltage_v = [1.0, 1.0, -1.0, -1.0, 1.0, 1.0, -1.0, -1.0, 1.0]
    grid_v = [0.0] * len(time_s)
    fundamental_a = [0.0] * len(time_s)

    current_a = _integrate_phase_current_by_cycle(
        time_s,
        voltage_v,
        grid_v,
        fundamental_a,
        inductance_h=1.0,
        samples_per_switching_period=2,
    )

    assert current_a[2] != pytest.approx(fundamental_a[2])
    assert current_a[2] == pytest.approx(current_a[1])
    assert current_a[-1] == pytest.approx(fundamental_a[-1])
    assert max(current_a) - min(current_a) > 0.0


def test_npc_stress_preserves_outer_inner_and_clamp_roles() -> None:
    plugin = _plugin()
    candidate = plugin.synthesize(plugin.build_spec(MODULE.build_default_inputs()))
    waveform = plugin.generate_waveforms(candidate)
    stress = plugin.extract_stress(candidate, waveform)
    roles = waveform.metadata["three_phase_npc_device_currents"]["roles"]

    assert stress.switch.voltage_max_v == pytest.approx(350.0)
    assert stress.rectifier.voltage_max_v == pytest.approx(350.0)
    assert stress.switch.current_peak_a == pytest.approx(roles["inner_switch"]["peak_absolute_current_a"])
    assert stress.switch.current_rms_a == pytest.approx(roles["inner_switch"]["rms_current_a"])
    assert stress.rectifier.current_rms_a == pytest.approx(roles["clamp_diode"]["rms_current_a"])
    assert roles["outer_switch"]["physical_position_count"] == 6
    assert roles["inner_switch"]["physical_position_count"] == 6
    assert roles["clamp_diode"]["physical_position_count"] == 6
    assert any("neutral-point balancing" in note.lower() for note in stress.notes)


def test_full_pipeline_returns_npc_specific_report_and_device_roles() -> None:
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
    assert set(report.device.selected_devices) >= {"npc_outer_switch", "npc_inner_switch", "npc_clamp_diode"}
    for loss in report.device.design_point_losses.values():
        if loss.role in {"npc_outer_switch", "npc_inner_switch"}:
            assert any("NPC event-level switching loss" in note for note in loss.thermal_design_notes)
    assert any("NPC PD level-shifted SPWM" in line for line in report.topology_result.summary_lines)
    assert any("split DC-link capacitor" in line for line in report.topology_result.summary_lines)
    assert all("buck" not in line.lower() and "boost" not in line.lower() for line in report.topology_result.summary_lines)
    assert any("neutral-point balancing" in note.lower() for note in report.notes)


def test_npc_report_switching_loss_matches_event_energy_per_physical_position() -> None:
    plugin = _plugin()
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=MODULE.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=NO_DOWNSTREAM,
    )

    assert report.waveform is not None
    assert report.device is not None
    line_frequency_hz = float(report.spec.metadata["f_line_hz"])
    line_period_s = 1.0 / line_frequency_hz
    events = report.waveform.metadata["three_phase_npc_switching_events"]
    registry = build_default_semiconductor_registry()
    for role in ("npc_outer_switch", "npc_inner_switch"):
        device = registry.get_device(report.device.selected_devices[role])
        role_events = [event for event in events if event["role"] == role.removeprefix("npc_")]
        loss = next(item for item in report.device.design_point_losses.values() if item.role == role)
        event_losses = evaluate_npc_switching_events(device, role_events, junction_temp_c=loss.tj_est_C)

        assert loss.p_sw_on_W == pytest.approx(
            sum(float(item["eon_J"]) for item in event_losses) / 6.0 / line_period_s
        )
        assert loss.p_sw_off_W == pytest.approx(
            sum(float(item["eoff_J"]) for item in event_losses) / 6.0 / line_period_s
        )


def test_operating_refresh_updates_npc_load_and_pf_without_redesigning_hardware() -> None:
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


def test_npc_form_exposes_design_and_operating_point_controls() -> None:
    form = ThreePhaseThreeLevelNPCInverterForm
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
    assert "Generate Waveforms" in form_source
