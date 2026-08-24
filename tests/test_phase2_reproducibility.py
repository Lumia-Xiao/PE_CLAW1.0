from __future__ import annotations

from dataclasses import asdict, is_dataclass
from importlib import import_module
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.runtime import (  # noqa: E402
    DETERMINISTIC_ENVIRONMENT,
    canonicalize_for_comparison,
    configure_deterministic_runtime,
    environment_snapshot,
    stable_json_fingerprint,
)
from pe_claw_gui.topologies.base.registry import build_default_registry  # noqa: E402


def _contract_payload(value):
    if is_dataclass(value):
        return asdict(value)
    return value


def test_step2_runtime_policy_is_applied_before_pipeline_imports() -> None:
    applied = configure_deterministic_runtime()
    assert applied == {name: value for name, value in DETERMINISTIC_ENVIRONMENT.items()}
    assert os.environ["TZ"] == "UTC"
    assert os.environ["OMP_NUM_THREADS"] == "1"
    assert os.environ["MKL_NUM_THREADS"] == "1"


def test_step2_canonical_comparison_ignores_paths_and_runtime_metadata() -> None:
    first = {
        "candidate": {"duty": 0.12, "part": "Q1"},
        "generated_at": "2026-08-24T00:00:00Z",
        "report_path": r"C:\run-a\reports\final_report.json",
        "nested": {"output_root": r"C:\run-a"},
    }
    second = {
        "nested": {"output_root": r"D:\run-b"},
        "report_path": r"D:\run-b\reports\final_report.json",
        "generated_at": "2026-08-25T00:00:00Z",
        "candidate": {"part": "Q1", "duty": 0.12},
    }
    assert canonicalize_for_comparison(first) == canonicalize_for_comparison(second)
    assert stable_json_fingerprint(first) == stable_json_fingerprint(second)


def test_step2_default_contracts_are_repeatable_for_all_registered_topologies() -> None:
    registry = build_default_registry()
    for definition in registry.list_definitions():
        plugin = registry.get_plugin(definition.topology_id)
        module = import_module(plugin.__module__)
        raw_input = module.build_default_inputs()

        first_spec = plugin.build_spec(dict(raw_input))
        first_candidate = plugin.synthesize(first_spec)
        first_result = plugin.evaluate(first_candidate)
        second_spec = plugin.build_spec(dict(raw_input))
        second_candidate = plugin.synthesize(second_spec)
        second_result = plugin.evaluate(second_candidate)

        assert stable_json_fingerprint(_contract_payload(first_spec)) == stable_json_fingerprint(_contract_payload(second_spec))
        assert stable_json_fingerprint(_contract_payload(first_candidate)) == stable_json_fingerprint(_contract_payload(second_candidate))
        assert stable_json_fingerprint(_contract_payload(first_result)) == stable_json_fingerprint(_contract_payload(second_result))


def test_step2_environment_snapshot_has_required_contract_fields() -> None:
    snapshot = environment_snapshot(project_root=Path(__file__).resolve().parents[1])
    assert snapshot["contract_version"] == "pe_claw_runtime_reproducibility_v1"
    assert snapshot["python_version"]
    assert snapshot["runtime_packages"]["numpy"]
    assert snapshot["deterministic_environment"]["PYTHONHASHSEED"] == "0"
