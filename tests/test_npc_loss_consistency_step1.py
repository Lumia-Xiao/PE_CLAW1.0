from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from dataclasses import replace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.record_npc_loss_consistency_baseline import build_baseline
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_device_pipeline import run_device_operating_point_refresh
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import _semiconductor_loss_w, run_efficiency_sweep
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import _npc_switching_loss_audit
from pe_claw_gui.engines.hardware_overview import build_hardware_overview_payload
from pe_claw_gui.app.result_views.device_view import build_device_summary_text
from pe_claw_gui.app.result_views.loss_view import build_semiconductor_loss_summary
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter.input_schema import build_default_inputs


TOPOLOGY_ID = "three_phase_three_level_npc_inverter"
NO_DOWNSTREAM = PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False)


def test_npc_loss_step1_baseline_records_contract_and_three_load_points(tmp_path: Path) -> None:
    baseline = build_baseline(output_root=tmp_path / "npc-loss-step1")

    assert baseline["topology_id"] == "three_phase_three_level_npc_inverter"
    assert baseline["loss_contract"]["device_loss_result_p_total_W"] == "one physical device"
    assert baseline["loss_contract"]["npc_physical_positions"] == {
        "npc_outer_switch": 6,
        "npc_inner_switch": 6,
        "npc_clamp_diode": 6,
    }
    assert [point["load_ratio"] for point in baseline["load_points"]] == [0.05, 0.5, 1.0]
    assert all(point["current_operating_losses_present"] for point in baseline["load_points"])
    assert all(point["event_count"] > 0 for point in baseline["load_points"])
    assert all(
        point["event_current_min_a"] < point["event_current_max_a"]
        for point in baseline["load_points"]
    )
    assert all(
        set(point["roles"]) == {"npc_outer_switch", "npc_inner_switch", "npc_clamp_diode"}
        for point in baseline["load_points"]
    )
    assert all(
        point["roles"][role]["topology_position_count"] == 6
        for point in baseline["load_points"]
        for role in ("npc_outer_switch", "npc_inner_switch", "npc_clamp_diode")
    )


def test_npc_loss_step1_baseline_exposes_current_vs_reported_aggregation(tmp_path: Path) -> None:
    baseline = build_baseline(output_root=tmp_path / "npc-loss-step1")
    points = baseline["load_points"]

    assert all(point["contract_semiconductor_loss_w"] is not None for point in points)
    assert all(point["reported_semiconductor_loss_w"] is not None for point in points)
    assert points[0]["event_current_max_a"] < points[-1]["event_current_max_a"]
    assert all(
        point["reported_semiconductor_loss_w"] == pytest.approx(point["contract_semiconductor_loss_w"])
        for point in points
    )


def test_npc_loss_step1_baseline_is_json_serializable(tmp_path: Path) -> None:
    baseline = build_baseline(output_root=tmp_path / "npc-loss-step1")
    encoded = json.dumps(baseline, ensure_ascii=True)
    assert json.loads(encoded)["schema_version"] == "npc_loss_consistency_baseline_v1"


def _report_at_load(load_ratio: float):
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=build_default_inputs(),
        include_waveforms=True,
        pipeline_options=NO_DOWNSTREAM,
    )
    operating_point = OperatingPoint(vin_v=report.spec.vin_min, load_ratio=load_ratio, power_factor=1.0)
    waveform = plugin.generate_waveforms(report.candidate, operating_point=operating_point)
    stress = plugin.extract_stress(report.candidate, waveform_set=waveform)
    return plugin, replace(report, operating_point=operating_point, waveform=waveform, stress=stress)


def test_npc_current_refresh_contains_every_selected_role_and_reuses_hardware() -> None:
    plugin, report = _report_at_load(0.5)
    assert report.device is not None
    selected_devices = dict(report.device.selected_devices)

    refreshed = run_device_operating_point_refresh(report, plugin=plugin)

    assert refreshed.device is not None
    assert refreshed.device.selected_devices == selected_devices
    assert refreshed.device.current_operating_summary is not None
    assert refreshed.device.current_operating_point_key == "current"
    assert {loss.role for loss in refreshed.device.current_operating_losses.values()} == {
        "npc_outer_switch",
        "npc_inner_switch",
        "npc_clamp_diode",
    }
    assert all(
        any("NPC event-level switching loss" in note for note in loss.thermal_design_notes)
        for loss in refreshed.device.current_operating_losses.values()
        if loss.role in {"npc_outer_switch", "npc_inner_switch"}
    )
    design_by_role = {
        loss.role: loss
        for loss in report.device.design_point_losses.values()
    }
    assert any(
        refreshed_loss.p_total_W != pytest.approx(design_by_role[refreshed_loss.role].p_total_W)
        for refreshed_loss in refreshed.device.current_operating_losses.values()
        if refreshed_loss.role in design_by_role
    )


