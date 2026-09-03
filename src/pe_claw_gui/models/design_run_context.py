"""Run-scoped identity and output-directory contract for every design."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping
from uuid import uuid4


DESIGN_RUN_STAGES = (
    "design",
    "semiconductor_design",
    "capacitor_design",
    "inductor_design",
    "loss",
    "thermal",
    "efficiency_sweep",
    "hardware_overview",
    "validation",
)
DESIGN_RUN_SUBDIRECTORIES = (
    "design_request",
    "semiconductor_design",
    "capacitor_design",
    "inductor_design",
    "efficiency_sweep",
    "hardware_overview",
    "validation",
    "logs",
)
DESIGN_RUN_STATUSES = frozenset({"not_started", "running", "succeeded", "failed", "blocked"})

_ACTIVE_RUN_CONTEXT: ContextVar["DesignRunContext | None"] = ContextVar(
    "pe_claw_active_design_run", default=None
)


@dataclass(frozen=True)
class DesignRunContext:
    """Immutable identity and lifecycle state for one converter-design run."""

    run_id: str
    topology_id: str
    input_sha256: str
    raw_input_snapshot: dict[str, str] = field(default_factory=dict)
    output_root: str = ""
    created_at: str = ""
    stage_status: dict[str, str] = field(default_factory=dict)
    failure_stage: str | None = None
    failure_reason: str | None = None
    manifest_path: str | None = None

    @classmethod
    def create(
        cls,
        topology_id: str,
        raw_input: Mapping[str, object],
        *,
        output_root: str | Path | None = None,
        output_base_root: str | Path | None = None,
    ) -> "DesignRunContext":
        """Create an isolated run directory and its initial manifest."""

        snapshot = {str(key): str(value) for key, value in raw_input.items()}
        encoded = json.dumps(snapshot, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
        run_id = uuid4().hex
        created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        resolved_root = (
            Path(output_root)
            if output_root is not None
            else _default_output_root(
                topology_id=str(topology_id),
                run_id=run_id,
                created_at=created_at,
                output_base_root=output_base_root,
            )
        ).resolve()
        resolved_root.mkdir(parents=True, exist_ok=True)
        for name in DESIGN_RUN_SUBDIRECTORIES:
            (resolved_root / name).mkdir(exist_ok=True)
        statuses = {stage: "not_started" for stage in DESIGN_RUN_STAGES}
        statuses["design"] = "running"
        context = cls(
            run_id=run_id,
            topology_id=str(topology_id),
            input_sha256=hashlib.sha256(encoded).hexdigest(),
            raw_input_snapshot=snapshot,
            output_root=str(resolved_root),
            created_at=created_at,
            stage_status=statuses,
            manifest_path=str(resolved_root / "manifest.json"),
        )
        request_path = resolved_root / "design_request" / "design_request.json"
        request_path.write_text(
            json.dumps(
                {
                    "topology_id": str(topology_id),
                    "run_id": run_id,
                    "input_sha256": context.input_sha256,
                    "raw_input": snapshot,
                },
                indent=2,
                sort_keys=True,
                ensure_ascii=True,
            ),
            encoding="utf-8",
        )
        write_design_run_manifest(context)
        return context

    def transition(self, stage: str, status: str, *, reason: str | None = None) -> "DesignRunContext":
        """Return a copy with one validated stage status."""

        if stage not in DESIGN_RUN_STAGES:
            raise ValueError(f"Unknown design run stage: {stage!r}")
        if status not in DESIGN_RUN_STATUSES:
            raise ValueError(f"Unknown design run stage status: {status!r}")
        statuses = dict(self.stage_status)
        statuses[stage] = status
        failed = status in {"failed", "blocked"}
        return replace(
            self,
            stage_status=statuses,
            failure_stage=stage if failed else (None if self.failure_stage == stage else self.failure_stage),
            failure_reason=reason if failed else (None if self.failure_stage == stage else self.failure_reason),
        )

    def output_dir(self, name: str) -> Path:
        """Return a child output directory contained by this run root."""

        if name not in DESIGN_RUN_SUBDIRECTORIES:
            raise ValueError(f"Unknown design run output directory: {name!r}")
        return Path(self.output_root) / name

    @contextmanager
    def activate(self):
        """Make this run available to topology internals during one call chain."""

        token = _ACTIVE_RUN_CONTEXT.set(self)
        try:
            yield self
        finally:
            _ACTIVE_RUN_CONTEXT.reset(token)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible run snapshot."""

        return {
            "run_id": self.run_id,
            "topology_id": self.topology_id,
            "input_sha256": self.input_sha256,
            "raw_input_snapshot": dict(self.raw_input_snapshot),
            "output_root": self.output_root,
            "created_at": self.created_at,
            "stage_status": dict(self.stage_status),
            "failure_stage": self.failure_stage,
            "failure_reason": self.failure_reason,
            "manifest_path": self.manifest_path,
        }


