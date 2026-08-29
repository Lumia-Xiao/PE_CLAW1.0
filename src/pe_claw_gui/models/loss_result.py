"""Loss-stage result model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LossResult:
    """Aggregate for loss-estimation outputs."""

    total_loss_w: float | None = None
    breakdown_w: dict[str, float] = field(default_factory=dict)
    recommended_design_id: str | None = None
    recommended_design_total_volume_m3: float | None = None
    component_volumes_m3: dict[str, float] = field(default_factory=dict)
    top_design_losses: dict[str, dict[str, float]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    core_loss_audit: dict[str, object] = field(default_factory=dict)
    core_loss_status: str = "not_evaluated"