def test_npc_step7_disabled_downstream_stages_are_not_applicable() -> None:
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=build_default_inputs(),
        include_waveforms=True,
        pipeline_options=NO_DOWNSTREAM,
        output_root=Path("pytest_temp") / "npc-step7-disabled-stages",
    )

    assert report.run_context is not None
    statuses = report.run_context.stage_status
    assert statuses["design"] == "succeeded"
    assert statuses["semiconductor_design"] == "succeeded"
    assert statuses["inductor_design"] == "not_applicable"
    assert statuses["capacitor_design"] == "not_applicable"
    assert statuses["loss"] == "not_applicable"
    assert statuses["thermal"] == "not_applicable"
    assert statuses["efficiency_sweep"] == "not_started"
    assert statuses["hardware_overview"] == "not_started"


def test_npc_step7_manifest_status_is_running_until_efficiency_and_overview_finish(tmp_path: Path) -> None:
    plugin, report = _report_at_load(0.5)
    assert report.run_context is not None
    manifest = json.loads(Path(report.run_context.manifest_path).read_text(encoding="utf-8"))
    assert manifest["status"] == "running"
    assert manifest["stage_status"]["efficiency_sweep"] == "not_started"
    assert manifest["stage_status"]["hardware_overview"] == "not_started"


def test_npc_current_refresh_failure_keeps_explicit_warning_instead_of_falling_back() -> None:
    plugin, report = _report_at_load(0.5)
    assert report.device is not None
    selected_devices = dict(report.device.selected_devices)
    selected_devices.pop("npc_inner_switch")
    report = replace(report, device=replace(report.device, selected_devices=selected_devices))

    refreshed = run_device_operating_point_refresh(report, plugin=plugin)

    assert refreshed.device is not None
    assert refreshed.device.current_operating_losses == {}
    assert any("selected device is missing for role(s): npc_inner_switch" in note for note in refreshed.device.notes)


def test_npc_current_refresh_requires_current_waveform_in_report() -> None:
    plugin, report = _report_at_load(0.5)
    assert report.device is not None
    refreshed = run_device_operating_point_refresh(replace(report, waveform=None), plugin=plugin)

    assert refreshed.device is not None
    assert refreshed.device.current_operating_losses == {}
    assert any("current waveform is missing from the report" in note for note in refreshed.device.notes)


def test_npc_scheme_and_current_aggregation_have_one_quantity_multiplier(tmp_path: Path) -> None:
    plugin, report = _report_at_load(0.5)
    assert report.device is not None
    refreshed = run_device_operating_point_refresh(report, plugin=plugin)
    assert refreshed.device is not None

    current_role_totals = {
        loss.role: loss.p_total_W * next(
            role_result.total_physical_device_count
            for scheme in refreshed.device.scheme_results
            if scheme.scheme_id == (refreshed.device.active_scheme_id or refreshed.device.recommended_scheme_id)
            for role_result in scheme.role_results
            if role_result.role == loss.role
        )
        for loss in refreshed.device.current_operating_losses.values()
    }
    assert _semiconductor_loss_w(refreshed) == pytest.approx(sum(current_role_totals.values()))

    active_scheme = next(
        scheme for scheme in refreshed.device.scheme_results
        if scheme.scheme_id == (refreshed.device.active_scheme_id or refreshed.device.recommended_scheme_id)
    )
    assert active_scheme.total_scheme_loss_w == pytest.approx(
        sum(role.total_loss_w for role in active_scheme.role_results if role.total_loss_w is not None)
    )

    payload = build_hardware_overview_payload(refreshed, tmp_path / "hardware-overview")
    group = next(group for group in payload.component_groups if group.group_id == "semiconductor")
    child_losses = [child.loss_w for child in group.child_entries if child.loss_w is not None]
    assert group.loss_w == pytest.approx(sum(child_losses))
    assert group.metadata["loss_basis_label"].startswith("current operating point")