def write_design_run_manifest(context: DesignRunContext) -> Path:
    """Write the current run manifest without reading artifacts from other runs."""

    root = Path(context.output_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, list[dict[str, object]]] = {}
    for name in DESIGN_RUN_SUBDIRECTORIES:
        directory = root / name
        directory.mkdir(exist_ok=True)
        artifacts[name] = [
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "modified_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(timespec="seconds"),
            }
            for path in sorted(directory.rglob("*"))
            if path.is_file()
        ]
    payload = {
        "manifest_version": 1,
        "status": _overall_run_status(context),
        "run": {
            "run_id": context.run_id,
            "topology_id": context.topology_id,
            "input_sha256": context.input_sha256,
            "raw_input_snapshot": dict(context.raw_input_snapshot),
            "output_root": str(root),
            "created_at": context.created_at,
            "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
        "software": {"name": "pe-claw-gui", "version": "0.1.0"},
        "stage_status": dict(context.stage_status),
        "failure": {
            "stage": context.failure_stage,
            "reason": context.failure_reason,
        },
        "artifact_groups": artifacts,
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")
    return path


def _overall_run_status(context: DesignRunContext) -> str:
    if context.failure_stage is not None:
        return "failed" if context.stage_status.get(context.failure_stage) == "failed" else "blocked"
    if context.stage_status.get("validation") == "succeeded":
        return "succeeded"
    return "running"


def get_run_context(report: Any) -> DesignRunContext | Any | None:
    """Return the generic context, with the legacy LLC context as fallback."""

    return getattr(report, "run_context", None) or getattr(report, "llc_run_context", None)


def get_run_output_root(report: Any) -> Path | None:
    """Return the isolated output root attached to a report, when available."""

    context = get_run_context(report)
    output_root = getattr(context, "output_root", None)
    return Path(output_root) if output_root else None


def get_run_output_dir(report: Any, name: str) -> Path | None:
    """Return one run-scoped child directory without creating a legacy fallback."""

    root = get_run_output_root(report)
    return None if root is None else root / name


@contextmanager
def activate_report_run(report: Any):
    """Activate the report's run context for legacy plugin APIs without output arguments."""

    context = get_run_context(report)
    if context is None:
        yield
        return
    with context.activate():
        yield


def call_with_report_run(report: Any, callback, /, *args, **kwargs):
    """Call a topology/plugin function while preserving the report's run scope."""

    with activate_report_run(report):
        return callback(*args, **kwargs)


def get_active_run_output_dir(name: str = "validation") -> Path | None:
    """Resolve an output directory for low-level topology code in an active run."""

    context = _ACTIVE_RUN_CONTEXT.get()
    return None if context is None else context.output_dir(name)


def update_design_run(
    report: Any,
    stage_status: Mapping[str, str],
    *,
    reason: str | None = None,
) -> Any:
    """Update generic run stages, persist the manifest, and return the report."""

    context = getattr(report, "run_context", None)
    if context is None:
        return report
    updated = context
    for stage, status in stage_status.items():
        updated = updated.transition(stage, status, reason=reason if status in {"failed", "blocked"} else None)
    write_design_run_manifest(updated)
    return replace(report, run_context=updated)


def _default_output_root(
    *,
    topology_id: str,
    run_id: str,
    created_at: str,
    output_base_root: str | Path | None,
) -> Path:
    project_root = Path(__file__).resolve().parents[3]
    base = Path(output_base_root) if output_base_root is not None else project_root / "outputs"
    timestamp = datetime.fromisoformat(created_at).astimezone(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_topology_id = re.sub(r"[^A-Za-z0-9_-]+", "_", topology_id).strip("_") or "unknown_topology"
    return base / f"{timestamp}_{safe_topology_id}_{run_id}"
