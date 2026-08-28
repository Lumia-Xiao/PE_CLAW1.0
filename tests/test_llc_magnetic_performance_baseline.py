from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.transformer_design import (
    LLCTransformerTurnsCandidate,
    _NormalizedCoreRecord,
    _NormalizedWireRecord,
    _prefilter_transformer_candidate,
    build_transformer_design_inputs_from_fha,
)
from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.fha_design import design_llc_fha
from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.input_schema import (
    build_default_inputs,
    build_spec,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "freeze_llc_magnetic_performance_baseline.py"


def _prefilter_fixture():
    spec = build_spec(build_default_inputs())
    inputs = build_transformer_design_inputs_from_fha(design_llc_fha(spec))
    core = _NormalizedCoreRecord(
        core_id="fixture-core",
        ae_m2=1.0e-4,
        ae_source_field="fixture",
        le_m=0.1,
        ve_m3=1.0e-5,
        window_area_m2=1.0e-4,
        outer_width_m=0.02,
        outer_height_m=0.02,
        mean_length_per_turn_m=0.04,
        gross_volume_m3=1.0e-5,
    )
    wire = _NormalizedWireRecord(
        wire_id="fixture-wire",
        strand_diameter_m=0.0001,
        strands_per_bundle=100,
        bundle_copper_area_m2=1.0e-5,
        outer_diameter_m=0.001,
        equivalent_bundle_diameter_m=0.001,
    )
    return inputs, core, [wire]


def _turns(*, np: int, ns: int = 2) -> LLCTransformerTurnsCandidate:
    return LLCTransformerTurnsCandidate(
        base_np=8,
        base_ns=2,
        scale_factor=max(1, np // 8),
        np=np,
        ns=ns,
        actual_turns_ratio=np / ns,
        ratio_error_percent=0.0,
    )


def test_transformer_prefilter_rejects_saturation_before_precise_evaluation() -> None:
    inputs, core, wires = _prefilter_fixture()
    reasons = _prefilter_transformer_candidate(
        inputs=inputs,
        core=core,
        wires=wires,
        turns=_turns(np=1),
        turns_diagnostics={"np_required_by_saturation": 100},
    )

    assert "saturation_b_limit" in reasons


def test_transformer_prefilter_keeps_boundary_candidate_when_checks_pass() -> None:
    inputs, core, wires = _prefilter_fixture()
    turns = _turns(np=100, ns=25)
    reasons = _prefilter_transformer_candidate(
        inputs=inputs,
        core=core,
        wires=wires,
        turns=turns,
        turns_diagnostics={"np_required_by_saturation": turns.np},
    )

    assert "saturation_b_limit" not in reasons
    assert "current_density_limit" not in reasons


def test_transformer_prefilter_does_not_hide_missing_wire_data() -> None:
    inputs, core, _wires = _prefilter_fixture()
    turns = _turns(np=100, ns=25)
    reasons = _prefilter_transformer_candidate(
        inputs=inputs,
        core=core,
        wires=[],
        turns=turns,
        turns_diagnostics={"np_required_by_saturation": turns.np},
    )

    assert reasons == ()


def test_transformer_prefilter_reports_current_density_rejection() -> None:
    inputs, core, wires = _prefilter_fixture()
    turns = _turns(np=100, ns=25)
    overloaded_wire = [
        _NormalizedWireRecord(
            wire_id="fixture-overloaded-wire",
            strand_diameter_m=0.00001,
            strands_per_bundle=1,
            bundle_copper_area_m2=1.0e-12,
            outer_diameter_m=0.00001,
            equivalent_bundle_diameter_m=0.00001,
        )
    ]

    reasons = _prefilter_transformer_candidate(
        inputs=inputs,
        core=core,
        wires=overloaded_wire,
        turns=turns,
        turns_diagnostics={"np_required_by_saturation": turns.np},
    )

    assert "current_density_limit" in reasons


def test_llc_baseline_script_has_bounded_repeatable_cases() -> None:
    output_dir = ROOT / ".test-llc-baseline-output"
    shutil.rmtree(output_dir, ignore_errors=True)
    try:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--case",
                "transformer-small",
                "--timeout-seconds",
                "60",
                "--output-dir",
                str(output_dir),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        output = json.loads(completed.stdout)
        assert output["summary"] == {"case_count": 1, "completed_count": 1, "error_count": 0, "timeout_count": 0}
        evidence = json.loads((output_dir / "llc_magnetic_performance_baseline.json").read_text(encoding="ascii"))
        case = evidence["cases"][0]
        assert case["status"] == "completed"
        assert case["input_sha256"]
        assert case["registered_database_counts"]["cores"] > 0
        assert case["fha_boundary_cache"]["solver_version"] == "fha-grid-scan-v1"
        assert case["fha_boundary_cache"]["maxsize"] == 512
        assert case["scalar_triangular_loss_cache"]["maxsize"] == 4096
        assert case["scalar_triangular_loss_cache"]["misses"] > 0
        assert case["scalar_triangular_loss_cache"]["size"] <= 4096
        assert case["transformer"]["counts"]["evaluated_candidate_count"] > 0
        assert case["transformer"]["timing"]["total_seconds"] >= 0.0
        counts = case["transformer"]["counts"]
        assert counts["generated_candidate_count"] == (
            counts["prefilter_rejected_candidate_count"]
            + counts["precise_evaluated_candidate_count"]
        )
        assert counts["prefilter_rejected_candidate_count"] == 0 or (
            counts["prefilter_rejected_by_saturation_count"]
            + counts["prefilter_rejected_by_lm_count"]
            + counts["prefilter_rejected_by_fill_count"]
            + counts["prefilter_rejected_by_missing_data_count"]
            > 0
        )
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)
