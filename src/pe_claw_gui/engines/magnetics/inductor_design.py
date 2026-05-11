"""Fixed inductor search, Pareto extraction, and operating-point evaluation."""

from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from ...models.inductor import FixedInductorDesignCandidate, InductorDesignRequest, InductorOperatingEvaluation, InductorOperatingPointRequest
from ...utils.core_family_semantics import is_paired_half_core_family, resolve_core_assembly_envelope

_MU0 = 4.0 * math.pi * 1e-7
_COPPER_RESISTIVITY_25C = 1.724e-8
_LITZ_PACKING_FACTOR = 1.10
_OUTPUT_SUBDIR = Path("outputs") / "inductor_design"
_STACKED_CORE_LOSS_BETA_FLOOR = 1.5


class InductorDatabaseUnavailableError(FileNotFoundError):
    """Raised when the external OpenMagnetics-derived database cannot be found."""


@dataclass(frozen=True)
class _DatabaseBundle:
    cores: pd.DataFrame
    materials: pd.DataFrame
    wires: pd.DataFrame


@dataclass(frozen=True)
class MagneticArtifactExportResult:
    """Artifact export result, including plot metadata."""

    artifact_paths: list[str]
    plot_source_name: str | None = None
    plot_color_dimension: str | None = None
    plot_fallback_note: str | None = None


def synthesize_fixed_inductor_candidates(request: InductorDesignRequest) -> list[FixedInductorDesignCandidate]:
    """Search feasible fixed inductor designs for a normalized design request."""
    database = _load_default_databases()
    candidates = _generate_candidates(request, database, core_limit=14, material_limit=8, wire_limit=8)
    if candidates:
        return _sort_candidates(candidates)

    expanded = _generate_candidates(request, database, core_limit=24, material_limit=12, wire_limit=12)
    return _sort_candidates(expanded)


def build_pareto_front(candidates: Iterable[FixedInductorDesignCandidate]) -> list[FixedInductorDesignCandidate]:
    """Extract a deterministic Pareto front over volume and reference loss."""
    ordered = _sort_candidates(candidates)
    if not ordered:
        return []

    pareto: list[FixedInductorDesignCandidate] = []
    best_loss_so_far = math.inf
    for candidate in ordered:
        cand_loss = _metric_or_inf(candidate.reference_total_loss_w)
        if cand_loss < best_loss_so_far:
            pareto.append(candidate)
            best_loss_so_far = cand_loss
    return _sort_candidates(pareto)


def choose_representative_designs(
    pareto_candidates: Iterable[FixedInductorDesignCandidate],
    count: int = 5,
) -> list[FixedInductorDesignCandidate]:
    """Choose spread-out representative designs from a Pareto set."""
    ordered = _sort_candidates(pareto_candidates)
    if not ordered:
        return []
    if len(ordered) <= count:
        return ordered

    fractions = [0.0, 0.25, 0.50, 0.75, 1.0]
    requested = [min(len(ordered) - 1, int(round((len(ordered) - 1) * fraction))) for fraction in fractions[:count]]
    chosen: list[FixedInductorDesignCandidate] = []
    seen_ids: set[str] = set()
    for index in requested:
        candidate = ordered[index]
        if candidate.candidate_id in seen_ids:
            continue
        chosen.append(candidate)
        seen_ids.add(candidate.candidate_id)

    if len(chosen) < count:
        for candidate in ordered:
            if candidate.candidate_id in seen_ids:
                continue
            chosen.append(candidate)
            seen_ids.add(candidate.candidate_id)
            if len(chosen) >= count:
                break
    return chosen


def select_best_by_stack_count(
    candidates: Iterable[FixedInductorDesignCandidate],
    stack_counts: Iterable[int] = (1, 2, 3),
) -> dict[int, FixedInductorDesignCandidate]:
    """Select one balanced surviving design for each requested stack-count group."""
    candidate_list = list(candidates)
    result: dict[int, FixedInductorDesignCandidate] = {}
    for stack_count in stack_counts:
        group = [candidate for candidate in candidate_list if candidate.stack_count == stack_count]
        if not group:
            continue
        result[stack_count] = _best_balanced_candidate(group)
    return result


def evaluate_fixed_inductor_design(
    design: FixedInductorDesignCandidate,
    operating_point_request: InductorOperatingPointRequest,
) -> InductorOperatingEvaluation:
    """Evaluate one fixed inductor design at the requested operating point."""
    metadata = design.metadata
    turns = max(design.turns, 1)
    ae = _as_float(metadata.get("core_effective_area_m2"))
    ve = _as_float(metadata.get("core_effective_volume_m3"))
    bundle_copper_area = _as_float(metadata.get("bundle_copper_area_m2"))
    strand_diameter = _as_float(metadata.get("strand_diameter_m"))
    total_strands = max(int(metadata.get("total_strands", 0) or 0), 1)
    b_sat_t = _as_float(metadata.get("b_sat_t"))
    steinmetz_ranges = metadata.get("steinmetz_ranges")

    notes = list(operating_point_request.notes)
    if operating_point_request.mode != "CCM":
        notes.append("Current RMS uses a DCM triangular-current approximation.")

    copper_loss_w: float | None = None
    if design.rdc_25c_ohm is not None:
        copper_loss_w = (operating_point_request.i_rms_a**2) * design.rdc_25c_ohm * _ac_resistance_multiplier(
            strand_diameter=strand_diameter,
            total_strands=total_strands,
            fs_hz=operating_point_request.fs_hz,
        )

    b_peak_t: float | None = None
    core_loss_w: float | None = None
    if ae is not None and ve is not None:
        b_peak_t = abs(operating_point_request.v_l_on_v) * operating_point_request.duty / (
            operating_point_request.fs_hz * ae * turns
        )
        if steinmetz_ranges:
            core_loss_w = _compute_operating_core_loss_w(
                design=design,
                ve_m3=ve,
                b_peak_t=b_peak_t,
                fs_hz=operating_point_request.fs_hz,
            )

    total_loss_w: float | None = None
    if copper_loss_w is not None or core_loss_w is not None:
        total_loss_w = (copper_loss_w or 0.0) + (core_loss_w or 0.0)

    current_density_a_per_mm2: float | None = None
    if bundle_copper_area is not None:
        total_copper_area_m2 = max(bundle_copper_area * design.parallel_bundles, 1e-12)
        current_density_a_per_mm2 = operating_point_request.i_rms_a / (total_copper_area_m2 * 1e6)

    if b_peak_t is not None and b_sat_t is not None and b_sat_t > 0.0:
        sat_margin_percent = max(0.0, (1.0 - (b_peak_t / b_sat_t)) * 100.0)
        notes.append(f"Estimated saturation margin = {sat_margin_percent:.2f} %.")

    return InductorOperatingEvaluation(
        design_id=design.candidate_id,
        operating_vin_v=operating_point_request.operating_vin_v,
        operating_iout_a=operating_point_request.operating_iout_a,
        fs_hz=operating_point_request.fs_hz,
        i_rms_a=operating_point_request.i_rms_a,
        i_peak_a=operating_point_request.i_peak_a,
        delta_il_pp_a=operating_point_request.delta_il_pp_a,
        copper_loss_w=copper_loss_w,
        core_loss_w=core_loss_w,
        total_loss_w=total_loss_w,
        b_peak_t=b_peak_t,
        current_density_a_per_mm2=current_density_a_per_mm2,
        notes=notes,
    )


