"""Build first-pass capacitor bank layouts from library dimensions."""

from __future__ import annotations

from ...models.capacitor import CapacitorBankLayout, CapacitorSelectionEntry

_ROLE_LABELS = {
    "min_volume": "Min-volume",
    "min_loss": "Min-loss",
    "compromise": "Compromise",
}


def build_capacitor_bank_layout(entry: CapacitorSelectionEntry, *, side: str, role: str) -> CapacitorBankLayout:
    """Build a deterministic layout for one parallel capacitor bank."""

    candidate = entry.candidate
    if entry.parallel_count < 1 or entry.parallel_count > 5:
        raise ValueError("Capacitor geometry supports parallel counts from 1 to 5.")
    if candidate.diameter_mm <= 0.0 or candidate.height_mm <= 0.0:
        raise ValueError(f"Capacitor {candidate.part_number} is missing positive diameter/height dimensions.")

    body_width_mm = candidate.body_width_mm or candidate.diameter_mm
    body_depth_mm = candidate.body_depth_mm or candidate.diameter_mm
    body_height_mm = candidate.body_height_mm or candidate.height_mm
    max_body_span_mm = max(body_width_mm, body_depth_mm)
    spacing_mm = max(8.0, 0.10 * max_body_span_mm)
    pitch_mm = max_body_span_mm + spacing_mm
    positions = _positions_for_parallel_count(entry.parallel_count, pitch_mm)
    xs = [position[0] for position in positions]
    ys = [position[1] for position in positions]
    footprint_width_mm = (max(xs) - min(xs)) + body_width_mm
    footprint_depth_mm = (max(ys) - min(ys)) + body_depth_mm
    terminal_pitch_mm = candidate.terminal_pitch_mm
    terminal_pitch_secondary_mm = candidate.lead_spacing_secondary_mm
    if candidate.package_shape == "rectangular_box":
        notes = [
            "Capacitor geometry uses datasheet rectangular-box length, thickness, and height.",
            f"First-pass bank spacing is max body span plus {spacing_mm:.3g} mm clearance.",
        ]
    elif candidate.package_shape == "axial_cylindrical":
        notes = [
            "Capacitor geometry uses datasheet axial body length and diameter.",
            f"First-pass bank spacing is max body span plus {spacing_mm:.3g} mm clearance.",
        ]
    else:
        notes = [
            "Capacitor geometry uses datasheet can diameter and height.",
            f"First-pass bank spacing is diameter plus {spacing_mm:.3g} mm clearance.",
        ]
    if terminal_pitch_mm is None:
        notes.append("Terminal pitch unavailable in the library; top terminal cue uses a 0.45D first-pass visual spacing.")

    return CapacitorBankLayout(
        side=side,
        role=role,
        label=_ROLE_LABELS.get(role, role.replace("_", "-").title()),
        part_number=candidate.part_number,
        parallel_count=entry.parallel_count,
        capacitance_f=candidate.capacitance_f,
        equivalent_capacitance_f=entry.equivalent_capacitance_f,
        total_loss_w=entry.p_total_w,
        total_volume_cm3=entry.total_volume_cm3,
        package_shape=candidate.package_shape,
        can_diameter_mm=candidate.diameter_mm,
        can_height_mm=candidate.height_mm,
        pitch_mm=pitch_mm,
        footprint_width_mm=footprint_width_mm,
        footprint_depth_mm=footprint_depth_mm,
        footprint_area_mm2=footprint_width_mm * footprint_depth_mm,
        bank_height_mm=body_height_mm,
        terminal_count=candidate.terminal_count,
        terminal_diameter_mm=candidate.terminal_diameter_mm,
        terminal_pitch_mm=terminal_pitch_mm,
        terminal_pitch_secondary_mm=terminal_pitch_secondary_mm,
        terminal_type=candidate.terminal_type,
        positions_mm=positions,
        body_width_mm=body_width_mm,
        body_depth_mm=body_depth_mm,
        body_height_mm=body_height_mm,
        notes=notes,
    )


def _positions_for_parallel_count(parallel_count: int, pitch_mm: float) -> list[tuple[float, float]]:
    if parallel_count == 1:
        return [(0.0, 0.0)]
    if parallel_count == 2:
        return [(-0.5 * pitch_mm, 0.0), (0.5 * pitch_mm, 0.0)]
    if parallel_count == 3:
        return [(-pitch_mm, 0.0), (0.0, 0.0), (pitch_mm, 0.0)]
    if parallel_count == 4:
        return [
            (-0.5 * pitch_mm, -0.5 * pitch_mm),
            (0.5 * pitch_mm, -0.5 * pitch_mm),
            (-0.5 * pitch_mm, 0.5 * pitch_mm),
            (0.5 * pitch_mm, 0.5 * pitch_mm),
        ]
    if parallel_count == 5:
        return [
            (-pitch_mm, -0.5 * pitch_mm),
            (0.0, -0.5 * pitch_mm),
            (pitch_mm, -0.5 * pitch_mm),
            (-0.5 * pitch_mm, 0.5 * pitch_mm),
            (0.5 * pitch_mm, 0.5 * pitch_mm),
        ]
    raise ValueError("Capacitor geometry supports parallel counts from 1 to 5.")
