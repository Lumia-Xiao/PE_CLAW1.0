from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import shutil

from scripts.build_llc_magnetic_result_display_step1_baseline import (
    COMBINED_ID,
    EXTERNAL_LR_ID,
    TRANSFORMER_ID,
    build_baseline_report,
)
from pe_claw_gui.models.magnetic_result import (
    LlcMagneticResultSummary,
    LlcMagneticStageSummary,
)
from pe_claw_gui.app.result_views.inductor_view import build_inductor_summary_text
from pe_claw_gui.app.result_views.magnetic_view import MagneticView
from pe_claw_gui.app.result_views.inductor_pf_view import (
    build_inductor_pf_summary_text,
    build_llc_pf_side_summary,
    is_llc_report,
    resolve_llc_pf_plot_paths,
)
from pe_claw_gui.pipeline.run_magnetic_pipeline import (
    _llc_external_lr_stage_summary,
    _llc_stage_summary,
    build_llc_combined_magnetic_design_id,
)
from pe_claw_gui.reports.structured_output import build_structured_report


def test_llc_stage_summary_maps_search_counts_without_fixed_inductor_fields() -> None:
    report = build_baseline_report()
    transformer_search = report.magnetic.llc_transformer_result
    external_search = report.magnetic.llc_external_resonant_inductor_search_result

    transformer = _llc_stage_summary(
        transformer_search,
        pareto_count=16,
        recommended_design_id=TRANSFORMER_ID,
        status="available",
    )
    external = _llc_external_lr_stage_summary(
        None,
        external_search,
    )

    assert transformer.generated_candidate_count == 19216
    assert transformer.prefilter_rejected_candidate_count == 0
    assert transformer.prefilter_pass_count == 19216
    assert transformer.precise_evaluated_candidate_count == 19216
    assert transformer.feasible_candidate_count == 10269
    assert transformer.pareto_candidate_count == 16
    assert transformer.chosen_candidate_count == 0
    assert external.generated_candidate_count == 3020
    assert external.prefilter_rejected_candidate_count == 2764
    assert external.prefilter_pass_count == 256
    assert external.precise_evaluated_candidate_count == 256
    assert external.feasible_candidate_count == 186
    assert external.pareto_candidate_count == 18
    assert external.chosen_candidate_count == 0
    assert external.status == "available"


def test_llc_stage_summary_accepts_real_transformer_and_external_chosen_counts() -> None:
    report = build_baseline_report()
    transformer_search = report.magnetic.llc_transformer_result
    external_search = report.magnetic.llc_external_resonant_inductor_search_result
    transformer = _llc_stage_summary(
        transformer_search,
        pareto_count=16,
        chosen_count=4,
        recommended_design_id=TRANSFORMER_ID,
        status="available",
    )
    external_search.chosen_candidates = [object(), object(), object(), object()]
    external = _llc_external_lr_stage_summary(None, external_search)
    assert transformer.chosen_candidate_count == 4
    assert external.chosen_candidate_count == 4


def test_combined_id_requires_both_recommendations_and_available_external_lr() -> None:
    assert build_llc_combined_magnetic_design_id(
        TRANSFORMER_ID,
        EXTERNAL_LR_ID,
        "available",
    ) == COMBINED_ID
    assert build_llc_combined_magnetic_design_id(TRANSFORMER_ID, None, "available") is None
    assert build_llc_combined_magnetic_design_id(TRANSFORMER_ID, EXTERNAL_LR_ID, "not_required") is None
    assert build_llc_combined_magnetic_design_id(None, EXTERNAL_LR_ID, "available") is None


