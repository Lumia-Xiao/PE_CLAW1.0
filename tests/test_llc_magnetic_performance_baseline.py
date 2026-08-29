from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
import pytest

from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.transformer_design import (
    LLCTransformerTurnsCandidate,
    _NormalizedCoreRecord,
    _NormalizedWireRecord,
    _NormalizedMaterialRecord,
    _build_llc_reusable_magnetic_metrics,
    _get_llc_reusable_magnetic_metrics,
    clear_llc_reusable_magnetic_metrics_cache,
    llc_reusable_magnetic_metrics_cache_info,
    _prefilter_transformer_candidate,
    _select_search_cores,
    _select_search_wires,
    build_llc_magnetic_search_bounds,
    build_transformer_design_inputs_from_fha,
)
from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.fha_design import design_llc_fha
from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.input_schema import (
    build_default_inputs,
    build_spec,
)
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_magnetic_pipeline import _llc_output_policy
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry


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


def test_llc_search_bounds_are_design_driven_and_auditable() -> None:
    inputs, _core, _wires = _prefilter_fixture()

    bounds = build_llc_magnetic_search_bounds(inputs, mode="fast")

    assert bounds.mode == "fast"
    assert bounds.transformer_core_limit is not None
    assert bounds.transformer_material_limit is not None
    assert bounds.transformer_wire_limit is not None
    assert bounds.design_basis["pout_max_w"] == inputs.pout_max_w
    serialized = bounds.to_dict()
    assert serialized["selection_policy"]
    assert serialized["transformer"]["core_limit"] == bounds.transformer_core_limit
    assert serialized["external_lr"]["max_turns"] == bounds.external_lr_max_turns


def test_llc_full_search_removes_catalog_truncation() -> None:
    inputs, _core, _wires = _prefilter_fixture()

    bounds = build_llc_magnetic_search_bounds(inputs, mode="full_search")

    assert bounds.mode == "full"
    assert bounds.transformer_core_limit is None
    assert bounds.transformer_material_limit is None
    assert bounds.transformer_wire_limit is None
    assert bounds.external_lr_core_limit is None
    assert bounds.external_lr_max_turns == 180


def test_llc_search_bounds_reject_unknown_mode() -> None:
    inputs, _core, _wires = _prefilter_fixture()

    with pytest.raises(ValueError, match="must be 'fast' or 'full'"):
        build_llc_magnetic_search_bounds(inputs, mode="database_magic")


def test_llc_fast_selection_is_stable_when_database_order_changes() -> None:
    inputs, core, wires = _prefilter_fixture()
    cores = [
        core,
        _NormalizedCoreRecord(
            core_id="larger-core",
            ae_m2=2.0e-4,
            ae_source_field="fixture",
            le_m=0.1,
            ve_m3=2.0e-5,
            window_area_m2=2.0e-4,
            outer_width_m=0.02,
            outer_height_m=0.02,
            mean_length_per_turn_m=0.04,
            gross_volume_m3=2.0e-5,
        ),
        _NormalizedCoreRecord(
            core_id="middle-core",
            ae_m2=1.5e-4,
            ae_source_field="fixture",
            le_m=0.1,
            ve_m3=1.5e-5,
            window_area_m2=1.5e-4,
            outer_width_m=0.02,
            outer_height_m=0.02,
            mean_length_per_turn_m=0.04,
            gross_volume_m3=1.5e-5,
        ),
    ]
    wires = [
        *wires,
        _NormalizedWireRecord(
            wire_id="larger-wire",
            strand_diameter_m=0.0002,
            strands_per_bundle=100,
            bundle_copper_area_m2=2.0e-5,
            outer_diameter_m=0.002,
            equivalent_bundle_diameter_m=0.002,
        ),
        _NormalizedWireRecord(
            wire_id="middle-wire",
            strand_diameter_m=0.00015,
            strands_per_bundle=100,
            bundle_copper_area_m2=1.5e-5,
            outer_diameter_m=0.0015,
            equivalent_bundle_diameter_m=0.0015,
        ),
    ]

    selected_cores = _select_search_cores(cores, inputs, 2)
    selected_cores_reversed = _select_search_cores(list(reversed(cores)), inputs, 2)
    selected_wires = _select_search_wires(wires, inputs, 2)
    selected_wires_reversed = _select_search_wires(list(reversed(wires)), inputs, 2)

    assert [item.core_id for item in selected_cores] == [item.core_id for item in selected_cores_reversed]
    assert [item.wire_id for item in selected_wires] == [item.wire_id for item in selected_wires_reversed]


