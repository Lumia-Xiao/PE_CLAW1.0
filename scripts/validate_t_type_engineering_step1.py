"""Explicit step-1 gates with current-environment receipts and scoped outputs."""

from __future__ import annotations
import argparse
from contextlib import redirect_stdout, redirect_stderr
import os
from pathlib import Path
import sys
import time
import subprocess
import hashlib
from validate_t_type_engineering_step0 import (
    ROOT,
    TESTS,
    environment,
    write_json,
    capture_baselines,
)

TOPOLOGY_TESTS = list(
    dict.fromkeys(["tests/test_t_type_input_parity.py", "tests/test_t_type_engineering_step1_devices.py", *TESTS])
)
CONSUMER_TESTS = [
    "tests/test_semiconductor_package_library.py",
    "tests/test_npc_loss_model_step5.py",
    "tests/test_npc_loss_consistency_step1.py",
    "tests/test_npc_switching_loss_events.py",
    "tests/test_npc_thermal_design_step6.py",
    "tests/test_two_phase_interleaved_boost_pfc_step5_devices.py",
    "tests/test_phase4_topology_contracts.py",
    "tests/test_phase9_dc_ac_topologies.py",
    "tests/test_phase9_operating_point_migration.py",
    "tests/test_phase10_gui_integration.py",
    "tests/test_phase10_structured_output.py",
    "tests/test_phase11_structured_comparison.py",
    "tests/test_phase12_verification.py",
]
SHARED_TESTS = [
    "tests/test_phase3_shared_contracts.py",
    "tests/test_phase5_pipeline_closure.py",
    "tests/test_phase7_dc_dc_topologies.py",
    "tests/test_phase8_ac_dc_topologies.py",
    "tests/test_semiconductor_package_library.py",
    "tests/test_phase10_structured_output.py",
    "tests/test_phase11_structured_comparison.py",
]
GUI_CONSUMER_TESTS = [
    "tests/test_phase10_gui_integration.py",
    "tests/test_ac_dc_efficiency_gui_end_to_end.py",
    "tests/test_two_phase_interleaved_boost_pfc_step9_gui.py",
]
GUI_REPAIR_TESTS = [
    "tests/test_t_type_step6_gui.py",
    "tests/test_t_type_step7_operating_point.py::test_real_gui_two_refreshes_current_numbers_and_invalidation",
    "tests/test_t_type_step8_acceptance.py::test_real_gui_first_pass_user_chain_and_current_readback",
]
T_TYPE_TESTS = [
    node for node in TOPOLOGY_TESTS
    if node.startswith("tests/test_t_type_")
    and node != "tests/test_t_type_step8_isolation.py"
] + ["tests/test_t_type_step8_isolation.py::test_repeated_t_type_refreshes_do_not_share_mutable_payloads"]
T_TYPE_EXCLUDED_NODES = [
    "tests/test_t_type_step5_pipeline.py::test_npc_t_type_order_repeat_isolation",
    "tests/test_t_type_step5_pipeline.py::test_npc_empty_solver_retains_four_empty_gates",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "group", choices=("focus", "topology", "t_type", "consumers", "shared", "gui_consumers", "gui_repair", "baseline")
    )
    args = parser.parse_args()
    os.chdir(ROOT)
    sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(ROOT / "scripts")]
    os.environ.update(
        PYTHONPATH=os.pathsep.join((str(ROOT / "src"), str(ROOT))),
        PYTHONDONTWRITEBYTECODE="1",
        MPLBACKEND="Agg",
    )
    out = args.output.resolve()
    if not out.is_relative_to(ROOT) or not out.name.startswith(".tt-r2-s1-"):
        raise ValueError("Fresh .tt-r2-s1-* evidence directory required")
    out.mkdir(exist_ok=False)
    receipt = environment()
    write_json(out / "preflight.json", receipt)
    start = time.monotonic()
    if args.group == "baseline":
        try:
            capture_baselines(out)
        except Exception as exc:
            write_json(
                out / "failure.json", {"type": type(exc).__name__, "reason": str(exc)}
            )
            raise
        write_json(
            out / "completion.json",
            {**receipt, "exit_code": 0, "elapsed_seconds": time.monotonic() - start},
        )
        return
    import pytest

    class ScopedOutputs:
        def pytest_runtest_logreport(self, report):
            with (out / "progress.jsonl").open("a", encoding="utf-8") as progress:
                progress.write(__import__("json").dumps({"nodeid": report.nodeid, "when": report.when, "outcome": report.outcome, "failure": str(report.longrepr) if report.failed else None}) + "\n")

        @pytest.fixture(autouse=True)
        def scoped_outputs(self, monkeypatch):
            from pe_claw_gui.models.design_run_context import DesignRunContext

            actual = DesignRunContext.create.__func__

            def create(cls, *a, **kw):
                if kw.get("output_root") is None and kw.get("output_base_root") is None:
                    kw["output_base_root"] = out / "outputs"
                return actual(cls, *a, **kw)

            monkeypatch.setattr(DesignRunContext, "create", classmethod(create))
        @pytest.fixture(autouse=True)
        def preserved_historical_evidence(self, request, monkeypatch):
            # User-deleted historical evidence stays deleted in the workspace.
            # Tests read byte-identical committed evidence from a scoped copy.
            module = request.module
            for attribute in ("PLAN", "EVIDENCE"):
                original = getattr(module, attribute, None)
                if not isinstance(original, Path) or not original.is_relative_to(ROOT / "migration" / "evidence"):
                    continue
                relative = original.relative_to(ROOT).as_posix()
                paths = subprocess.check_output(["git","ls-tree","-r","--name-only","HEAD","--",relative],cwd=ROOT).decode().splitlines()
                destination = out / "historical_evidence" / relative
                checksums = {}
                for path in paths:
                    data = subprocess.check_output(["git","show",f"HEAD:{path}"],cwd=ROOT)
                    target = out / "historical_evidence" / path
                    target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_bytes(data)
                    checksums[path] = hashlib.sha256(data).hexdigest()
                write_json(out / f"historical_{module.__name__}.json",{"source_revision":receipt["head"],"source_paths":checksums,"redirected_attribute":attribute,"workspace_unchanged":True})
                monkeypatch.setattr(module,attribute,destination)

    tests = {
        "focus": ["tests/test_t_type_engineering_step1_devices.py"],
        "topology": TOPOLOGY_TESTS,
        "consumers": CONSUMER_TESTS,
        "shared": SHARED_TESTS,
        "gui_consumers": GUI_CONSUMER_TESTS,
        "gui_repair": GUI_REPAIR_TESTS,
        "t_type": T_TYPE_TESTS,
    }[args.group]
    for node in tests:
        assert (ROOT / node.split("::")[0]).is_file(), node
    argv = [
        "-o",
        "addopts=",
        "-p",
        "no:cacheprovider",
        "-q",
        "--basetemp",
        str(out / "temp"),
        "--junitxml",
        str(out / "junit.xml"),
        *tests,
    ]
    if args.group == "t_type":
        argv.extend(f"--deselect={node}" for node in T_TYPE_EXCLUDED_NODES)
    with (
        (out / "pytest.log").open("w", encoding="utf-8") as log,
        redirect_stdout(log),
        redirect_stderr(log),
    ):
        status = pytest.main(argv, plugins=[ScopedOutputs()])
    write_json(
        out / "test_receipt.json",
        {
            **receipt,
            "pytest_argv": argv,
            "exit_code": int(status),
            "elapsed_seconds": time.monotonic() - start,
        },
    )
    print((out / "pytest.log").read_text(encoding="utf-8"), flush=True)
    raise SystemExit(status)


if __name__ == "__main__":
    main()
