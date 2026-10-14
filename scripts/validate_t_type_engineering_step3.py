"""Execute only current T-type step-three or cumulative gates with receipts."""
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
import argparse
import os
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(ROOT / "scripts")]
from validate_t_type_engineering_step0 import environment, write_json
from validate_t_type_engineering_step1 import T_TYPE_TESTS, T_TYPE_EXCLUDED_NODES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("group", choices=("focus", "t_type", "gui", "waveform", "pipeline", "summary"))
    args = parser.parse_args()
    os.chdir(ROOT)
    out = args.output.resolve()
    if not out.is_relative_to(ROOT) or not out.name.startswith(".tt-r2-s3-"):
        raise ValueError("Fresh .tt-r2-s3-* workspace evidence directory required")
    out.mkdir(exist_ok=False)
    os.environ.update(PYTHONPATH=os.pathsep.join((str(ROOT / "src"), str(ROOT))),
                      PYTHONDONTWRITEBYTECODE="1", MPLBACKEND="Agg")
    preflight = environment()
    write_json(out / "preflight.json", preflight)
    tests = ["tests/test_t_type_engineering_step3_capacitors.py"]
    if args.group == "gui":
        tests = [tests[0] + "::test_real_gui_capacitor_action_current_numbers_invalidation_export"]
    if args.group == "waveform":
        tests = ["tests/test_t_type_step3_waveforms.py", "tests/test_t_type_common_solver.py",
                 "tests/test_t_type_engineering_step2_magnetics.py::test_invalid_prerequisites_are_explicit_and_do_not_start_search"]
    if args.group == "pipeline":
        tests = ["tests/test_t_type_step5_pipeline.py"]
    if args.group == "summary":
        tests = ["tests/test_t_type_summary_view.py"]
    if args.group == "t_type":
        tests += ["tests/test_t_type_engineering_step2_magnetics.py", *T_TYPE_TESTS]
    assert all((ROOT / node.split("::")[0]).is_file() for node in tests)
    import pytest

    class ScopedOutputs:
        @pytest.fixture(autouse=True)
        def scoped_outputs(self, monkeypatch):
            from pe_claw_gui.models.design_run_context import DesignRunContext
            create = DesignRunContext.create.__func__
            def scoped(cls, *a, **kw):
                if kw.get("output_root") is None and kw.get("output_base_root") is None:
                    kw["output_base_root"] = out / "outputs"
                return create(cls, *a, **kw)
            monkeypatch.setattr(DesignRunContext, "create", classmethod(scoped))

        def pytest_runtest_logreport(self, report):
            import json
            with (out / "progress.jsonl").open("a", encoding="utf-8") as log:
                log.write(json.dumps({"nodeid": report.nodeid, "when": report.when,
                    "outcome": report.outcome, "failure": str(report.longrepr) if report.failed else None}) + "\n")

    argv = ["-o", "addopts=", "-p", "no:cacheprovider", "-q", "--basetemp", str(out / "temp"),
            "--junitxml", str(out / "junit.xml"), *tests]
    if args.group in {"t_type", "pipeline"}:
        argv.extend(f"--deselect={node}" for node in T_TYPE_EXCLUDED_NODES)
    start = time.monotonic()
    with (out / "pytest.log").open("w", encoding="utf-8") as log, redirect_stdout(log), redirect_stderr(log):
        code = pytest.main(argv, plugins=[ScopedOutputs()])
    write_json(out / "test_receipt.json", {**preflight, "pytest_argv": argv,
        "exit_code": int(code), "elapsed_seconds": time.monotonic() - start})
    print((out / "pytest.log").read_text(encoding="utf-8"), flush=True)
    return int(code)


if __name__ == "__main__":
    raise SystemExit(main())
