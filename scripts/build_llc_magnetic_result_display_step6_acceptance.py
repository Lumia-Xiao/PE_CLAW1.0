"""Build Step 6 acceptance evidence from one current LLC E2E run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from .validate_llc_manifest_step8 import validate_llc_manifest_file
except ImportError:
    from validate_llc_manifest_step8 import validate_llc_manifest_file


REQUIRED_STAGES = (
    "design", "magnetics", "capacitors", "loss", "thermal", "geometry",
    "efficiency_sweep", "hardware_overview", "manifest",
)
REQUIRED_REPRESENTATIVE_ROLES = ("recommended", "min-volume", "min-loss")
REQUIRED_GEOMETRY_ROLES = ("min_volume", "min_loss", "recommended")


def build_acceptance_payload(
    e2e_evidence: dict[str, Any], *, test_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate one run-scoped E2E evidence payload without historical fallback."""

    failures: list[str] = []
    manifest_path = Path(str(e2e_evidence.get("manifest_path") or ""))
    manifest_validation = validate_llc_manifest_file(manifest_path)
    if not manifest_validation.get("valid"):
        failures.extend(str(item) for item in manifest_validation.get("failures", []))

    run_id = str(e2e_evidence.get("run_id") or "")
    output_root = Path(str(e2e_evidence.get("output_root") or "")).resolve()
    if manifest_validation.get("run_id") != run_id:
        failures.append("manifest run ID differs from E2E run ID")
    if not run_id:
        failures.append("run ID is unavailable")
    if not output_root.is_dir():
        failures.append(f"run output root does not exist: {output_root}")

    input_snapshot = e2e_evidence.get("input_snapshot") or {}
    for key in ("vin_min", "vin_nom", "vin_max", "vout_min", "vout_nom", "vout_max"):
        try:
            value = float(input_snapshot.get(key))
        except (TypeError, ValueError):
            failures.append(f"acceptance input is unavailable: {key}")
            continue
        if abs(value - 400.0) > 1e-9:
            failures.append(f"acceptance input is not 400 V: {key}={value:g}")

    stages = e2e_evidence.get("stage_status") or {}
    for stage in REQUIRED_STAGES:
        if stages.get(stage) != "succeeded":
            failures.append(f"stage {stage} is {stages.get(stage, 'missing')}")

    ui = e2e_evidence.get("ui_acceptance") or {}
    failures.extend(str(item) for item in ui.get("failures", []))
    if ui.get("run_id") != run_id:
        failures.append("UI acceptance run ID differs from E2E run ID")
    if Path(str(ui.get("output_root") or "")).resolve() != output_root:
        failures.append("UI acceptance output root differs from E2E output root")

    pf_artifacts = ui.get("pf_artifacts") or {}
    expected_pf_names = {
        "transformer": {
            "pareto_png_path": "llc_transformer_pareto_front.png",
            "pareto_csv_path": "llc_transformer_pareto_front.csv",
            "feasible_csv_path": "llc_transformer_feasible_candidates.csv",
            "chosen_csv_path": "llc_transformer_chosen_candidates.csv",
        },
        "external_lr": {
            "pareto_png_path": "llc_external_resonant_inductor_pareto_front.png",
            "pareto_csv_path": "llc_external_resonant_inductor_pareto_front.csv",
            "feasible_csv_path": "llc_external_resonant_inductor_feasible_candidates.csv",
            "chosen_csv_path": "llc_external_resonant_inductor_chosen_candidates.csv",
        },
    }
    for component in ("transformer", "external_lr"):
        contract = pf_artifacts.get(component) or {}
        if contract.get("status") != "available":
            failures.append(f"{component} PF artifact contract is unavailable")
        if contract.get("run_id") != run_id:
            failures.append(f"{component} PF artifact contract is stale")
        for field, record in (contract.get("files") or {}).items():
            _validate_current_file(record, output_root, failures, f"{component}.{field}")
            expected_name = expected_pf_names[component].get(field)
            if expected_name and Path(str(record.get("path") or "")).name != expected_name:
                failures.append(f"{component} PF artifact has the wrong role filename: {field}")

    representatives = ui.get("representatives") or {}
    for component in ("transformer", "external_lr"):
        for role in REQUIRED_REPRESENTATIVE_ROLES:
            entry = (representatives.get(component) or {}).get(role) or {}
            if entry.get("status") != "available" or not entry.get("design_id"):
                failures.append(f"{component} representative is unavailable: {role}")

    geometry_targets = {
        item.get("role"): item for item in (ui.get("geometry") or {}).get("targets", [])
    }
    for role in REQUIRED_GEOMETRY_ROLES:
        target = geometry_targets.get(role) or {}
        if not target.get("design_id") or target.get("error"):
            failures.append(f"external Lr geometry target is unavailable: {role}")
        if target.get("component_role") != "external_resonant_inductor":
            failures.append(f"external Lr geometry component role is invalid: {role}")
        if not target.get("artifact_paths"):
            failures.append(f"external Lr geometry has no artifacts: {role}")
        for raw_path in target.get("artifact_paths", []):
            _validate_path(Path(str(raw_path)).resolve(), output_root, failures, f"geometry.{role}")

    transformer_geometry = ui.get("transformer_geometry") or {}
    if transformer_geometry.get("status") == "unavailable" and not transformer_geometry.get("diagnostics"):
        failures.append("transformer geometry is unavailable without a diagnostic")

    structured_llc = ui.get("structured_llc") or {}
    structured_recommendations = structured_llc.get("recommendations") or {}
    expected_recommendations = {
        "transformer_design_id": ui.get("source_ids", {}).get("transformer_design_id"),
        "external_lr_design_id": ui.get("source_ids", {}).get("external_lr_design_id"),
        "combined_magnetic_design_id": ui.get("source_ids", {}).get("combined_magnetic_design_id"),
    }
    if structured_recommendations != expected_recommendations:
        failures.append("structured LLC recommendations differ from the current run IDs")

    return {
        "schema_version": "llc_magnetic_pf_representatives_step6_acceptance_v2",
        "valid": not failures,
        "failures": list(dict.fromkeys(failures)),
        "run": {
            "run_id": run_id, "output_root": str(output_root),
            "input_snapshot": input_snapshot, "stage_status": stages,
        },
        "source_ids": ui.get("source_ids") or {},
        "pf_artifacts": pf_artifacts,
        "representatives": representatives,
        "geometry": ui.get("geometry") or {},
        "transformer_geometry": transformer_geometry,
        "thermal_component_ids": ui.get("thermal_component_ids") or {},
        "structured_selection": ui.get("structured_selection") or {},
        "structured_recommendations": structured_recommendations,
        "manifest_validation": manifest_validation,
        "test_summary": test_summary or {},
    }


def _validate_current_file(record: dict[str, Any], output_root: Path, failures: list[str], label: str) -> None:
    path = Path(str(record.get("path") or "")).resolve()
    if not record.get("exists") or not record.get("non_empty"):
        failures.append(f"artifact is missing or empty: {label}")
    _validate_path(path, output_root, failures, label)


def _validate_path(path: Path, output_root: Path, failures: list[str], label: str) -> None:
    if not path.is_file() or path.stat().st_size <= 0:
        failures.append(f"artifact does not exist or is empty: {label}")
    if output_root not in path.parents:
        failures.append(f"artifact is outside the current run: {label}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--e2e-evidence", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--test-summary", type=Path, default=None)
    args = parser.parse_args()
    e2e = json.loads(args.e2e_evidence.read_text(encoding="utf-8"))
    test_summary = json.loads(args.test_summary.read_text(encoding="utf-8")) if args.test_summary else None
    payload = build_acceptance_payload(e2e, test_summary=test_summary)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "llc_magnetic_pf_representatives_step6_acceptance.json"
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "valid": payload["valid"]}, sort_keys=True))
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