def evaluate_selected_designs(
    designs: Iterable[FixedInductorDesignCandidate],
    operating_point_request: InductorOperatingPointRequest,
) -> list[InductorOperatingEvaluation]:
    """Evaluate multiple fixed designs at the same operating point."""
    return [evaluate_fixed_inductor_design(design, operating_point_request) for design in designs]


def export_design_artifacts(
    feasible_candidates: Iterable[FixedInductorDesignCandidate],
    pareto_candidates: Iterable[FixedInductorDesignCandidate],
    chosen_candidates: Iterable[FixedInductorDesignCandidate],
    stack_count_comparison: dict[int, FixedInductorDesignCandidate] | None = None,
    screened_candidates: Iterable[FixedInductorDesignCandidate] | None = None,
    compressed_candidates: Iterable[FixedInductorDesignCandidate] | None = None,
    recommended_design_id: str | None = None,
    write_csvs: bool = True,
    output_dir: Path | None = None,
) -> MagneticArtifactExportResult:
    """Persist search artifacts and return the created file paths."""
    output_root = Path(output_dir or _project_root() / _OUTPUT_SUBDIR)
    output_root.mkdir(parents=True, exist_ok=True)

    feasible_list = list(feasible_candidates)
    screened_list = list(screened_candidates) if screened_candidates is not None else []
    compressed_list = list(compressed_candidates) if compressed_candidates is not None else []
    pareto_list = list(pareto_candidates)
    chosen_list = list(chosen_candidates)
    stack_count_list = list((stack_count_comparison or {}).values())
    artifact_paths: list[str] = []

    if write_csvs:
        export_sets = [
            ("feasible_candidates.csv", feasible_list),
        ]
        if screened_candidates is not None:
            export_sets.append(("screened_candidates.csv", screened_list))
        if compressed_candidates is not None:
            export_sets.append(("compressed_candidates.csv", compressed_list))
        export_sets.extend(
            [
                ("pareto_front.csv", pareto_list),
                ("chosen_designs.csv", chosen_list),
                ("stack_count_comparison.csv", stack_count_list),
            ]
        )

        for name, candidates in export_sets:
            path = output_root / name
            _candidate_frame(candidates).to_csv(path, index=False)
            artifact_paths.append(str(path))

    plot_path = output_root / "pareto_front.png"
    plot_result = _write_pareto_plot(
        feasible_candidates=feasible_list,
        screened_candidates=screened_list,
        compressed_candidates=compressed_list,
        chosen_candidates=chosen_list,
        recommended_design_id=recommended_design_id,
        output_path=plot_path,
    )
    if plot_result["success"]:
        artifact_paths.append(str(plot_path))
    return MagneticArtifactExportResult(
        artifact_paths=artifact_paths,
        plot_source_name=plot_result["plot_source_name"],
        plot_color_dimension=plot_result["plot_color_dimension"],
        plot_fallback_note=plot_result["plot_fallback_note"],
    )


def describe_design_spread(designs: Iterable[FixedInductorDesignCandidate]) -> str:
    """Build a short text summary for the selected design spread."""
    ordered = _sort_candidates(designs)
    if not ordered:
        return "No fixed inductor designs were selected."
    if len(ordered) == 1:
        return f"Only one fixed design is available: {ordered[0].candidate_id}."

    smallest = ordered[0]
    largest = ordered[-1]
    min_loss = min(ordered, key=lambda item: (_metric_or_inf(item.reference_total_loss_w), item.candidate_id))
    return (
        f"Selected designs span {len(ordered)} Pareto points from minimum volume {smallest.candidate_id} "
        f"to minimum loss {min_loss.candidate_id}; the largest selected volume is {largest.candidate_id}."
    )


def describe_best_by_stack_count(best_by_stack_count: dict[int, FixedInductorDesignCandidate]) -> list[str]:
    """Build short summary lines for the subgroup-best 1-core/2-core/3-core designs."""
    lines: list[str] = []
    for stack_count in (1, 2, 3):
        candidate = best_by_stack_count.get(stack_count)
        if candidate is None:
            lines.append(f"No surviving {stack_count}-core candidate remained after merged compression.")
            continue
        lines.append(
            f"Best {stack_count}-core candidate: {candidate.candidate_id} "
            f"(volume={_display_value(candidate.total_volume_m3, 1e6, 'cm^3')}, "
            f"loss={_display_value(candidate.reference_total_loss_w, 1.0, 'W')})."
        )
    return lines


def _generate_candidates(
    request: InductorDesignRequest,
    database: _DatabaseBundle,
    core_limit: int,
    material_limit: int,
    wire_limit: int,
) -> list[FixedInductorDesignCandidate]:
    cores = _select_valid_cores(database.cores, request, limit=core_limit)
    materials = _select_candidate_materials(database.materials, request, limit=material_limit)
    wires = _select_candidate_wires(database.wires, request, limit=wire_limit)

    turns_base = np.arange(8, 81, dtype=float)
    parallel_base = np.arange(1, 9, dtype=float)
    turns_grid = np.repeat(turns_base, len(parallel_base))
    parallel_grid = np.tile(parallel_base, len(turns_base))

    candidates: list[FixedInductorDesignCandidate] = []
    for core in cores.itertuples():
        for material in materials.itertuples():
            for wire in wires.itertuples():
                candidates.extend(
                    _evaluate_core_material_wire_combo(
                        request=request,
                        core=core,
                        material=material,
                        wire=wire,
                        turns_grid=turns_grid,
                        parallel_grid=parallel_grid,
                    )
                )
    return candidates


