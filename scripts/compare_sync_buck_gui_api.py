"""Compare the GUI Run Design result with the synchronous Buck HTTP API.

The comparison executes both public paths from one versioned request. Numeric
leaves use documented absolute/relative tolerances; schemas, units, status
values, device identifiers, and all other leaves require exact equality.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest.mock import patch

import httpx

from pe_claw_gui.app.controllers.run_design_controller import RunDesignController
from pe_claw_gui.app.controllers import run_design_controller as run_design_controller_module
from pe_claw_gui.app.shell.state_store import AppStateStore
from pe_claw_gui.reports import build_structured_report
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_dc.buck_diode_rectified_unidirectional.input_schema import (
    build_default_inputs,
)
from pe_claw_web.schemas import BuckDesignRequest, DesignResultResponse


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUEST = REPOSITORY_ROOT / "docs" / "web-api-v1-buck-request.json"
ENDPOINT = "/api/v1/design/buck"
ABSOLUTE_TOLERANCE = 1e-12
RELATIVE_TOLERANCE = 1e-12


def _difference(
    *,
    path: str,
    source_value: Any,
    target_value: Any,
    category: str,
    basis: str,
    absolute_error: float | None = None,
    relative_error: float | None = None,
) -> dict[str, Any]:
    return {
        "source_value": source_value,
        "target_value": target_value,
        "absolute_error": absolute_error,
        "relative_error": relative_error,
        "tolerance": {
            "absolute": ABSOLUTE_TOLERANCE,
            "relative": RELATIVE_TOLERANCE,
        },
        "basis": basis,
        "owner": "web_migration_step_6",
        "category": category,
        "evidence_path": path,
    }


def compare_payloads(source: Any, target: Any, path: str = "$") -> tuple[int, list[dict[str, Any]]]:
    """Return the leaf count and fully attributed comparison differences."""

    if isinstance(source, Mapping) and isinstance(target, Mapping):
        differences: list[dict[str, Any]] = []
        compared = 0
        source_keys = set(source)
        target_keys = set(target)
        for key in sorted(source_keys | target_keys):
            child_path = f"{path}.{key}"
            if key not in source:
                compared += 1
                differences.append(
                    _difference(
                        path=child_path,
                        source_value=None,
                        target_value=target[key],
                        category="missing_source_field",
                        basis="Structured report fields must exist on both paths.",
                    )
                )
            elif key not in target:
                compared += 1
                differences.append(
                    _difference(
                        path=child_path,
                        source_value=source[key],
                        target_value=None,
                        category="missing_target_field",
                        basis="Structured report fields must exist on both paths.",
                    )
                )
            else:
                child_count, child_differences = compare_payloads(
                    source[key], target[key], child_path
                )
                compared += child_count
                differences.extend(child_differences)
        return compared, differences

    if (
        isinstance(source, Sequence)
        and not isinstance(source, (str, bytes))
        and isinstance(target, Sequence)
        and not isinstance(target, (str, bytes))
    ):
        differences = []
        compared = 0
        for index in range(max(len(source), len(target))):
            child_path = f"{path}[{index}]"
            if index >= len(source) or index >= len(target):
                compared += 1
                differences.append(
                    _difference(
                        path=child_path,
                        source_value=source[index] if index < len(source) else None,
                        target_value=target[index] if index < len(target) else None,
                        category="sequence_length",
                        basis="Structured report arrays require identical length and order.",
                    )
                )
            else:
                child_count, child_differences = compare_payloads(
                    source[index], target[index], child_path
                )
                compared += child_count
                differences.extend(child_differences)
        return compared, differences

    if (
        isinstance(source, (int, float))
        and not isinstance(source, bool)
        and isinstance(target, (int, float))
        and not isinstance(target, bool)
    ):
        source_number = float(source)
        target_number = float(target)
        absolute_error = abs(source_number - target_number)
        scale = max(abs(source_number), abs(target_number))
        relative_error = absolute_error / scale if scale else 0.0
        if math.isclose(
            source_number,
            target_number,
            rel_tol=RELATIVE_TOLERANCE,
            abs_tol=ABSOLUTE_TOLERANCE,
        ):
            return 1, []
        return 1, [
            _difference(
                path=path,
                source_value=source,
                target_value=target,
                category="numeric",
                basis="Numeric report leaves use explicit absolute and relative tolerances.",
                absolute_error=absolute_error,
                relative_error=relative_error,
            )
        ]

    if source == target and type(source) is type(target):
        return 1, []
    return 1, [
        _difference(
            path=path,
            source_value=source,
            target_value=target,
            category="value_or_type",
            basis="Units, status, provenance, identifiers, and other nonnumeric leaves require exact equality.",
        )
    ]


def _gui_summary(request: BuckDesignRequest, output_root: Path) -> dict[str, Any]:
    registry = build_default_registry()
    plugin = registry.get_plugin(request.topology)
    state = AppStateStore(registry)
    state.set_selected_topology(request.topology, plugin)
    raw_input = build_default_inputs()
    raw_input.update({key: str(value) for key, value in request.pipeline_input().items()})
    real_run_full_pipeline = run_design_controller_module.run_full_pipeline

    def run_isolated(*args: Any, **kwargs: Any):
        kwargs["output_root"] = output_root
        return real_run_full_pipeline(*args, **kwargs)

    with patch.object(run_design_controller_module, "run_full_pipeline", run_isolated):
        report = RunDesignController(state).run_active_topology(raw_input)
    return build_structured_report(report)


async def _api_result(payload: dict[str, Any]) -> DesignResultResponse:
    from pe_claw_web.api import main as main_module
    from pe_claw_web.jobs.store import JobStore

    repository = JobStore()
    main_module.store = repository
    try:
        transport = httpx.ASGITransport(app=main_module.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://step6.local") as client:
            repository.create_user('comparison-user', 'comparison-password-123')
            login = await client.post('/api/v1/auth/login', json={
                'username': 'comparison-user', 'password': 'comparison-password-123',
            })
            login.raise_for_status()
            response = await client.post(
                ENDPOINT,
                json=payload,
                headers={'Authorization': 'Bearer ' + login.json()['access_token']},
            )
    finally:
        repository.engine.dispose()
    if response.status_code != 200:
        raise RuntimeError(f"{ENDPOINT} returned HTTP {response.status_code}: {response.text}")
    return DesignResultResponse.model_validate(response.json())


def run_comparison(request_path: Path) -> dict[str, Any]:
    resolved_request = request_path.resolve()
    payload = json.loads(resolved_request.read_text(encoding="utf-8"))
    request = BuckDesignRequest.model_validate(payload)
    with TemporaryDirectory(prefix="pe-claw-step6-") as temporary_directory:
        database_path = Path(temporary_directory) / "jobs.db"
        previous_directory = Path.cwd()
        previous_database_url = os.environ.get("PE_CLAW_DATABASE_URL")
        try:
            os.chdir(temporary_directory)
            os.environ["PE_CLAW_DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
            gui_summary = _gui_summary(request, Path(temporary_directory) / "gui-output")
            api_result = asyncio.run(_api_result(payload))
        finally:
            os.chdir(previous_directory)
            if previous_database_url is None:
                os.environ.pop("PE_CLAW_DATABASE_URL", None)
            else:
                os.environ["PE_CLAW_DATABASE_URL"] = previous_database_url
    compared, differences = compare_payloads(gui_summary, api_result.summary)
    return {
        "schema_version": "1.0",
        "comparison": "gui_run_design_vs_sync_buck_http",
        "source": "RunDesignController.run_active_topology",
        "target": f"POST {ENDPOINT}",
        "request": str(resolved_request),
        "numeric_tolerance": {
            "absolute": ABSOLUTE_TOLERANCE,
            "relative": RELATIVE_TOLERANCE,
            "basis": "Only finite numeric leaves may use tolerance; all other leaves are exact.",
        },
        "compared_leaf_count": compared,
        "difference_count": len(differences),
        "verdict": "pass" if not differences else "fail",
        "differences": differences,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_comparison(args.request)
    rendered = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
