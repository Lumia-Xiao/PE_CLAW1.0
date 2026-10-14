"""Run T-type step-four gates in a fresh, scoped evidence directory."""
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
    parser.add_argument("group", choices=("focus", "t_type", "gui", "summary", "matrix", "banks", "source", "legacy_gui", "staged_gui", "invalidation", "capacitor_gui"))
    args = parser.parse_args()
    os.chdir(ROOT)
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / "pytest_temp") or not out.name.startswith("tt-r2-s4-"):
        raise ValueError("Fresh pytest_temp/tt-r2-s4-* evidence directory required")
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(PYTHONPATH=os.pathsep.join((str(ROOT / "src"), str(ROOT))),
        PYTHONDONTWRITEBYTECODE="1", MPLBACKEND="Agg")
    preflight = environment()
    write_json(out / "preflight.json", preflight)
    tests = ["tests/test_t_type_engineering_step4_refresh.py"]
    if args.group == "t_type":
        tests += ["tests/test_t_type_engineering_step2_magnetics.py", "tests/test_t_type_engineering_step3_capacitors.py", *T_TYPE_TESTS]
    elif args.group == "gui":
        tests = ["tests/test_t_type_engineering_step4_refresh.py::test_controller_clear_and_current_views_export",
            "tests/test_t_type_engineering_step4_refresh.py::test_real_Tk_complete_hardware_current_numbers_invalidation_export"]
    elif args.group == "summary":
        tests = ["tests/test_t_type_summary_view.py"]
    elif args.group == "matrix":
        tests = ["tests/test_t_type_engineering_step4_matrix.py"]
    elif args.group == "banks":
        tests = ["tests/test_t_type_engineering_step4_matrix.py::test_unequal_actual_banks_explicit_update_and_Q_over_C"]
    elif args.group == "source":
        tests = ["tests/test_t_type_engineering_step4_refresh.py::test_schema_rejects_current_waveform_hardware_source"]
    elif args.group == "legacy_gui":
        tests = ["tests/test_t_type_step7_operating_point.py::test_real_gui_two_refreshes_current_numbers_and_invalidation"]
    elif args.group == "staged_gui":
        tests = ["tests/test_t_type_engineering_step2_magnetics.py::test_real_gui_magnetics_button_readback_refresh_invalidation_recovery",
            "tests/test_t_type_engineering_step3_capacitors.py::test_real_gui_capacitor_action_current_numbers_invalidation_export"]
    elif args.group == "capacitor_gui":
        tests = ["tests/test_t_type_engineering_step3_capacitors.py::test_real_gui_capacitor_action_current_numbers_invalidation_export"]
    elif args.group == "invalidation":
        tests = ["tests/test_t_type_engineering_step4_refresh.py::" + name for name in (
            "test_invalid_hardware_atomic_clear", "test_bad_point_and_recovery",
            "test_controller_clear_and_current_views_export",
            "test_public_bank_refresh_is_atomic_and_preserves_complete_selection",
            "test_public_device_refresh_uses_requested_point_and_clears_on_failure",
            "test_real_Tk_complete_hardware_current_numbers_invalidation_export")]
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
