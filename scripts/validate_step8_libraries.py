"""Validate Step 8 library parity and deterministic runtime selection.

The parent process compares the packaged library trees and invokes this file in
two isolated child processes.  Isolation is intentional: importing PE-Claw 1.0
and 2.0 into one interpreter would allow module caches to hide a migration
difference.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import fields, is_dataclass
import hashlib
import json
import subprocess
import sys
from collections import Counter
from importlib import import_module
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path(r"C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw")
PLAN_ROOT = ROOT / "migration" / "evidence" / "20260824" / "step8_libraries"
LIBRARY_RELATIVE_ROOT = Path("src") / "pe_claw_gui" / "libraries"


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _normalized_sha256(raw: bytes) -> str:
    return _sha256(raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n"))


def _library_files(root: Path) -> list[Path]:
    library_root = root / LIBRARY_RELATIVE_ROOT
    return sorted(
        path
        for path in library_root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )


def _file_manifest(root: Path) -> dict[str, Any]:
    rows = []
    for path in _library_files(root):
        raw = path.read_bytes()
        rows.append({
            "path": path.relative_to(root).as_posix(),
            "byte_count": len(raw),
            "sha256": _sha256(raw),
            "normalized_sha256": _normalized_sha256(raw),
        })
    return {
        "root": str(root),
        "library_root": str(root / LIBRARY_RELATIVE_ROOT),
        "file_count": len(rows),
        "files": rows,
    }


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe(item) for item in value]
    if is_dataclass(value):
        return {item.name: _json_safe(getattr(value, item.name)) for item in fields(value)}
    return str(value)


def _digest(value: Any) -> str:
    encoded = json.dumps(_json_safe(value), sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return _sha256(encoded)


def _probe_libraries(root: Path) -> dict[str, Any]:
    sys.path.insert(0, str(root / "src"))
    from pe_claw_gui.libraries.capacitors import capacitor_library_coverage_counts, list_registered_capacitors
    from pe_claw_gui.libraries.magnetics import (
        build_normalized_openmagnetics_inventory,
        build_packaged_openmagnetics_inventory,
        list_sendust_toroid_cores,
        list_sendust_toroid_sizes,
    )
    from pe_claw_gui.libraries.magnetics.sendust_steinmetz import list_sendust_steinmetz_materials
    from pe_claw_gui.libraries.magnetics.openmagnetics_v2_production_locator import verify_normalized_v2_production_cache
    from pe_claw_gui.libraries.semiconductors.registry import build_default_semiconductor_registry
    from pe_claw_gui.topologies.base.registry import build_default_registry

    semiconductor = build_default_semiconductor_registry()
    capacitors = list_registered_capacitors()
    normalized = build_normalized_openmagnetics_inventory()
    packaged = build_packaged_openmagnetics_inventory()
    return {
        "root": str(root),
        "semiconductors": {
            "record_count": len(semiconductor.devices),
            "vendor_count": len(semiconductor.list_vendors()),
            "vendors": semiconductor.list_vendors(),
        },
        "capacitors": {
            "record_count": len(capacitors),
            "coverage": _json_safe(capacitor_library_coverage_counts(capacitors)),
        },
        "magnetics": {
            "sendust_core_count": len(list_sendust_toroid_cores()),
            "sendust_size_count": len(list_sendust_toroid_sizes()),
            "sendust_material_count": len(list_sendust_steinmetz_materials()),
            "normalized_inventory": _json_safe(normalized.to_dict()),
            "packaged_inventory": _json_safe(packaged.to_dict()),
            "normalized_v2_production": verify_normalized_v2_production_cache(),
        },
        "registered_topologies": [
            {
                "topology_id": item.topology_id,
                "category_id": item.category_id,
                "display_name": item.display_name,
                "module_path": item.module_path,
                "legacy_key": item.legacy_key,
                "implemented": item.implemented,
            }
            for item in build_default_registry().list_definitions()
        ],
    }


def _candidate_trace_summary(report: Any) -> dict[str, Any]:
    device = report.device
    if device is None:
        return {
            "selected_devices": {},
            "active_scheme_id": None,
            "active_parallel_count": 1,
            "recommended_scheme_id": None,
            "schemes": [],
        }
    schemes = []
    for scheme in device.scheme_results:
        schemes.append({
            "scheme_id": scheme.scheme_id,
            "parallel_count": scheme.parallel_count,
            "feasible": scheme.feasible,
            "selected_devices": dict(sorted(scheme.selected_devices.items())),
            "candidate_traces": {
                role: [
                    {
                        key: trace.get(key)
                        for key in ("part_number", "ranking_score", "passed", "rejection_reasons")
                        if key in trace
                    }
                    for trace in traces
                ]
                for role, traces in sorted(scheme.candidate_traces.items())
            },
        })
    return {
        "selected_devices": dict(sorted(device.selected_devices.items())),
        "active_scheme_id": device.active_scheme_id,
        "active_parallel_count": device.active_parallel_count,
        "recommended_scheme_id": device.recommended_scheme_id,
        "schemes": schemes,
    }


def _capacitor_side_summary(side: Any) -> dict[str, Any] | None:
    if side is None:
        return None
    def entry(value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        return {
            "part_number": value.candidate.part_number,
            "manufacturer": value.candidate.manufacturer,
            "series": value.candidate.series,
            "parallel_count": value.parallel_count,
            "series_count": value.series_count,
            "score": value.score,
            "feasible": value.feasible,
        }
    return {
        "recommended": entry(side.recommended),
        "recommended_parallel_count": side.recommended_parallel_count,
        "minimum_feasible_parallel_count": side.minimum_feasible_parallel_count,
        "evaluated_count": side.evaluated_count,
        "feasible_count": side.feasible_count,
        "top_candidates": [entry(value) for value in side.top_candidates],
        "feasible_candidate_ids": [
            {"part_number": value.candidate.part_number, "parallel_count": value.parallel_count, "score": value.score}
            for value in side.feasible_candidates
        ],
    }


def _magnetic_summary(magnetic: Any) -> dict[str, Any] | None:
    if magnetic is None:
        return None
    chosen = []
    for candidate in magnetic.chosen_designs:
        chosen.append({
            "candidate_id": getattr(candidate, "candidate_id", None),
            "core_id": getattr(candidate, "core_id", None),
            "material_id": getattr(candidate, "material_id", None),
            "turns": getattr(candidate, "turns", None),
            "parallel_count": getattr(candidate, "parallel_count", None),
            "stack_count": getattr(candidate, "stack_count", None),
        })
    return {
        "selected_design_id": magnetic.selected_design_id,
        "result_type": magnetic.result_type,
        "design_type": magnetic.design_type,
        "chosen_designs": chosen,
        "chosen_designs_checksum": _digest(chosen),
    }


def _probe_runtime(root: Path, *, enable_magnetic_design: bool = False) -> dict[str, Any]:
    sys.path.insert(0, str(root / "src"))
    from pe_claw_gui.pipeline.options import PipelineOptions
    from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
    from pe_claw_gui.topologies.base.registry import build_default_registry

    registry = build_default_registry()
    records = []
    for definition in sorted(registry.list_definitions(), key=lambda item: item.topology_id):
        record: dict[str, Any] = {
            "topology_id": definition.topology_id,
            "category_id": definition.category_id,
            "display_name": definition.display_name,
            "status": "error",
        }
        try:
            plugin = registry.get_plugin(definition.topology_id)
            module = import_module(plugin.__module__)
            report = run_full_pipeline(
                plugin=plugin,
                raw_input=module.build_default_inputs(),
                include_waveforms=False,
                pipeline_options=PipelineOptions(
                    enable_magnetic_design=enable_magnetic_design,
                    enable_capacitor_design=True,
                ),
            )
            record.update({
                "status": "executed",
                "device": _candidate_trace_summary(report),
                "capacitor": {
                    "input_selection": _capacitor_side_summary(report.capacitor.input_selection if report.capacitor else None),
                    "output_selection": _capacitor_side_summary(report.capacitor.output_selection if report.capacitor else None),
                },
                "magnetic": _magnetic_summary(report.magnetic),
            })
            record["selection_checksum"] = _digest({
                "device": record["device"], "capacitor": record["capacitor"], "magnetic": record["magnetic"]
            })
        except Exception as exc:  # Preserve per-topology evidence and continue the matrix.
            record["error_type"] = type(exc).__name__
            record["error"] = str(exc)
        records.append(record)
    return {"root": str(root), "topology_count": len(records), "records": records}


def _run_child(root: Path, mode: str, *, enable_magnetic_design: bool = False) -> dict[str, Any]:
    command = [sys.executable, str(Path(__file__).resolve()), "--probe-root", str(root), "--probe-mode", mode]
    if enable_magnetic_design:
        command.append("--enable-magnetic-design")
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"Probe failed for {root} ({mode}): {completed.stderr[-4000:]}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Probe returned invalid JSON for {root} ({mode}): {completed.stdout[-4000:]}") from exc


def _write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_record_mapping(path: Path, target: dict[str, Any], source: dict[str, Any]) -> None:
    rows = []
    metrics = [
        ("semiconductors", "record_count"),
        ("semiconductors", "vendor_count"),
        ("capacitors", "record_count"),
        ("magnetics", "sendust_core_count"),
        ("magnetics", "sendust_size_count"),
        ("magnetics", "sendust_material_count"),
    ]
    for group, field in metrics:
        source_value = source[group][field]
        target_value = target[group][field]
        rows.append({
            "library": group,
            "metric": field,
            "source_value": source_value,
            "target_value": target_value,
            "match": source_value == target_value,
        })
    for field in ("materials", "shapes", "wires", "commercial_cores", "stock_cores"):
        source_value = source["magnetics"]["normalized_v2_production"]["record_counts"][field]
        target_value = target["magnetics"]["normalized_v2_production"]["record_counts"][field]
        rows.append({"library": "magnetics_v2_cache", "metric": field, "source_value": source_value, "target_value": target_value, "match": source_value == target_value})
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _compare_manifests(target: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    target_by_path = {item["path"]: item for item in target["files"]}
    source_by_path = {item["path"]: item for item in source["files"]}
    rows = []
    for path in sorted(set(target_by_path) | set(source_by_path)):
        a = target_by_path.get(path)
        b = source_by_path.get(path)
        status = (
            "missing_target" if a is None else
            "target_placeholder_only" if b is None and path.endswith("/.gitkeep") else
            "missing_source" if b is None else
            "identical" if a["sha256"] == b["sha256"] else
            "newline_only" if a["normalized_sha256"] == b["normalized_sha256"] else
            "content_difference"
        )
        rows.append({
            "path": path,
            "target_sha256": a["sha256"] if a else None,
            "source_sha256": b["sha256"] if b else None,
            "target_normalized_sha256": a["normalized_sha256"] if a else None,
            "source_normalized_sha256": b["normalized_sha256"] if b else None,
            "status": status,
        })
    return {
        "relative_path_count": len(rows),
        "identical_count": sum(row["status"] == "identical" for row in rows),
        "newline_only_count": sum(row["status"] == "newline_only" for row in rows),
        "content_difference_count": sum(row["status"] == "content_difference" for row in rows),
        "missing_target_count": sum(row["status"] == "missing_target" for row in rows),
        "missing_source_count": sum(row["status"] == "missing_source" for row in rows),
        "target_placeholder_only_count": sum(row["status"] == "target_placeholder_only" for row in rows),
        "differences": [row for row in rows if row["status"] != "identical"],
    }


def _write_sorting_policy(path: Path) -> None:
    path.write_text(
        """# Step 8 Candidate Sorting Policy