def test_npc_semiconductor_loss_does_not_fall_back_to_design_point() -> None:
    plugin, report = _report_at_load(0.5)
    assert report.device is not None
    cleared_device = replace(
        report.device,
        current_operating_losses={},
        current_operating_point_key="current",
    )
    incomplete_report = replace(report, device=cleared_device)

    assert _semiconductor_loss_w(incomplete_report) is None


def test_npc_step7_audit_resolves_frequency_and_device_specific_reverse_recovery() -> None:
    plugin, report = _report_at_load(0.5)
    audit = _npc_switching_loss_audit(report)

    assert audit["switching_frequency_Hz"] == pytest.approx(20000.0)
    assert audit["switching_frequency_source"] == "candidate.metadata.fsw_hz"
    assert audit["reverse_recovery"]["roles"]["npc_clamp_diode"]["status"] == "zero_by_sic_device_model"
    assert audit["reverse_recovery"]["roles"]["npc_outer_switch"]["status"] == "internal_diode_qrr_model"


def test_npc_result_pages_share_loss_basis_and_totals(tmp_path: Path) -> None:
    plugin, report = _report_at_load(0.5)
    refreshed = run_device_operating_point_refresh(report, plugin=plugin)
    assert refreshed.device is not None

    device_text = build_device_summary_text(refreshed)
    loss_text = "\n".join(build_semiconductor_loss_summary(refreshed))
    payload = build_hardware_overview_payload(refreshed, tmp_path / "hardware-overview")
    group = next(group for group in payload.component_groups if group.group_id == "semiconductor")

    assert "displayed loss basis: current operating point" in device_text
    assert "Current operating-point NPC semiconductor losses" in device_text
    assert "semiconductor loss basis: current operating point" in loss_text
    assert group.metadata["loss_basis_label"].startswith("current operating point")
    assert group.metadata["loss_scope"] == "group_total"
    assert group.metadata["current_operating_losses_complete"] is True
    assert group.loss_w == pytest.approx(sum(child.loss_w for child in group.child_entries if child.loss_w is not None))

    incomplete = replace(
        refreshed,
        device=replace(
            refreshed.device,
            current_operating_losses={"current:npc_outer_switch": next(
                loss for loss in refreshed.device.current_operating_losses.values()
                if loss.role == "npc_outer_switch"
            )},
        ),
    )
    incomplete_device_text = build_device_summary_text(incomplete)
    incomplete_loss_text = "\n".join(build_semiconductor_loss_summary(incomplete))
    incomplete_payload = build_hardware_overview_payload(incomplete, tmp_path / "hardware-overview-incomplete")
    incomplete_group = next(item for item in incomplete_payload.component_groups if item.group_id == "semiconductor")

    assert "displayed loss basis: design point" in incomplete_device_text
    assert "incomplete; design-point loss values are shown" in incomplete_device_text
    assert "semiconductor loss basis: design point" in incomplete_loss_text
    assert "current operating-point NPC losses are incomplete" in incomplete_loss_text
    assert incomplete_group.metadata["loss_basis_label"].startswith("design-point")
    assert incomplete_group.metadata["current_operating_losses_complete"] is False
    assert (
        any("current npc role losses are incomplete" in warning.lower() for warning in incomplete_group.warnings)
        or any("current npc role losses are incomplete" in note.lower() for note in incomplete_group.notes)
    )


def test_npc_efficiency_point_is_incomplete_when_current_semiconductor_loss_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    plugin, report = _report_at_load(1.0)
    efficiency_module = __import__(
        "pe_claw_gui.pipeline.run_efficiency_sweep_pipeline",
        fromlist=["run_device_operating_point_refresh"],
    )
    original_refresh = efficiency_module.run_device_operating_point_refresh

    def fail_current_refresh(refreshed_report, *, plugin=None):
        failed = original_refresh(refreshed_report, plugin=plugin)
        assert failed.device is not None
        return replace(
            failed,
            device=replace(
                failed.device,
                current_operating_losses={},
                current_operating_point_key="current",
            ),
        )

    monkeypatch.setattr(efficiency_module, "run_device_operating_point_refresh", fail_current_refresh)
    result = run_efficiency_sweep(report, plugin=plugin, load_points=(0.5,), output_dir=tmp_path)

    point = result.points[0]
    assert point.semiconductor_loss_w is None
    assert point.total_loss_w is None
    assert point.efficiency is None
    assert any("design-point semiconductor loss is not used" in warning for warning in point.warnings)
