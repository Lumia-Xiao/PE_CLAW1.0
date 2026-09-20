from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.engines.magnetics.npc_output_filter_audit import (
    build_npc_output_filter_audit,
    export_npc_output_filter_audit,
)
from pe_claw_gui.engines.magnetics.inductor_adapter import build_inductor_design_request
from pe_claw_gui.pipeline import run_full_pipeline
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter import build_default_inputs


def _report(tmp_path: Path):
    plugin = build_default_registry().get_plugin("three_phase_three_level_npc_inverter")
    return run_full_pipeline(
        plugin=plugin,
        raw_input=build_default_inputs(),
        include_waveforms=True,
        pipeline_options=PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=False),
        output_root=tmp_path / "npc-run",
    )


def test_npc_step8_audit_reproduces_baseline_and_litz_tradeoff(tmp_path: Path) -> None:
    report = _report(tmp_path)
    assert report.magnetic is not None
    audit = report.magnetic.npc_output_filter_audit
    assert audit is not None
    assert audit.baseline is not None
    assert audit.litz_candidate is not None
    assert audit.baseline.core_name == "E 80/38/20"
    assert audit.baseline.turns == 34
    assert audit.baseline.parallel_bundles == 6
    assert audit.baseline.inductance_uH == pytest.approx(271.102, rel=1e-5)
    assert audit.baseline.reference_total_loss_w == pytest.approx(4.8096, rel=1e-3)
    assert "600x0.08" in audit.litz_candidate.wire_name
    assert audit.litz_candidate.parallel_bundles == 2
    assert audit.litz_candidate.reference_total_loss_w == pytest.approx(3.9393, rel=1e-3)
    assert len(audit.baseline.cases) == 5
    assert all(case.saturation_margin_percent > 0.0 for case in audit.baseline.cases)
    assert audit.output_filter.resonance_frequency_hz > audit.output_filter.control_loop_bandwidth_hz
    assert audit.output_filter.damping_check == "pass"


def test_npc_step8_artifacts_and_structured_payload_are_run_scoped(tmp_path: Path) -> None:
    report = _report(tmp_path)
    audit = report.magnetic.npc_output_filter_audit
    assert audit is not None
    assert all(Path(path).is_file() for path in audit.artifact_paths)
    assert all(Path(path).parent.name == "inductor_design" for path in audit.artifact_paths)
    payload = json.loads(Path(audit.artifact_paths[0]).read_text(encoding="ascii"))
    assert payload["baseline"]["material_checks"]["source_provenance_present"]
    assert payload["output_filter"]["damping_resistance_ohm"] > 0.0

    from pe_claw_gui.reports.structured_output import build_structured_report

    structured = build_structured_report(report)
    assert structured["magnetic"]["npc_output_filter_audit"]["status"] in {"pass", "conditional_pass"}


def test_npc_step8_direct_audit_accepts_design_request() -> None:
    from pe_claw_gui.topologies.base.registry import build_default_registry
    from pe_claw_gui.pipeline import run_topology_pipeline

    plugin = build_default_registry().get_plugin("three_phase_three_level_npc_inverter")
    bundle = run_topology_pipeline(plugin=plugin, raw_input=build_default_inputs(), include_waveforms=True)
    request = build_inductor_design_request(bundle.report)
    audit = build_npc_output_filter_audit(request, [])
    assert audit.baseline is not None
    assert audit.litz_candidate is not None
    assert audit.baseline.candidate_id == "missing_baseline"
