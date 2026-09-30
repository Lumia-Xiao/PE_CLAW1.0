from __future__ import annotations

import hashlib
from dataclasses import asdict
from importlib import import_module
import json
from pathlib import Path
import pickle

from pe_claw_gui.models.design_run_context import get_active_run_output_dir
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import run_efficiency_sweep
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry


OLD_TOPOLOGY_ID = "single_phase_boost_pfc_diode_bridge"
NEW_TOPOLOGY_ID = "single_phase_interleaved_boost_pfc_diode_bridge"
LOAD_POINTS = (0.1, 0.5, 1.0)


def test_step10_old_and_new_topologies_are_isolated_in_both_orders(tmp_path: Path) -> None:
    first_order = (OLD_TOPOLOGY_ID, NEW_TOPOLOGY_ID)
    second_order = (NEW_TOPOLOGY_ID, OLD_TOPOLOGY_ID)

    registry = build_default_registry()
    # Reuse plugin instances and leave every prior report/artifact alive, so a
    # later design cannot silently mutate a cached object or overwrite a run.
    prior_runs = []
    first_snapshots = _run_order(first_order, tmp_path / "a", registry, prior_runs)
    second_snapshots = _run_order(second_order, tmp_path / "b", registry, prior_runs)

    assert first_snapshots.keys() == second_snapshots.keys() == {OLD_TOPOLOGY_ID, NEW_TOPOLOGY_ID}
    for topology_id in first_order:
        assert first_snapshots[topology_id] == second_snapshots[topology_id]


def _run_order(order: tuple[str, str], root: Path, registry, prior_runs) -> dict[str, dict[str, object]]:
    snapshots: dict[str, dict[str, object]] = {}
    options = PipelineOptions(
        enable_magnetic_design=True,
        enable_capacitor_design=True,
        enable_bridge_rectifier_selection=True,
    )
    for topology_id in order:
        plugin = registry.get_plugin(topology_id)
        topology_module = import_module(plugin.__module__)
        # Keep Windows artifact filenames below MAX_PATH in long checkout paths.
        run_root = root / ("sp" if topology_id == OLD_TOPOLOGY_ID else "tp")
        report = run_full_pipeline(
            plugin=plugin,
            raw_input=topology_module.build_default_inputs(),
            include_waveforms=True,
            pipeline_options=options,
            output_root=run_root,
        )
        sweep = run_efficiency_sweep(
            report,
            plugin=plugin,
            load_points=LOAD_POINTS,
            output_dir=run_root / "efficiency_sweep",
        )
        assert sweep.is_complete()
        assert report.run_context.topology_id == topology_id
        assert get_active_run_output_dir() is None
        for prior_report, prior_bytes, prior_root, prior_files in prior_runs:
            assert pickle.dumps(prior_report) == prior_bytes
            assert _file_hashes(prior_root) == prior_files
            assert prior_report.run_context.run_id != report.run_context.run_id
        snapshots[topology_id] = _snapshot(report, sweep, run_root)
        prior_runs.append((report, pickle.dumps(report), run_root, _file_hashes(run_root)))
    return snapshots


def _snapshot(report, sweep, run_root: Path) -> dict[str, object]:
    candidate = report.candidate
    assert candidate is not None
    bridge_candidate = getattr(report.bridge_rectifier, "selected_candidate", None)
    capacitor = getattr(getattr(report.capacitor, "output_selection", None), "recommended", None)
    device = report.device
    magnetic = report.magnetic
    manifest = json.loads((run_root / "manifest.json").read_text(encoding="utf-8"))
    artifact_hashes = {
        name: _artifact_hash(Path(path), report, run_root)
        for name, path in sorted(sweep.artifact_paths.items())
    }
    assert all(Path(path).resolve().is_relative_to(run_root.resolve()) for path in sweep.artifact_paths.values())
    for stage in (report.capacitor, report.magnetic, report.geometry):
        for path in getattr(stage, "artifact_paths", ()):
            assert Path(path).resolve().is_relative_to(run_root.resolve())
    return {
        "topology_id": report.spec.topology_id,
        "candidate": {
            key: _stable(getattr(candidate, key))
            for key in (
                "topology_id",
                "vin_min",
                "vin_max",
                "vin_nom",
                "vout_target",
                "pout_target",
                "duty_nom",
                "iout",
                "fs_hz",
                "inductance_h",
                "capacitance_f",
                "delta_il",
                "delta_vo",
                "il_peak",
                "il_valley",
                "ccm_valid",
                "feasible",
                "failure_reason",
            )
        },
        "hardware": {
            "selected_devices": dict(device.selected_devices) if device is not None else None,
            "bridge_part_number": getattr(bridge_candidate, "part_number", None),
            "magnetic_designs": sorted(
                (
                    design.metadata.get("phase_role"),
                    design.metadata.get("physical_instance_id"),
                    design.candidate_id,
                )
                for design in (magnetic.chosen_designs if magnetic is not None else [])
            ),
            "capacitor_part_number": getattr(getattr(capacitor, "candidate", None), "part_number", None),
            "capacitor_bank_capacitance_f": _stable(getattr(capacitor, "equivalent_capacitance_f", None)),
        },
        "loss": {
            "total_loss_w": _stable(getattr(report.loss, "total_loss_w", None)),
            "breakdown_w": _stable(getattr(report.loss, "breakdown_w", {})),
        },
        "stage_status": manifest["stage_status"],
        "report": _normalize({
            name: asdict(getattr(report, name))
            for name in ("candidate", "stress", "topology_result", "loss", "thermal")
        }, report, run_root),
        "warnings": _normalize({
            name: list(getattr(getattr(report, name), "warnings", ()))
            for name in ("device", "bridge_rectifier", "magnetic", "capacitor", "loss", "thermal", "geometry")
        }, report, run_root),
        "sweep": {
            "status": sweep.status,
            "load_grid": [_stable(value) for value in sweep.load_grid],
            "points": [
                {
                    "load_pu": _stable(point.load_pu),
                    "output_power_w": _stable(point.output_power_w),
                    "total_loss_w": _stable(point.total_loss_w),
                    "efficiency": _stable(point.efficiency),
                    "loss_breakdown_w": _stable(point.loss_breakdown_w),
                    "warnings": list(point.warnings),
                }
                for point in sweep.points
            ],
            "warnings": list(sweep.warnings),
            "artifact_hashes": artifact_hashes,
        },
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _file_hashes(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): _sha256(path) for path in sorted(root.rglob("*")) if path.is_file()}


def _artifact_hash(path: Path, report, run_root: Path) -> str:
    if path.suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["run_id"] == report.run_context.run_id
        assert payload["topology_id"] == report.spec.topology_id
        content = json.dumps(_normalize(payload, report, run_root), sort_keys=True).encode("utf-8")
        return hashlib.sha256(content).hexdigest()
    return _sha256(path)


def _normalize(value, report, run_root: Path):
    # Only run identity and this run's path may differ. Engineering values,
    # warnings, status, hardware IDs and sweep signatures remain comparable.
    if isinstance(value, str):
        return value.replace(str(run_root.resolve()), "<RUN>").replace(
            str(run_root.resolve()).replace("\\", "/"), "<RUN>"
        ).replace(report.run_context.run_id, "<RUN_ID>")
    if isinstance(value, dict):
        return {key: _normalize(item, report, run_root) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(item, report, run_root) for item in value]
    return value


def _stable(value):
    if isinstance(value, float):
        return round(value, 12)
    if isinstance(value, dict):
        return {str(key): _stable(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [_stable(item) for item in value]
    return value
