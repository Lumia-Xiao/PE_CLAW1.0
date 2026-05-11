"""Runtime topology evaluation result model."""

from __future__ import annotations

from dataclasses import dataclass, field

from .candidate import TopologyCandidate


@dataclass(frozen=True)
class TopologyResult:
    """Evaluation summary for a synthesized topology candidate."""

    topology_id: str
    display_name: str
    candidate: TopologyCandidate
    feasible: bool = True
    summary_lines: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
