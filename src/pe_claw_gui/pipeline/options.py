"""Pipeline feature gates for staged development workflows."""

from __future__ import annotations

from dataclasses import dataclass

MAGNETIC_STAGE_DISABLED_NOTE = "Magnetic design stage: disabled for current semiconductor/thermal development focus."
MAGNETIC_LOSS_DISABLED_NOTE = "Magnetic-loss stage disabled by pipeline option."
MAGNETIC_THERMAL_DISABLED_NOTE = "Magnetic thermal stage disabled by pipeline option."
MAGNETIC_GEOMETRY_DISABLED_NOTE = "Magnetic geometry stage disabled by pipeline option."


@dataclass(frozen=True)
class PipelineOptions:
    """Runtime stage gates for the PE-Claw pipeline."""

    enable_magnetic_design: bool = False
    enable_capacitor_design: bool = True
    enable_bridge_rectifier_selection: bool = True


def resolve_pipeline_options(options: PipelineOptions | None = None) -> PipelineOptions:
    """Return explicit options or the current development-phase defaults."""

    return options or PipelineOptions()


def append_unique_note(notes: list[str], note: str) -> list[str]:
    """Append one note without duplicating existing audit text."""

    if note in notes:
        return notes
    return [*notes, note]
