"""Device database helpers."""

from __future__ import annotations

import csv
from pathlib import Path


def load_device_database(csv_path: str | Path) -> list[dict[str, str]]:
    """Load a device database CSV file."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Device database not found: {path}")

    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
