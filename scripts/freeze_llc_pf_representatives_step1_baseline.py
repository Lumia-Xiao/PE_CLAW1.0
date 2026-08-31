"""Freeze a run-scoped baseline for LLC PF and magnetic representatives."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


LLC_TOPOLOGY_ID = "llc_resonant_converter_diode_rectifier"
REQUIRED_ROLES = ("recommended", "min-volume", "min-loss")
ARTIFACTS = {
    "transformer": {
        "feasible_csv": "transformer_design/llc_transformer_feasible_candidates.csv",
        "pareto_csv": "transformer_design/llc_transformer_pareto_front.csv",
        "chosen_csv": "transformer_design/llc_transformer_chosen_candidates.csv",
        "pareto_png": "transformer_design/llc_transformer_pareto_front.png",
    },
    "external_lr": {
        "feasible_csv": "resonant_inductor_design/llc_external_resonant_inductor_feasible_candidates.csv",
        "pareto_csv": "resonant_inductor_design/llc_external_resonant_inductor_pareto_front.csv",
        "chosen_csv": "resonant_inductor_design/llc_external_resonant_inductor_chosen_candidates.csv",
        "pareto_png": "resonant_inductor_design/llc_external_resonant_inductor_pareto_front.png",
    },
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _number(value: Any) -> float | int | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return int(parsed) if parsed.is_integer() else parsed


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def _artifact_record(run_dir: Path, relative_path: str) -> dict[str, Any]:
    path = (run_dir / relative_path).resolve()
    inside_run = path == run_dir or run_dir in path.parents
    exists = path.is_file()
    return {
        "path": str(path),
        "relative_path": relative_path,
        "exists": exists,
        "non_empty": bool(exists and path.stat().st_size > 0),
        "bytes": path.stat().st_size if exists else None,
        "sha256": _sha256(path) if exists else None,
        "current_run_scoped": inside_run,
    }


def _candidate_record(row: dict[str, str], role: str, id_field: str) -> dict[str, Any]:
    return {
        "role": role,
        "design_id": row.get(id_field) or None,
        "estimated_volume_cm3": _number(row.get("estimated_volume_cm3")),
        "total_loss_w": _number(row.get("total_loss_w")),
        "hotspot_c": _number(row.get("hotspot_c")),
    }


def _role_summary(path: Path, id_field: str, role_field: str) -> dict[str, Any]:
    rows = _read_csv(path) if path.is_file() else []
    by_role: dict[str, dict[str, Any]] = {}
    for row in rows:
        role = row.get(role_field, "")
        if role in REQUIRED_ROLES and role not in by_role:
            by_role[role] = _candidate_record(row, role, id_field)
    return {
        "row_count": len(rows),
        "roles": list(by_role),
        "required_roles": list(REQUIRED_ROLES),
        "missing_roles": [role for role in REQUIRED_ROLES if role not in by_role],
        "candidates": by_role,
    }


def _load_run_payload(run_dir: Path) -> dict[str, Any]:
    payload_path = run_dir / "hardware_overview" / "hardware_overview_payload.json"
    if not payload_path.is_file():
        return {"path": str(payload_path.resolve()), "exists": False}
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    transformer_group = next(
        (group for group in payload.get("component_groups", []) if group.get("group_id") == "transformer"),
        {},
    )
    source_contract = transformer_group.get("metadata", {}).get("source_contract", {})
    return {
        "path": str(payload_path.resolve()),
        "exists": True,
        "run_id": payload.get("run_id"),
        "topology_id": payload.get("topology_id"),
        "status": payload.get("status"),
        "source_contract": {
            key: source_contract.get(key)
            for key in (
                "vin_min_v",
                "vin_nom_v",
                "vin_max_v",
                "vout_min_v",
                "vout_nom_v",
                "vout_max_v",
                "transformer_design_id",
                "external_lr_design_id",
                "combined_magnetic_design_id",
            )
        },
        "warnings": list(payload.get("dependency_diagnostics", {}).get("warnings", [])),
    }


def _manifest_status(run_dir: Path) -> dict[str, Any]:
    candidates = sorted(
        path
        for path in run_dir.rglob("*.json")
        if "manifest" in path.name.casefold() and path.name != "hardware_overview_payload.json"
    )
    return {
        "status": "available" if candidates else "unavailable",
        "path": str(candidates[0].resolve()) if candidates else None,
        "reason": None if candidates else "No run-scoped manifest JSON was generated for this baseline run.",
    }


def _display_baseline(repo_root: Path, topology_id: str) -> dict[str, Any]:
    view_path = repo_root / "src" / "pe_claw_gui" / "app" / "result_views" / "inductor_pf_view.py"
    source = view_path.read_text(encoding="utf-8") if view_path.is_file() else ""
    is_llc = topology_id == LLC_TOPOLOGY_ID
    return {
        "topology_id": topology_id,
        "is_llc": is_llc,
        "inductor_pf_view_source": str(view_path.resolve()),
        "single_generic_plot_host": "self.plot_host = ttk.Frame" in source,
        "generic_plot_resolver": "def resolve_pareto_front_path" in source,
        "notebook_tabs_present": "ttk.Notebook" in source,
        "llc_role_specific_tabs_present": is_llc and "Transformer PF" in source and "External Resonant Inductor PF" in source,
        "observed_llc_geometry_roles": ["recommended"] if is_llc else [],
    }


def freeze_baseline(run_dir: str | Path, repo_root: str | Path | None = None) -> dict[str, Any]:
    run_path = Path(run_dir).resolve()
    root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[1]
    payload = _load_run_payload(run_path)
    topology_id = payload.get("topology_id") or ""
    artifacts: dict[str, Any] = {}
    stages: dict[str, Any] = {}
    for role, names in ARTIFACTS.items():
        artifacts[role] = {name: _artifact_record(run_path, relative) for name, relative in names.items()}
        id_field, role_field = (
            ("candidate_id", "role") if role == "transformer" else ("design_id", "representative_role")
        )
        chosen_path = run_path / names["chosen_csv"]
        pareto_path = run_path / names["pareto_csv"]
        feasible_path = run_path / names["feasible_csv"]
        stages[role] = {
            "feasible_count": len(_read_csv(feasible_path)) if feasible_path.is_file() else None,
            "pareto_count": len(_read_csv(pareto_path)) if pareto_path.is_file() else None,
            "chosen": _role_summary(chosen_path, id_field, role_field),
        }
    missing_or_invalid = [
        f"{role}.{name}"
        for role, entries in artifacts.items()
        for name, entry in entries.items()
        if not entry["exists"] or not entry["non_empty"] or not entry["current_run_scoped"]
    ]
    missing_or_invalid.extend(
        f"{role}.chosen.{missing}"
        for role, stage in stages.items()
        for missing in stage["chosen"]["missing_roles"]
    )
    result = {
        "schema_version": "llc_pf_representatives_step1_baseline_v1",
        "baseline_source": "current_run_artifacts",
        "run": {
            "run_id": payload.get("run_id") or run_path.name,
            "run_path": str(run_path),
            "topology_id": topology_id or None,
            "input_checksum": None,
            "input_checksum_status": "unavailable",
            "input_checksum_reason": "Current run payload does not include an input checksum.",
            "manifest": _manifest_status(run_path),
            "source_contract": payload.get("source_contract", {}),
        },
        "artifact_contract": artifacts,
        "candidate_stages": stages,
        "current_display_behavior": _display_baseline(root, topology_id),
        "boundary_cases": [
            "complete_llc_result",
            "missing_external_lr_pf_artifact",
            "missing_representative_role",
            "non_llc_inductor_result",
        ],
        "baseline_status": "available" if not missing_or_invalid else "blocked",
        "diagnostics": {
            "missing_or_invalid": missing_or_invalid,
            "payload_status": payload.get("status"),
            "payload_warnings": payload.get("warnings", []),
        },
    }
    return result


def write_baseline(run_dir: str | Path, output_path: str | Path, repo_root: str | Path | None = None) -> dict[str, Any]:
    result = freeze_baseline(run_dir, repo_root)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args()
    result = write_baseline(args.run_dir, args.output, args.repo_root)
    print(json.dumps({"output": str(args.output.resolve()), "status": result["baseline_status"]}, sort_keys=True))
    return 0 if result["baseline_status"] == "available" else 1


if __name__ == "__main__":
    raise SystemExit(main())
