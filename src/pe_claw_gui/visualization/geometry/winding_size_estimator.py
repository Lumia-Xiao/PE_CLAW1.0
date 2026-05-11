"""First-pass winding size estimator for engineering geometry views."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

WIRE_BUNDLE_OUTER_ENVELOPE_FACTOR = 1.4


@dataclass(frozen=True)
class ParsedLitzWire:
    """Resolved Litz bundle details parsed from a wire name."""

    strand_count: int
    strand_diameter_mm: float
    copper_area_mm2: float
    outer_bundle_area_mm2: float
    equivalent_bundle_diameter_mm: float


@dataclass(frozen=True)
class WindingSizeEstimate:
    """Structured first-pass winding envelope estimate."""

    method: str
    parsed_wire: bool
    bundle_outer_factor: float
    strand_count: int | None = None
    strand_diameter_mm: float | None = None
    copper_area_mm2: float | None = None
    outer_bundle_area_mm2: float | None = None
    equivalent_bundle_diameter_mm: float | None = None
    bundle_columns: int | None = None
    bundle_rows: int | None = None
    per_turn_width_mm: float | None = None
    per_turn_height_mm: float | None = None
    per_turn_axial_size_mm: float | None = None
    per_turn_radial_size_mm: float | None = None
    insulation_margin_mm: float | None = None
    turns_per_layer: int | None = None
    layers: int | None = None
    occupied_axial_mm: float | None = None
    radial_build_mm: float | None = None
    opening_width_mm: float | None = None
    estimated_outer_width_mm: float | None = None
    estimated_outer_height_mm: float | None = None
    estimated_depth_mm: float | None = None
    notes: list[str] = field(default_factory=list)


def parse_litz_wire_name(wire_name: str) -> ParsedLitzWire | None:
    """Parse a Litz wire name such as 'Litz_200x0.18 - Grade 2 - Unserved'."""
    raw_name = (wire_name or "").strip()
    if not raw_name or "litz" not in raw_name.lower():
        return None

    normalized = raw_name.replace(",", ".")
    for match in re.finditer(r"(\d+)\s*[xX×]\s*(\d+(?:\.\d+)?)", normalized):
        strand_count = int(match.group(1))
        strand_diameter_mm = float(match.group(2))
        if strand_count < 1 or strand_diameter_mm <= 0.0:
            continue
        copper_area_mm2 = strand_count * (math.pi / 4.0) * (strand_diameter_mm ** 2)
        outer_bundle_area_mm2 = WIRE_BUNDLE_OUTER_ENVELOPE_FACTOR * copper_area_mm2
        equivalent_bundle_diameter_mm = math.sqrt((4.0 * outer_bundle_area_mm2) / math.pi)
        return ParsedLitzWire(
            strand_count=strand_count,
            strand_diameter_mm=strand_diameter_mm,
            copper_area_mm2=copper_area_mm2,
            outer_bundle_area_mm2=outer_bundle_area_mm2,
            equivalent_bundle_diameter_mm=equivalent_bundle_diameter_mm,
        )
    return None


def estimate_first_pass_winding_size(
    *,
    wire_name: str,
    turn_count: int,
    parallel_count: int,
    available_region_width_mm: float,
    available_axial_span_mm: float,
    available_depth_mm: float,
    opening_leg_width_mm: float | None,
) -> WindingSizeEstimate:
    """Estimate a winding envelope from parsed wire bundle size, P, N, and the local region."""
    notes: list[str] = []
    resolved_turn_count = max(int(turn_count or 0), 1)
    resolved_parallel_count = max(int(parallel_count or 0), 1)
    if resolved_turn_count != int(turn_count or 0):
        notes.append("Turn count was non-positive; geometry display used one minimum turn for a stable first-pass estimate.")
    if resolved_parallel_count != int(parallel_count or 0):
        notes.append("Parallel count was non-positive; geometry display used one minimum parallel bundle for a stable first-pass estimate.")

    parsed_wire = parse_litz_wire_name(wire_name)
    if parsed_wire is None:
        notes.append(
            f"Wire name '{wire_name or 'n/a'}' could not be parsed as Litz strand-count x strand-diameter; geometry fell back to the existing fill-factor proxy."
        )
        return WindingSizeEstimate(
            method="fill_factor_fallback",
            parsed_wire=False,
            bundle_outer_factor=WIRE_BUNDLE_OUTER_ENVELOPE_FACTOR,
            notes=notes,
        )

    bundle_columns, bundle_rows = _resolve_compact_bundle_grid(resolved_parallel_count)
    per_turn_width_mm = bundle_columns * parsed_wire.equivalent_bundle_diameter_mm
    per_turn_height_mm = bundle_rows * parsed_wire.equivalent_bundle_diameter_mm
    insulation_margin_mm = _clamp(max(0.08 * parsed_wire.equivalent_bundle_diameter_mm, 0.15), 0.15, 0.8)
    opening_width_mm = max(float(opening_leg_width_mm or 0.0) + (2.0 * insulation_margin_mm), 0.0)
    available_radial_build_mm = max(0.5 * (available_region_width_mm - opening_width_mm), 0.0)

    orientation = _select_orientation(
        turn_count=resolved_turn_count,
        available_axial_span_mm=available_axial_span_mm,
        available_radial_build_mm=available_radial_build_mm,
        turn_sizes_mm=((per_turn_width_mm, per_turn_height_mm), (per_turn_height_mm, per_turn_width_mm)),
    )
    estimated_outer_width_mm = opening_width_mm + (2.0 * orientation["radial_build_mm"])
    estimated_outer_height_mm = orientation["occupied_axial_mm"]
    estimated_depth_mm = 0.88 * available_depth_mm if available_depth_mm > 0.0 else max(per_turn_width_mm, per_turn_height_mm)

    notes.append(
        "Winding size used the first-pass bundle estimate: parse Litz strand-count x diameter, apply the 1.4 outer-envelope factor, pack P bundles per turn, then stack N turns into layers inside the local winding region."
    )
    if available_radial_build_mm <= 0.0:
        notes.append("The local winding region leaves no radial clearance beyond the leg opening; the final fit check may clamp the displayed sleeve.")

    return WindingSizeEstimate(
        method="bundle_first_pass",
        parsed_wire=True,
        bundle_outer_factor=WIRE_BUNDLE_OUTER_ENVELOPE_FACTOR,
        strand_count=parsed_wire.strand_count,
        strand_diameter_mm=parsed_wire.strand_diameter_mm,
        copper_area_mm2=parsed_wire.copper_area_mm2,
        outer_bundle_area_mm2=parsed_wire.outer_bundle_area_mm2,
        equivalent_bundle_diameter_mm=parsed_wire.equivalent_bundle_diameter_mm,
        bundle_columns=bundle_columns,
        bundle_rows=bundle_rows,
        per_turn_width_mm=per_turn_width_mm,
        per_turn_height_mm=per_turn_height_mm,
        per_turn_axial_size_mm=orientation["axial_size_mm"],
        per_turn_radial_size_mm=orientation["radial_size_mm"],
        insulation_margin_mm=insulation_margin_mm,
        turns_per_layer=orientation["turns_per_layer"],
        layers=orientation["layers"],
        occupied_axial_mm=orientation["occupied_axial_mm"],
        radial_build_mm=orientation["radial_build_mm"],
        opening_width_mm=opening_width_mm,
        estimated_outer_width_mm=estimated_outer_width_mm,
        estimated_outer_height_mm=estimated_outer_height_mm,
        estimated_depth_mm=estimated_depth_mm,
        notes=notes,
    )


def _resolve_compact_bundle_grid(bundle_count: int) -> tuple[int, int]:
    if bundle_count <= 1:
        return 1, 1
    columns = max(1, math.ceil(math.sqrt(bundle_count)))
    rows = max(1, math.ceil(bundle_count / columns))
    if rows > columns:
        rows, columns = columns, rows
    while columns > 1 and rows * (columns - 1) >= bundle_count:
        columns -= 1
    return columns, rows


def _select_orientation(
    *,
    turn_count: int,
    available_axial_span_mm: float,
    available_radial_build_mm: float,
    turn_sizes_mm: tuple[tuple[float, float], tuple[float, float]],
) -> dict[str, float | int]:
    candidates: list[dict[str, float | int]] = []
    seen: set[tuple[float, float]] = set()
    usable_axial_span_mm = max(float(available_axial_span_mm), 1e-6)
    usable_radial_build_mm = max(float(available_radial_build_mm), 0.0)

    for axial_size_mm, radial_size_mm in turn_sizes_mm:
        key = (round(axial_size_mm, 9), round(radial_size_mm, 9))
        if key in seen:
            continue
        seen.add(key)
        turns_per_layer = max(1, math.floor(usable_axial_span_mm / max(axial_size_mm, 1e-6)))
        layers = max(1, math.ceil(turn_count / turns_per_layer))
        occupied_axial_mm = min(turn_count, turns_per_layer) * axial_size_mm
        radial_build_mm = layers * radial_size_mm
        axial_overflow_mm = max(occupied_axial_mm - usable_axial_span_mm, 0.0)
        radial_overflow_mm = max(radial_build_mm - usable_radial_build_mm, 0.0)
        candidates.append(
            {
                "axial_size_mm": axial_size_mm,
                "radial_size_mm": radial_size_mm,
                "turns_per_layer": turns_per_layer,
                "layers": layers,
                "occupied_axial_mm": occupied_axial_mm,
                "radial_build_mm": radial_build_mm,
                "score_fit": axial_overflow_mm + radial_overflow_mm,
                "score_radial": radial_overflow_mm,
                "score_axial": axial_overflow_mm,
            }
        )

    candidates.sort(
        key=lambda candidate: (
            candidate["score_radial"],
            candidate["score_axial"],
            candidate["score_fit"],
            candidate["layers"],
            candidate["radial_build_mm"],
            candidate["axial_size_mm"],
        )
    )
    return candidates[0]


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))