def _evaluate_core_material_wire_combo(
    request: InductorDesignRequest,
    core: Any,
    material: Any,
    wire: Any,
    turns_grid: np.ndarray,
    parallel_grid: np.ndarray,
) -> list[FixedInductorDesignCandidate]:
    gap_m = (_MU0 * (turns_grid**2) * float(core.Ae)) / request.target_inductance_h
    fill_factor = turns_grid * parallel_grid * float(wire.bundle_copper_area) * _LITZ_PACKING_FACTOR / float(core.Aw)
    mask = (gap_m > 0.02e-3) & (gap_m < 8.0e-3) & (fill_factor > 0.01) & (fill_factor < 0.60)
    if not mask.any():
        return []

    turns = turns_grid[mask]
    parallels = parallel_grid[mask]
    gaps = gap_m[mask]
    fills = fill_factor[mask]
    total_strands = parallels * int(wire.strands_per_bundle)
    rdc = _COPPER_RESISTIVITY_25C * float(core.mlt) * turns / (parallels * float(wire.bundle_copper_area))
    fac = _ac_resistance_multiplier(
        strand_diameter=float(wire.d_strand),
        total_strands=total_strands,
        fs_hz=request.fs_hz,
    )
    copper_loss_w = (request.i_rms_a**2) * rdc * fac
    b_peak_design_t = abs(request.v_l_on_v) * request.duty_nom / (request.fs_hz * float(core.Ae) * turns)
    feasible = b_peak_design_t < (0.85 * float(material.B_sat))
    if not feasible.any():
        return []

    coeffs = _select_steinmetz_range(material.steinmetz_ranges, request.fs_hz)
    turns = turns[feasible]
    parallels = parallels[feasible]
    gaps = gaps[feasible]
    fills = fills[feasible]
    total_strands = total_strands[feasible]
    rdc = rdc[feasible]
    copper_loss_w = copper_loss_w[feasible]
    b_peak_design_t = b_peak_design_t[feasible]
    core_loss_w = (
        coeffs["k"]
        * (request.fs_hz**coeffs["alpha"])
        * (b_peak_design_t**coeffs["beta"])
        * float(core.Ve)
        * 1e3
    )
    total_loss_w = copper_loss_w + core_loss_w
    winding_volume_m3 = (
        turns
        * parallels
        * float(core.mlt)
        * (math.pi * (float(wire.outer_diameter) / 2.0) ** 2)
        * _LITZ_PACKING_FACTOR
    )
    core_volume_m3 = np.full(len(turns), float(core.gross_volume))
    total_volume_m3 = core_volume_m3 + winding_volume_m3
    saturation_current_a = 0.85 * float(material.B_sat) * gaps / (_MU0 * turns)

    results: list[FixedInductorDesignCandidate] = []
    for index in range(len(turns)):
        turns_i = int(round(float(turns[index])))
        parallels_i = int(round(float(parallels[index])))
        candidate_id = _candidate_id(
            core_name=str(core.Index),
            material_name=str(material.Index),
            wire_name=str(wire.Index),
            turns=turns_i,
            parallel_bundles=parallels_i,
        )
        results.append(
            FixedInductorDesignCandidate(
                candidate_id=candidate_id,
                assembly_type="single_core",
                stack_count=1,
                base_core_name=str(core.Index),
                core_name=str(core.Index),
                material_name=str(material.Index),
                wire_name=str(wire.Index),
                turns=turns_i,
                parallel_bundles=parallels_i,
                gap_m=float(gaps[index]),
                inductance_h=request.target_inductance_h,
                rdc_25c_ohm=float(rdc[index]),
                fill_factor=float(fills[index]),
                core_volume_m3=float(core_volume_m3[index]),
                winding_volume_m3=float(winding_volume_m3[index]),
                total_volume_m3=float(total_volume_m3[index]),
                b_peak_design_t=float(b_peak_design_t[index]),
                saturation_current_a=float(saturation_current_a[index]),
                reference_copper_loss_w=float(copper_loss_w[index]),
                reference_core_loss_w=float(core_loss_w[index]),
                reference_total_loss_w=float(total_loss_w[index]),
                notes=[
                    "Fixed inductor geometry synthesized from the design-point request.",
                    "Operating-point evaluation should reuse this geometry unchanged.",
                ],
                metadata={
                    "shape_label": str(getattr(core, "shape_label", core.Index)),
                    "family": str(getattr(core, "family", "")),
                    "wire_family": _derive_wire_family(str(wire.Index)),
                    "bundle_strands": int(wire.strands_per_bundle),
                    "total_strands": int(round(float(total_strands[index]))),
                    "bundle_copper_area_m2": float(wire.bundle_copper_area),
                    "strand_diameter_m": float(wire.d_strand),
                    "wire_outer_diameter_m": float(wire.outer_diameter),
                    "core_effective_area_m2": float(core.Ae),
                    "core_effective_volume_m3": float(core.Ve),
                    "core_window_area_m2": float(core.Aw),
                    "core_path_length_m": float(core.le),
                    "mean_length_per_turn_m": float(core.mlt),
                    "gross_volume_m3": float(core.gross_volume),
                    "core_width_m": float(core.width),
                    "core_height_m": float(core.height),
                    "core_depth_m": float(core.depth),
                    "library_core_width_m": float(getattr(core, "library_width", core.width)),
                    "library_core_height_m": float(getattr(core, "library_height", core.height)),
                    "library_core_depth_m": float(getattr(core, "library_depth", core.depth)),
                    "library_item_is_half_core": bool(getattr(core, "library_item_is_half_core", False)),
                    "half_cores_per_assembly": 2 if is_paired_half_core_family(str(getattr(core, "family", ""))) else 1,
                    "paired_assembly_axis": "height" if is_paired_half_core_family(str(getattr(core, "family", ""))) else None,
                    "magnetic_effective_parameter_basis": (
                        "Paired-core-family effective parameters remain paired-assembly approximations; only physical bbox/gross volume are expanded from half-core library geometry."
                        if is_paired_half_core_family(str(getattr(core, "family", "")))
                        else "Library geometry maps directly to the assembled magnetic body."
                    ),
                    "b_sat_t": float(material.B_sat),
                    "b_sat_100c_t": _as_float(getattr(material, "B_sat_100c", None)),
                    "b_sat_100c_source": str(getattr(material, "b_sat_100c_source", "unknown")),
                    "steinmetz_ranges": material.steinmetz_ranges,
                    "core_loss_model": "steinmetz_raw",
                    "core_loss_beta_raw": float(coeffs["beta"]),
                    "core_loss_beta_effective": float(coeffs["beta"]),
                    "reference_b_peak_t": float(b_peak_design_t[index]),
                    "reference_core_loss_density_w_per_m3": float(core_loss_w[index]) / max(float(core.Ve), 1e-18),
                    "material_type": str(getattr(material, "material_type", "")),
                    "manufacturer": str(getattr(material, "manufacturer", "")),
                    "reference_i_rms_a": request.i_rms_a,
                    "reference_current_density_a_per_mm2": request.i_rms_a / max(float(wire.bundle_copper_area) * parallels_i * 1e6, 1e-12),
                },
            )
        )
    return results