def test_llc_search_selection_handles_empty_candidate_pools() -> None:
    inputs, _core, _wires = _prefilter_fixture()

    assert _select_search_cores([], inputs, 4) == []
    assert _select_search_wires([], inputs, 4) == []


def test_llc_pipeline_exposes_selected_search_bounds() -> None:
    plugin = build_default_registry().get_plugin("llc_resonant_converter_diode_rectifier")
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=build_default_inputs(),
        include_waveforms=False,
        pipeline_options=PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=False),
    )

    assert report.magnetic is not None
    bounds = report.magnetic.design_requirements["magnetic_search_bounds"]
    assert bounds["mode"] == "fast"
    assert report.magnetic.performance_timing["search_bounds"] == bounds
    output_policy = report.magnetic.design_requirements["magnetic_output_policy"]
    assert output_policy["debug_outputs_enabled"] is False
    assert output_policy["geometry_roles"] == ["recommended"]
    assert output_policy["transformer_debug_csv"] is False
    assert output_policy["transformer_pareto_artifacts"] is False
    assert output_policy["transformer_formal_csv"] is True
    assert output_policy["transformer_formal_pareto_artifacts"] is True
    assert output_policy["external_lr_artifacts"] is False
    assert output_policy["external_lr_formal_artifacts"] is True
    assert report.magnetic.performance_timing["pipeline"]["output_policy"] == output_policy


def test_llc_output_policy_defaults_to_one_formal_geometry_target() -> None:
    policy = _llc_output_policy(debug_outputs=False, geometry_roles=None)

    assert policy["debug_outputs_enabled"] is False
    assert policy["geometry_roles"] == ["recommended"]
    assert policy["transformer_debug_csv"] is False
    assert policy["transformer_pareto_artifacts"] is False
    assert policy["transformer_formal_csv"] is True
    assert policy["transformer_formal_pareto_artifacts"] is True
    assert policy["external_lr_artifacts"] is False
    assert policy["external_lr_formal_artifacts"] is True
    assert policy["diagnostic_output_root"] == ""


def test_llc_output_policy_debug_mode_restores_complete_diagnostics() -> None:
    policy = _llc_output_policy(debug_outputs=True, geometry_roles=None)

    assert policy["debug_outputs_enabled"] is True
    assert policy["geometry_roles"] == ["min-volume", "min-loss", "recommended"]
    assert policy["transformer_debug_csv"] is True
    assert policy["transformer_pareto_artifacts"] is True
    assert policy["external_lr_artifacts"] is True
    assert str(policy["diagnostic_output_root"]).endswith("outputs\\llc_diagnostics") or str(
        policy["diagnostic_output_root"]
    ).endswith("outputs/llc_diagnostics")


def test_llc_output_policy_accepts_explicit_geometry_roles() -> None:
    policy = _llc_output_policy(
        debug_outputs=False,
        geometry_roles=("min-loss", "recommended", "min-loss"),
    )

    assert policy["geometry_roles"] == ["min-loss", "recommended"]
    assert policy["transformer_debug_csv"] is False
    assert policy["transformer_formal_csv"] is True


def test_llc_output_policy_rejects_unknown_geometry_roles() -> None:
    with pytest.raises(ValueError, match="geometry roles"):
        _llc_output_policy(debug_outputs=False, geometry_roles=("all",))


