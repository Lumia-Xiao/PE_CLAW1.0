"""Run explicit topology engineering levels and retain a scoped JSON receipt.

Only the two-phase adapter is supported; old Boost appears solely in isolation.
No production calculation, baseline generation or cleanup is performed here.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
TOPOLOGY = "single_phase_interleaved_boost_pfc_diode_bridge"
LEVELS = ("quick", "integration", "gui", "isolation")
PREFIX = "tests/test_two_phase_interleaved_boost_pfc_"


def _case(file, function=None):
    return PREFIX + file + ".py" + ("::" + function if function else "")


# Counts freeze the reviewed parameterized coverage; changes require a reviewed update.
SELECTIONS = {
    "quick": (
        ("tests/test_validate_topology_engineering.py", 43),
        ("tests/test_topology_engineering_checks.py", 76),
        (_case("current_reference"), 20),
        (_case("loss_display_consistency"), 21),
        *tuple((_case(file), count) for file, count in (
            ("step1_contract", 5), ("step2_core", 5), ("step3_waveform", 5),
            ("step4_integration", 4), ("step6_magnetics", 3), ("step10b_boundaries", 2),
            ("step10c_stress", 2), ("step10g_frontier", 5), ("step10i_contract", 18))),
        *tuple((_case("step10a_baseline", function), 1) for function in (
            "test_step10g_audit_snapshot_retains_non_finite_diagnostics_as_strict_json",
            "test_step10a_baseline_freezes_design_boundaries_and_semantics",
            "test_step10f_historical_snapshot_preserves_10d_engineering",
            "test_step10g_historical_baseline_preserves_electrical_design",
            "test_step10h_historical_baseline_preserves_10g_engineering")),
        (_case("step5_devices", "test_step5_declares_four_independent_phase_roles"), 1),
        (_case("step9_gui", "test_step9_user_guide_documents_fixed_assumptions_and_boundaries"), 1),
    ),
    "integration": (
        *tuple((_case("step5_devices", function), 1) for function in (
            "test_step5_selects_bridge_and_four_auditable_device_positions",
            "test_step5_bridge_request_uses_aggregate_input_current",
            "test_step5_failed_phase_candidate_is_explicit")),
        *tuple((_case(file), count) for file, count in (
            ("step10d_requests", 3), ("step10i2_loss", 3), ("step10i3_artifacts", 1),
            ("step7_pipeline", 1), ("step8_efficiency", 16), ("step10e_results", 16))),
        (_case("step10a_baseline", "test_step6_current_reference_is_repeatable_and_preserves_history"), 1),
        (_case("step9_gui", "test_step9_gui_contract_exposes_supported_flow_and_phase_results"), 1),
        (_case("step9_gui", "test_step9_loss_view_reports_phase_components_and_system_total"), 1),
    ),
    "gui": ((_case("step9_gui", "test_step9_real_gui_runs_two_phase_design_results_and_efficiency"), 1),),
    "isolation": ((_case("step10_isolation"), 2),),
}

PREFLIGHT = r'''
import json, pathlib, sys, importlib
from scripts.topology_validation_probe import verify_sources
root = pathlib.Path.cwd()
sources = verify_sources(root)
package = importlib.import_module("pe_claw_gui")
assert pathlib.Path(package.__file__).resolve() == pathlib.Path(sources["pe_claw_gui"])
runtime = importlib.import_module("pe_claw_gui.runtime.reproducibility")
assert pathlib.Path(runtime.__file__).resolve().is_relative_to(root / "src")
print(json.dumps({"sources": sources, "environment": runtime.environment_snapshot(project_root=root),
                  "deterministic_environment": runtime.DETERMINISTIC_ENVIRONMENT,
                  "executable": sys.executable}, allow_nan=False))
'''
GUI_PROBE = "import tkinter as tk; w=tk.Tk(); w.withdraw(); w.update_idletasks(); w.destroy()"


class ValidationError(Exception):
    def __init__(self, message, code=2):
        super().__init__(message)
        self.code = code


def strict_json(value):
    """Keep non-finite diagnostics explicitly encoded without dropping fields."""
    if isinstance(value, float) and not math.isfinite(value):
        return {"non_finite": "NaN" if math.isnan(value) else "Infinity" if value > 0 else "-Infinity"}
    if isinstance(value, dict):
        return {str(key): strict_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [strict_json(item) for item in value]
    return value


def _write_json(path, value):
    path.write_text(json.dumps(strict_json(value), indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def _read_json(path):
    def invalid(value):
        raise ValueError(f"Non-finite JSON literal: {value}")
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=invalid)


def child_environment(root, temp):
    env = dict(os.environ)
    for key in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONHOME"):
        env.pop(key, None)
    env.update(PYTHONPATH=os.pathsep.join(str(root / part) for part in ("src", "tests", ".")),
               PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", MPLBACKEND="Agg",
               PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp),
               PE_CLAW_VALIDATION_ROOT=str(root))
    return env


def run_child(argv, *, root, env, directory, name, timeout=None):
    start = time.perf_counter()
    record = {"argv": list(argv), "cwd": str(root), "returncode": None,
              "stdout_path": str(directory / f"{name}.stdout.txt"),
              "stderr_path": str(directory / f"{name}.stderr.txt")}
    try:
        result = subprocess.run(argv, cwd=root, env=env, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=timeout, check=False)
        stdout, stderr = result.stdout, result.stderr
        record["returncode"] = result.returncode
    except (OSError, subprocess.TimeoutExpired, KeyboardInterrupt) as error:
        stdout, stderr = getattr(error, "stdout", "") or "", getattr(error, "stderr", "") or ""
        if isinstance(stdout, bytes): stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes): stderr = stderr.decode("utf-8", errors="replace")
        record["exception"] = type(error).__name__ + ": " + str(error)
    record["duration_s"] = time.perf_counter() - start
    Path(record["stdout_path"]).write_text(stdout, encoding="utf-8")
    Path(record["stderr_path"]).write_text(stderr, encoding="utf-8")
    return record


def check_collection(evidence, selectors, root):
    if evidence["collection_errors"] or evidence["internal_errors"]:
        raise ValidationError("COLLECTION_ERROR: " + str(evidence["collection_errors"] or evidence["internal_errors"]))
    nodes = evidence["nodes"]
    ids = [item["nodeid"] for item in nodes]
    if not ids or len(set(ids)) != len(ids):
        raise ValidationError("COLLECTION_EMPTY_OR_DUPLICATE: " + str(ids))
    for item in nodes:
        path = Path(item["path"]).resolve()
        expected_path = (root / item["nodeid"].split("::")[0]).resolve()
        if not path.is_relative_to(root / "tests") or path != expected_path:
            raise ValidationError(f"TEST_SOURCE: {item}")
    covered = []
    for selector, count in selectors:
        matched = [node for node in ids if node == selector or node.startswith(selector + "::") or node.startswith(selector + "[")]
        if len(matched) != count:
            raise ValidationError(f"COLLECTION_COUNT: {selector}: expected {count}; actual {matched}")
        covered.extend(matched)
    if Counter(covered) != Counter(ids):
        raise ValidationError("COLLECTION_SCOPE: unexpected or overlapping nodes")
    return ids


def check_execution(expected, evidence, junit_path, returncode, stdout):
    """Require call/setup/teardown evidence and cross-check JUnit per node/count."""
    if evidence["collection_errors"] or evidence["internal_errors"]:
        raise ValidationError("EXECUTION_COLLECTION_OR_INTERNAL_ERROR")
    actual = [item["nodeid"] for item in evidence["nodes"]]
    if actual != expected or evidence["exitstatus"] != returncode:
        raise ValidationError("EXECUTION_SCOPE_OR_EXIT: collected nodes/exit status changed")
    reports = evidence["reports"]
    if any(item["nodeid"] not in expected for item in reports):
        raise ValidationError("EXECUTION_SCOPE: foreign node report")
    cases = list(ET.parse(junit_path).iter("testcase"))
    junit_ids = [case.attrib.get("classname", "").removeprefix("tests.") + "::" + case.attrib["name"] for case in cases]
    expected_ids = [node.split("::", 1)[0].removeprefix("tests/").removesuffix(".py").replace("/", ".")
                    + "::" + node.split("::", 1)[1] for node in expected]
    counts = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "xfail": 0}
    expected_junit_ids = []
    complete = 0
    for node, junit_id in zip(expected, expected_ids):
        stages = [item for item in reports if item["nodeid"] == node]
        by_phase = {item["when"]: item for item in stages}
        if len(by_phase) != len(stages) or not stages:
            raise ValidationError(f"EXECUTION_MISSING_OR_DUPLICATE: {node}")
        if any(item["wasxfail"] is not None for item in stages): counts["xfail"] += 1
        if any(item["outcome"] == "skipped" for item in stages): counts["skipped"] += 1
        if any(item["outcome"] == "failed" and item["when"] == "call" for item in stages): counts["failed"] += 1
        counts["errors"] += sum(item["outcome"] == "failed" and item["when"] != "call" for item in stages)
        if any(item["when"] == "call" and item["outcome"] == "passed" and item["wasxfail"] is None for item in stages):
            counts["passed"] += 1
        # Pytest writes a second JUnit case when call failure/skip and teardown error coexist.
        junit_multiplicity = 1 + int(by_phase.get("teardown", {}).get("outcome") == "failed" and
                                     by_phase.get("call", {}).get("outcome") in ("failed", "skipped"))
        expected_junit_ids.extend([junit_id] * junit_multiplicity)
        if set(by_phase) == {"setup", "call", "teardown"} and all(item["outcome"] == "passed" and item["wasxfail"] is None for item in stages):
            complete += 1
        elif all(item["outcome"] == "passed" and item["wasxfail"] is None for item in stages):
            raise ValidationError(f"EXECUTION_MISSING_PHASE: {node}")
    if Counter(junit_ids) != Counter(expected_junit_ids):
        raise ValidationError("JUNIT_SCOPE: expected test identities do not match JUnit")
    junit_counts = {"failed": sum(case.find("failure") is not None for case in cases),
                    "errors": sum(case.find("error") is not None for case in cases),
                    "skipped": sum(case.find("skipped") is not None for case in cases)}
    for key, count in junit_counts.items():
        if counts[key] != count:
            raise ValidationError(f"JUNIT_COUNTS: {key}: reports={counts[key]}; junit={count}")
    summaries = [line for line in stdout.splitlines() if " in " in line and
                 re.search(r"\d+ (?:passed|failed|errors?|skipped|xfailed|xpassed)", line)]
    if not summaries:
        raise ValidationError("STDOUT_SUMMARY_MISSING")
    summary = {key.rstrip("s") if key in ("error", "errors") else key: int(count)
               for count, key in re.findall(r"(\d+) (passed|failed|errors?|skipped|xfailed|xpassed)", summaries[-1])}
    if (summary.get("failed", 0) != counts["failed"] or summary.get("error", 0) != counts["errors"] or
            summary.get("skipped", 0) != counts["skipped"] - summary.get("xfailed", 0) or
            summary.get("xfailed", 0) + summary.get("xpassed", 0) != counts["xfail"] or
            summary.get("passed", 0) != counts["passed"]):
        raise ValidationError(f"STDOUT_COUNTS: reports={counts}; terminal={summary}")
    if counts["failed"] or counts["errors"]:
        return "failed", 1, counts
    if returncode != 0 or complete != len(expected) or counts["skipped"] or counts["xfail"]:
        return "incomplete", 2, counts
    return "passed", 0, counts


def run_validation(topology, levels, output_dir, *, root=ROOT, selections=None):
    root, output = Path(root).resolve(), Path(output_dir).resolve()
    if topology != TOPOLOGY or not levels or any(level not in LEVELS for level in levels):
        raise ValidationError("CONFIGURATION: explicit supported topology and levels required")
    selected = [level for level in LEVELS if level in levels]
    manifest = SELECTIONS if selections is None else selections
    for level in selected:
        if not manifest.get(level) or any(count < 1 for _, count in manifest[level]):
            raise ValidationError(f"CONFIGURATION: empty/invalid selection: {level}")
    # Exclusive creation prevents pytest's basetemp cleanup from touching earlier runs.
    output.mkdir(parents=True, exist_ok=False)
    receipt = {"schema_version": "topology_engineering_validation_v1", "topology": topology,
               "requested_levels": selected, "scope": "selected levels only; not release or all-topology acceptance",
               "root": str(root), "output_dir": str(output), "status": "incomplete", "exit_code": 2,
               "levels": {level: {"status": "not_executed" if level in selected else "not_requested"} for level in LEVELS},
               "diagnostics": [], "commands": [], "not_applicable": [
                   {"scope": "other standalone topology adapters", "reason": "only two-phase is adapted; old Boost is isolation pairing only"}]}
    for level in selected:
        receipt["levels"][level].update(
            selectors=[{"selector": selector, "count": count} for selector, count in manifest[level]],
            expected_count=sum(count for _, count in manifest[level]),
        )
    started = time.perf_counter()
    temp = output / "temp"
    temp.mkdir()
    env = child_environment(root, temp)
    try:
        for label, args in (("version", ["--version"]), ("head", ["rev-parse", "HEAD"]), ("branch", ["branch", "--show-current"]),
                            ("status", ["status", "--porcelain=v1", "--untracked-files=all"])):
            record = run_child(["git", *args], root=root, env=env, directory=output, name="git-" + label, timeout=30)
            receipt["commands"].append(record)
            if record["returncode"] != 0: raise ValidationError("GIT_METADATA: " + label)
            receipt.setdefault("git", {})[label] = Path(record["stdout_path"]).read_text(encoding="utf-8").strip()
        receipt["git"]["dirty"] = bool(receipt["git"]["status"])
        record = run_child([sys.executable, "-B", "-c", PREFLIGHT], root=root, env=env, directory=output, name="preflight", timeout=60)
        receipt["commands"].append(record)
        if record["returncode"] != 0: raise ValidationError("ENVIRONMENT_OR_SOURCE: see preflight logs")
        preflight = _read_json(Path(record["stdout_path"]))
        for name, parent in (("pe_claw_gui", root / "src"), ("engineering_support", root / "tests")):
            if not Path(preflight["sources"][name]).resolve().is_relative_to(parent):
                raise ValidationError("SOURCE_MISMATCH: " + name)
        receipt["environment"] = preflight
        env.update(preflight["deterministic_environment"])
        receipt["child_environment"] = {key: env[key] for key in (*preflight["deterministic_environment"],
            "PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "MPLBACKEND", "PYTEST_DISABLE_PLUGIN_AUTOLOAD", "TEMP", "TMP", "TMPDIR")}
        code = 0
        for level in selected:
            directory = output / level
            directory.mkdir()
            selectors = manifest[level]
            entry = receipt["levels"][level]
            entry.update(status="incomplete", selectors=[{"selector": s, "count": c} for s, c in selectors],
                         expected_count=sum(count for _, count in selectors), commands=[])
            entry["junit_path"] = str(directory / "junit.xml")
            if level == "gui":
                record = run_child([sys.executable, "-B", "-c", GUI_PROBE], root=root, env=env, directory=directory, name="tk-probe", timeout=30)
                entry["commands"].append(record)
                if record["returncode"] != 0: raise ValidationError("GUI_ENVIRONMENT: see Tk probe logs")
            common = [sys.executable, "-B", "-m", "pytest", "-o", "addopts=", "-o", "junit_family=xunit2",
                      "--rootdir", str(root), "-p", "no:cacheprovider", "-p", "scripts.topology_validation_probe", "-q", *[s for s, _ in selectors]]
            for phase in ("collect", "execute"):
                evidence_path = directory / f"{phase}.json"
                entry[phase + "_evidence_path"] = str(evidence_path)
                child_env = {**env, "PE_CLAW_VALIDATION_EVIDENCE": str(evidence_path)}
                argv = [*common, "--basetemp", str(directory / (phase + "-temp"))]
                if phase == "collect": argv += ["--collect-only"]
                else: argv += ["--junitxml", str(directory / "junit.xml")]
                print(f"{level}: {phase} ({entry['expected_count']} required cases)", flush=True)
                record = run_child(argv, root=root, env=child_env, directory=directory, name=phase,
                                   timeout=120 if phase == "collect" else None)
                entry["commands"].append(record)
                if not evidence_path.is_file(): raise ValidationError(f"EVIDENCE_MISSING: {level}/{phase}")
                evidence = _read_json(evidence_path)
                entry[phase + "_nodes"] = evidence["nodes"]
                if phase == "collect" and record["returncode"] != 0:
                    raise ValidationError(f"COLLECTION_FAILED: {level}: {record['returncode']}")
                if evidence["sources"] != preflight["sources"]:
                    raise ValidationError(f"SOURCE_CHANGED: {level}/{phase}")
                if phase == "collect":
                    expected = check_collection(evidence, selectors, root)
                    entry["expected_nodes"] = expected
                else:
                    entry["actual_nodes"] = [item["nodeid"] for item in evidence["nodes"]]
                    entry["status"], layer_code, entry["counts"] = check_execution(
                        expected, evidence, directory / "junit.xml", record["returncode"],
                        Path(record["stdout_path"]).read_text(encoding="utf-8"))
                    code = max(code, layer_code)
            print(f"{level}: {entry['status']}", flush=True)
        receipt["exit_code"] = code
        receipt["status"] = "passed" if code == 0 else "failed" if code == 1 else "incomplete"
    except (ValidationError, OSError, ValueError, KeyError, TypeError, ET.ParseError, KeyboardInterrupt) as error:
        receipt["diagnostics"].append(type(error).__name__ + ": " + str(error))
        receipt["exit_code"] = error.code if isinstance(error, ValidationError) else 2
    finally:
        for entry in receipt["levels"].values():
            if "commands" in entry:
                entry["duration_s"] = sum(record["duration_s"] for record in entry["commands"])
        receipt["duration_s"] = time.perf_counter() - started
        _write_json(output / "receipt.json", receipt)
    print(f"Validation {receipt['status']}; receipt: {output / 'receipt.json'}", flush=True)
    return receipt["exit_code"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topology", required=True, choices=(TOPOLOGY,))
    parser.add_argument("--level", required=True, action="append", choices=LEVELS)
    parser.add_argument("--output-dir", required=True, type=Path, help="New dedicated output directory; existing paths are refused")
    args = parser.parse_args(argv)
    try:
        return run_validation(args.topology, args.level, args.output_dir)
    except (ValidationError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
