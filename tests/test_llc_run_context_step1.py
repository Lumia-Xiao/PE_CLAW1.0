from __future__ import annotations

from pathlib import Path

from pe_claw_gui.models.llc_run_context import (
    LLC_RUN_STAGES,
    LlcRunContext,
    is_llc_topology,
)
from pe_claw_gui.pipeline.run_topology_pipeline import run_topology_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.input_schema import build_default_inputs


def test_llc_context_has_fresh_identity_and_isolated_output_root(tmp_path: Path) -> None:
    output_root = tmp_path / "llc-run-context"
    first = LlcRunContext.create(
        "llc_resonant_converter_diode_rectifier",
        {"vin": 400, "pout": 1000},
        output_root=output_root / "first",
    )
    second = LlcRunContext.create(
        "llc_resonant_converter_diode_rectifier",
        {"pout": 1000, "vin": 400},
        output_root=output_root / "second",
    )

    assert first.run_id != second.run_id
    assert first.input_sha256 == second.input_sha256
    assert first.output_root == str((output_root / "first").resolve())
    assert set(first.stage_status) == set(LLC_RUN_STAGES)
    assert first.stage_status["design"] == "running"
    assert all(status == "not_started" for stage, status in first.stage_status.items() if stage != "design")
    assert first.transformer_design_id is None
    assert first.external_lr_design_id is None


def test_llc_context_transition_records_failure_reason(tmp_path: Path) -> None:
    context = LlcRunContext.create(
        "llc_resonant_converter_diode_rectifier", {}, output_root=tmp_path / "transition"
    )
    failed = context.transition("magnetics", "failed", reason="transformer search failed")

    assert failed.stage_status["magnetics"] == "failed"
    assert failed.failure_stage == "magnetics"
    assert failed.failure_reason == "transformer search failed"
    assert context.stage_status["magnetics"] == "not_started"


def test_llc_context_result_ids_accumulate_and_serialize(tmp_path: Path) -> None:
    context = LlcRunContext.create(
        "llc_resonant_converter_diode_rectifier", {}, output_root=tmp_path / "ids"
    )
    updated = context.with_result_ids(transformer_design_id="transformer-a")
    updated = updated.with_result_ids(external_lr_design_id="inductor-a")

    assert updated.transformer_design_id == "transformer-a"
    assert updated.external_lr_design_id == "inductor-a"
    assert updated.to_dict()["stage_status"] == context.stage_status


def test_llc_topology_scope_is_explicit() -> None:
    assert is_llc_topology("llc_resonant_converter_diode_rectifier")
    assert is_llc_topology("llc_resonant_converter_synchronous_rectifier")
    assert not is_llc_topology("buck_diode_rectified_unidirectional")


def test_topology_pipeline_attaches_a_new_llc_context(tmp_path: Path) -> None:
    plugin = build_default_registry().get_plugin("llc_resonant_converter_diode_rectifier")
    bundle = run_topology_pipeline(plugin, build_default_inputs(), output_root=tmp_path / "pipeline-run")

    assert bundle.report.llc_run_context is not None
    assert bundle.report.llc_run_context.topology_id == "llc_resonant_converter_diode_rectifier"
    assert bundle.report.llc_run_context.stage_status["design"] == "running"
