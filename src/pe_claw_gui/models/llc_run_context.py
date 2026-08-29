"""Run-scoped state for LLC design results."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Mapping
from uuid import uuid4


LLC_TOPOLOGY_IDS = frozenset(
    {
        "llc_resonant_converter_diode_rectifier",
        "llc_resonant_converter_synchronous_rectifier",
    }
)
LLC_RUN_STAGES = (
    "design",
    "magnetics",
    "capacitors",
    "loss",
    "thermal",
    "geometry",
    "efficiency_sweep",
    "hardware_overview",
    "manifest",
)
LLC_STAGE_STATUSES = frozenset({"not_started", "running", "succeeded", "failed", "blocked"})


@dataclass(frozen=True)
class LlcRunContext:
    """Immutable identity and lifecycle state for one LLC design run."""

    run_id: str
    topology_id: str
    input_sha256: str
    raw_input_snapshot: dict[str, str] = field(default_factory=dict)
    output_root: str = ""
    created_at: str = ""
    stage_status: dict[str, str] = field(default_factory=dict)
    failure_stage: str | None = None
    failure_reason: str | None = None
    transformer_design_id: str | None = None
    external_lr_design_id: str | None = None
    cr_design_id: str | None = None
    device_design_id: str | None = None

    @classmethod
    def create(
        cls,
        topology_id: str,
        raw_input: Mapping[str, object],
        *,
        output_root: str | Path | None = None,
    ) -> "LlcRunContext":
        """Create a fresh context without inheriting any prior stage state."""

        snapshot = {str(key): str(value) for key, value in raw_input.items()}
        encoded = json.dumps(snapshot, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
        run_id = uuid4().hex
        resolved_root = Path(output_root) if output_root is not None else _default_output_root(run_id)
        statuses = {stage: "not_started" for stage in LLC_RUN_STAGES}
        statuses["design"] = "running"
        return cls(
            run_id=run_id,
            topology_id=str(topology_id),
            input_sha256=hashlib.sha256(encoded).hexdigest(),
            raw_input_snapshot=snapshot,
            output_root=str(resolved_root.resolve()),
            created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            stage_status=statuses,
        )

    def transition(self, stage: str, status: str, *, reason: str | None = None) -> "LlcRunContext":
        """Return a copy with one validated stage status."""

        if stage not in LLC_RUN_STAGES:
            raise ValueError(f"Unknown LLC run stage: {stage!r}")
        if status not in LLC_STAGE_STATUSES:
            raise ValueError(f"Unknown LLC stage status: {status!r}")
        statuses = dict(self.stage_status)
        statuses[stage] = status
        failed = status in {"failed", "blocked"}
        return replace(
            self,
            stage_status=statuses,
            failure_stage=stage if failed else (None if self.failure_stage == stage else self.failure_stage),
            failure_reason=reason if failed else (None if self.failure_stage == stage else self.failure_reason),
        )

    def with_result_ids(
        self,
        *,
        transformer_design_id: str | None = None,
        external_lr_design_id: str | None = None,
        cr_design_id: str | None = None,
        device_design_id: str | None = None,
    ) -> "LlcRunContext":
        """Return a copy with result IDs produced by this run."""

        return replace(
            self,
            transformer_design_id=(
                self.transformer_design_id if transformer_design_id is None else transformer_design_id
            ),
            external_lr_design_id=(
                self.external_lr_design_id if external_lr_design_id is None else external_lr_design_id
            ),
            cr_design_id=self.cr_design_id if cr_design_id is None else cr_design_id,
            device_design_id=self.device_design_id if device_design_id is None else device_design_id,
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible snapshot for reports and manifests."""

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
            "transformer_design_id": self.transformer_design_id,
            "external_lr_design_id": self.external_lr_design_id,
            "cr_design_id": self.cr_design_id,
            "device_design_id": self.device_design_id,
        }


def _default_output_root(run_id: str) -> Path:
    project_root = Path(__file__).resolve().parents[3]
    return project_root / "outputs" / "llc_runs" / run_id


def is_llc_topology(topology_id: str | None) -> bool:
    """Return whether a topology uses the separated LLC run contract."""

    return topology_id in LLC_TOPOLOGY_IDS