def test_llc_structured_output_exposes_dedicated_counts_and_recommendations() -> None:
    report = build_baseline_report()
    magnetic = report.magnetic
    summary = LlcMagneticResultSummary(
        transformer=LlcMagneticStageSummary(
            status="available",
            generated_candidate_count=19216,
            prefilter_pass_count=19216,
            precise_evaluated_candidate_count=19216,
        feasible_candidate_count=10269,
        pareto_candidate_count=16,
        chosen_candidate_count=4,
        recommended_design_id=TRANSFORMER_ID,
        ),
        external_lr=LlcMagneticStageSummary(
            status="available",
            generated_candidate_count=3020,
            prefilter_rejected_candidate_count=2764,
            prefilter_pass_count=256,
            precise_evaluated_candidate_count=256,
        feasible_candidate_count=186,
        pareto_candidate_count=18,
        chosen_candidate_count=4,
        recommended_design_id=EXTERNAL_LR_ID,
        ),
        recommended_transformer_design_id=TRANSFORMER_ID,
        recommended_external_lr_design_id=EXTERNAL_LR_ID,
        recommended_combined_magnetic_design_id=COMBINED_ID,
    )
    report = replace(
        report,
        magnetic=replace(
            magnetic,
            llc_result_summary=summary,
            recommended_transformer_design_id=TRANSFORMER_ID,
            recommended_external_lr_design_id=EXTERNAL_LR_ID,
            recommended_combined_magnetic_design_id=COMBINED_ID,
        ),
    )

    payload = build_structured_report(report)
    llc = payload["magnetic"]["llc"]
    assert llc["transformer"]["metrics"]["generated_candidates"]["value"] == 19216.0
    assert llc["transformer"]["metrics"]["prefilter_rejected_candidates"]["value"] == 0.0
    assert llc["external_lr"]["metrics"]["prefilter_rejected_candidates"]["value"] == 2764.0
    assert llc["recommendations"] == {
        "transformer_design_id": TRANSFORMER_ID,
        "external_lr_design_id": EXTERNAL_LR_ID,
        "combined_magnetic_design_id": COMBINED_ID,
    }
    assert payload["hardware"]["magnetic"] == {
        "selected_design_id": COMBINED_ID,
        "chosen_design_ids": [TRANSFORMER_ID, EXTERNAL_LR_ID],
        "selection_status": "pass",
    }


def test_llc_external_lr_not_required_has_no_combined_id() -> None:
    assert build_llc_combined_magnetic_design_id(TRANSFORMER_ID, EXTERNAL_LR_ID, "not_required") is None


def _report_with_llc_display_summary():
    report = build_baseline_report()
    magnetic = report.magnetic
    summary = LlcMagneticResultSummary(
        transformer=LlcMagneticStageSummary(
            status="available",
            generated_candidate_count=19216,
            prefilter_pass_count=19216,
            precise_evaluated_candidate_count=19216,
        feasible_candidate_count=10269,
        pareto_candidate_count=16,
        chosen_candidate_count=4,
        recommended_design_id=TRANSFORMER_ID,
        ),
        external_lr=LlcMagneticStageSummary(
            status="available",
            generated_candidate_count=3020,
            prefilter_rejected_candidate_count=2764,
            prefilter_pass_count=256,
            precise_evaluated_candidate_count=256,
        feasible_candidate_count=186,
        pareto_candidate_count=18,
        chosen_candidate_count=4,
        recommended_design_id=EXTERNAL_LR_ID,
        ),
        recommended_transformer_design_id=TRANSFORMER_ID,
        recommended_external_lr_design_id=EXTERNAL_LR_ID,
        recommended_combined_magnetic_design_id=COMBINED_ID,
    )
    return replace(report, magnetic=replace(magnetic, llc_result_summary=summary))


def test_llc_views_share_dedicated_counts_and_recommendations() -> None:
    report = _report_with_llc_display_summary()
    captured: dict[str, str] = {}

    class CaptureView:
        def _set_text(self, value: str) -> None:
            captured["magnetic"] = value

    MagneticView.render(CaptureView(), report)
    inductor_text = build_inductor_summary_text(report)
    assert captured["magnetic"] == inductor_text
    assert "Candidate counts" in inductor_text
    assert "Transformer: available" in inductor_text
    assert "generated candidates: 19216" in inductor_text
    assert "prefilter rejected candidates: 2764" in inductor_text
    assert "precise evaluated candidates: 256" in inductor_text
    assert "feasible candidates: 186" in inductor_text
    assert "Pareto candidates: 18" in inductor_text
    assert f"Transformer: {TRANSFORMER_ID}" in inductor_text
    assert f"External resonant inductor: {EXTERNAL_LR_ID}" in inductor_text
    assert f"Combined magnetic design: {COMBINED_ID}" in inductor_text
    assert "single-core after engineering allow screening" not in inductor_text
    assert "redundancy compression" not in inductor_text
    assert "Best by stack count" not in inductor_text


