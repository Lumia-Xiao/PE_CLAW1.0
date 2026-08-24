"""Structured design-report contracts and exporters."""

from .structured_output import (
    REPORT_SCHEMA_VERSION,
    build_structured_report,
    canonical_json,
    flatten_quantity_rows,
    render_markdown_report,
)

__all__ = [
    "REPORT_SCHEMA_VERSION",
    "build_structured_report",
    "canonical_json",
    "flatten_quantity_rows",
    "render_markdown_report",
]
