from __future__ import annotations

from importlib import import_module
import hashlib
import inspect
import json
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
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.models.design_run_context import DesignRunContext
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter.topology_contract import (
    CONVENTIONAL_NPC_CONTRACT,
    validate_npc_role_positions,
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


def test_npc_topology_contract_is_conventional_and_complete() -> None:
    contract = CONVENTIONAL_NPC_CONTRACT
    assert contract.topology_family == "conventional_diode_clamped_npc"
    assert contract.active_switch_position_count == 12
    assert contract.clamp_diode_position_count == 6
    assert contract.total_semiconductor_position_count == 18
    assert contract.role_position_counts == {
        "npc_outer_switch": 6,
        "npc_inner_switch": 6,
        "npc_clamp_diode": 6,
    }
    validate_npc_role_positions(contract.role_position_counts)
    assert len(contract.role_position_labels["npc_clamp_diode"]) == 6


def test_npc_clamp_role_is_an_independent_physical_diode() -> None:
    from pe_claw_gui.libraries.semiconductors.topology_roles import get_semiconductor_role_spec

    clamp = get_semiconductor_role_spec("npc_clamp_diode", topology_id=TOPOLOGY_ID)
    assert clamp is not None
    assert clamp.role_kind == "clamp_diode"
    assert clamp.quantity_per_power_cell == 6
    assert clamp.can_use_internal_diode is False


def test_npc_design_basis_is_explicit_and_normalized() -> None:
    plugin = _plugin()
    raw = MODULE.build_default_inputs()
    raw.update({"vdc_min": "640", "vdc_nom": "700", "vdc_max": "760", "pout_w": "12000"})
    spec = plugin.build_spec(raw)
    basis = spec.metadata["design_basis"]

    assert basis["dc_link_voltage_v"] == {"min": 640.0, "nominal": 700.0, "max": 760.0}
    assert basis["ac_output"]["frequency_hz"] == pytest.approx(50.0)
    assert basis["switching"]["modulation_index_limit"] == pytest.approx(1.0)
    assert basis["power_factor"] == {"design": 1.0, "min": 0.8, "max": 1.0}
    assert basis["operating_range"]["overload_ratio_max"] == pytest.approx(1.1)
    assert basis["ac_output"]["phase_current_rms_a"] == pytest.approx(
        12000.0 / (3.0**0.5 * 400.0)
    )
    assert spec.vin_min == pytest.approx(640.0)
    assert spec.vin_max == pytest.approx(760.0)


def test_original_npc_form_inputs_use_backend_defaults_for_hidden_basis() -> None:
    form = ThreePhaseThreeLevelNPCInverterForm
    raw = {field.key: field.default for field in form.design_fields}
    spec = _plugin().build_spec(raw)
    basis = spec.metadata["design_basis"]

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
    assert not hasattr(form, "design_basis_fields")
    assert basis["dc_link_voltage_v"] == {"min": 700.0, "nominal": 700.0, "max": 700.0}
    assert basis["voltage_stress"]["neutral_point_stress_factor"] == pytest.approx(1.02)
    assert basis["losses"]["auxiliary_total_w"] == pytest.approx(37.0)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [("vdc_min", "800", "Vdc_min"), ("power_factor_min", "1.1", "PF_min"), ("efficiency_target", "1.1", "Efficiency")],
)
def test_npc_design_basis_ranges_are_rejected(field: str, value: str, message: str) -> None:
    raw = MODULE.build_default_inputs()
    raw[field] = value
    with pytest.raises(ValueError, match=message):
        _plugin().build_spec(raw)


def test_npc_voltage_stress_inputs_are_validated_and_used() -> None:
    raw = MODULE.build_default_inputs()
    raw.update({
        "vdc_max": "800",
        "neutral_point_voltage_stress_factor": "1.05",
        "switching_overvoltage_v": "80",
        "static_voltage_margin_ratio": "0.25",
    })
    plugin = _plugin()
    candidate = plugin.synthesize(plugin.build_spec(raw))
    assert candidate.metadata["npc_worst_case_blocking_voltage_v"] == pytest.approx(500.0)
    assert candidate.metadata["npc_static_voltage_margin_ratio"] == pytest.approx(0.25)

    for field, value in (
        ("neutral_point_voltage_stress_factor", "0.99"),
        ("switching_overvoltage_v", "-1"),
        ("static_voltage_margin_ratio", "0.19"),
    ):
        invalid = MODULE.build_default_inputs()
        invalid[field] = value
        with pytest.raises(ValueError):
            plugin.build_spec(invalid)