def test_llc_view_does_not_show_zero_counts_for_not_required_external_lr() -> None:
    report = _report_with_llc_display_summary()
    magnetic = report.magnetic
    summary = magnetic.llc_result_summary
    summary = replace(
        summary,
        external_lr=LlcMagneticStageSummary(status="not_required"),
        recommended_external_lr_design_id=None,
        recommended_combined_magnetic_design_id=None,
    )
    report = replace(report, magnetic=replace(magnetic, llc_result_summary=summary))
    text = build_inductor_summary_text(report)
    assert "External resonant inductor: not required" in text
    assert "External resonant inductor: N/A (not required)" in text
    assert "External resonant inductor: N/A (not required)\n    generated candidates" not in text
    assert "Combined magnetic design: N/A (not required)" in text


def test_llc_pareto_view_uses_component_counts_and_recommendations() -> None:
    report = _report_with_llc_display_summary()
    text = build_inductor_pf_summary_text(report)

    assert "result type: separated LLC transformer + external resonant inductor" in text
    assert "Transformer Pareto count: 16" in text
    assert "Transformer chosen count: 4" in text
    assert "External resonant inductor Pareto count: 18" in text
    assert "External resonant inductor chosen count: 4" in text
    assert f"Transformer: {TRANSFORMER_ID}" in text
    assert f"External resonant inductor: {EXTERNAL_LR_ID}" in text
    assert f"Combined magnetic design: {COMBINED_ID}" in text
    assert "chosen design count: 0" not in text
    assert "fixed-inductor" not in text


def test_llc_structured_stage_payload_exposes_chosen_counts() -> None:
    report = _report_with_llc_display_summary()
    payload = build_structured_report(report)
    llc = payload["magnetic"]["llc"]

    assert llc["transformer"]["metrics"]["chosen_candidates"]["value"] == 4.0
    assert llc["external_lr"]["metrics"]["chosen_candidates"]["value"] == 4.0


def test_llc_pf_paths_are_resolved_by_role() -> None:
    report = _report_with_llc_display_summary()
    magnetic = report.magnetic
    transformer_path = Path("transformer") / "llc_transformer_pareto_front.png"
    external_path = Path("external") / "llc_external_resonant_inductor_pareto_front.png"
    magnetic.transformer_pareto_result.artifact_paths = [str(transformer_path)]
    magnetic.llc_external_resonant_inductor_search_result.artifact_paths = [str(external_path)]
    # The resolver is intentionally path-contract based; existence is checked at consumption time.
    paths = resolve_llc_pf_plot_paths(report)
    assert paths == {"transformer": None, "external_lr": None}


def test_llc_pf_paths_resolve_existing_role_specific_images(tmp_path: Path) -> None:
    root = tmp_path / "llc-step2"
    transformer_path = root / "transformer" / "llc_transformer_pareto_front.png"
    external_path = root / "external" / "llc_external_resonant_inductor_pareto_front.png"
    transformer_path.parent.mkdir(parents=True)
    external_path.parent.mkdir(parents=True)
    transformer_path.write_bytes(b"transformer-png")
    external_path.write_bytes(b"external-png")
    report = _report_with_llc_display_summary()
    magnetic = report.magnetic
    magnetic.transformer_pareto_result.artifact_paths = [str(transformer_path)]
    magnetic.llc_external_resonant_inductor_search_result.artifact_paths = [str(external_path)]
    paths = resolve_llc_pf_plot_paths(report)
    assert paths == {"transformer": transformer_path, "external_lr": external_path}


def test_llc_pf_side_summary_keeps_role_identity_when_artifact_is_missing() -> None:
    report = _report_with_llc_display_summary()
    transformer = build_llc_pf_side_summary(report, "transformer")
    external = build_llc_pf_side_summary(report, "external_lr")
    assert "Transformer PF" in transformer
    assert "External Resonant Inductor PF" in external
    assert "transformer" not in external.casefold() or "external" in external.casefold()
    assert "Unavailable" in transformer
    assert "Unavailable" in external


def test_llc_result_type_uses_role_tabs_even_when_summary_is_missing() -> None:
    report = build_baseline_report()
    report = replace(report, magnetic=replace(report.magnetic, llc_result_summary=None))
    assert is_llc_report(report) is True
    assert resolve_llc_pf_plot_paths(report) == {"transformer": None, "external_lr": None}
    assert "summary is missing" in build_llc_pf_side_summary(report, "transformer")
