"""Step-8 isolation: repeated and cross-topology runs own their state."""
from __future__ import annotations

from dataclasses import asdict
import copy
import json
from pathlib import Path

from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.run_topology_pipeline import run_topology_pipeline
from pe_claw_gui.pipeline.run_operating_point_refresh import run_operating_point_refresh
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import PLUGIN as T_TYPE
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter import PLUGIN as NPC
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter.input_schema import build_default_inputs as npc_inputs


def test_npc_t_type_npc_t_type_runs_are_isolated(tmp_path: Path):
    first_npc = run_topology_pipeline(NPC, npc_inputs(), include_waveforms=True, output_root=tmp_path / "npc-a")
    first_t = run_topology_pipeline(T_TYPE, {}, include_waveforms=True, output_root=tmp_path / "t-a")
    second_npc = run_topology_pipeline(NPC, npc_inputs(), include_waveforms=True, output_root=tmp_path / "npc-b")
    second_t = run_topology_pipeline(T_TYPE, {}, include_waveforms=True, output_root=tmp_path / "t-b")
    assert first_npc.report.spec.topology_id == second_npc.report.spec.topology_id
    assert first_t.report.spec.topology_id == second_t.report.spec.topology_id
    assert first_npc.report.run_context.run_id != second_npc.report.run_context.run_id
    assert first_t.report.run_context.run_id != second_t.report.run_context.run_id
    assert first_npc.report.run_context.output_root != second_npc.report.run_context.output_root
    assert first_t.report.run_context.output_root != second_t.report.run_context.output_root
    assert asdict(first_npc.waveform) == asdict(second_npc.waveform)
    assert asdict(first_t.waveform) == asdict(second_t.waveform)
    assert "three_phase_npc_pd_spwm_waveforms" in first_npc.waveform.metadata
    assert "three_phase_t_type_pd_spwm_waveforms" in first_t.waveform.metadata
    assert "npc" not in first_t.waveform.metadata
    assert "three_phase_t_type_pd_spwm_waveforms" not in first_npc.waveform.metadata
    npc_manifest = json.loads(Path(first_npc.report.run_context.manifest_path).read_text(encoding="utf-8"))
    t_manifest = json.loads(Path(first_t.report.run_context.manifest_path).read_text(encoding="utf-8"))
    assert npc_manifest["run"]["topology_id"] == NPC.topology_id
    assert t_manifest["run"]["topology_id"] == T_TYPE.topology_id
    assert Path(first_npc.report.run_context.output_root).exists()
    assert Path(first_t.report.run_context.output_root).exists()


def test_repeated_t_type_refreshes_do_not_share_mutable_payloads(tmp_path: Path):
    report = run_topology_pipeline(T_TYPE, {}, include_waveforms=False, output_root=tmp_path / "design").report
    first = run_operating_point_refresh(report, T_TYPE, OperatingPoint(vin_v=700, load_ratio=.1))
    second = run_operating_point_refresh(report, T_TYPE, OperatingPoint(vin_v=800, load_ratio=.5, power_factor=.8))
    first_snapshot = copy.deepcopy(asdict(first))
    second_snapshot = copy.deepcopy(asdict(second))
    first.waveform.metadata["three_phase_t_type_pd_spwm_waveforms"]["phases"]["a"]["current_a"][0] = -1234
    first.waveform.metadata["three_phase_t_type_pd_spwm_waveforms"]["basis"]["vdc_v"] = -1
    assert asdict(second) == second_snapshot
    assert asdict(report).get("waveform") is None
    assert second.waveform.metadata["three_phase_t_type_pd_spwm_waveforms"]["basis"]["vdc_v"] == 800
    assert first_snapshot["waveform"] != second_snapshot["waveform"]


def test_manifest_and_current_report_remain_topology_specific(tmp_path: Path):
    registry = build_default_registry()
    npc = run_topology_pipeline(registry.get_plugin("three_phase_three_level_npc_inverter"), npc_inputs(),
                                include_waveforms=False, output_root=tmp_path / "npc")
    t_type = run_topology_pipeline(registry.get_plugin("three_phase_three_level_t_type_inverter"), {},
                                   include_waveforms=False, output_root=tmp_path / "t-type")
    for bundle in (npc, t_type):
        manifest = json.loads(Path(bundle.report.run_context.manifest_path).read_text(encoding="utf-8"))
        assert manifest["run"]["topology_id"] == bundle.report.spec.topology_id
        assert manifest["run"]["run_id"] == bundle.report.run_context.run_id
        assert bundle.report.candidate.topology_id == bundle.report.spec.topology_id
