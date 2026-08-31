from __future__ import annotations

import csv
from pathlib import Path
from types import SimpleNamespace

from pe_claw_gui.models.llc_run_context import LlcRunContext
from pe_claw_gui.pipeline.run_magnetic_pipeline import (
    _llc_transformer_failure_result,
    _llc_transformer_output_dir,
    _validate_llc_transformer_artifacts,
)


REQUIRED_FILES = (
    "llc_transformer_feasible_candidates.csv",
    "llc_transformer_pareto_front.csv",
    "llc_transformer_chosen_candidates.csv",
    "llc_transformer_leakage_rejection_audit.csv",
)


def _pareto_result():
    candidates = [SimpleNamespace(candidate_id=f"candidate-{role}") for role in ("recommended", "min-volume", "min-loss")]
    selections = [
        SimpleNamespace(role=role, candidate=candidate)
        for role, candidate in zip(("recommended", "min-volume", "min-loss"), candidates)
    ]
    return SimpleNamespace(chosen_candidates=selections, feasible_candidates=candidates)


def _write_required_artifacts(root: Path) -> list[str]:
    paths = []
    for name in REQUIRED_FILES:
        path = root / name
        if name == "llc_transformer_chosen_candidates.csv":
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["role", "candidate_id", "estimated_volume_cm3", "total_loss_w", "hotspot_c"],
                )
                writer.writeheader()
                for role in ("recommended", "min-volume", "min-loss"):
                    writer.writerow({
                        "role": role,
                        "candidate_id": f"candidate-{role}",
                        "estimated_volume_cm3": "10",
                        "total_loss_w": "2",
                        "hotspot_c": "40",
                    })
        else:
            path.write_text("header\nvalue\n", encoding="utf-8")
        paths.append(str(path))
    return paths


def test_transformer_artifacts_require_all_files_and_representative_roles(tmp_path: Path) -> None:
    pareto_result = _pareto_result()
    paths = _write_required_artifacts(tmp_path)

    assert _validate_llc_transformer_artifacts(paths, pareto_result) == {"valid": True, "reason": ""}

    missing = [path for path in paths if Path(path).name != "llc_transformer_chosen_candidates.csv"]
    validation = _validate_llc_transformer_artifacts(missing, pareto_result)
    assert validation["valid"] is False
    assert "llc_transformer_chosen_candidates.csv" in str(validation["reason"])


def test_transformer_failure_result_has_structured_status_and_no_recommendation() -> None:
    result = _llc_transformer_failure_result(
        failure_code="no_feasible_candidate",
        failure_reason="No transformer candidate passed.",
    )

    stage = result.llc_result_summary.transformer
    assert stage.status == "no_feasible_candidate"
    assert stage.failure_code == "no_feasible_candidate"
    assert stage.failure_reason == "No transformer candidate passed."
    assert result.recommended_transformer_design_id is None
    assert result.selected_design_id is None


def test_transformer_output_uses_run_scoped_context(tmp_path: Path) -> None:
    context = LlcRunContext.create("llc_resonant_converter_diode_rectifier", {}, output_root=tmp_path)
    report = SimpleNamespace(llc_run_context=context)

    assert _llc_transformer_output_dir(report) == tmp_path.resolve() / "transformer_design"