def _sort_candidates(candidates: Iterable[FixedInductorDesignCandidate]) -> list[FixedInductorDesignCandidate]:
    return sorted(
        list(candidates),
        key=lambda item: (
            _metric_or_inf(item.total_volume_m3),
            _metric_or_inf(item.reference_total_loss_w),
            item.candidate_id,
        ),
    )


def _best_balanced_candidate(candidates: list[FixedInductorDesignCandidate]) -> FixedInductorDesignCandidate:
    volumes = [_metric_or_inf(candidate.total_volume_m3) for candidate in candidates]
    losses = [_metric_or_inf(candidate.reference_total_loss_w) for candidate in candidates]
    min_volume, max_volume = min(volumes), max(volumes)
    min_loss, max_loss = min(losses), max(losses)

    def normalize(value: float, low: float, high: float) -> float:
        if high <= low:
            return 0.0
        return (value - low) / (high - low)

    return min(
        candidates,
        key=lambda candidate: (
            0.5 * normalize(_metric_or_inf(candidate.total_volume_m3), min_volume, max_volume)
            + 0.5 * normalize(_metric_or_inf(candidate.reference_total_loss_w), min_loss, max_loss),
            _metric_or_inf(candidate.total_volume_m3),
            _metric_or_inf(candidate.reference_total_loss_w),
            candidate.candidate_id,
        ),
    )


def _metric_or_inf(value: float | None) -> float:
    if value is None:
        return math.inf
    return float(value)


def _display_value(value: float | None, scale: float, unit: str) -> str:
    if value is None:
        return "-"
    return f"{float(value) * scale:.6g} {unit}"


def _compute_operating_core_loss_w(
    design: FixedInductorDesignCandidate,
    ve_m3: float,
    b_peak_t: float,
    fs_hz: float,
) -> float | None:
    metadata = design.metadata
    steinmetz_ranges = metadata.get("steinmetz_ranges")
    if not steinmetz_ranges:
        return None

    core_loss_model = str(metadata.get("core_loss_model") or "steinmetz_raw")
    raw_beta = _as_float(metadata.get("core_loss_beta_raw"))
    effective_beta = _as_float(metadata.get("core_loss_beta_effective")) or raw_beta
    if (
        core_loss_model == "stacked_seed_anchored_beta_floor"
        and effective_beta is not None
        and design.reference_core_loss_w is not None
    ):
        reference_b_peak_t = _as_float(metadata.get("reference_b_peak_t")) or design.b_peak_design_t
        reference_ve_m3 = _as_float(metadata.get("core_effective_volume_m3"))
        if reference_b_peak_t is not None and reference_b_peak_t > 0.0 and reference_ve_m3 is not None and reference_ve_m3 > 0.0:
            reference_density = design.reference_core_loss_w / reference_ve_m3
            return reference_density * ((b_peak_t / reference_b_peak_t) ** effective_beta) * ve_m3

    coeffs = _select_steinmetz_range(steinmetz_ranges, fs_hz)
    beta = raw_beta if raw_beta is not None else coeffs["beta"]
    return (
        coeffs["k"]
        * (fs_hz**coeffs["alpha"])
        * (b_peak_t**beta)
        * ve_m3
        * 1e3
    )


def _candidate_id(
    core_name: str,
    material_name: str,
    wire_name: str,
    turns: int,
    parallel_bundles: int,
) -> str:
    raw = f"{core_name}_{material_name}_{wire_name}_N{turns}_P{parallel_bundles}"
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", raw)


def _ac_resistance_multiplier(
    strand_diameter: float | None,
    total_strands: int | np.ndarray,
    fs_hz: float,
) -> float | np.ndarray:
    if strand_diameter is None or strand_diameter <= 0.0 or fs_hz <= 0.0:
        return 1.0
    skin_depth = math.sqrt(_COPPER_RESISTIVITY_25C / (math.pi * fs_hz * _MU0))
    if skin_depth <= 0.0:
        return 1.0
    x = strand_diameter / skin_depth
    return 1.0 + ((x**4) / 192.0) * np.sqrt(np.asarray(total_strands, dtype=float))


def _select_valid_cores(cores: pd.DataFrame, request: InductorDesignRequest, limit: int) -> pd.DataFrame:
    kf, kw, j_target, b_target = 0.5, 0.3, 4e6, 0.2
    ap_target = request.pout_nom_w / max(kf * kw * j_target * b_target * request.fs_hz, 1e-12)
    selected = cores[cores["Ap"] >= (0.35 * ap_target)].copy()
    if selected.empty:
        selected = cores.copy()
    return selected.sort_values(["Ve", "Ap"]).head(limit)


