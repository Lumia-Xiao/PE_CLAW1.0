"""Runtime topology specification model."""

from __future__ import annotations

from dataclasses import dataclass

from ...models.common_spec import CommonSpec


@dataclass(frozen=True)
class TopologySpec(CommonSpec):
    """Concrete runtime spec used by topology plugins."""
