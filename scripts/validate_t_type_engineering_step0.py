"""Capture the current engineering baseline without enabling T-type stages.

Snapshots retain all engineering fields. Only named timing fields, run IDs and
the current run/evidence path prefixes are normalized; nonfinite data is tagged
and inventoried, never silently converted to zero or treated as acceptance.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
import dataclasses
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]

# Explicit keys: no generic removal of status, source, hardware or warnings.
VOLATILE_KEYS = frozenset({
    "run_id", "created_at", "updated_at", "started_at", "finished_at",
    "run_design_started_at", "run_design_finished_at", "run_design_runtime_seconds",
    "run_magnetics_started_at", "run_magnetics_finished_at", "run_magnetics_runtime_seconds",
    "run_efficiency_sweep_started_at", "run_efficiency_sweep_finished_at",
    "run_efficiency_sweep_runtime_seconds",
})
TESTS = [
    "tests/test_t_type_engineering_step0_contract.py",
    "tests/test_t_type_step1_contract.py",
    "tests/test_t_type_step2_synthesis.py",
    "tests/test_t_type_step3_waveforms.py",
    "tests/test_t_type_step4_paths_events.py",
    "tests/test_t_type_step5_pipeline.py",
    "tests/test_t_type_common_solver.py",
    "tests/test_t_type_step6_gui.py",
    "tests/test_t_type_step7_operating_point.py",
    "tests/test_t_type_step8_acceptance.py",
    "tests/test_t_type_step8_isolation.py",
    "tests/test_dc_ac_three_phase_three_level_npc_contract.py",
    "tests/test_npc_step2_current_reference.py",
    "tests/test_npc_step3_average_voltage_target.py",
    "tests/test_npc_step4_level_sequence.py",
    "tests/test_npc_step4_periodic_warm_start.py",
    "tests/test_npc_step5_event_segmented_current.py",
    "tests/test_semiconductor_registry_structure.py",
    "tests/test_device_selector_single_candidate.py",
    "tests/test_device_selector_rejects_overstress.py",
    "tests/test_capacitor_registry.py",
    "tests/test_phase4_topology_contracts.py::test_phase4_registry_has_unique_ids_and_capabilities",
    "tests/test_phase4_topology_contracts.py::test_phase4_router_fails_closed_for_unknown_topology",
]


def encode(value):
    """Convert complete dataclass payloads to strict JSON-compatible evidence."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: encode(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, dict):
        return {str(k): encode(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return {"$nonfinite": repr(value)}
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if hasattr(value, "tolist"):
        return encode(value.tolist())
    raise TypeError(f"Unsupported evidence object: {type(value).__name__}")


def normalize(value, replacements=()):
    if isinstance(value, dict):
        return {k: normalize(v, replacements) for k, v in value.items() if k not in VOLATILE_KEYS}
    if isinstance(value, list):
        return [normalize(v, replacements) for v in value]
    if isinstance(value, str):
        for source, target in replacements:
            value = value.replace(source, target)
        return value
    return value


def write_json(path, payload):
    data = json.dumps(encode(payload), ensure_ascii=False, sort_keys=True,
                      indent=2, allow_nan=False).encode("utf-8")
    path.write_bytes(data)
    return {"file": path.name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def environment():
    import pe_claw_gui
    assert Path(pe_claw_gui.__file__).resolve().is_relative_to(ROOT / "src")
    def git(*args):
        return subprocess.check_output(["git", "-c", "core.longpaths=true", *args],
                                       cwd=ROOT).decode("utf-8").strip()
    paths = subprocess.check_output(["rg", "--files", "src", "scripts", "tests", "docs",
                                     "-g", "*.py", "-g", "*.md"], cwd=ROOT).decode("utf-8").splitlines()
    return {
        "python": sys.executable, "version": sys.version, "package": pe_claw_gui.__file__,
        "cwd": str(ROOT), "head": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"), "dirty_status": git("status", "--porcelain=v1"),
        "source_sha256": {p.replace("\\", "/"): hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                          for p in sorted(paths)},
    }


def library_inventory():
    from pe_claw_gui.libraries.semiconductors.registry import build_default_semiconductor_registry
    from pe_claw_gui.libraries.capacitors.registry import list_registered_capacitors
    from pe_claw_gui.libraries.magnetics.openmagnetics_v2_production_locator import verify_normalized_v2_production_cache
    devices = build_default_semiconductor_registry().list_devices()
    capacitors = list_registered_capacitors()
    records = {
        "semiconductors": [{"part_number": d.part_number, "vendor": d.vendor,
                             "static": encode(d.static), "payload_class": type(d.payload).__name__}
                            for d in devices],
        "capacitors": encode(capacitors),
    }
    paths = subprocess.check_output([
        "rg", "--files", "src/pe_claw_gui/libraries/semiconductors",
        "src/pe_claw_gui/libraries/capacitors", "-g", "*.py", "-g", "*.xml", "-g", "*.json",
    ], cwd=ROOT).decode("utf-8").splitlines()
    return {
        "semiconductor_count": len(devices), "device_type_counts": dict(Counter(d.selection_device_type for d in devices)),
        "capacitor_count": len(capacitors),
        "runtime_record_sha256": {k: hashlib.sha256(json.dumps(v, sort_keys=True,
                                      allow_nan=False).encode()).hexdigest() for k, v in records.items()},
        "source_file_sha256": {p.replace("\\", "/"): hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                               for p in sorted(paths)},
        "magnetic_production": verify_normalized_v2_production_cache(),
        "filter_policy": "Unfiltered registered devices/capacitors; inventory only, no topology selection",
        "record_order": "Existing registry order retained in runtime hash; source paths sorted",
    }


def capture_baselines(out):
    from dataclasses import replace
    from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
    from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import run_efficiency_sweep
    from pe_claw_gui.pipeline.options import PipelineOptions
    from pe_claw_gui.topologies.base.registry import build_default_registry
    from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter import build_default_inputs
    from pe_claw_gui.topologies.dc_ac.three_phase_two_level_voltage_source_inverter.input_schema import build_default_inputs as two_level_inputs
    from pe_claw_gui.topologies.dc_ac.single_phase_full_bridge_inverter.input_schema import build_default_inputs as full_bridge_inputs
    from pe_claw_gui.engines.hardware_overview import build_hardware_overview_payload
    from pe_claw_gui.reports.structured_output import build_structured_report
    from report_schema_validation import validate_report
    from validate_t_type_step3_completion import compare_npc

    print("Capturing six current NPC electrical snapshots", flush=True)
    electrical = compare_npc(out)
    write_json(out / "library_inventory.json", library_inventory())
    registry = build_default_registry()
    cases = [
        ("npc_full", "three_phase_three_level_npc_inverter", build_default_inputs(), True),
        ("two_level_devices", "three_phase_two_level_voltage_source_inverter", two_level_inputs(), False),
        ("full_bridge_devices", "single_phase_full_bridge_inverter", full_bridge_inputs(), False),
    ]
    receipts = []
    for case, topology_id, raw, full in cases:
        started = time.monotonic()
        print(f"Baseline {case}: actual registered-library pipeline starting", flush=True)
        run_root = out / f"run_{case}"
        report = run_full_pipeline(
            registry.get_plugin(topology_id), raw, include_waveforms=True,
            pipeline_options=PipelineOptions(enable_magnetic_design=full, enable_capacitor_design=full),
            output_root=run_root,
        )
        assert report.device is not None and report.device.selected_devices
        if full:
            assert report.magnetic is not None and report.magnetic.selected_design_id
            assert report.capacitor is not None
            for side in (report.capacitor.input_selection, report.capacitor.output_selection):
                assert side is not None and side.recommended is not None
            sweep = run_efficiency_sweep(report, plugin=registry.get_plugin(topology_id),
                                        load_points=(0.5, 1.0), output_dir=run_root / "efficiency_sweep")
            assert len(sweep.points) == 2
            for point in sweep.points:
                for key in ("semiconductor_loss_w", "magnetic_loss_w", "capacitor_loss_w", "total_loss_w", "efficiency"):
                    value = getattr(point, key)
                    assert value is not None and math.isfinite(value) and value >= 0, (case, key)
                required_total = point.semiconductor_loss_w + point.magnetic_loss_w + point.capacitor_loss_w
                assert math.isclose(point.total_loss_w, required_total, rel_tol=1e-9, abs_tol=1e-8)
                assert point.output_power_w > 0
                assert math.isclose(point.efficiency, point.output_power_w / (point.output_power_w + required_total),
                                    rel_tol=1e-9, abs_tol=1e-12)
            report = replace(report, efficiency_sweep=sweep)
        structured = build_structured_report(report)
        errors = validate_report(structured)
        assert not errors, errors
        payload = {"raw_input": raw, "report": report, "structured": structured,
                   "overview": build_hardware_overview_payload(report)}
        actual = encode(payload)
        snapshot = write_json(out / f"{case}_raw.json", actual)
        replacements = [(str(run_root), "$RUN_ROOT"), (run_root.as_posix(), "$RUN_ROOT"),
                        (report.run_context.run_id, "$RUN_ID")]
        normalized = write_json(out / f"{case}_normalized.json", normalize(actual, replacements))
        receipts.append({"case": case, "topology_id": topology_id, "full_components": full,
                         "raw": snapshot, "normalized": normalized,
                         "selected_devices": report.device.selected_devices,
                         "stage_status": report.run_context.stage_status,
                         "schema_errors": errors, "elapsed_seconds": time.monotonic() - started,
                         "acceptance_scope": "Current-code preservation baseline, not independent physical acceptance"})
        print(f"Baseline {case} saved ({receipts[-1]['elapsed_seconds']:.1f}s)", flush=True)
    manifest = {
        "cases": receipts, "electrical_snapshots": electrical,
        "normalization": {"removed_keys": sorted(VOLATILE_KEYS),
                          "replacements": "Only each case's exact run-root variants and exact current run ID",
                          "nonfinite": "Preserved as $nonfinite tags; not acceptance evidence"},
        "not_executed": ["NPC step9 analytical proxy matrix", "complete old AC-DC/DC-DC family acceptance",
                         "T-type component selection", "full pytest suite", "GUI acceptance"],
    }
    write_json(out / "baseline_manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--baseline-only", action="store_true")
    parser.add_argument("tests", nargs="*")
    args = parser.parse_args()
    os.chdir(ROOT)
    sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(ROOT / "scripts")]
    os.environ.update(PYTHONPATH=os.pathsep.join([str(ROOT / "src"), str(ROOT)]),
                      PYTHONDONTWRITEBYTECODE="1", MPLBACKEND="Agg")
    out = args.output.resolve()
    if not out.is_relative_to(ROOT) or out == ROOT or not out.name.startswith(".tt-r2-s0-"):
        raise ValueError("Use a fresh .tt-r2-s0-* evidence directory inside the workspace")
    out.mkdir(exist_ok=False)
    receipt = environment()
    write_json(out / "preflight.json", receipt)
    started = time.monotonic()
    if not args.baseline_only:
        import pytest
        tests = args.tests or TESTS
        for node in tests:
            assert (ROOT / node.split("::")[0]).is_file(), node
        class ScopedOutputs:
            @pytest.fixture(autouse=True)
            def scoped_outputs(self, monkeypatch):
                from pe_claw_gui.models.design_run_context import DesignRunContext
                create_actual = DesignRunContext.create.__func__
                def create(cls, *a, **kw):
                    if kw.get("output_root") is None and kw.get("output_base_root") is None:
                        kw["output_base_root"] = out / "outputs"
                    return create_actual(cls, *a, **kw)
                monkeypatch.setattr(DesignRunContext, "create", classmethod(create))
        argv = ["-o", "addopts=", "-p", "no:cacheprovider", "-q", "--basetemp", str(out / "temp"),
                "--junitxml", str(out / "junit.xml"), *tests]
        with (out / "pytest.log").open("w", encoding="utf-8") as log, redirect_stdout(log), redirect_stderr(log):
            status = pytest.main(argv, plugins=[ScopedOutputs()])
        receipt.update(pytest_argv=argv, exit_code=int(status), elapsed_seconds=time.monotonic() - started)
        write_json(out / "test_receipt.json", receipt)
        print((out / "pytest.log").read_text(encoding="utf-8"), flush=True)
        if status:
            raise SystemExit(status)
        if args.tests:
            return
    try:
        manifest = capture_baselines(out)
    except Exception as exc:
        write_json(out / "baseline_failure.json", {"type": type(exc).__name__, "reason": str(exc)})
        raise
    receipt.update(baseline_cases=[c["case"] for c in manifest["cases"]],
                   exit_code=0, elapsed_seconds=time.monotonic() - started)
    write_json(out / "completion.json", receipt)
    print(f"Evidence completed: {out}", flush=True)


if __name__ == "__main__":
    main()