def test_npc_voltage_stress_inputs_are_validated_and_used() -> None:
    raw = MODULE.build_default_inputs()
    raw.update({
        "vdc_max": "800",
        "neutral_point_voltage_stress_factor": "1.05",
        "switching_overvoltage_v": "80",
        "static_voltage_margin_ratio": "0.25",
    })
    plugin = _plugin()
    candidate = plugin.synthesize(plugin.build_spec(raw))
    assert candidate.metadata["npc_worst_case_blocking_voltage_v"] == pytest.approx(500.0)
    assert candidate.metadata["npc_static_voltage_margin_ratio"] == pytest.approx(0.25)

    for field, value in (("neutral_point_voltage_stress_factor", "0.99"), ("switching_overvoltage_v", "-1"), ("static_voltage_margin_ratio", "0.19")):
        invalid = MODULE.build_default_inputs()
        invalid[field] = value
        with pytest.raises(ValueError):
            plugin.build_spec(invalid)


def test_design_request_snapshot_is_registered_in_manifest(tmp_path: Path) -> None:
    context = DesignRunContext.create(TOPOLOGY_ID, MODULE.build_default_inputs(), output_root=tmp_path / "run")
    basis = _plugin().build_spec(MODULE.build_default_inputs()).metadata["design_basis"]
    from pe_claw_gui.models.design_run_context import attach_design_request

    updated = attach_design_request(context, basis)
    request_path = Path(updated.output_root) / "design_request" / "design_request.json"
    manifest = json.loads(Path(updated.manifest_path or "").read_text(encoding="utf-8"))
    assert request_path.is_file()
    assert (request_path.with_suffix(".md")).is_file()
    assert manifest["design_request"]["path"] == "design_request/design_request.json"
    assert manifest["design_request"]["sha256"] == hashlib.sha256(request_path.read_bytes()).hexdigest()


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


def test_npc_stress_preserves_outer_inner_and_clamp_roles() -> None:
    plugin = _plugin()
    candidate = plugin.synthesize(plugin.build_spec(MODULE.build_default_inputs()))
    waveform = plugin.generate_waveforms(candidate)
    stress = plugin.extract_stress(candidate, waveform)
    roles = waveform.metadata["three_phase_npc_device_currents"]["roles"]

    assert stress.switch.voltage_max_v == pytest.approx(432.5)
    assert stress.rectifier.voltage_max_v == pytest.approx(432.5)
    assert set(stress.role_voltage_checks) == {
        "npc_outer_switch",
        "npc_inner_switch",
        "npc_clamp_diode",
    }
    assert stress.role_voltage_checks["npc_outer_switch"].required_device_rating_v == pytest.approx(519.0)
    assert stress.role_voltage_checks["npc_clamp_diode"].overvoltage_validation_status == "unverified_assumption"
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
    assert all(role.total_physical_device_count == 6 for role in report.device.scheme_results[0].role_results)
    assert any("NPC PD level-shifted SPWM" in line for line in report.topology_result.summary_lines)
    assert any("split DC-link capacitor" in line for line in report.topology_result.summary_lines)
    assert all("buck" not in line.lower() and "boost" not in line.lower() for line in report.topology_result.summary_lines)
    assert any("neutral-point balancing" in note.lower() for note in report.notes)


def test_npc_device_and_overview_counts_are_consistent(tmp_path: Path) -> None:
    plugin = _plugin()
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=MODULE.build_default_inputs(),
        pipeline_options=NO_DOWNSTREAM,
        output_root=tmp_path / "npc-run",
    )
    assert report.device is not None
    assert report.semiconductor_geometry is not None
    target = next(item for item in report.semiconductor_geometry.targets if item.scheme_id == "single")
    role_counts = {item.role_name: item.total_physical_device_count for item in target.role_layouts}
    assert role_counts == CONVENTIONAL_NPC_CONTRACT.role_position_counts

    from pe_claw_gui.engines.hardware_overview import build_hardware_overview_payload

    overview = build_hardware_overview_payload(report)
    group = next(item for item in overview.component_groups if item.group_id == "semiconductor")
    assert group.metadata["active_switch_position_count"] == 12
    assert group.metadata["clamp_diode_position_count"] == 6
    assert group.metadata["active_switch_physical_count"] == 12
    assert group.metadata["clamp_diode_physical_count"] == 6
    assert group.metadata["total_physical_device_count"] == 18
    assert {item.entry_id: item.quantity for item in group.child_entries} == role_counts
    assert set(group.metadata["voltage_checks"]) == {
        "npc_outer_switch",
        "npc_inner_switch",
        "npc_clamp_diode",
    }
    assert group.metadata["voltage_checks"]["npc_inner_switch"]["passed"] is True


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
