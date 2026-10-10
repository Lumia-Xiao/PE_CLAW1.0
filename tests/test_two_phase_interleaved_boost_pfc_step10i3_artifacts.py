from __future__ import annotations

from importlib import import_module

from pe_claw_gui.models.design_report import DesignReport
from pe_claw_gui.models.efficiency_sweep import EfficiencySweepPoint
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import run_efficiency_sweep
from pe_claw_gui.topologies.ac_dc.single_phase_interleaved_boost_pfc_diode_bridge.input_schema import build_spec
from pe_claw_gui.topologies.ac_dc.single_phase_interleaved_boost_pfc_diode_bridge.synthesizer import synthesize


TOPOLOGY_ID = "single_phase_interleaved_boost_pfc_diode_bridge"
sweep_pipeline = import_module("pe_claw_gui.pipeline.run_efficiency_sweep_pipeline")


def test_incomplete_two_phase_point_is_blocked_without_efficiency_artifacts(tmp_path, monkeypatch) -> None:
    topology = import_module("pe_claw_gui.topologies.ac_dc.single_phase_interleaved_boost_pfc_diode_bridge")
    spec = build_spec(topology.build_default_inputs())
    report = DesignReport(spec=spec, candidate=synthesize(spec))
    incomplete = EfficiencySweepPoint(
        load_pu=0.5,
        output_power_w=500.0,
        total_loss_w=None,
        efficiency=None,
        semiconductor_loss_w=1.0,
        magnetic_loss_w=None,
        capacitor_loss_w=2.0,
        other_loss_w=0.0,
        warnings=("Selected phase inductor loss was unavailable at 0.5 p.u.",),
    )
    monkeypatch.setattr(sweep_pipeline, "_blocking_warning", lambda report, plugin: None)
    monkeypatch.setattr(
        sweep_pipeline,
        "_evaluate_sweep_load_point",
        lambda report, plugin, load_pu, npc_periodic_initial_current_a=None: (incomplete, list(incomplete.warnings)),
    )

    result = run_efficiency_sweep(report, plugin=None, load_points=(0.5,), output_dir=tmp_path / "sweep")

    assert result.status == "blocked"
    assert result.blocked_reason is not None
    assert "required loss components" in result.blocked_reason
    assert result.points[0].total_loss_w is None
    assert result.artifact_paths == {}
    assert not (tmp_path / "sweep").exists()
    assert result.topology_id == TOPOLOGY_ID
