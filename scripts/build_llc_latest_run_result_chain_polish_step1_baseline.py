"""Build a deterministic baseline for the latest LLC result-chain run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

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
RUN_ID = "255120bd9d1b45a5ac3845bf2830927d"


def _transformer() -> SimpleNamespace:
    return SimpleNamespace(
        candidate_id=TRANSFORMER_ID,
        core_id="E 80/38/32",
        material_id="SMP97",
        np=18,
        ns=18,
        gap_m=2.183590679213007e-3,
        lm_target_h=118.25562625506478e-6,
        lm_actual_h=118.25562625506478e-6,
        estimated_lk_uH=1.3799072325679307,
        total_loss_w=3.7437450963848313,
        estimated_volume_m3=108.89213208549563e-6,
        hotspot_c=54.974980385539325,
        core_loss_w=1.0008456815817937,
        copper_loss_w=2.7428994148030377,
        b_peak_t=0.08935272117377237,
    )


def _external_lr() -> SimpleNamespace:
    return SimpleNamespace(
        design_id=EXTERNAL_LR_ID,
        target_l_h=22.271218018445026e-6,
        actual_l_h=22.27121801844503e-6,
        total_lr_actual_h=23.651125251012964e-6,
        total_loss_w=1.275889037192824,
        estimated_volume_m3=41.858095528281176e-6,
        hotspot_c=46.61442743105247,
        core_loss_w=0.6754248627720233,
        copper_loss_w=0.6004641744208007,
        b_peak_t=0.08250434378774468,
        turns=11,
        wire_parallel_count=4,
    )


def build_latest_baseline_report() -> DesignReport:
    """Return a report shaped from run 255120... without reading outputs."""

    transformer = _transformer()
    external = _external_lr()
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
        chosen_count=4,
        recommended_policy="minimum volume/loss compromise",
    )
    external_search = SimpleNamespace(
        candidates=[external],
        feasible_candidates=[external],
        pareto_candidates=[external],
        chosen_candidates=[
            SimpleNamespace(role=role, candidate=external)
            for role in ("min-volume", "min-loss", "recommended", "compromise")
        ],
        recommended_candidate=external,
        min_volume_candidate=external,
        min_loss_candidate=external,
        compromise_candidate=external,
        performance_counts={
            "generated_candidate_count": 0,
            "prefilter_rejected_candidate_count": 0,
            "prefilter_pass_count": 0,
            "precise_evaluated_candidate_count": 0,
            "feasible_candidate_count": 0,
            "pareto_candidate_count": 0,
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
            "lm_target_h": 118.25562625506478e-6,
            "total_lr_target_h": 23.65112525101296e-6,
            "fs_basis_hz": 149666.6666666667,
            "b_limit_t": 0.18,
            "primary_bridge_type": "full_bridge",
            "secondary_rectifier_type": "full_bridge_rectifier",
            "boundary_case": "Vin_min/Vout_max/Pmax",
        },
        basic_feasible_count=19216,
        feasible_count=10269,
        pareto_count=16,
        selected_design_id=TRANSFORMER_ID,
        llc_transformer_result=transformer_search,
        transformer_pareto_result=transformer_pareto,
        transformer_chosen_candidates=[transformer] * 4,
        llc_external_resonant_inductor_search_result=external_search,
        artifact_paths=[
            "outputs/llc_runs/255120bd9d1b45a5ac3845bf2830927d/transformer_design/llc_transformer_pareto_front.csv",
            "outputs/llc_runs/255120bd9d1b45a5ac3845bf2830927d/resonant_inductor_design/llc_external_resonant_inductor_pareto_front.csv",
            "outputs/llc_runs/255120bd9d1b45a5ac3845bf2830927d/resonant_inductor_design/llc_external_resonant_inductor_recommended_geometry_2d.png",
        ],
        performance_timing={"pipeline": {"total_seconds": 0.0}},
        notes=[
            "LLC transformer design type: separated LLC transformer.",
            "Transformer realizes Np:Ns and Lm; external resonant inductor realizes Lr.",
            "Transformer visualization is separate from external Lr geometry.",
        ],
    )
    loss = LossResult(
        total_loss_w=5.019634133577655,
        breakdown_w={
            "llc_transformer_core_loss_w": transformer.core_loss_w,
            "llc_transformer_copper_loss_w": transformer.copper_loss_w,
            "llc_transformer_total_loss_w": transformer.total_loss_w,
            "llc_external_resonant_inductor_core_loss_w": external.core_loss_w,
            "llc_external_resonant_inductor_copper_loss_w": external.copper_loss_w,
            "llc_external_resonant_inductor_total_loss_w": external.total_loss_w,
            "llc_magnetic_core_loss_w": transformer.core_loss_w + external.core_loss_w,
            "llc_magnetic_copper_loss_w": transformer.copper_loss_w + external.copper_loss_w,
            "llc_magnetic_total_loss_w": 5.019634133577655,
        },
        recommended_design_id=COMBINED_ID,
        recommended_design_total_volume_m3=150.7502276137768e-6,
        component_volumes_m3={
            "transformer_volume_m3": transformer.estimated_volume_m3,
            "external_lr_volume_m3": external.estimated_volume_m3,
            "combined_magnetic_volume_m3": 150.7502276137768e-6,
        },
    )
    thermal = ThermalResult(
        summary="LLC transformer and external resonant-inductor thermal screening uses magnetic first-pass hotspot estimates.",
        ambient_temp_c=25.0,
        recommended_design_id=COMBINED_ID,
        llc_component_thermal={
            "transformer": {
                "status": "available",
                "design_id": TRANSFORMER_ID,
                "hotspot_c": transformer.hotspot_c,
                "source": "LLC transformer magnetic screening",
            },
            "external_lr": {
                "status": "available",
                "design_id": EXTERNAL_LR_ID,
                "hotspot_c": external.hotspot_c,
                "source": "External Lr magnetic screening first-pass hotspot estimate",
            },
        },
        notes=[
            "The separated LLC transformer screening includes a first-pass hotspot estimate.",
            "Transformer and external Lr hotspots are reported separately; no combined thermal network is inferred.",
            "Thermal summary artifact saved to outputs/llc_runs/255120bd9d1b45a5ac3845bf2830927d/thermal/thermal_summary.csv.",
        ],
    )
    geometry = GeometryResult(
        summary="External resonant inductor geometry prepared with fixed targets.",
        component_type="external_resonant_inductor",
        selected_design_id=EXTERNAL_LR_ID,
        targets=[
            GeometryTarget(
                role="recommended",
                label="Recommended",
                design_id=EXTERNAL_LR_ID,
                volume_m3=external.estimated_volume_m3,
                loss_w=external.total_loss_w,
                artifact_paths=[
                    "outputs/llc_runs/255120bd9d1b45a5ac3845bf2830927d/resonant_inductor_design/llc_external_resonant_inductor_recommended_geometry_2d.png",
                ],
            )
        ],
        artifact_paths=[
            "outputs/llc_runs/255120bd9d1b45a5ac3845bf2830927d/resonant_inductor_design/llc_external_resonant_inductor_recommended_geometry_2d.png",
        ],
        notes=["Min-volume and min-loss representatives exist in the candidate CSV but are absent from this baseline geometry view."],
    )
    spec = CommonSpec(
        topology_id="llc_resonant_converter_diode_rectifier",
        display_name="LLC Resonant Converter Diode Rectifier",
        vin_min=380.0,
        vin_max=420.0,
        vout=400.0,
        pout=4000.0,
        fs_khz=149.6666666666667,
        ripple_current_ratio=0.2,
        ripple_voltage_ratio_percent=1.0,
        raw_input={"fixture": "user-run-255120bd9d1b45a5ac3845bf2830927d"},
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
    report = report or build_latest_baseline_report()
    magnetic = report.magnetic
    assert magnetic is not None
    magnetic_view_text = render_magnetic_view_text(report)
    inductor_view_text = build_inductor_summary_text(report)
    structured = build_structured_report(report)
    return {
        "schema_version": "llc_latest_run_result_chain_polish_step1_baseline_v1",
        "baseline_source": f"user_supplied_llc_run_{RUN_ID}",
        "fixture": "deterministic completed separated-LLC report fixture",
        "calculation_source_contract": {
            "run_id": RUN_ID,
            "transformer": {
                "evaluated": 19216,
                "feasible": 10269,
                "pareto": 16,
                "recommended_id": TRANSFORMER_ID,
                "loss_w": 3.7437450963848313,
                "hotspot_c": 54.974980385539325,
            },
            "external_lr": {
                "target_uH": 22.271218018445026,
                "recommended_id": EXTERNAL_LR_ID,
                "loss_w": 1.275889037192824,
                "hotspot_c": 46.61442743105247,
            },
            "combined": {
                "recommended_id": COMBINED_ID,
                "total_loss_w": report.loss.total_loss_w if report.loss else None,
                "volume_cm3": report.loss.recommended_design_total_volume_m3 * 1e6 if report.loss else None,
            },
            "geometry_roles_present": [target.role for target in report.geometry.targets] if report.geometry else [],
        },
        "current_display_behavior": {
            "magnetic_view": {
                "shows_zero_fixed_inductor_counts": "Single-core after engineering allow screening: 0" in magnetic_view_text,
                "shows_stack_count_block": "Best Design By Stack Count" in magnetic_view_text,
                "shows_requirement_dash": "fs = - Hz" in magnetic_view_text,
            },
            "inductor_view": {
                "shows_zero_fixed_inductor_counts": "single-core after allow screening: 0" in inductor_view_text,
                "shows_stack_count_block": "Best by stack count" in inductor_view_text,
                "shows_requirement_dash": "fs: - Hz" in inductor_view_text,
            },
            "thermal_view": {
                "shows_hotspot_dash": "Recommended hotspot proxy: - C" in _render_thermal_view_text(report),
                "shows_stack_count_block": "Best Design By Stack Count" in _render_thermal_view_text(report),
            },
        },
        "structured_output_baseline": {
            "magnetic_available": structured["magnetic"]["available"],
            "selected_design_id": structured["magnetic"]["selected_design_id"],
            "hardware_selection_status": structured["hardware"]["magnetic"]["selection_status"],
        },
        "magnetic_view_text": magnetic_view_text,
        "inductor_view_text": inductor_view_text,
        "thermal_view_text": _render_thermal_view_text(report),
    }


def _render_thermal_view_text(report: DesignReport) -> str:
    from pe_claw_gui.app.result_views.thermal_view import ThermalView

    captured: dict[str, str] = {}

    class CaptureView:
        def _set_text(self, value: str) -> None:
            captured["text"] = value

    ThermalView.render(CaptureView(), report)
    return captured["text"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "llc_latest_run_result_chain_polish_step1_baseline.json"
    output.write_text(
        json.dumps(build_baseline_payload(), indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(json.dumps({"output": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
