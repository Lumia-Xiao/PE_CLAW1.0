"""Build final acceptance evidence for the LLC magnetic-performance plan."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.fha_design import (
    design_llc_fha,
    solve_operating_frequency,
)
from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.input_schema import (
    build_default_inputs,
    build_spec,
)
from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.transformer_design import (
    LLCMagneticSearchBounds,
    _NormalizedCoreRecord,
    _NormalizedMaterialRecord,
    _NormalizedWireRecord,
    build_transformer_design_inputs_from_fha,
    generate_llc_external_resonant_inductor_candidates,
)
from pe_claw_gui.models.magnetic_result import LlcExternalResonantInductorTarget


ROOT = Path(__file__).resolve().parents[1]
REPRESENTATIVE_FLOAT_FIELDS = (
    "total_loss_w",
    "estimated_volume_cm3",
    "hotspot_c",
)


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="ascii"))


def _write_comparison_artifacts(
    output_dir: Path,
    comparisons: list[dict[str, object]],
    regression_summary: dict[str, object] | None,
) -> tuple[Path, Path]:
    csv_path = output_dir / "llc_magnetic_performance_comparison.csv"
    csv_lines = [
        "case,transformer_before_seconds,transformer_after_seconds,transformer_speedup,"
        "external_lr_before_seconds,external_lr_after_seconds,external_lr_speedup"
    ]
    for row in comparisons:
        csv_lines.append(
            ",".join(
                str(row.get(field, ""))
                for field in (
                    "case",
                    "transformer_before_seconds",
                    "transformer_after_seconds",
                    "transformer_speedup",
                    "external_lr_before_seconds",
                    "external_lr_after_seconds",
                    "external_lr_speedup",
                )
            )
        )
    csv_path.write_text("\n".join(csv_lines) + "\n", encoding="ascii")

    markdown_path = output_dir / "llc_magnetic_performance_comparison.md"
    lines = [
        "# LLC Magnetic Performance Step 10",
        "",
        "The optimized implementation was compared with the Step 1 baseline using the same",
        "input checksums, packaged normalized magnetic database, and explicit search limits.",
        "",
        "| Case | Transformer before (s) | Transformer after (s) | Speedup | External Lr before (s) | External Lr after (s) | Speedup |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in comparisons:
        external_before = row.get("external_lr_before_seconds", "n/a")
        external_after = row.get("external_lr_after_seconds", "n/a")
        external_speedup = (
            f"{float(row['external_lr_speedup']):.2f}x"
            if "external_lr_speedup" in row
            else "n/a"
        )
        lines.append(
            f"| {row['case']} | {float(row['transformer_before_seconds']):.6f} | "
            f"{float(row['transformer_after_seconds']):.6f} | {float(row['transformer_speedup']):.2f}x | "
            f"{external_before} | {external_after} | {external_speedup} |"
        )
    lines.extend(
        [
            "",
            "## Regression",
            "",
        ]
    )
    if regression_summary is None:
        lines.append("Regression summary was not supplied to the generator.")
    else:
        lines.extend(
            [
                f"- Command: `{regression_summary['command']}`",
                f"- Result: `{regression_summary['result']}`",
                f"- Duration: `{regression_summary['duration_seconds']}` seconds",
                f"- Excluded test: `{regression_summary['excluded_test']}`",
                f"- Exclusion reason: {regression_summary['exclusion_reason']}",
            ]
        )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="ascii")
    return csv_path, markdown_path


def _assert_close(left: object, right: object, *, tolerance: float = 1.0e-9) -> None:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        scale = max(abs(float(left)), abs(float(right)), 1.0)
        if abs(float(left) - float(right)) > tolerance * scale:
            raise AssertionError(f"numeric mismatch: {left!r} != {right!r}")
        return
    if left != right:
        raise AssertionError(f"value mismatch: {left!r} != {right!r}")


def _compare_representative(before: dict[str, object] | None, after: dict[str, object] | None) -> None:
    if before is None or after is None:
        if before != after:
            raise AssertionError(f"representative presence changed: {before!r} != {after!r}")
        return
    if set(before) != set(after):
        raise AssertionError(f"representative fields changed: {set(before)} != {set(after)}")
    for field, old_value in before.items():
        _assert_close(old_value, after[field])


def _compare_case(before: dict[str, object], after: dict[str, object]) -> dict[str, object]:
    if before.get("case") != after.get("case"):
        raise AssertionError("baseline case order or names changed")
    if before.get("status") != "completed" or after.get("status") != "completed":
        raise AssertionError(f"case {after.get('case')} did not complete")
    if before.get("input_sha256") != after.get("input_sha256"):
        raise AssertionError(f"case {after.get('case')} input checksum changed")

    before_transformer = before["transformer"]
    after_transformer = after["transformer"]
    before_counts = before_transformer["counts"]
    after_counts = after_transformer["counts"]
    before_generated = before_counts.get("generated_candidate_count", before_counts.get("evaluated_candidate_count"))
    after_generated = after_counts.get("generated_candidate_count", after_counts.get("evaluated_candidate_count"))
    if before_generated != after_generated:
        raise AssertionError(f"{after.get('case')} transformer generated_candidate_count changed")
    if before_counts.get("feasible_candidate_count") != after_counts.get("feasible_candidate_count"):
        raise AssertionError(f"{after.get('case')} transformer feasible_candidate_count changed")
    before_rep = before_transformer.get("representative")
    after_rep = after_transformer.get("representative")
    try:
        _compare_representative(before_rep, after_rep)
    except AssertionError as exc:
        raise AssertionError(f"{after.get('case')} transformer representative changed: {exc}") from exc

    comparison: dict[str, object] = {
        "case": after["case"],
        "input_checksum_preserved": True,
        "transformer_generated_preserved": True,
        "transformer_feasible_preserved": True,
        "transformer_representative_preserved": True,
        "transformer_speedup": (
            float(before_transformer["timing"]["total_seconds"])
            / max(float(after_transformer["timing"]["total_seconds"]), 1.0e-12)
        ),
        "transformer_before_seconds": before_transformer["timing"]["total_seconds"],
        "transformer_after_seconds": after_transformer["timing"]["total_seconds"],
    }
    before_external = before.get("external_lr")
    after_external = after.get("external_lr")
    if before_external is None or after_external is None:
        comparison["external_lr_checked"] = False
        return comparison
    before_external_counts = before_external["counts"]
    after_external_counts = after_external["counts"]
    before_external_generated = before_external_counts.get(
        "generated_candidate_count", before_external_counts.get("evaluated_candidate_count")
    )
    after_external_generated = after_external_counts.get(
        "generated_candidate_count", after_external_counts.get("evaluated_candidate_count")
    )
    if before_external_generated != after_external_generated:
        raise AssertionError(f"{after.get('case')} external Lr generated_candidate_count changed")
    for field in ("feasible_candidate_count", "pareto_candidate_count"):
        if before_external_counts.get(field) != after_external_counts.get(field):
            raise AssertionError(f"{after.get('case')} external Lr {field} changed")
    try:
        _compare_representative(before_external.get("representative"), after_external.get("representative"))
    except AssertionError as exc:
        raise AssertionError(f"{after.get('case')} external Lr representative changed: {exc}") from exc
    comparison.update(
        {
            "external_lr_checked": True,
            "external_lr_generated_preserved": True,
            "external_lr_feasible_preserved": True,
            "external_lr_pareto_preserved": True,
            "external_lr_representative_preserved": True,
            "external_lr_speedup": (
                float(before_external["timing"]["total_seconds"])
                / max(float(after_external["timing"]["total_seconds"]), 1.0e-12)
            ),
            "external_lr_before_seconds": before_external["timing"]["total_seconds"],
            "external_lr_after_seconds": after_external["timing"]["total_seconds"],
        }
    )
    return comparison


def _external_request() -> LlcExternalResonantInductorTarget:
    return LlcExternalResonantInductorTarget(
        lr_target_h=1.2e-3,
        transformer_lk_h=0.1e-3,
        external_lr_target_h=1.1e-3,
        external_lr_target_uH=1100.0,
        lr_total_target_h=1.2e-3,
        lr_external_fraction=1.1 / 1.2,
        current_basis="step10_acceptance",
        frequency_basis="step10_acceptance",
        current_rms_a=3.0,
        current_peak_a=5.0,
        fs_basis_hz=100_000.0,
        fs_min_hz=80_000.0,
        fs_max_hz=120_000.0,
        transformer_design_id="step10-transformer",
        transformer_leakage_method="step10_acceptance",
        transformer_leakage_status="acceptable",
    )


def _external_fixture(*, window_area_m2: float) -> tuple[object, object, object]:
    core = _NormalizedCoreRecord(
        core_id="step10-core",
        ae_m2=1.0e-3,
        ae_source_field="step10",
        le_m=0.1,
        ve_m3=1.0e-5,
        window_area_m2=window_area_m2,
        outer_width_m=0.02,
        outer_height_m=0.02,
        mean_length_per_turn_m=0.04,
        gross_volume_m3=1.0e-5,
    )
    material = _NormalizedMaterialRecord(material_id="step10-material", b_sat_t=0.3, steinmetz_ranges=[])
    wire = _NormalizedWireRecord(
        wire_id="step10-wire",
        strand_diameter_m=1.0e-4,
        strands_per_bundle=100,
        bundle_copper_area_m2=1.0e-5,
        outer_diameter_m=0.01,
        equivalent_bundle_diameter_m=0.01,
    )
    return core, material, wire


def _scenario_matrix() -> list[dict[str, object]]:
    defaults = build_default_inputs()
    design = design_llc_fha(build_spec(defaults))
    scenarios: list[dict[str, object]] = []
    for name, vin_v, pout_w in (
        ("nominal_full_load", design.vin_nom_v, design.pout_max_w),
        ("low_input_full_load", design.vin_min_v, design.pout_max_w),
        ("high_input_full_load", design.vin_max_v, design.pout_max_w),
        ("nominal_light_load", design.vin_nom_v, design.pout_min_w),
    ):
        result = solve_operating_frequency(design, vin_v, design.vout_nom_v, pout_w)
        scenarios.append(
            {
                "name": name,
                "status": "executed",
                "feasible": result.feasible,
                "fs_hz": result.fs_hz,
                "gain_error": result.gain_error,
            }
        )

    disabled = generate_llc_external_resonant_inductor_candidates(
        replace(_external_request(), is_design_required=False),
        output_dir=ROOT / ".step10-disabled-output",
    )
    scenarios.append(
        {
            "name": "external_lr_disabled",
            "status": "executed",
            "is_design_required": False,
            "candidate_count": len(disabled.candidates),
            "invalid_target_count": disabled.rejection_counts["invalid_target"],
        }
    )

    core, material, wire = _external_fixture(window_area_m2=1.0e-6)
    no_feasible = generate_llc_external_resonant_inductor_candidates(
        _external_request(),
        core_records=[core],
        material_records=[material],
        wire_records=[wire],
        search_bounds=LLCMagneticSearchBounds(
            mode="full",
            max_scale_factor=8,
            transformer_core_limit=None,
            transformer_material_limit=None,
            transformer_wire_limit=None,
            external_lr_core_limit=None,
            external_lr_material_limit=None,
            external_lr_wire_limit=None,
            external_lr_max_turns=180,
            design_basis={},
            selection_policy="step10 acceptance fixture",
        ),
        output_dir=ROOT / ".step10-no-feasible-output",
    )
    scenarios.append(
        {
            "name": "external_lr_no_feasible_candidate",
            "status": "executed",
            "candidate_count": len(no_feasible.candidates),
            "feasible_count": len(no_feasible.feasible_candidates),
            "prefilter_rejection_counts": no_feasible.prefilter_rejection_counts,
        }
    )
    return scenarios


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--regression-summary", type=Path)
    args = parser.parse_args()
    before = _load(args.before)
    after = _load(args.after)
    regression_summary = _load(args.regression_summary) if args.regression_summary else None
    before_cases = before["cases"]
    after_cases = after["cases"]
    if len(before_cases) != len(after_cases):
        raise AssertionError("baseline case count changed")
    comparisons = [_compare_case(old, new) for old, new in zip(before_cases, after_cases)]
    scenarios = _scenario_matrix()
    required_scenarios = {
        "nominal_full_load",
        "low_input_full_load",
        "high_input_full_load",
        "nominal_light_load",
        "external_lr_disabled",
        "external_lr_no_feasible_candidate",
    }
    if {row["name"] for row in scenarios} != required_scenarios:
        raise AssertionError("acceptance scenario matrix is incomplete")
    no_feasible = next(row for row in scenarios if row["name"] == "external_lr_no_feasible_candidate")
    if no_feasible["feasible_count"] != 0:
        raise AssertionError("no-feasible acceptance fixture unexpectedly produced a feasible candidate")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    comparison_csv, comparison_markdown = _write_comparison_artifacts(
        args.output_dir, comparisons, regression_summary
    )
    payload = {
        "schema_version": "llc_magnetic_performance_step10_acceptance_v1",
        "before": str(args.before),
        "after": str(args.after),
        "baseline_summary": before["summary"],
        "final_summary": after["summary"],
        "case_comparisons": comparisons,
        "scenario_matrix": scenarios,
        "regression_summary": regression_summary,
        "comparison_artifacts": {
            "csv": str(comparison_csv),
            "markdown": str(comparison_markdown),
        },
        "acceptance": {
            "all_baseline_cases_completed": after["summary"] == {
                "case_count": 4,
                "completed_count": 4,
                "error_count": 0,
                "timeout_count": 0,
            },
            "candidate_and_representative_contract_preserved": True,
            "scenario_matrix_complete": True,
            "no_feasible_path_preserved": True,
            "pareto_oracle_equivalence": after["pareto_benchmark"]["equivalent_order"],
        },
    }
    output = args.output_dir / "llc_magnetic_performance_step10_acceptance.json"
    output.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="ascii")
    print(json.dumps({"output": str(output), "scenario_count": len(scenarios)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
