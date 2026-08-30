"""Run-scoped manifest generation for LLC results."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from ..models.design_report import DesignReport
from ..models.llc_run_context import is_llc_topology


def write_llc_manifest(
    report: DesignReport,
    *,
    hardware_overview: Any | None = None,
) -> tuple[DesignReport, Path]:
    """Write a deterministic audit manifest and update the LLC manifest stage."""

    context = report.llc_run_context
    if context is None or not is_llc_topology(report.spec.topology_id):
        raise ValueError("LLC manifest requires an LLC run context.")
    manifest_dir = Path(context.output_root) / "manifest"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / "llc_manifest.json"
    payload = build_llc_manifest(report, hardware_overview=hardware_overview)
    valid, failures = _manifest_validity(payload)
    status = "succeeded" if valid else "blocked"
    reason = None if valid else "LLC manifest validation failed: " + "; ".join(failures)
    payload["stage_status"] = {
        **dict(payload.get("stage_status") or {}),
        "manifest": status,
    }
    payload["validation"] = {"valid": valid, "failures": failures}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    updated_context = replace(
        context.transition("manifest", status, reason=reason),
        manifest_path=str(path),
    )
    return replace(report, llc_run_context=updated_context), path


def build_llc_manifest(report: DesignReport, *, hardware_overview: Any | None = None) -> dict[str, object]:
    """Build a JSON-compatible manifest for one LLC run."""

    context = report.llc_run_context
    if context is None:
        raise ValueError("LLC manifest requires an LLC run context.")
    source_ids = _source_ids(report)
    fixed_parameters = _fixed_parameters(report)
    stages = _stage_entries(report, hardware_overview)
    return {
        "manifest_version": 1,
        "run": {
            "run_id": context.run_id,
            "topology_id": report.spec.topology_id,
            "input_sha256": context.input_sha256,
            "raw_input_snapshot": dict(context.raw_input_snapshot),
            "output_root": context.output_root,
        },
        "stage_status": dict(context.stage_status),
        "source_ids": source_ids,
        "fixed_parameters": fixed_parameters,
        "stages": stages,
        "warnings": _warnings(report, hardware_overview),
        "validation": {"valid": False, "failures": ["validation pending"]},
    }


def _stage_entries(report: DesignReport, hardware_overview: Any | None) -> dict[str, object]:
    magnetic = report.magnetic
    capacitor = report.capacitor
    efficiency = report.efficiency_sweep
    overview_paths = _paths_from_overview(hardware_overview)
    return {
        "design": {"status": _stage_status(report, "design"), "result_ids": {}, "files": []},
        "magnetics": {
            "status": _stage_status(report, "magnetics"),
            "result_ids": {
                "transformer_design_id": _source_ids(report)["transformer_design_id"],
                "external_lr_design_id": _source_ids(report)["external_lr_design_id"],
                "combined_magnetic_design_id": _source_ids(report)["combined_magnetic_design_id"],
            },
            "files": _file_records(getattr(magnetic, "artifact_paths", []) if magnetic is not None else []),
        },
        "capacitors": {
            "status": _stage_status(report, "capacitors"),
            "result_ids": {"cr_design_id": _source_ids(report)["cr_design_id"]},
            "files": _file_records(getattr(capacitor, "artifact_paths", []) if capacitor is not None else []),
        },
        "loss": {
            "status": _stage_status(report, "loss"),
            "result_ids": {"combined_magnetic_design_id": _source_ids(report)["combined_magnetic_design_id"]},
            "files": [],
        },
        "thermal": {
            "status": _stage_status(report, "thermal"),
            "result_ids": {"combined_magnetic_design_id": _source_ids(report)["combined_magnetic_design_id"]},
            "files": _file_records(getattr(report.thermal, "artifact_paths", []) if report.thermal is not None else []),
        },
        "geometry": {
            "status": _stage_status(report, "geometry"),
            "result_ids": {"external_lr_design_id": _source_ids(report)["external_lr_design_id"]},
            "files": _file_records(getattr(report.geometry, "artifact_paths", []) if report.geometry is not None else []),
        },
        "efficiency_sweep": {
            "status": _stage_status(report, "efficiency_sweep"),
            "result_ids": dict(_source_ids(report)),
            "files": _file_records(_efficiency_paths(efficiency)),
            "result_status": getattr(efficiency, "status", None),
            "complete": bool(efficiency is not None and efficiency.is_complete()),
        },
        "hardware_overview": {
            "status": _stage_status(report, "hardware_overview"),
            "result_ids": dict(_source_ids(report)),
            "files": _file_records(overview_paths),
            "result_status": getattr(hardware_overview, "status", None),
        },
    }


def _manifest_validity(payload: dict[str, object]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    run = payload.get("run") or {}
    if not run.get("run_id") or not run.get("topology_id") or not run.get("input_sha256"):
        failures.append("run identity is incomplete")
    statuses = payload.get("stage_status") or {}
    for stage in (
        "design",
        "magnetics",
        "capacitors",
        "loss",
        "thermal",
        "geometry",
        "efficiency_sweep",
        "hardware_overview",
    ):
        if statuses.get(stage) != "succeeded":
            failures.append(f"stage {stage} is {statuses.get(stage, 'missing')}")
    stages = payload.get("stages") or {}
    efficiency = stages.get("efficiency_sweep") or {}
    if efficiency.get("result_status") != "available" or not efficiency.get("complete"):
        failures.append("efficiency sweep is incomplete")
    for stage_name, entry in stages.items():
        for file_record in entry.get("files", []):
            if not file_record.get("exists") or not file_record.get("non_empty"):
                failures.append(f"{stage_name} artifact is missing or empty: {file_record.get('path')}")
    source_ids = payload.get("source_ids") or {}
    for key in ("transformer_design_id", "external_lr_design_id", "combined_magnetic_design_id", "cr_design_id", "device_design_id"):
        if not source_ids.get(key):
            failures.append(f"missing source ID: {key}")
    return not failures, failures


def _file_records(paths: list[str] | tuple[str, ...]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    seen: set[str] = set()
    for value in paths:
        if not value:
            continue
        path = str(value)
        if path in seen:
            continue
        seen.add(path)
        file_path = Path(path)
        exists = file_path.is_file()
        non_empty = exists and file_path.stat().st_size > 0
        records.append(
            {
                "path": path,
                "exists": exists,
                "non_empty": non_empty,
                "size_bytes": file_path.stat().st_size if exists else 0,
                "sha256": _sha256(file_path) if exists else None,
            }
        )
    return records


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _efficiency_paths(result: Any | None) -> list[str]:
    if result is None:
        return []
    return [*getattr(result, "artifact_paths", {}).values(), *getattr(result, "pf_sweep_artifact_paths", {}).values()]


def _paths_from_overview(overview: Any | None) -> list[str]:
    if overview is None:
        return []
    return [*getattr(overview, "artifact_paths", []), *getattr(overview, "overview_artifacts", {}).values(), *getattr(overview, "integrated_overview_artifacts", {}).values()]


def _source_ids(report: DesignReport) -> dict[str, str | None]:
    context = report.llc_run_context
    contract = getattr(report.magnetic, "llc_magnetic_contract", None) if report.magnetic is not None else None
    return {
        "transformer_design_id": getattr(contract, "transformer_design_id", None),
        "external_lr_design_id": getattr(contract, "external_lr_design_id", None),
        "combined_magnetic_design_id": getattr(contract, "combined_magnetic_design_id", None),
        "cr_design_id": getattr(context, "cr_design_id", None),
        "device_design_id": getattr(context, "device_design_id", None),
    }


def _fixed_parameters(report: DesignReport) -> dict[str, object]:
    contract = getattr(report.magnetic, "llc_magnetic_contract", None) if report.magnetic is not None else None
    cr_search = getattr(report.capacitor, "llc_resonant_capacitor_search_result", None) if report.capacitor is not None else None
    cr = getattr(cr_search, "recommended_candidate", None) if cr_search is not None else None
    return {
        "fs_hz": getattr(contract, "fs_hz", None) or getattr(report.candidate, "fs_hz", None),
        "lm_target_h": getattr(contract, "lm_target_h", None),
        "lm_actual_h": getattr(contract, "lm_actual_h", None),
        "total_lr_target_h": getattr(contract, "total_lr_target_h", None),
        "total_lr_actual_h": getattr(contract, "total_lr_actual_h", None),
        "cr_target_f": getattr(cr, "cr_target_f", None),
        "cr_actual_f": getattr(cr, "bank_capacitance_f", None),
        "cr_error_percent": getattr(cr, "capacitance_error_percent", None),
    }


def _stage_status(report: DesignReport, stage: str) -> str:
    return str(getattr(report.llc_run_context, "stage_status", {}).get(stage, "not_started"))


def _warnings(report: DesignReport, hardware_overview: Any | None) -> list[str]:
    warnings = list(report.notes)
    warnings.extend(getattr(report.efficiency_sweep, "warnings", ()) if report.efficiency_sweep is not None else ())
    warnings.extend(getattr(hardware_overview, "warnings", []) if hardware_overview is not None else [])
    if _llc_magnetic_result_is_available(report):
        warnings = [warning for warning in warnings if warning != _STALE_GENERIC_MAGNETIC_WARNING]
    return list(dict.fromkeys(str(item) for item in warnings if item))


_STALE_GENERIC_MAGNETIC_WARNING = "Magnetic design has not been run; magnetic loss is omitted."


def _llc_magnetic_result_is_available(report: DesignReport) -> bool:
    """Return true only when the current LLC magnetic result is complete enough for loss reporting."""

    if not is_llc_topology(report.spec.topology_id):
        return False
    magnetic = report.magnetic
    context = report.llc_run_context
    contract = getattr(magnetic, "llc_magnetic_contract", None) if magnetic is not None else None
    loss = report.loss
    return bool(
        context is not None
        and context.stage_status.get("magnetics") == "succeeded"
        and magnetic is not None
        and getattr(magnetic, "result_type", "") == "separated_llc_transformer"
        and contract is not None
        and getattr(contract, "combined_magnetic_design_id", None)
        and loss is not None
        and loss.recommended_design_id == contract.combined_magnetic_design_id
        and loss.total_loss_w is not None
    )
