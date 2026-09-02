from __future__ import annotations

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.pipeline import run_full_pipeline
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter import build_default_inputs


def _report(tmp_path: Path):
    inputs = build_default_inputs()
    plugin = build_default_registry().get_plugin("three_phase_three_level_npc_inverter")
    return run_full_pipeline(
        plugin=plugin,
        raw_input=inputs,
        include_waveforms=True,
        pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
        output_root=tmp_path / "npc-run",
    )


def test_npc_thermal_has_five_scenarios_three_roles_and_corrected_loss_basis(tmp_path: Path) -> None:
    report = _report(tmp_path)
    thermal = report.thermal
    assert thermal is not None
    assert [item.scenario_id for item in thermal.npc_scenarios] == [
        "rated", "max_bus", "minimum_pf", "overload", "maximum_ambient"
    ]
    assert all(len(item.roles) == 3 for item in thermal.npc_scenarios)
    assert all(role.physical_device_count == 6 for item in thermal.npc_scenarios for role in item.roles)
    assert thermal.npc_worst_case is not None
    assert thermal.npc_worst_case.total_semiconductor_loss_w > 80.0
    assert thermal.npc_worst_case.worst_junction_temp_c < 125.0


def test_npc_thermal_scenario_inputs_change_results_and_artifacts_are_run_scoped(tmp_path: Path) -> None:
    report = _report(tmp_path)
    scenarios = {item.scenario_id: item for item in report.thermal.npc_scenarios}
    assert scenarios["minimum_pf"].total_semiconductor_loss_w > scenarios["rated"].total_semiconductor_loss_w
    assert scenarios["maximum_ambient"].worst_junction_temp_c > scenarios["rated"].worst_junction_temp_c
    assert scenarios["max_bus"].vdc_v == pytest.approx(750.0)
    assert scenarios["overload"].load_ratio == pytest.approx(1.10)
    for path in report.thermal.artifact_paths:
        assert Path(path).is_file()
        assert Path(path).parent.name == "semiconductor_design"


def test_npc_thermal_assumptions_are_structured(tmp_path: Path) -> None:
    thermal = _report(tmp_path).thermal
    assert thermal is not None
    assert thermal.npc_assumptions["heatsink_model"] == "forced_air_shared_extrusion_proxy_v1"
    assert thermal.npc_assumptions["installation_pressure_mpa"] == pytest.approx(0.35)
    assert thermal.npc_assumptions["thermal_coupling_factor"] == pytest.approx(1.15)
    assert "grease" in thermal.npc_assumptions["interface_material_stack"]
