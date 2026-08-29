"""Build a small, deterministic baseline for LLC magnetic-result presentation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

from pe_claw_gui.app.result_views.inductor_view import build_inductor_summary_text
from pe_claw_gui.app.result_views.magnetic_view import MagneticView
from pe_claw_gui.models.common_spec import CommonSpec
from pe_claw_gui.models.design_report import DesignReport
from pe_claw_gui.models.geometry_result import GeometryResult, GeometryTarget
from pe_claw_gui.models.loss_result import LossResult
from pe_claw_gui.models.magnetic_result import MagneticResult
from pe_claw_gui.models.thermal_result import ThermalResult
from pe_claw_gui.reports.structured_output import build_structured_report


TRANSFORMER_ID = "E_80_38_32_SMP97_Np18_Ns18"
EXTERNAL_LR_ID = "Lr_ext_E_55_28_25_SMP97_N11_P4"
COMBINED_ID = f"{TRANSFORMER_ID}+{EXTERNAL_LR_ID}"


def build_baseline_report() -> DesignReport:
    """Return an LLC report shaped like the user-provided completed run."""

    transformer = SimpleNamespace(
        candidate_id=TRANSFORMER_ID,
        core_id="E 80/38/32",
        material_id="SMP97",
        np=18,
        ns=18,
        gap_m=2.18359e-3,
        total_loss_w=3.74375,
        estimated_volume_m3=108.8919e-6,
        hotspot_c=76.2,
        core_loss_w=2.1,
        copper_loss_w=1.64375,
    )
    external = SimpleNamespace(
        design_id=EXTERNAL_LR_ID,
        target_l_h=1.1e-3,
        total_loss_w=1.27589,
        estimated_volume_m3=41.8581e-6,
        hotspot_c=48.5,
        core_loss_w=0.7,
        copper_loss_w=0.57589,
    )
    transformer_search = SimpleNamespace(
        evaluated_candidate_count=19216,
        feasible_candidate_count=10269,
        performance_counts={
            "generated_candidate_count": 19216,
            "prefilter_rejected_candidate_count": 0,
            "prefilter_pass_count": 19216,
            "precise_evaluated_candidate_count": 19216,
            "feasible_candidate_count": 10269,
        },
        recommended_preliminary_candidate=transformer,
    )
    transformer_pareto = SimpleNamespace(
        pareto_count=16,
        recommended_candidate=transformer,
        chosen_count=16,
        recommended_policy="minimum volume/loss compromise",
    )
    external_search = SimpleNamespace(
        candidates=[external],
        feasible_candidates=[external],
        pareto_candidates=[external],
        recommended_candidate=external,
        performance_counts={
            "generated_candidate_count": 3020,
            "prefilter_rejected_candidate_count": 2764,
            "prefilter_pass_count": 256,
            "precise_evaluated_candidate_count": 256,
            "feasible_candidate_count": 186,
            "pareto_candidate_count": 18,
        },
    )
    magnetic = MagneticResult(
        summary=(
            "Separated LLC transformer first-pass magnetic screening evaluated 19216 candidates "
            "and found 10269 feasible candidates. Transformer Pareto front contains 16 candidates. "
            "Preliminary transformer recommendation: E 80/38/32/SMP97, Np:Ns=18:18, "
            "gap=2.18359 mm, loss=3.74375 W."
        ),
        result_type="separated_llc_transformer",
        design_type="separated_llc_transformer",
        design_requirements={
            "topology_id": "llc_resonant_converter_diode_rectifier",
            "design_type": "separated_llc_transformer",
            "np": 18,
            "ns": 18,
            "lm_target_h": 0.0018,
            "lr_target_h": 0.0012,
            "b_limit_t": 0.24,
            "primary_bridge_type": "full_bridge",
            "secondary_rectifier_type": "diode_rectifier",
            "boundary_saturation_cases": "nominal_full_load, low_input_full_load",
            "evaluated_candidate_count": 19216,
            "feasible_candidate_count": 10269,
        },
        basic_feasible_count=19216,
        feasible_count=10269,
        pareto_count=16,
        selected_design_id=TRANSFORMER_ID,
        llc_transformer_result=transformer_search,
        transformer_pareto_result=transformer_pareto,
        llc_external_resonant_inductor_search_result=external_search,
        artifact_paths=[
            "outputs/resonant_inductor_design/llc_external_resonant_inductor_recommended_geometry_2d.png",
            "outputs/resonant_inductor_design/llc_external_resonant_inductor_recommended_geometry_2d.svg",
            "outputs/resonant_inductor_design/llc_external_resonant_inductor_recommended_geometry_3d.png",
            "outputs/resonant_inductor_design/llc_external_resonant_inductor_recommended_geometry_3d.svg",
        ],
        performance_timing={"pipeline": {"total_seconds": 3.2}},
        notes=[
            "LLC transformer design type: separated LLC transformer.",
            "Transformer realizes Np:Ns and Lm; external resonant inductor realizes Lr.",
            "Transformer geometry is shown on the Transformer page; these artifacts are for external Lr.",
        ],
    )
    loss = LossResult(
        total_loss_w=5.01963,
        breakdown_w={
            "llc_transformer_core_loss_w": 2.1,
            "llc_transformer_copper_loss_w": 1.64375,
            "llc_transformer_total_loss_w": 3.74375,
            "llc_external_resonant_inductor_core_loss_w": 0.7,
            "llc_external_resonant_inductor_copper_loss_w": 0.57589,
            "llc_external_resonant_inductor_total_loss_w": 1.27589,
            "llc_magnetic_core_loss_w": 2.8,
            "llc_magnetic_copper_loss_w": 2.21964,
            "llc_magnetic_total_loss_w": 5.01963,
        },
        recommended_design_id=COMBINED_ID,
        recommended_design_total_volume_m3=150.75e-6,
    )
    thermal = ThermalResult(
        summary="LLC transformer thermal screening is reported on the Magnetics page.",
        ambient_temp_c=25.0,
        notes=["The fixed-inductor thermal comparison stage is not applied to LLC transformer candidates."],
    )
    geometry = GeometryResult(
        summary="External resonant inductor geometry prepared with fixed targets.",
        selected_design_id=EXTERNAL_LR_ID,
        targets=[
            GeometryTarget(
                role="recommended",
                label="Recommended",
                design_id=EXTERNAL_LR_ID,
                volume_m3=external.estimated_volume_m3,
                loss_w=external.total_loss_w,
                artifact_paths=magnetic.artifact_paths,
            )
        ],
        artifact_paths=magnetic.artifact_paths,
        notes=["Separated LLC transformer visualization remains on the Transformer page."],
    )
    spec = CommonSpec(
        topology_id="llc_resonant_converter_diode_rectifier",
        display_name="LLC Resonant Converter Diode Rectifier",
        vin_min=360.0,
        vin_max=420.0,
        vout=48.0,
        pout=4000.0,
        fs_khz=100.0,
        ripple_current_ratio=0.2,
        ripple_voltage_ratio_percent=1.0,
        raw_input={"fixture": "user-run-step1-baseline"},
    )
    return DesignReport(spec=spec, magnetic=magnetic, loss=loss, thermal=thermal, geometry=geometry)


def render_magnetic_view_text(report: DesignReport) -> str:
    captured: dict[str, str] = {}

    class CaptureView:
        def _set_text(self, value: str) -> None:
            captured["text"] = value

    MagneticView.render(CaptureView(), report)
    return captured["text"]


def build_baseline_payload(report: DesignReport | None = None) -> dict[str, object]:
    report = report or build_baseline_report()
    magnetic = report.magnetic
    assert magnetic is not None
    magnetic_view_text = render_magnetic_view_text(report)
    inductor_view_text = build_inductor_summary_text(report)
    structured = build_structured_report(report)
    return {
        "schema_version": "llc_magnetic_result_display_step1_baseline_v1",
        "baseline_source": "user_supplied_llc_run_2026-08-29",
        "fixture": "deterministic completed separated-LLC report fixture",
        "calculation_source_contract": {
            "transformer": {
                "evaluated": magnetic.llc_transformer_result.evaluated_candidate_count,
                "feasible": magnetic.llc_transformer_result.feasible_candidate_count,
                "pareto": magnetic.transformer_pareto_result.pareto_count,
                "recommended_id": TRANSFORMER_ID,
            },
            "external_lr": {
                "generated": magnetic.llc_external_resonant_inductor_search_result.performance_counts[
                    "generated_candidate_count"
                ],
                "feasible": magnetic.llc_external_resonant_inductor_search_result.performance_counts[
                    "feasible_candidate_count"
                ],
                "pareto": magnetic.llc_external_resonant_inductor_search_result.performance_counts[
                    "pareto_candidate_count"
                ],
                "recommended_id": EXTERNAL_LR_ID,
            },
            "combined": {
                "recommended_id": COMBINED_ID,
                "total_loss_w": report.loss.total_loss_w if report.loss else None,
                "volume_cm3": (report.loss.recommended_design_total_volume_m3 * 1e6 if report.loss else None),
            },
            "geometry_roles": [target.role for target in report.geometry.targets] if report.geometry else [],
        },
        "current_display_behavior": {
            "magnetic_view": {
                "contains_basic_19216": "Single-core basic feasible candidates: 19216" in magnetic_view_text,
                "shows_allow_zero": "Single-core after engineering allow screening: 0" in magnetic_view_text,
                "shows_compression_zero": "Single-core after redundancy compression: 0" in magnetic_view_text,
                "shows_final_zero": "Final combined after engineering allow screening: 0" in magnetic_view_text,
                "shows_stack_count_block": "Best Design By Stack Count" in magnetic_view_text,
                "shows_requirement_dash": "fs = - Hz" in magnetic_view_text,
            },
            "inductor_view": {
                "contains_basic_19216": "single-core basic feasible: 19216" in inductor_view_text,
                "shows_allow_zero": "single-core after allow screening: 0" in inductor_view_text,
                "shows_compression_zero": "single-core after compression: 0" in inductor_view_text,
                "shows_final_zero": "final after allow screening: 0" in inductor_view_text,
                "shows_stack_count_block": "Best by stack count" in inductor_view_text,
                "shows_requirement_dash": "fs: - Hz" in inductor_view_text,
            },
        },
        "structured_output_baseline": {
            "hardware_selection_status": structured["hardware"]["magnetic"]["selection_status"],
            "magnetic_available": structured["magnetic"]["available"],
            "selected_design_id": structured["magnetic"]["selected_design_id"],
            "feasible_count": structured["magnetic"]["metrics"]["feasible_count"]["value"],
            "pareto_count": structured["magnetic"]["metrics"]["pareto_count"]["value"],
        },
        "magnetic_view_text": magnetic_view_text,
        "inductor_view_text": inductor_view_text,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "llc_magnetic_result_display_step1_baseline.json"
    output.write_text(
        json.dumps(build_baseline_payload(), indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(json.dumps({"output": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
