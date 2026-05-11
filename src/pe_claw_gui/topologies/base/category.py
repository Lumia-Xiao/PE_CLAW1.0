"""Category metadata for first-level converter selection."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConverterCategory:
    """One top-level converter family exposed by the GUI."""

    category_id: str
    display_name: str
    description: str
