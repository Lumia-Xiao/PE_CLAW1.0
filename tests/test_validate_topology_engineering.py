"""Lightweight real-subprocess checks of the validation entry point, no library search."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from scripts import validate_topology_engineering as runner


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / "repo"
    for directory in ("src/pe_claw_gui/runtime", "tests/engineering_support", "scripts"):
        (root / directory).mkdir(parents=True)
    for file in ("src/pe_claw_gui/__init__.py", "src/pe_claw_gui/runtime/__init__.py", "tests/engineering_support/__init__.py"):
        (root / file).write_text("", encoding="utf-8")
    shutil.copyfile(runner.ROOT / "src/pe_claw_gui/runtime/reproducibility.py", root / "src/pe_claw_gui/runtime/reproducibility.py")
    shutil.copyfile(runner.ROOT / "scripts/topology_validation_probe.py", root / "scripts/topology_validation_probe.py")
    (root / "tests/test_case.py").write_text("def test_one():\n    assert True\n", encoding="utf-8")
    for args in (["init", "-q"], ["add", "."], ["-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture"]):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)
    return root


def execute(root, output, selectors=None, levels=("quick",)):
    return runner.run_validation(runner.TOPOLOGY, levels, output, root=root,
        selections=selectors or {"quick": (("tests/test_case.py", 1),)})


def read_receipt(output):
    return json.loads((output / "receipt.json").read_text(encoding="utf-8"))


def test_success_records_real_sources_nodes_phases_git_and_scoped_artifacts(repository, tmp_path, monkeypatch):
    monkeypatch.setenv("PYTEST_ADDOPTS", "--collect-only")
    monkeypatch.setenv("PYTEST_PLUGINS", "unavailable_plugin")
    output = tmp_path / "success"
    assert execute(repository, output) == 0
    receipt = read_receipt(output)
    assert receipt["status"] == "passed" and receipt["requested_levels"] == ["quick"]
    assert receipt["git"]["head"] and not receipt["git"]["dirty"]
    assert Path(receipt["environment"]["sources"]["pe_claw_gui"]).is_relative_to(repository / "src")
    assert receipt["child_environment"]["PYTHONHASHSEED"] == "0"
    assert receipt["child_environment"]["TMP"] == str(output / "temp")
    entry = receipt["levels"]["quick"]
    assert entry["expected_nodes"] == entry["actual_nodes"] == ["tests/test_case.py::test_one"]
    assert entry["counts"] == dict(passed=1, failed=0, errors=0, skipped=0, xfail=0)
    assert receipt["levels"]["integration"]["status"] == "not_requested"
    for record in [*receipt["commands"], *entry["commands"]]:
        assert record["returncode"] == 0 and record["duration_s"] >= 0
        assert Path(record["stdout_path"]).is_file() and Path(record["stderr_path"]).is_file()
    evidence = read_receipt_evidence(output, "execute")
    assert {report["when"] for report in evidence["reports"]} == {"setup", "call", "teardown"}
    assert (output / "quick/junit.xml").is_file()


def read_receipt_evidence(output, phase):
    return json.loads((output / "quick" / f"{phase}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("body,code,status,diagnostic", [
    ("def test_one():\n    assert False\n", 1, "failed", None),
    ("import pytest\n@pytest.fixture(autouse=True)\ndef setup():\n    raise RuntimeError('fixture error')\ndef test_one(): pass\n", 1, "failed", None),
    ("import pytest\n@pytest.fixture(autouse=True)\ndef setup():\n    yield\n    raise RuntimeError('teardown error')\ndef test_one(): pass\n", 1, "failed", None),
    ("import pytest\n@pytest.fixture(autouse=True)\ndef setup():\n    yield\n    raise RuntimeError('teardown error')\ndef test_one(): assert False\n", 1, "failed", None),
    ("import pytest\ndef test_one(): pytest.skip('required case')\n", 2, "incomplete", None),
    ("import pytest\n@pytest.mark.xfail(reason='required')\ndef test_one(): assert False\n", 2, "incomplete", None),
    ("import pytest\n@pytest.mark.xfail(reason='required')\ndef test_one(): pass\n", 2, "incomplete", None),
    ("", 2, "incomplete", "COLLECTION_FAILED"),
    ("raise RuntimeError('import failure')\n", 2, "incomplete", "COLLECTION_FAILED"),
    ("import pytest\npytest.skip('module unavailable', allow_module_level=True)\n", 2, "incomplete", "COLLECTION_FAILED"),
    ("def test_one(): pass\ndef test_two(): pass\n", 2, "incomplete", "COLLECTION_COUNT"),
    ("import os\ndef test_one(): os._exit(7)\n", 2, "incomplete", "EVIDENCE_MISSING"),
])
def test_actual_child_failure_modes_never_report_success(repository, tmp_path, body, code, status, diagnostic):
    (repository / "tests/test_case.py").write_text(body, encoding="utf-8")
    output = tmp_path / "result"
    assert execute(repository, output) == code
    receipt = read_receipt(output)
    assert receipt["status"] == status
    if diagnostic:
        assert diagnostic in " ".join(receipt["diagnostics"])
    else:
        assert receipt["levels"]["quick"]["status"] == status


def test_each_requested_level_executes_separately_and_unknown_scope_is_not_implied(repository, tmp_path):
    output = tmp_path / "two-levels"
    manifest = {level: (("tests/test_case.py", 1),) for level in ("quick", "integration")}
    assert execute(repository, output, manifest, ("integration", "quick", "quick")) == 0
    receipt = read_receipt(output)
    assert receipt["requested_levels"] == ["quick", "integration"]
    assert receipt["levels"]["isolation"]["status"] == "not_requested"
    assert (output / "quick/execute.json").is_file() and (output / "integration/execute.json").is_file()


def test_foreign_test_path_is_rejected_by_real_collection_probe(repository, tmp_path):
    foreign = repository / "foreign_test.py"
    foreign.write_text("def test_one(): pass\n", encoding="utf-8")
    output = tmp_path / "foreign-test"
    assert execute(repository, output, {"quick": (("foreign_test.py", 1),)}) == 2
    receipt = read_receipt(output)
    assert "COLLECTION_FAILED" in " ".join(receipt["diagnostics"])
    logs = (output / "quick/collect.stderr.txt").read_text(encoding="utf-8")
    assert "TEST_SOURCE" in logs


@pytest.mark.parametrize("args", [[], ["--topology", "unknown"],
    ["--topology", runner.TOPOLOGY, "--level", "all", "--output-dir", "unused"],
    ["--topology", runner.TOPOLOGY, "--output-dir", "unused"]])
def test_cli_rejects_missing_or_unknown_configuration(args, tmp_path):
    result = subprocess.run([sys.executable, "-B", str(runner.ROOT / "scripts/validate_topology_engineering.py"), *args],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 2 and "error:" in result.stderr
    assert not (tmp_path / "unused").exists()


@pytest.mark.parametrize("topology,levels,manifest", [("wrong", ("quick",), None),
    (runner.TOPOLOGY, (), None), (runner.TOPOLOGY, ("all",), None),
    (runner.TOPOLOGY, ("quick",), {"quick": ()}),
    (runner.TOPOLOGY, ("quick",), {"quick": (("tests/test_case.py", 0),)})])
def test_invalid_internal_selection_cannot_create_output(topology, levels, manifest, tmp_path):
    output = tmp_path / "invalid"
    with pytest.raises(runner.ValidationError, match="CONFIGURATION"):
        runner.run_validation(topology, levels, output, selections=manifest)
    assert not output.exists()


def test_existing_output_and_files_are_never_reused_or_removed(tmp_path):
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("preserve", encoding="utf-8")
    with pytest.raises(FileExistsError):
        runner.run_validation(runner.TOPOLOGY, ("quick",), output)
    assert sentinel.read_text(encoding="utf-8") == "preserve"
    assert not (output / "receipt.json").exists()


def test_foreign_support_package_is_refused_before_collection(repository, tmp_path):
    shutil.rmtree(repository / "tests/engineering_support")
    output = tmp_path / "source"
    assert execute(repository, output) == 2
    receipt = read_receipt(output)
    assert "ENVIRONMENT_OR_SOURCE" in " ".join(receipt["diagnostics"])
    assert "SOURCE_MISMATCH" in (output / "preflight.stderr.txt").read_text(encoding="utf-8")
    assert not (output / "quick").exists()


def test_probe_rejects_foreign_production_origin_without_importing_it(tmp_path, monkeypatch):
    from scripts.topology_validation_probe import verify_sources
    foreign = tmp_path / "foreign.py"
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: importlib.util.spec_from_file_location(name, foreign))
    with pytest.raises(RuntimeError, match="SOURCE_MISMATCH.*pe_claw_gui"):
        verify_sources(tmp_path / "repo")


def test_gui_environment_failure_is_separate_from_assertion_failure(repository, tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "GUI_PROBE", "raise RuntimeError('controlled no display')")
    output = tmp_path / "gui"
    assert execute(repository, output, {"gui": (("tests/test_case.py", 1),)}, ("gui",)) == 2
    receipt = read_receipt(output)
    assert "GUI_ENVIRONMENT" in " ".join(receipt["diagnostics"])
    assert receipt["levels"]["gui"]["commands"][0]["returncode"] == 1


@pytest.mark.parametrize("mode", ("timeout", "missing_executable", "interrupted"))
def test_child_environment_faults_retain_logs_and_never_return_zero(tmp_path, monkeypatch, mode):
    argv = [sys.executable, "-B", "-c", "import time; print('started', flush=True); time.sleep(2)"]
    if mode == "missing_executable": argv = [str(tmp_path / "does-not-exist")]
    if mode == "interrupted":
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(KeyboardInterrupt()))
    record = runner.run_child(argv, root=tmp_path, env=dict(os.environ), directory=tmp_path, name="child", timeout=0.1)
    assert record["returncode"] is None and "exception" in record
    assert Path(record["stdout_path"]).is_file() and Path(record["stderr_path"]).is_file()


def test_strict_json_encodes_nonfinite_diagnostics_and_retains_provenance(tmp_path):
    payload = {"source": "run-a", "artifact_path": "original/path", "values": [float("nan"), float("inf"), -float("inf")]}
    path = tmp_path / "strict.json"
    runner._write_json(path, payload)
    result = runner._read_json(path)
    assert result["source"] == "run-a" and result["artifact_path"] == "original/path"
    assert result["values"] == [{"non_finite": value} for value in ("NaN", "Infinity", "-Infinity")]
    path.write_text('{"invalid": NaN}', encoding="utf-8")
    with pytest.raises(ValueError, match="Non-finite"):
        runner._read_json(path)


@pytest.mark.parametrize("fault", ("empty", "foreign", "duplicate", "missing"))
def test_collection_checker_rejects_unexecuted_or_wrong_node_scope(tmp_path, fault):
    root = tmp_path
    evidence = {"nodes": [{"nodeid": "tests/test_one.py::test_one", "path": str(root / "tests/test_one.py")}],
                "collection_errors": [], "internal_errors": []}
    if fault == "empty": evidence["nodes"] = []
    elif fault == "foreign": evidence["nodes"][0]["path"] = str(root / "outside.py")
    elif fault == "duplicate": evidence["nodes"] *= 2
    else: evidence["nodes"][0]["nodeid"] = "tests/test_one.py::test_other"
    with pytest.raises(runner.ValidationError):
        runner.check_collection(evidence, (("tests/test_one.py::test_one", 1),), root)


@pytest.mark.parametrize("fault", ("scope", "phase", "stdout", "junit", "exit", "internal"))
def test_execution_checker_detects_missing_phase_or_inconsistent_receipts(tmp_path, fault):
    node = "tests/test_one.py::test_one"
    evidence = {"nodes": [{"nodeid": node}], "collection_errors": [], "internal_errors": [], "exitstatus": 0,
                "reports": [{"nodeid": node, "when": when, "outcome": "passed", "wasxfail": None} for when in ("setup", "call", "teardown")]}
    xml = tmp_path / "junit.xml"
    xml.write_text('<testsuites><testsuite><testcase classname="tests.test_one" name="test_one" /></testsuite></testsuites>', encoding="utf-8")
    stdout = "1 passed in 0.01s"
    if fault == "scope": evidence["nodes"] = []
    elif fault == "phase": evidence["reports"].pop()
    elif fault == "stdout": stdout = "2 passed in 0.01s"
    elif fault == "junit": xml.write_text('<testsuites />', encoding="utf-8")
    elif fault == "exit": evidence["exitstatus"] = 1
    else: evidence["internal_errors"] = ["controlled"]
    with pytest.raises(runner.ValidationError):
        runner.check_execution([node], evidence, xml, 0, stdout)


def test_adapter_manifest_is_explicit_and_levels_do_not_overlap():
    all_selectors = [selector for selections in runner.SELECTIONS.values() for selector, count in selections]
    assert len(all_selectors) == len(set(all_selectors))
    assert {level: sum(count for selector, count in entries) for level, entries in runner.SELECTIONS.items()} == {
        "quick": 216, "integration": 46, "gui": 1, "isolation": 2}
    assert all(selector.startswith("tests/") and not selector.startswith("tests/test_single_phase") for selector in all_selectors)
