"""Simplified magnetic thermal estimator built on existing PE-Claw magnetic outputs."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from ...models.inductor import FixedInductorDesignCandidate, InductorOperatingEvaluation
from ...models.thermal_result import ThermalComparisonEntry, ThermalEstimate
from ...utils.ambient_temperature import (
    AMBIENT_TEMP_INPUT_KEY,
    DEFAULT_AMBIENT_TEMP_C,
    parse_ambient_temperature_c,
)
from .resistance_chain import estimate_thermal_resistances
from .temperature_solver import solve_lumped_magnetic_temperatures
from .thermal_proxies import build_geometry_proxy

_OUTPUT_SUBDIR = Path("outputs") / "inductor_design"


@dataclass(frozen=True)
class MagneticLossSnapshot:
    """Loss inputs used by the thermal stage for one design."""

    core_loss_w: float
    copper_loss_w: float
    total_loss_w: float
    loss_basis: str
    notes: list[str]


def resolve_ambient_temperature_c(report) -> float:
    """Resolve ambient temperature with a simple default-first policy."""
    spec = report.spec
    for key in (AMBIENT_TEMP_INPUT_KEY, "ambient_c", "ta_c"):
        raw_value = spec.metadata.get(key, spec.raw_input.get(key))
        if raw_value is None:
            continue
        try:
            return parse_ambient_temperature_c(raw_value)
        except ValueError:
            continue
    return DEFAULT_AMBIENT_TEMP_C


def resolve_loss_snapshot(
    design: FixedInductorDesignCandidate,
    evaluation: InductorOperatingEvaluation | None = None,
) -> MagneticLossSnapshot | None:
    """Resolve the best available core/copper loss inputs for thermal estimation."""
    notes: list[str] = []

    if evaluation is not None and evaluation.core_loss_w is not None and evaluation.copper_loss_w is not None:
        total_loss_w = evaluation.total_loss_w
        if total_loss_w is None:
            total_loss_w = evaluation.core_loss_w + evaluation.copper_loss_w
        notes.append("Used operating-point reevaluated magnetic losses from the loss stage.")
        return MagneticLossSnapshot(
            core_loss_w=evaluation.core_loss_w,
            copper_loss_w=evaluation.copper_loss_w,
            total_loss_w=total_loss_w,
            loss_basis="operating_point",
            notes=notes,
        )

    core_loss_w = design.reference_core_loss_w
    copper_loss_w = design.reference_copper_loss_w
    total_loss_w = design.reference_total_loss_w
    if core_loss_w is not None and copper_loss_w is not None:
        if total_loss_w is None:
            total_loss_w = core_loss_w + copper_loss_w
        notes.append("Used design-point reference magnetic losses from the magnetic search result.")
        return MagneticLossSnapshot(
            core_loss_w=core_loss_w,
            copper_loss_w=copper_loss_w,
            total_loss_w=total_loss_w,
            loss_basis="design_reference",
            notes=notes,
        )

    if total_loss_w is not None and core_loss_w is not None:
        copper_loss_w = max(total_loss_w - core_loss_w, 0.0)
        notes.append("Copper loss was reconstructed from total minus core loss.")
    elif total_loss_w is not None and copper_loss_w is not None:
        core_loss_w = max(total_loss_w - copper_loss_w, 0.0)
        notes.append("Core loss was reconstructed from total minus copper loss.")

    if core_loss_w is not None and copper_loss_w is not None:
        if total_loss_w is None:
            total_loss_w = core_loss_w + copper_loss_w
        notes.append("Used partially reconstructed magnetic loss components.")
        return MagneticLossSnapshot(
            core_loss_w=core_loss_w,
            copper_loss_w=copper_loss_w,
            total_loss_w=total_loss_w,
            loss_basis="reconstructed_reference",
            notes=notes,
        )
    return None


def estimate_design_thermal_entry(
    *,
    design: FixedInductorDesignCandidate,
    ambient_temp_c: float,
    evaluation: InductorOperatingEvaluation | None = None,
) -> ThermalComparisonEntry:
    """Estimate thermal behavior for one selected magnetic design."""
    geometry = build_geometry_proxy(design)
    loss_snapshot = resolve_loss_snapshot(design, evaluation=evaluation)
    entry_notes = list(geometry.notes)
    if loss_snapshot is None:
        entry_notes.append("Magnetic loss components were unavailable; thermal estimate could not be computed.")
        return ThermalComparisonEntry(
            design_id=design.candidate_id,
            stack_count=design.stack_count,
            assembly_type=design.assembly_type,
            loss_basis="unavailable",
            notes=entry_notes,
        )

    resistance_estimate = estimate_thermal_resistances(
        core_loss_w=loss_snapshot.core_loss_w,
        copper_loss_w=loss_snapshot.copper_loss_w,
        geometry=geometry,
    )
    estimate = solve_lumped_magnetic_temperatures(
        ambient_temp_c=ambient_temp_c,
        core_loss_w=loss_snapshot.core_loss_w,
        copper_loss_w=loss_snapshot.copper_loss_w,
        geometry=geometry,
        resistance_estimate=resistance_estimate,
    )
    return ThermalComparisonEntry(
        design_id=design.candidate_id,
        stack_count=design.stack_count,
        assembly_type=design.assembly_type,
        loss_basis=loss_snapshot.loss_basis,
        estimate=estimate,
        notes=loss_snapshot.notes,
    )


def export_thermal_summary(
    entries: list[ThermalComparisonEntry],
    output_dir: Path | None = None,
) -> list[str]:
    """Write a compact thermal summary CSV for the available entries."""
    if not entries:
        return []

    output_root = Path(output_dir or _project_root() / _OUTPUT_SUBDIR)
    output_root.mkdir(parents=True, exist_ok=True)
    csv_path = output_root / "thermal_summary.csv"

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "design_id",
                "stack_count",
                "assembly_type",
                "loss_basis",
                "ambient_temp_c",
                "core_loss_w",
                "copper_loss_w",
                "total_loss_w",
                "rth_core_to_ambient_k_per_w",
                "rth_winding_to_ambient_k_per_w",
                "estimated_core_temp_rise_c",
                "estimated_winding_temp_rise_c",
                "estimated_core_temp_c",
                "estimated_winding_temp_c",
                "hotspot_proxy_temp_c",
                "total_surface_area_proxy_m2",
            ],
        )
        writer.writeheader()
        for entry in entries:
            estimate = entry.estimate
            writer.writerow(
                {
                    "design_id": entry.design_id,
                    "stack_count": entry.stack_count,
                    "assembly_type": entry.assembly_type or "",
                    "loss_basis": entry.loss_basis,
                    "ambient_temp_c": estimate.ambient_temp_c if estimate else None,
                    "core_loss_w": estimate.core_loss_w if estimate else None,
                    "copper_loss_w": estimate.copper_loss_w if estimate else None,
                    "total_loss_w": estimate.total_loss_w if estimate else None,
                    "rth_core_to_ambient_k_per_w": estimate.rth_core_to_ambient_k_per_w if estimate else None,
                    "rth_winding_to_ambient_k_per_w": estimate.rth_winding_to_ambient_k_per_w if estimate else None,
                    "estimated_core_temp_rise_c": estimate.estimated_core_temp_rise_c if estimate else None,
                    "estimated_winding_temp_rise_c": estimate.estimated_winding_temp_rise_c if estimate else None,
                    "estimated_core_temp_c": estimate.estimated_core_temp_c if estimate else None,
                    "estimated_winding_temp_c": estimate.estimated_winding_temp_c if estimate else None,
                    "hotspot_proxy_temp_c": estimate.hotspot_proxy_temp_c if estimate else None,
                    "total_surface_area_proxy_m2": estimate.total_surface_area_proxy_m2 if estimate else None,
                }
            )

    return [str(csv_path)]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]
