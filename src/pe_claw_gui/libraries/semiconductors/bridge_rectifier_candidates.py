"""Load normalized AC-DC bridge-rectifier candidate CSV files."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from ...models.bridge_rectifier import BridgeRectifierCandidate


REQUIRED_BRIDGE_CANDIDATE_FIELDS = (
    "bridge_candidate_id",
    "topology_kind",
    "mfr_part_number",
    "manufacturer",
    "digikey_part_number",
    "package_family",
    "package_case",
    "mounting_type",
    "v_rrm_v",
    "io_avg_rectified_a",
    "vf_max_v",
    "vf_test_current_a",
    "tj_min_c",
    "tj_max_c",
    "body_length_mm",
    "body_width_mm",
    "body_height_mm",
    "unit_price_usd",
    "price_currency",
    "price_valid",
    "stock_qty",
)


@dataclass(frozen=True)
class BridgeRectifierCandidateLoadIssue:
    """One rejected normalized CSV row and the reason it was rejected."""

    row_number: int
    candidate_id: str
    reason: str


@dataclass(frozen=True)
class BridgeRectifierCandidateLoadResult:
    """Loaded bridge-rectifier candidates plus row-level load diagnostics."""

    source_path: Path
    raw_row_count: int
    candidates: tuple[BridgeRectifierCandidate, ...]
    rejected_rows: tuple[BridgeRectifierCandidateLoadIssue, ...] = field(default_factory=tuple)
    filtered_count: int = 0

    @property
    def loaded_count(self) -> int:
        """Return the number of rows converted into candidate models."""

        return len(self.candidates)

    @property
    def rejected_count(self) -> int:
        """Return the number of rows rejected by loader validation."""

        return len(self.rejected_rows)


def load_bridge_rectifier_candidates(
    csv_path: str | Path,
    topology_kind: str | None = None,
) -> BridgeRectifierCandidateLoadResult:
    """Load normalized bridge-rectifier candidates from a CSV file."""

    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Bridge rectifier candidate CSV not found: {path}")

    candidates: list[BridgeRectifierCandidate] = []
    rejected_rows: list[BridgeRectifierCandidateLoadIssue] = []
    raw_row_count = 0
    filtered_count = 0
    requested_topology_kind = (topology_kind or "").strip()

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        _validate_header(reader.fieldnames, path)
        for row_number, row in enumerate(reader, start=2):
            raw_row_count += 1
            row_topology_kind = _text(row, "topology_kind")
            if requested_topology_kind and row_topology_kind != requested_topology_kind:
                filtered_count += 1
                continue
            try:
                candidates.append(_candidate_from_row(row))
            except ValueError as exc:
                rejected_rows.append(
                    BridgeRectifierCandidateLoadIssue(
                        row_number=row_number,
                        candidate_id=(row.get("bridge_candidate_id") or "").strip(),
                        reason=str(exc),
                    )
                )

    return BridgeRectifierCandidateLoadResult(
        source_path=path,
        raw_row_count=raw_row_count,
        candidates=tuple(candidates),
        rejected_rows=tuple(rejected_rows),
        filtered_count=filtered_count,
    )


def _validate_header(fieldnames: list[str] | None, path: Path) -> None:
    if fieldnames is None:
        raise ValueError(f"Bridge rectifier candidate CSV has no header: {path}")
    missing = [field for field in REQUIRED_BRIDGE_CANDIDATE_FIELDS if field not in fieldnames]
    if missing:
        raise ValueError(f"Bridge rectifier candidate CSV missing required fields: {', '.join(missing)}")


def _candidate_from_row(row: dict[str, str]) -> BridgeRectifierCandidate:
    _require_truthy(row, "bridge_candidate_id")
    _require_truthy(row, "mfr_part_number")
    _require_truthy(row, "manufacturer")
    _require_truthy(row, "digikey_part_number")
    _require_truthy(row, "package_family")
    _require_truthy(row, "package_case")
    _require_truthy(row, "mounting_type")
    if row.get("price_currency", "").strip().upper() != "USD":
        raise ValueError("price currency must be USD")
    if row.get("price_valid", "").strip().casefold() != "true":
        raise ValueError("price_valid must be true")

    return BridgeRectifierCandidate(
        candidate_id=_text(row, "bridge_candidate_id"),
        part_number=_text(row, "mfr_part_number"),
        manufacturer=_text(row, "manufacturer"),
        digikey_part_number=_text(row, "digikey_part_number"),
        package_family=_text(row, "package_family"),
        package_case=_text(row, "package_case"),
        mounting_type=_text(row, "mounting_type"),
        v_rrm_v=_positive_float(row, "v_rrm_v"),
        io_avg_rectified_a=_positive_float(row, "io_avg_rectified_a"),
        vf_max_v=_positive_float(row, "vf_max_v"),
        vf_test_current_a=_positive_float(row, "vf_test_current_a"),
        tj_min_c=_float(row, "tj_min_c"),
        tj_max_c=_float(row, "tj_max_c"),
        body_length_mm=_positive_float(row, "body_length_mm"),
        body_width_mm=_positive_float(row, "body_width_mm"),
        body_height_mm=_positive_float(row, "body_height_mm"),
        unit_price_usd=_positive_float(row, "unit_price_usd"),
        stock_qty=_non_negative_float(row, "stock_qty"),
        rth_jc_k_per_w=_optional_positive_float(row, "rth_jc_k_per_w"),
        rth_ja_k_per_w=_optional_positive_float(row, "rth_ja_k_per_w"),
        rth_jl_k_per_w=_optional_positive_float(row, "rth_jl_k_per_w"),
        leakage_current_a=_optional_positive_float(row, "leakage_current_a"),
        leakage_test_voltage_v=_optional_positive_float(row, "leakage_test_voltage_v"),
        thermal_condition=_text(row, "thermal_condition"),
        package_dimension_status=_text(row, "package_dimension_status"),
        thermal_status=_text(row, "thermal_status"),
        datasheet_url=_text(row, "datasheet_url"),
        digikey_url=_text(row, "digikey_url"),
        source_notes=_source_notes(row),
        topology_kind=_text(row, "topology_kind"),
    )


def _source_notes(row: dict[str, str]) -> tuple[str, ...]:
    notes = _text(row, "source_notes")
    if not notes:
        return ()
    return tuple(note.strip() for note in notes.split(";") if note.strip())


def _require_truthy(row: dict[str, str], field: str) -> None:
    if not _text(row, field):
        raise ValueError(f"required field is missing or blank: {field}")


def _text(row: dict[str, str], field: str) -> str:
    return (row.get(field) or "").strip()


def _float(row: dict[str, str], field: str) -> float:
    value = _text(row, field)
    if not value:
        raise ValueError(f"required numeric field is missing: {field}")
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"numeric field is invalid: {field}={value}") from exc


def _positive_float(row: dict[str, str], field: str) -> float:
    value = _float(row, field)
    if value <= 0.0:
        raise ValueError(f"numeric field must be positive: {field}={value:.6g}")
    return value


def _non_negative_float(row: dict[str, str], field: str) -> float:
    value = _float(row, field)
    if value < 0.0:
        raise ValueError(f"numeric field must be non-negative: {field}={value:.6g}")
    return value


def _optional_positive_float(row: dict[str, str], field: str) -> float | None:
    value = _text(row, field)
    if not value:
        return None
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"numeric field is invalid: {field}={value}") from exc
    if parsed <= 0.0:
        raise ValueError(f"numeric field must be positive when supplied: {field}={parsed:.6g}")
    return parsed
