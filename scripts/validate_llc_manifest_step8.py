"""Validate one run-scoped LLC manifest for final acceptance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_STAGES = (
    "design",
    "magnetics",
    "capacitors",
    "loss",
    "thermal",
    "geometry",
    "efficiency_sweep",
    "hardware_overview",
    "manifest",
)

REQUIRED_ARTIFACT_NAMES = (
    "llc_transformer_feasible_candidates.csv",
    "llc_transformer_pareto_front.csv",
    "llc_transformer_chosen_candidates.csv",
    "llc_transformer_leakage_rejection_audit.csv",
    "llc_external_resonant_inductor_feasible_candidates.csv",
    "llc_external_resonant_inductor_pareto_front.csv",
    "llc_external_resonant_inductor_chosen_candidates.csv",
    "llc_resonant_capacitor_feasible_candidates.csv",
    "llc_resonant_capacitor_pareto_front.csv",
    "llc_resonant_capacitor_chosen_candidates.csv",
    "llc_resonant_capacitor_near_miss_candidates.csv",
    "llc_external_resonant_inductor_recommended_geometry_2d.png",
    "llc_external_resonant_inductor_recommended_geometry_3d.png",
    "llc_resonant_capacitor_recommended_geometry_2d.png",
    "llc_resonant_capacitor_recommended_geometry_3d.png",
    "thermal_summary.csv",
    "efficiency_sweep.csv",
    "hardware_overview_payload.json",
    "overview_hardware_2d.png",
    "overview_hardware_3d.png",
    "hardware_volume_pie.png",
)


def validate_llc_manifest_file(path: str | Path) -> dict[str, Any]:
    """Return a deterministic acceptance report without modifying the manifest."""

    manifest_path = Path(path).resolve()
    failures: list[str] = []
    if not manifest_path.is_file():
        return {"valid": False, "failures": [f"manifest does not exist: {manifest_path}"]}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"valid": False, "failures": [f"manifest cannot be read: {exc}"]}

    run = payload.get("run") or {}
    run_id = str(run.get("run_id") or "")
    output_root = Path(str(run.get("output_root") or "")).resolve()
    if not run_id or not run.get("topology_id") or not run.get("input_sha256"):
        failures.append("run identity is incomplete")
    if not output_root.is_dir():
        failures.append(f"run output root does not exist: {output_root}")
    stages = payload.get("stage_status") or {}
    for stage in REQUIRED_STAGES:
        if stages.get(stage) != "succeeded":
            failures.append(f"stage {stage} is {stages.get(stage, 'missing')}")

    source_ids = payload.get("source_ids") or {}
    for key in (
        "transformer_design_id",
        "external_lr_design_id",
        "combined_magnetic_design_id",
        "cr_design_id",
        "device_design_id",
    ):
        if not source_ids.get(key):
            failures.append(f"missing source ID: {key}")

    fixed = payload.get("fixed_parameters") or {}
    cr_error = _finite_float(fixed.get("cr_error_percent"))
    if cr_error is None:
        failures.append("Cr error is unavailable")
    elif abs(cr_error) > 10.0 + 1e-9:
        failures.append(f"Cr error exceeds 10%: {cr_error:g}%")
    if _finite_float(fixed.get("total_lr_target_h")) is None or _finite_float(fixed.get("total_lr_actual_h")) is None:
        failures.append("total Lr closure values are unavailable")

    entries = payload.get("stages") or {}
    recorded_names: set[str] = set()
    for stage_name, entry in entries.items():
        for file_record in entry.get("files", []):
            file_path = Path(str(file_record.get("path") or "")).resolve()
            recorded_names.add(file_path.name)
            if not file_record.get("exists") or not file_record.get("non_empty"):
                failures.append(f"{stage_name} artifact is missing or empty: {file_path}")
            try:
                file_path.relative_to(output_root)
            except ValueError:
                failures.append(f"{stage_name} artifact is outside the current run root: {file_path}")

    for name in REQUIRED_ARTIFACT_NAMES:
        if name not in recorded_names:
            failures.append(f"required artifact is not recorded in manifest: {name}")

    efficiency = entries.get("efficiency_sweep") or {}
    if efficiency.get("result_status") != "available" or not efficiency.get("complete"):
        failures.append("efficiency sweep is incomplete")
    if (entries.get("hardware_overview") or {}).get("result_status") != "available":
        failures.append("hardware overview is unavailable")
    recorded_validation = payload.get("validation") or {}
    if recorded_validation.get("valid") is not True:
        failures.append("manifest recorded validation is not valid")

    return {
        "valid": not failures,
        "manifest_path": str(manifest_path),
        "run_id": run_id or None,
        "topology_id": run.get("topology_id"),
        "failures": failures,
    }


def _finite_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number and abs(number) != float("inf") else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    result = validate_llc_manifest_file(args.manifest)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
