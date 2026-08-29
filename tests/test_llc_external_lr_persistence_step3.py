from __future__ import annotations

import csv
from pathlib import Path
from types import SimpleNamespace

from pe_claw_gui.pipeline.run_magnetic_pipeline import (
    _llc_external_lr_output_dir,
    _validate_llc_external_lr_artifacts,
)


REQUIRED_FILES = (
    "llc_external_resonant_inductor_feasible_candidates.csv",
    "llc_external_resonant_inductor_pareto_front.csv",
    "llc_external_resonant_inductor_chosen_candidates.csv",
)
ROLES = ("recommended", "min-volume", "min-loss")


def _search_result(root: Path):
    candidates = [SimpleNamespace(design_id=f"lr-{role}") for role in ROLES]
    selections = [
        SimpleNamespace(role=role, candidate=candidate)
        for role, candidate in zip(ROLES, candidates)
    ]
    paths = []
    for name in REQUIRED_FILES:
        path = root / name
        if name.endswith("chosen_candidates.csv"):
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["representative_role", "design_id"])
                writer.writeheader()
                for role in ROLES:
                    writer.writerow({"representative_role": role, "design_id": f"lr-{role}"})
        else:
            path.write_text("header\nvalue\n", encoding="utf-8")
        paths.append(str(path))
    return SimpleNamespace(
        artifact_paths=paths,
        chosen_candidates=selections,
        feasible_candidates=candidates,
    )


def test_external_lr_artifacts_require_csv_set_and_representative_roles(tmp_path: Path) -> None:
    result = _search_result(tmp_path)

    assert _validate_llc_external_lr_artifacts(result) == {"valid": True, "reason": ""}

    result.artifact_paths = [
        path for path in result.artifact_paths
        if Path(path).name != "llc_external_resonant_inductor_chosen_candidates.csv"
    ]
    validation = _validate_llc_external_lr_artifacts(result)
    assert validation["valid"] is False
    assert "chosen_candidates.csv" in str(validation["reason"])


def test_external_lr_artifacts_reject_stale_chosen_design_id(tmp_path: Path) -> None:
    result = _search_result(tmp_path)
    result.chosen_candidates[0].candidate = SimpleNamespace(design_id="stale-id")

    validation = _validate_llc_external_lr_artifacts(result)
    assert validation["valid"] is False
    assert "absent from feasible" in str(validation["reason"])


def test_external_lr_geometry_output_uses_run_scoped_context(tmp_path: Path) -> None:
    context = SimpleNamespace(output_root=str(tmp_path.resolve()))
    report = SimpleNamespace(llc_run_context=context)

    assert _llc_external_lr_output_dir(report) == tmp_path.resolve() / "resonant_inductor_design"