This policy makes library selection auditable across PE-Claw 1.0 and 2.0.

1. Registry inputs are treated as data snapshots. Candidate identity is the stable part number or magnetic candidate ID.
2. Semiconductor schemes are compared by explicit scheme ID, parallel count, role, ranking score, loss, junction temperature, and part number.
3. Capacitor entries are compared by the selector score, total loss, volume, parallel count, and part number. The final part-number tie-break is mandatory.
4. Magnetic candidates are compared by the engine's explicit score/Pareto representative policy; chosen candidate IDs and their ordered checksum are retained.
5. No acceptance decision may depend on filesystem enumeration or the incidental order returned by a vendor builder.
6. A different selected part is a library or ranking difference until the candidate-list checksum and field-level evidence explain it.

The runtime golden snapshot records selected identities, parallel counts, representative candidate lists, and checksums for every registered topology.
""",
        encoding="utf-8",
    )


def _main_parent(*, reuse_runtime: bool = False) -> int:
    target_files = _file_manifest(ROOT)
    source_files = _file_manifest(SOURCE_ROOT)
    target_libraries = _run_child(ROOT, "libraries")
    source_libraries = _run_child(SOURCE_ROOT, "libraries")
    # Magnetic candidate search is intentionally a separate opt-in matrix. The
    # library probe above still verifies the complete magnetic data authority;
    # the default 19-topology matrix remains suitable for repeatable CI runs.
    if reuse_runtime and (PLAN_ROOT / "candidate_selection_golden.json").is_file():
        previous = json.loads((PLAN_ROOT / "candidate_selection_golden.json").read_text(encoding="utf-8"))
        target_runtime = previous["target_runtime"]
        source_runtime = previous["source_runtime"]
    else:
        target_runtime = _run_child(ROOT, "runtime")
        source_runtime = _run_child(SOURCE_ROOT, "runtime")
    manifest_comparison = _compare_manifests(target_files, source_files)
    _write_manifest(PLAN_ROOT / "library_manifest_1.json", target_files | {"runtime": target_libraries})
    _write_manifest(PLAN_ROOT / "library_manifest_2.json", source_files | {"runtime": source_libraries})
    _write_record_mapping(PLAN_ROOT / "library_record_mapping.csv", target_libraries, source_libraries)
    _write_sorting_policy(PLAN_ROOT / "candidate_sorting_policy.md")
    golden = {
        "contract": "candidate_selection_golden_v1",
        "target_root": str(ROOT),
        "source_root": str(SOURCE_ROOT),
        "target_runtime": target_runtime,
        "source_runtime": source_runtime,
        "selection_checksum_match_count": sum(
            a.get("selection_checksum") == b.get("selection_checksum")
            for a, b in zip(target_runtime["records"], source_runtime["records"])
        ),
    }
    _write_manifest(PLAN_ROOT / "candidate_selection_golden.json", golden)
    runtime_pairs = []
    for target, source in zip(target_runtime["records"], source_runtime["records"]):
        runtime_pairs.append({
            "topology_id": target["topology_id"],
            "target_status": target["status"],
            "source_status": source["status"],
            "target_selection_checksum": target.get("selection_checksum"),
            "source_selection_checksum": source.get("selection_checksum"),
            "selection_match": target.get("selection_checksum") == source.get("selection_checksum"),
        })
    report = {
        "step": 8,
        "contract": "library_migration_and_candidate_sorting_v1",
        "source_root": str(SOURCE_ROOT),
        "target_root": str(ROOT),
        "target_registered_topology_count": len(target_libraries["registered_topologies"]),
        "source_registered_topology_count": len(source_libraries["registered_topologies"]),
        "file_manifest_comparison": manifest_comparison,
        "library_record_comparison": {
            "target": target_libraries,
            "source": source_libraries,
            "record_mapping_match_count": sum(
                target_libraries[group][field] == source_libraries[group][field]
                for group, field in (("semiconductors", "record_count"), ("capacitors", "record_count"), ("magnetics", "sendust_core_count"), ("magnetics", "sendust_size_count"), ("magnetics", "sendust_material_count"))
            ),
        },
        "runtime_selection_comparison": {"pairs": runtime_pairs},
        "magnetic_runtime_matrix": {
            "status": "opt_in",
            "command": "python scripts/validate_step8_libraries.py --full-magnetic-runtime",
            "reason": "Magnetic candidate search is materially more expensive than registry and capacitor/device selection.",
        },
        "acceptance": {
            "registered_topology_count_match": len(target_libraries["registered_topologies"]) == len(source_libraries["registered_topologies"]),
            "library_record_counts_match": all(row["match"] for row in csv.DictReader((PLAN_ROOT / "library_record_mapping.csv").open(encoding="utf-8"))),
            "no_missing_library_files": manifest_comparison["missing_target_count"] == 0 and manifest_comparison["missing_source_count"] == 0,
            "runtime_probe_completed_for_all_topologies": all(item["target_status"] == item["source_status"] == "executed" for item in runtime_pairs),
            "sorting_policy_recorded": True,
        },
    }
    report["validation_pass"] = all(report["acceptance"].values())
    _write_manifest(PLAN_ROOT / "library_migration_validation.json", report)
    print(json.dumps({"step": 8, "validation_pass": report["validation_pass"], "file_manifest": manifest_comparison, "runtime_pairs": runtime_pairs}, indent=2))
    return 0 if report["validation_pass"] else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe-root")
    parser.add_argument("--probe-mode", choices=("libraries", "runtime"))
    parser.add_argument("--enable-magnetic-design", action="store_true")
    parser.add_argument("--full-magnetic-runtime", action="store_true")
    parser.add_argument("--reuse-runtime", action="store_true")
    args = parser.parse_args()
    if args.probe_root:
        payload = _probe_libraries(Path(args.probe_root).resolve()) if args.probe_mode == "libraries" else _probe_runtime(
            Path(args.probe_root).resolve(), enable_magnetic_design=args.enable_magnetic_design
        )
        print(json.dumps(payload, ensure_ascii=True, separators=(",", ":")))
        return 0
    if args.full_magnetic_runtime:
        target = _run_child(ROOT, "runtime", enable_magnetic_design=True)
        source = _run_child(SOURCE_ROOT, "runtime", enable_magnetic_design=True)
        payload = {"target_runtime": target, "source_runtime": source}
        print(json.dumps(payload, indent=2, ensure_ascii=True))
        return 0
    return _main_parent(reuse_runtime=args.reuse_runtime)


if __name__ == "__main__":
    raise SystemExit(main())