def test_llc_reusable_metrics_cache_hits_and_returns_isolated_values() -> None:
    inputs, core, wires = _prefilter_fixture()
    turns = _turns(np=16, ns=4)
    clear_llc_reusable_magnetic_metrics_cache()
    first = _get_llc_reusable_magnetic_metrics(
        inputs=inputs,
        core=core,
        turns=turns,
        wires=wires,
        frequency_solver=None,
        performance_timing={},
    )
    second = _get_llc_reusable_magnetic_metrics(
        inputs=inputs,
        core=core,
        turns=turns,
        wires=wires,
        frequency_solver=None,
        performance_timing={},
    )

    info = llc_reusable_magnetic_metrics_cache_info()
    assert info["model_version"] == "llc-transformer-reusable-metrics-v1"
    assert info["units"].startswith("SI:")
    assert info["misses"] == 1
    assert info["hits"] == 1
    assert first is second
    assert isinstance(first.boundary_flux_cases, tuple)
    assert isinstance(first.primary_winding.notes, tuple)


def test_llc_reusable_metrics_cache_key_changes_for_core_turns_and_operating_point() -> None:
    inputs, core, wires = _prefilter_fixture()
    clear_llc_reusable_magnetic_metrics_cache()
    for changed_core, changed_turns, changed_inputs in (
        (core, _turns(np=16, ns=4), inputs),
        (core, _turns(np=24, ns=6), inputs),
        (_NormalizedCoreRecord(
            core_id="other-core",
            ae_m2=core.ae_m2,
            ae_source_field=core.ae_source_field,
            le_m=core.le_m,
            ve_m3=core.ve_m3,
            window_area_m2=core.window_area_m2,
            outer_width_m=core.outer_width_m,
            outer_height_m=core.outer_height_m,
            mean_length_per_turn_m=core.mean_length_per_turn_m,
            gross_volume_m3=core.gross_volume_m3,
        ), _turns(np=16, ns=4), inputs),
        (core, _turns(np=16, ns=4), replace(inputs, lm_target_h=inputs.lm_target_h * 1.01)),
    ):
        _get_llc_reusable_magnetic_metrics(
            inputs=changed_inputs,
            core=changed_core,
            turns=changed_turns,
            wires=wires,
            frequency_solver=None,
            performance_timing={},
        )
    info = llc_reusable_magnetic_metrics_cache_info()
    assert info["misses"] == 4
    assert info["hits"] == 0


def test_llc_reusable_metrics_search_reports_avoided_repeated_builds() -> None:
    inputs, core, wires = _prefilter_fixture()
    core = replace(
        core,
        ae_m2=1.0e-2,
        window_area_m2=1.0e-2,
    )
    materials = [
        _NormalizedMaterialRecord(
            material_id="material-a",
            b_sat_t=0.3,
            steinmetz_ranges=[],
        ),
        _NormalizedMaterialRecord(
            material_id="material-b",
            b_sat_t=0.3,
            steinmetz_ranges=[],
        ),
    ]
    clear_llc_reusable_magnetic_metrics_cache()
    from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.transformer_design import (
        generate_separated_llc_transformer_candidates,
    )

    result = generate_separated_llc_transformer_candidates(
        inputs,
        [core],
        materials,
        wires,
        max_scale_factor=1,
        core_limit=1,
        material_limit=2,
        wire_limit=1,
    )
    counts = result.performance_counts
    assert counts["precise_evaluated_candidate_count"] == 2
    assert counts["reusable_metrics_cache_misses"] == 1
    assert counts["reusable_metrics_cache_hits"] == 1
    assert counts["reusable_metrics_avoided_repeated_builds"] == 1
    assert result.performance_timing["reusable_metrics_cache_hit_rate"] == 0.5


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
        assert case["reusable_magnetic_metrics_cache"]["model_version"] == "llc-transformer-reusable-metrics-v1"
        assert case["reusable_magnetic_metrics_cache"]["units"].startswith("SI:")
        assert case["reusable_magnetic_metrics_cache"]["maxsize"] == 4096
        assert case["reusable_magnetic_metrics_cache"]["hits"] == case["transformer"]["counts"]["reusable_metrics_cache_hits"]
        assert case["transformer"]["counts"]["evaluated_candidate_count"] > 0
        assert case["transformer"]["timing"]["total_seconds"] >= 0.0
        assert case["transformer"]["search_bounds"]["mode"] == "explicit"
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
