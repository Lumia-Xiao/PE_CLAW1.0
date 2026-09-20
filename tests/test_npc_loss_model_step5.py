from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.engines.hardware_overview import build_hardware_overview_payload
from pe_claw_gui.engines.devices.loss_aggregation import semiconductor_losses_total_w
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline import run_efficiency_sweep, run_full_pipeline
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.topologies.base.registry import build_default_registry


TOPOLOGY_ID = "three_phase_three_level_npc_inverter"
NPC = import_module(
    "pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter"
)


def _report():
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    return plugin, run_full_pipeline(
        plugin=plugin,
        raw_input=NPC.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
    )


def test_npc_role_losses_use_physical_counts_and_sum_to_scheme_total() -> None:
    _, report = _report()
    assert report.device is not None
    scheme = next(item for item in report.device.scheme_results if item.scheme_id == report.device.active_scheme_id)
    role_total = sum(item.total_loss_w or 0.0 for item in scheme.role_results)
    assert scheme.total_scheme_loss_w == pytest.approx(role_total)
    assert {item.role: item.total_physical_device_count for item in scheme.role_results} == {
        "npc_outer_switch": 6,
        "npc_inner_switch": 6,
        "npc_clamp_diode": 6,
    }
    assert all(item.per_device_loss_w and item.total_loss_w == pytest.approx(item.per_device_loss_w * 6) for item in scheme.role_results)


def test_npc_loss_components_are_complete_and_deadtime_is_explicit() -> None:
    _, report = _report()
    assert report.device is not None
    for loss in report.device.design_point_losses.values():
        component_total = sum(
            getattr(loss, name, 0.0) or 0.0
            for name in (
                "p_cond_W",
                "p_sw_on_W",
                "p_sw_off_W",
                "p_rr_W",
                "p_reverse_conduction_W",
                "p_deadtime_W",
                "p_eoss_W",
                "p_gate_W",
            )
        )
        assert loss.p_total_W == pytest.approx(component_total)
    assert report.device.design_point_losses["design_point:npc_outer_switch"].p_deadtime_W > 0.0
    assert report.device.design_point_losses["design_point:npc_inner_switch"].p_deadtime_W > 0.0


def test_npc_efficiency_recomputes_loss_by_load_without_auxiliary_loss(tmp_path: Path) -> None:
    plugin, report = _report()
    result = run_efficiency_sweep(report, plugin=plugin, load_points=(0.5, 1.0), output_dir=tmp_path)
    assert result.points[0].semiconductor_loss_w < result.points[1].semiconductor_loss_w
    assert result.points[0].other_loss_w is None
    assert result.points[1].other_loss_w is None
    assert all("other" not in point.loss_breakdown_w for point in result.points)
    assert result.points[1].total_loss_w == pytest.approx(
        result.points[1].semiconductor_loss_w
        + (result.points[1].magnetic_loss_w or 0.0)
        + (result.points[1].capacitor_loss_w or 0.0)
    )
    assert result.points[1].efficiency == pytest.approx(10000.0 / (10000.0 + result.points[1].total_loss_w))


def test_npc_hardware_overview_uses_same_semiconductor_total(tmp_path: Path) -> None:
    plugin, report = _report()
    sweep = run_efficiency_sweep(report, plugin=plugin, load_points=(1.0,), output_dir=tmp_path)
    report = replace(report, efficiency_sweep=sweep)
    overview = build_hardware_overview_payload(report)
    group = next(item for item in overview.component_groups if item.group_id == "semiconductor")
    assert group.loss_w == pytest.approx(sweep.points[0].semiconductor_loss_w)
    assert sum(item.loss_w or 0.0 for item in group.child_entries) == pytest.approx(group.loss_w)


def test_npc_efficiency_boundary_reports_zero_pf_without_diverging(tmp_path: Path) -> None:
    plugin, report = _report()
    report = replace(report, operating_point=OperatingPoint(vin_v=700.0, load_ratio=1.0, power_factor=0.0))
    result = run_efficiency_sweep(report, plugin=plugin, load_points=(1.0,), output_dir=tmp_path)
    assert result.points[0].efficiency is None
    assert result.points[0].total_loss_w is None
    assert any("|PF| < 0.05" in warning for warning in result.points[0].warnings)