def _select_candidate_materials(materials: pd.DataFrame, request: InductorDesignRequest, limit: int) -> pd.DataFrame:
    selected = materials[
        (materials["f_max_recommended"] >= request.fs_hz)
        & (materials["f_min_recommended"] <= request.fs_hz)
        & (materials["B_sat"] >= 0.18)
    ].copy()
    if selected.empty:
        selected = materials.copy()
    return selected.sort_values(["B_sat", "f_max_recommended"], ascending=[False, True]).head(limit)


def _select_candidate_wires(wires: pd.DataFrame, request: InductorDesignRequest, limit: int) -> pd.DataFrame:
    required_area = request.i_rms_a / 4e6
    selected = wires[
        (wires["d_strand"] >= 0.04e-3)
        & (wires["d_strand"] <= 0.20e-3)
        & (wires["bundle_copper_area"] >= required_area / 12.0)
        & (wires["bundle_copper_area"] <= required_area * 1.25)
    ].copy()
    if selected.empty:
        selected = wires.copy()
    selected = selected.sort_values("bundle_copper_area")
    if len(selected) <= limit:
        return selected
    positions = np.linspace(0, len(selected) - 1, limit, dtype=int)
    return selected.iloc[np.unique(positions)].copy()


def _candidate_frame(candidates: Iterable[FixedInductorDesignCandidate]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        b_sat_t = _as_float(candidate.metadata.get("b_sat_t"))
        sat_margin = None
        if candidate.b_peak_design_t is not None and b_sat_t is not None and candidate.b_peak_design_t > 0.0:
            sat_margin = b_sat_t / candidate.b_peak_design_t
        rows.append(
            {
                "candidate_id": candidate.candidate_id,
                "assembly_type": candidate.assembly_type,
                "stack_count": candidate.stack_count,
                "base_core_name": candidate.base_core_name,
                "core_name": candidate.core_name,
                "material_name": candidate.material_name,
                "wire_name": candidate.wire_name,
                "turns": candidate.turns,
                "parallel_bundles": candidate.parallel_bundles,
                "gap_m": candidate.gap_m,
                "inductance_h": candidate.inductance_h,
                "rdc_25c_ohm": candidate.rdc_25c_ohm,
                "fill_factor": candidate.fill_factor,
                "core_volume_m3": candidate.core_volume_m3,
                "winding_volume_m3": candidate.winding_volume_m3,
                "total_volume_m3": candidate.total_volume_m3,
                "b_peak_design_t": candidate.b_peak_design_t,
                "b_sat_t": b_sat_t,
                "reference_sat_margin": sat_margin,
                "saturation_current_a": candidate.saturation_current_a,
                "reference_copper_loss_w": candidate.reference_copper_loss_w,
                "reference_core_loss_w": candidate.reference_core_loss_w,
                "reference_total_loss_w": candidate.reference_total_loss_w,
            }
        )
    return pd.DataFrame(rows)


def _write_pareto_plot(
    feasible_candidates: list[FixedInductorDesignCandidate],
    screened_candidates: list[FixedInductorDesignCandidate],
    compressed_candidates: list[FixedInductorDesignCandidate],
    chosen_candidates: list[FixedInductorDesignCandidate],
    recommended_design_id: str | None,
    output_path: Path,
) -> dict[str, Any]:
    plot_candidates, plot_source_name, plot_fallback_note = _resolve_plot_candidates(
        feasible_candidates=feasible_candidates,
        screened_candidates=screened_candidates,
        compressed_candidates=compressed_candidates,
        chosen_candidates=chosen_candidates,
    )
    plot_pareto_candidates = build_pareto_front(plot_candidates)
    if not plot_candidates or not plot_pareto_candidates:
        return {
            "success": False,
            "plot_source_name": plot_source_name,
            "plot_color_dimension": None,
            "plot_fallback_note": plot_fallback_note,
        }
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return {
            "success": False,
            "plot_source_name": plot_source_name,
            "plot_color_dimension": None,
            "plot_fallback_note": plot_fallback_note,
        }

    plot_df = _candidate_frame(plot_candidates).dropna(subset=["total_volume_m3", "reference_total_loss_w"])
    pareto_df = _candidate_frame(plot_pareto_candidates).dropna(subset=["total_volume_m3", "reference_total_loss_w"])
    chosen_df = _candidate_frame(chosen_candidates).dropna(subset=["total_volume_m3", "reference_total_loss_w"])
    if plot_df.empty or pareto_df.empty:
        return {
            "success": False,
            "plot_source_name": plot_source_name,
            "plot_color_dimension": None,
            "plot_fallback_note": plot_fallback_note,
        }

    plot_color_dimension, plot_df = _resolve_plot_color_dimension(plot_candidates, plot_df.copy())

    fig, ax = plt.subplots(figsize=(7.0, 4.6), dpi=160)
    color_map = _build_color_map(plot_df["plot_color_value"].dropna().astype(str).unique().tolist())
    for color_value in sorted(plot_df["plot_color_value"].dropna().astype(str).unique()):
        group = plot_df[plot_df["plot_color_value"].astype(str) == color_value]
        ax.scatter(
            group["total_volume_m3"] * 1e6,
            group["reference_total_loss_w"],
            s=18,
            color=color_map[color_value],
            alpha=0.55,
            edgecolors="none",
            label=color_value,
        )
    ax.plot(
        pareto_df["total_volume_m3"] * 1e6,
        pareto_df["reference_total_loss_w"],
        color="#111827",
        linewidth=2.0,
        linestyle="-",
        label="Pareto front",
    )
    for stack_count, group in pareto_df.groupby("stack_count", dropna=False):
        resolved_stack_count = _stack_count_or_default(stack_count)
        ax.scatter(
            group["total_volume_m3"] * 1e6,
            group["reference_total_loss_w"],
            s=36,
            color="#111827",
            marker=_stack_marker(resolved_stack_count),
            edgecolors="white",
            linewidths=0.5,
            zorder=4,
            label=f"Pareto {resolved_stack_count}-core",
        )
    if not chosen_df.empty:
        for stack_count, group in chosen_df.groupby("stack_count", dropna=False):
            resolved_stack_count = _stack_count_or_default(stack_count)
            ax.scatter(
                group["total_volume_m3"] * 1e6,
                group["reference_total_loss_w"],
                s=95,
                marker=_stack_marker(resolved_stack_count),
                facecolors="white",
                edgecolors="#111827",
                linewidths=1.1,
                zorder=5,
                label=f"Selected {resolved_stack_count}-core",
            )
        for index, row in enumerate(chosen_df.reset_index(drop=True).itertuples(), start=1):
            ax.annotate(
                f"{index} ({_stack_count_or_default(row.stack_count)}x)",
                xy=(row.total_volume_m3 * 1e6, row.reference_total_loss_w),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=8,
                color="#111827",
            )

    if recommended_design_id:
        recommended_df = chosen_df[chosen_df["candidate_id"] == recommended_design_id]
        if not recommended_df.empty:
            ax.scatter(
                recommended_df["total_volume_m3"] * 1e6,
                recommended_df["reference_total_loss_w"],
                s=190,
                marker="*",
                facecolors="#f59e0b",
                edgecolors="black",
                linewidths=1.0,
                zorder=6,
                label="Recommended",
            )
            recommended_row = recommended_df.iloc[0]
            ax.annotate(
                f"recommended ({_stack_count_or_default(recommended_row['stack_count'])}x)",
                xy=(recommended_row["total_volume_m3"] * 1e6, recommended_row["reference_total_loss_w"]),
                xytext=(8, -10),
                textcoords="offset points",
                fontsize=8,
                color="black",
            )

    ax.set_xlabel("Total volume (cm^3)")
    ax.set_ylabel("Reference total loss (W)")
    ax.set_title(_plot_title(plot_source_name))
    ax.grid(True, alpha=0.25)
    legend_title = plot_color_dimension.capitalize() if plot_color_dimension else "Design characteristic"
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, title=legend_title, loc="best", fontsize=7, title_fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return {
        "success": True,
        "plot_source_name": plot_source_name,
        "plot_color_dimension": plot_color_dimension,
        "plot_fallback_note": plot_fallback_note,
    }


@lru_cache(maxsize=1)
def _load_default_databases() -> _DatabaseBundle:
    data_root = _locate_mas_data_root()
    core_shapes = _read_ndjson(data_root / "core_shapes.ndjson")
    cores_stock = _read_ndjson(data_root / "cores_stock.ndjson")
    core_materials = _read_ndjson(data_root / "core_materials.ndjson")
    wires = _read_ndjson(data_root / "wires.ndjson")

    shapes_map = {shape["name"]: shape for shape in core_shapes}
    round_wires = {wire["name"]: wire for wire in wires if wire.get("type") == "round"}
    return _DatabaseBundle(
        cores=_build_cores_dataframe(cores_stock, shapes_map),
        materials=_build_materials_dataframe(core_materials),
        wires=_build_litz_dataframe(wires, round_wires),
    )


def _locate_mas_data_root() -> Path:
    env_root = os.environ.get("PE_CLAW_OPENMAGNETICS_DATA")
    candidates = [
        Path(env_root) if env_root else None,
        _project_root() / "external" / "OpenMagnetics-MAS" / "data",
        _project_root().parent / "Buck_Inductor_Opt_Design" / "New project" / "external" / "OpenMagnetics-MAS" / "data",
        _project_root().parent / "Buck_Inductor_Opt_Design" / "external" / "OpenMagnetics-MAS" / "data",
    ]
    for candidate in candidates:
        if candidate is not None and candidate.exists():
            return candidate
    raise InductorDatabaseUnavailableError(
        "OpenMagnetics-derived inductor database was not found. "
        "Set PE_CLAW_OPENMAGNETICS_DATA or place Buck_Inductor_Opt_Design beside PE_Claw."
    )


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _read_ndjson(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _dim_value(entry: dict[str, float] | None) -> float | None:
    if not entry:
        return None
    if "nominal" in entry:
        return float(entry["nominal"])
    if "minimum" in entry and "maximum" in entry:
        return 0.5 * (float(entry["minimum"]) + float(entry["maximum"]))
    if "minimum" in entry:
        return float(entry["minimum"])
    if "maximum" in entry:
        return float(entry["maximum"])
    return None


def _get_dims(shape: dict[str, Any]) -> dict[str, float]:
    return {
        key: value
        for key, value in (
            (dim_name, _dim_value(dim_data))
            for dim_name, dim_data in shape.get("dimensions", {}).items()
        )
        if value is not None
    }


def _build_cores_dataframe(
    cores_stock: list[dict[str, Any]],
    shapes_map: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    supported_families = {"t", "e", "etd", "er", "ec", "efd", "pq", "ep", "rm", "eq", "p", "u"}
    rows: list[dict[str, Any]] = []
    seen_shapes: set[str] = set()

    for core in cores_stock:
        functional = core.get("functionalDescription", {})
        shape_name = functional.get("shape")
        if not isinstance(shape_name, str) or shape_name in seen_shapes:
            continue

        shape = shapes_map.get(shape_name)
        if not shape or shape.get("family") not in supported_families:
            continue

        metrics = _approximate_core_metrics(shape)
        if not metrics:
            continue

        seen_shapes.add(shape_name)
        rows.append(
            {
                "core_name": shape_name,
                "shape_label": shape_name,
                "family": shape.get("family", ""),
                **metrics,
            }
        )

    cores = pd.DataFrame(rows).drop_duplicates(subset=["core_name"]).set_index("core_name")
    cores["Ap"] = cores["Ae"] * cores["Aw"]
    return cores.sort_values("Ve")


def _approximate_core_metrics(shape: dict[str, Any]) -> dict[str, float] | None:
    family = shape.get("family")
    dims = _get_dims(shape)
    if not dims:
        return None

    if family == "t":
        a = dims.get("A")
        b = dims.get("B")
        c = dims.get("C")
        if not all([a, b, c]) or a <= b:
            return None
        radial_thickness = 0.5 * (a - b)
        ae = radial_thickness * c
        le = math.pi * 0.5 * (a + b)
        aw = 0.25 * math.pi * b**2
        return {
            "Ae": ae,
            "Aw": max(aw, 1e-10),
            "Ve": ae * le,
            "le": le,
            "mlt": le,
            "gross_volume": 0.25 * math.pi * (a**2 - b**2) * c,
            "width": a,
            "height": a,
            "depth": c,
        }

    a = dims.get("A")
    b = dims.get("B")
    c = dims.get("C")
    d = dims.get("D")
    e = dims.get("E")
    f = dims.get("F")
    if not all([a, b, c]):
        return None

    assembly = resolve_core_assembly_envelope(
        family=str(family or ""),
        library_width_m=a,
        library_height_m=b,
        library_depth_m=c,
    )
    width = assembly.assembled_width_m
    height = assembly.assembled_height_m
    depth = assembly.assembled_depth_m
    gross_volume = assembly.assembled_volume_m3
    paired_family = is_paired_half_core_family(str(family or ""))
    effective_width = assembly.library_width_m if paired_family else width
    effective_height = assembly.library_height_m if paired_family else height
    effective_depth = assembly.library_depth_m if paired_family else depth

    if family == "pq":
        j = dims.get("J", 0.24 * min(effective_width, effective_height))
        l = dims.get("L", 0.55 * effective_width)
        g = dims.get("G", dims.get("F", 0.55 * effective_depth))
        ae = max(j * g, 1e-10)
        aw = max(2.0 * j * l, 1e-10)
        le = 2.0 * (dims.get("E", 0.8 * effective_width) + dims.get("F", 0.6 * effective_depth))
        return {
            "Ae": ae,
            "Aw": aw,
            "Ve": ae * le,
            "le": le,
            "mlt": 2.0 * (dims.get("E", 0.8 * effective_width) + effective_depth),
            "gross_volume": gross_volume,
            "width": width,
            "height": height,
            "depth": depth,
            "library_width": assembly.library_width_m,
            "library_height": assembly.library_height_m,
            "library_depth": assembly.library_depth_m,
            "library_item_is_half_core": assembly.library_item_is_half_core,
        }

    if family == "rm":
        g = dims.get("G", 0.45 * effective_width)
        h = dims.get("H", 0.25 * effective_height)
        j = dims.get("J", 0.75 * effective_width)
        c_dim = dims.get("C", effective_depth)
        ae = max(g * h, 1e-10)
        aw = max((j - g) * c_dim, 1e-10)
        le = 2.2 * (dims.get("E", 0.7 * effective_width) + dims.get("F", 0.45 * effective_depth))
        return {
            "Ae": ae,
            "Aw": aw,
            "Ve": ae * le,
            "le": le,
            "mlt": 2.0 * (j + c_dim),
            "gross_volume": gross_volume,
            "width": width,
            "height": height,
            "depth": depth,
            "library_width": assembly.library_width_m,
            "library_height": assembly.library_height_m,
            "library_depth": assembly.library_depth_m,
            "library_item_is_half_core": assembly.library_item_is_half_core,
        }

    # Paired families (U/E/ETD/PQ/RM) are stored as half-core library items. PE-Claw
    # now expands their physical bounding box and gross physical volume to the paired
    # assembly for reporting, geometry, and thermal use. The existing first-pass
    # effective-parameter approximations (Ae/Aw/le/Ve/MLT) are intentionally kept on
    # the same local shape basis that already drove the magnetic search, because the
    # semantics inspection showed the inconsistent part was the physical half-core
    # interpretation, not the effective magnetic-parameter basis.

    center_width = d or 0.35 * effective_width
    center_depth = f or 0.85 * effective_depth
    ae = max(center_width * center_depth, 1e-10)

    if family == "ep":
        aw = max((a - e) * max(b - f, 0.35 * b), 1e-10) if e and f else max(0.18 * width * height, 1e-10)
    elif family == "p":
        aw = max(dims.get("G", 0.18 * width) * dims.get("H", 0.45 * height), 1e-10)
    elif paired_family:
        aw = max(
            (effective_width - dims.get("D", 0.45 * effective_width))
            * dims.get("E", 0.35 * effective_height),
            1e-10,
        )
    else:
        aw = max((a - e) * max(b - f, 0.25 * b), 1e-10) if e and f else max(0.20 * width * height, 1e-10)

    if family == "efd":
        le = 2.0 * ((e or 0.75 * width) + dims.get("F2", center_depth))
    elif paired_family:
        le = 2.0 * ((e or 0.75 * effective_width) + (f or 0.6 * effective_depth))
    else:
        le = 2.0 * ((e or 0.75 * width) + (f or 0.6 * depth))

    return {
        "Ae": ae,
        "Aw": aw,
        "Ve": ae * le,
        "le": le,
        "mlt": 2.0 * ((e or 0.75 * effective_width) + effective_height),
        "gross_volume": gross_volume,
        "width": width,
        "height": height,
        "depth": depth,
        "library_width": assembly.library_width_m,
        "library_height": assembly.library_height_m,
        "library_depth": assembly.library_depth_m,
        "library_item_is_half_core": assembly.library_item_is_half_core,
    }


def _build_materials_dataframe(core_materials: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for material in core_materials:
        steinmetz_ranges = []
        for method in material.get("volumetricLosses", {}).get("default", []):
            if method.get("method") != "steinmetz":
                continue
            for range_data in method.get("ranges", []):
                steinmetz_ranges.append(
                    {
                        "minimumFrequency": float(range_data["minimumFrequency"]),
                        "maximumFrequency": float(range_data["maximumFrequency"]),
                        "k": float(range_data["k"]),
                        "alpha": float(range_data["alpha"]),
                        "beta": float(range_data["beta"]),
                    }
                )
        if not steinmetz_ranges:
            continue

        saturation = material.get("saturation", [])
        if not saturation:
            continue

        b_sat_t = max(float(point["magneticFluxDensity"]) for point in saturation if "magneticFluxDensity" in point)
        b_sat_100c_t, b_sat_100c_source = _resolve_b_sat_100c(saturation)

        rows.append(
            {
                "mat_name": material["name"],
                "manufacturer": material.get("manufacturerInfo", {}).get("name", ""),
                "material_type": material.get("material", ""),
                "B_sat": b_sat_t,
                "B_sat_100c": b_sat_100c_t,
                "b_sat_100c_source": b_sat_100c_source,
                "density": float(material.get("density", 4800.0)),
                "steinmetz_ranges": steinmetz_ranges,
                "f_min_recommended": float(material.get("recommendations", {}).get("minimumFrequency", 1.0)),
                "f_max_recommended": float(material.get("recommendations", {}).get("maximumFrequency", 1e9)),
            }
        )

    return pd.DataFrame(rows).drop_duplicates(subset=["mat_name"]).set_index("mat_name")


def _build_litz_dataframe(
    wires: list[dict[str, Any]],
    round_wires: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for wire in wires:
        if wire.get("type") != "litz":
            continue
        strand = wire.get("strand")
        strand_data = round_wires.get(strand) if isinstance(strand, str) else strand
        if not strand_data:
            continue

        strand_diameter = _dim_value(strand_data.get("conductingDiameter"))
        if not strand_diameter:
            continue

        strands_per_bundle = int(wire.get("numberConductors", 1))
        strand_area = math.pi * (strand_diameter / 2.0) ** 2
        rows.append(
            {
                "wire_id": wire["name"],
                "d_strand": strand_diameter,
                "a_strand": strand_area,
                "strands_per_bundle": strands_per_bundle,
                "bundle_copper_area": strands_per_bundle * strand_area,
                "outer_diameter": _dim_value(wire.get("outerDiameter")) or strand_diameter,
            }
        )

    return (
        pd.DataFrame(rows)
        .drop_duplicates(subset=["wire_id"])
        .sort_values("bundle_copper_area")
        .set_index("wire_id")
    )


def _select_steinmetz_range(ranges: list[dict[str, float]], frequency: float) -> dict[str, float]:
    for range_data in ranges:
        if range_data["minimumFrequency"] <= frequency <= range_data["maximumFrequency"]:
            return range_data
    return min(
        ranges,
        key=lambda item: min(
            abs(frequency - item["minimumFrequency"]),
            abs(frequency - item["maximumFrequency"]),
        ),
    )


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _derive_wire_family(wire_name: str) -> str:
    if "_" in wire_name:
        return wire_name.split("_", 1)[0]
    if "-" in wire_name:
        return wire_name.split("-", 1)[0]
    return wire_name


def _resolve_b_sat_100c(saturation_points: list[dict[str, Any]]) -> tuple[float | None, str]:
    points = [
        (float(point["temperature"]), float(point["magneticFluxDensity"]))
        for point in saturation_points
        if "temperature" in point and "magneticFluxDensity" in point
    ]
    if not points:
        return None, "missing"

    points.sort(key=lambda item: item[0])
    for temperature, flux in points:
        if temperature == 100.0:
            return flux, "exact"

    lower = max((item for item in points if item[0] < 100.0), default=None, key=lambda item: item[0])
    upper = min((item for item in points if item[0] > 100.0), default=None, key=lambda item: item[0])
    if lower is not None and upper is not None and upper[0] > lower[0]:
        ratio = (100.0 - lower[0]) / (upper[0] - lower[0])
        return lower[1] + ratio * (upper[1] - lower[1]), "interpolated"

    nominal = max(flux for _, flux in points)
    # Conservative fallback when the material database only exposes nominal or room-temperature saturation.
    return 0.80 * nominal, "fallback_0p80_nominal"


def _resolve_plot_candidates(
    feasible_candidates: list[FixedInductorDesignCandidate],
    screened_candidates: list[FixedInductorDesignCandidate],
    compressed_candidates: list[FixedInductorDesignCandidate],
    chosen_candidates: list[FixedInductorDesignCandidate],
) -> tuple[list[FixedInductorDesignCandidate], str, str | None]:
    if compressed_candidates:
        return compressed_candidates, "compressed_candidates", None
    if screened_candidates:
        return screened_candidates, "screened_candidates", "Compressed candidates were unavailable; PF plot fell back to screened_candidates."
    if feasible_candidates:
        return feasible_candidates, "basic_feasible_candidates", "Compressed and screened candidates were unavailable; PF plot fell back to basic feasible candidates."
    if chosen_candidates:
        return chosen_candidates, "chosen_designs", "Compressed, screened, and feasible candidate sets were unavailable; PF plot fell back to chosen designs."
    return [], "none", "No candidates were available for Pareto plotting."


def _resolve_plot_color_dimension(
    plot_candidates: list[FixedInductorDesignCandidate],
    plot_df: pd.DataFrame,
) -> tuple[str | None, pd.DataFrame]:
    dimensions = [
        ("core family", lambda candidate: str(candidate.metadata.get("family") or "").strip()),
        ("wire family", lambda candidate: str(candidate.metadata.get("wire_family") or "").strip()),
        ("material", lambda candidate: str(candidate.material_name or "").strip()),
    ]
    selected_dimension = None
    values: list[str] = []
    for label, getter in dimensions:
        resolved = [getter(candidate) for candidate in plot_candidates]
        unique = sorted({value for value in resolved if value})
        if len(unique) > 1:
            selected_dimension = label
            values = resolved
            break
    if selected_dimension is None:
        for label, getter in dimensions:
            resolved = [getter(candidate) for candidate in plot_candidates]
            unique = sorted({value for value in resolved if value})
            if unique:
                selected_dimension = label
                values = resolved
                break
    if selected_dimension is None:
        plot_df["plot_color_value"] = "unknown"
        return "material", plot_df

    plot_df["plot_color_value"] = [value if value else "unknown" for value in values]
    return selected_dimension, plot_df


def _build_color_map(values: list[str]) -> dict[str, str]:
    palette = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
        "#4c78a8",
        "#f58518",
        "#54a24b",
        "#e45756",
        "#72b7b2",
        "#b279a2",
        "#ff9da6",
        "#9d755d",
        "#bab0ab",
    ]
    unique_values = sorted(set(values))
    if not unique_values:
        unique_values = ["unknown"]
    return {
        value: palette[index % len(palette)]
        for index, value in enumerate(unique_values)
    }


def _plot_title(plot_source_name: str | None) -> str:
    if plot_source_name == "compressed_candidates":
        return "Compressed Candidate Pareto Front"
    if plot_source_name == "screened_candidates":
        return "Screened Candidate Pareto Front"
    if plot_source_name == "basic_feasible_candidates":
        return "Basic Feasible Candidate Pareto Front"
    if plot_source_name == "chosen_designs":
        return "Chosen Design Pareto View"
    return "Magnetic Pareto Front"


def _stack_marker(stack_count: int) -> str:
    return {
        1: "o",
        2: "s",
        3: "^",
    }.get(stack_count, "D")


def _stack_count_or_default(value: Any) -> int:
    try:
        return max(int(value), 1)
    except (TypeError, ValueError):
        return 1
