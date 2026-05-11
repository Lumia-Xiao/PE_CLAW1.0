"""Efficiency sweep result models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class EfficiencySweepPoint:
    """One fixed-hardware operating point in an efficiency sweep."""

    load_pu: float
    output_power_w: float
    total_loss_w: float | None
    efficiency: float | None
    semiconductor_loss_w: float | None
    magnetic_loss_w: float | None
    capacitor_loss_w: float | None
    other_loss_w: float | None
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Return a serializable representation."""
        return asdict(self)


@dataclass(frozen=True)
class EfficiencySweepResult:
    """Fixed-hardware efficiency sweep over a load grid."""

    points: tuple[EfficiencySweepPoint, ...] = ()
    load_grid: tuple[float, ...] = ()
    peak_efficiency: float | None = None
    peak_efficiency_load_pu: float | None = None
    full_load_efficiency: float | None = None
    light_load_efficiency: float | None = None
    artifact_paths: dict[str, str] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    signature: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Return a serializable representation."""
        return {
            "points": [point.to_dict() for point in self.points],
            "load_grid": self.load_grid,
            "peak_efficiency": self.peak_efficiency,
            "peak_efficiency_load_pu": self.peak_efficiency_load_pu,
            "full_load_efficiency": self.full_load_efficiency,
            "light_load_efficiency": self.light_load_efficiency,
            "artifact_paths": dict(self.artifact_paths),
            "warnings": self.warnings,
            "signature": self.signature,
        }

    def is_complete(self) -> bool:
        """Return True when every load point has efficiency and total loss."""
        return bool(self.points) and all(point.efficiency is not None and point.total_loss_w is not None for point in self.points)

    def summary_text(self) -> str:
        """Build a compact user-facing sweep summary."""
        if not self.points:
            warning_text = "\n".join(f"- {warning}" for warning in self.warnings)
            return "Efficiency sweep has no completed load points." + (f"\n{warning_text}" if warning_text else "")

        lines = ["Efficiency sweep"]
        if self.peak_efficiency is not None and self.peak_efficiency_load_pu is not None:
            lines.append(f"Peak efficiency: {100.0 * self.peak_efficiency:.3f}% at {self.peak_efficiency_load_pu:.1f} p.u.")
        else:
            lines.append("Peak efficiency: -")
        lines.append(_efficiency_line("Full-load efficiency", self.full_load_efficiency))
        lines.append(_efficiency_line("0.1 p.u. efficiency", self.light_load_efficiency))
        if self.warnings:
            lines.append("")
            lines.append("Warnings")
            lines.extend(f"- {warning}" for warning in self.warnings)
        if self.artifact_paths:
            lines.append("")
            lines.append("Artifacts")
            lines.extend(f"- {name}: {path}" for name, path in sorted(self.artifact_paths.items()))
        return "\n".join(lines)


def _efficiency_line(label: str, value: float | None) -> str:
    if value is None:
        return f"{label}: -"
    return f"{label}: {100.0 * value:.3f}%"
