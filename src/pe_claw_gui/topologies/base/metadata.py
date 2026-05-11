"""Lightweight runtime metadata for converter categories."""

from __future__ import annotations

from .category import ConverterCategory


CONVERTER_CATEGORIES: tuple[ConverterCategory, ...] = (
    ConverterCategory(
        category_id="dc_dc",
        display_name="DC-DC",
        description="Direct current to direct current conversion topologies.",
    ),
    ConverterCategory(
        category_id="dc_ac",
        display_name="DC-AC",
        description="Direct current to alternating current conversion topologies.",
    ),
    ConverterCategory(
        category_id="ac_dc",
        display_name="AC-DC",
        description="Alternating current to direct current conversion topologies.",
    ),
    ConverterCategory(
        category_id="ac_ac",
        display_name="AC-AC",
        description="Alternating current to alternating current conversion topologies.",
    ),
)

CONVERTER_CATEGORY_BY_ID = {category.category_id: category for category in CONVERTER_CATEGORIES}


def list_converter_categories() -> list[ConverterCategory]:
    """Return the supported top-level converter categories."""
    return list(CONVERTER_CATEGORIES)
