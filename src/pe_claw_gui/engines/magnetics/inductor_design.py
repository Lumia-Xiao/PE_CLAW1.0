"""Fixed inductor search, Pareto extraction, and operating-point evaluation."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from ...models.inductor import FixedInductorDesignCandidate, InductorDesignRequest, InductorOperatingEvaluation, InductorOperatingPointRequest
from ...utils.core_family_semantics import is_paired_half_core_family
from .data_backend import (
    MagneticDataBackendConfig,
    get_production_magnetic_backend_config,
    resolve_magnetic_data_backend,
)
from .legacy_external_openmagnetics import InductorDatabaseUnavailableError
from .core_loss_kernel import select_steinmetz_coefficients, steinmetz_loss_density_w_per_m3
from .core_loss_router import route_legacy_steinmetz_loss
from .catalog_core_binding import BoundCatalogCore, CatalogSelectionMode
from .core_loss_audit import core_loss_is_comparable

_MU0 = 4.0 * math.pi * 1e-7
_COPPER_RESISTIVITY_25C = 1.724e-8
_LITZ_PACKING_FACTOR = 1.10
_OUTPUT_SUBDIR = Path("outputs") / "inductor_design"
_STACKED_CORE_LOSS_BETA_FLOOR = 1.5


@dataclass(frozen=True)
class _DatabaseBundle:
    cores: pd.DataFrame
    materials: pd.DataFrame
    wires: pd.DataFrame
    catalog_cores: tuple[BoundCatalogCore, ...] = ()
    selection_mode: CatalogSelectionMode = "virtual"


@dataclass(frozen=True)
class MagneticArtifactExportResult:
    """Artifact export result, including plot metadata."""

    artifact_paths: list[str]
    plot_source_name: str | None = None
    plot_color_dimension: str | None = None
    plot_fallback_note: str | None = None


def synthesize_fixed_inductor_candidates(
    request: InductorDesignRequest,
    *,
    selection_mode: CatalogSelectionMode = "virtual",
) -> list[FixedInductorDesignCandidate]:
    """Search feasible fixed inductor designs for a normalized design request."""
    data_bundle = resolve_magnetic_data_backend(
        get_production_magnetic_backend_config(selection_mode=selection_mode)
    )
    database = _DatabaseBundle(
        cores=data_bundle.cores,
        materials=data_bundle.materials,
        wires=data_bundle.wires,
        catalog_cores=data_bundle.catalog_cores,
        selection_mode=data_bundle.selection_mode,
    )
    return _synthesize_fixed_inductor_candidates_from_database(request, database)


def synthesize_fixed_inductor_candidates_with_backend(
    request: InductorDesignRequest,
    backend_config: MagneticDataBackendConfig | None = None,
) -> list[FixedInductorDesignCandidate]:
    """Search feasible fixed inductor designs with an explicit data backend.

    The default public runtime path resolves the fixed normalized-v2 production
    cache. Callers may pass the explicit normalized-v1 rollback configuration
    for controlled diagnosis.
    """
    data_bundle = resolve_magnetic_data_backend(backend_config)
    database = _DatabaseBundle(
        cores=data_bundle.cores,
        materials=data_bundle.materials,
        wires=data_bundle.wires,
        catalog_cores=data_bundle.catalog_cores,
        selection_mode=data_bundle.selection_mode,
    )
    return _synthesize_fixed_inductor_candidates_from_database(request, database)


def synthesize_fixed_inductor_candidates_with_backend_audit(
    request: InductorDesignRequest,
    backend_config: MagneticDataBackendConfig | None = None,
) -> tuple[list[FixedInductorDesignCandidate], dict[str, int]]:
    """Search candidates and return the pre-candidate screening ledger."""
    data_bundle = resolve_magnetic_data_backend(backend_config)
    database = _DatabaseBundle(
        cores=data_bundle.cores,
        materials=data_bundle.materials,
        wires=data_bundle.wires,
        catalog_cores=data_bundle.catalog_cores,
        selection_mode=data_bundle.selection_mode,
    )
    audit: dict[str, int] = {}
    candidates = _generate_candidates(
        request, database, core_limit=14, material_limit=8, wire_limit=8, audit=audit
    )
    if not candidates:
        audit = {}
        candidates = _generate_candidates(
            request, database, core_limit=24, material_limit=12, wire_limit=12, audit=audit
        )
    audit["basic_feasible_candidate_count"] = len(candidates)
    return _sort_candidates(candidates), dict(sorted(audit.items()))


def _synthesize_fixed_inductor_candidates_from_database(
    request: InductorDesignRequest,
    database: _DatabaseBundle,
) -> list[FixedInductorDesignCandidate]:
    """Search feasible fixed inductor designs from a normalized data bundle."""
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

    if operating_point_request.mode == "tcm_triangular_current_first_pass":
        copper_loss_w, core_loss_w, b_peak_t, total_loss_w, segment_notes = _evaluate_tcm_segmented_operating_losses(
            design=design,
            operating_point_request=operating_point_request,
            ae=ae,
            ve=ve,
            strand_diameter=strand_diameter,
            total_strands=total_strands,
            turns=turns,
        )
        notes.extend(segment_notes)
    else:
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
            flux_peak_to_peak_t = abs(operating_point_request.v_l_on_v) * operating_point_request.duty / (
                operating_point_request.fs_hz * ae * turns
            )
            b_peak_t = design.inductance_h * operating_point_request.i_peak_a / (turns * ae)
            if steinmetz_ranges:
                core_loss_w = _compute_operating_core_loss_w(
                    design=design,
                    ve_m3=ve,
                    flux_peak_to_peak_t=flux_peak_to_peak_t,
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


def _evaluate_tcm_segmented_operating_losses(
    *,
    design: FixedInductorDesignCandidate,
    operating_point_request: InductorOperatingPointRequest,
    ae: float | None,
    ve: float | None,
    strand_diameter: float | None,
    total_strands: int,
    turns: int,
) -> tuple[float | None, float | None, float | None, float | None, list[str]]:
    metadata = design.metadata if isinstance(design.metadata, dict) else {}
    segments = metadata.get("tcm_segments")
    if not segments:
        return (None, None, None, None, ["TCM segmented magnetic loss data is unavailable; falling back to single-point evaluation."])
    if design.rdc_25c_ohm is None:
        return (None, None, None, None, ["TCM segmented magnetic loss data is unavailable because winding resistance is missing."])
    if ae is None or ve is None:
        return (None, None, None, None, ["TCM segmented magnetic loss data is unavailable because core geometry is missing."])
    if not metadata.get("steinmetz_ranges"):
        return (None, None, None, None, ["TCM segmented magnetic loss data is unavailable because Steinmetz data is missing."])

    total_time_s = 0.0
    total_copper_energy_j = 0.0
    total_core_energy_j = 0.0
    segment_b_peak_values: list[float] = []
    notes = [
        "TCM segmented magnetic loss is time-averaged from per-segment copper and core loss.",
        "Per-segment copper loss uses the segment switching frequency and the segment RMS current.",
        "Per-segment core loss uses the segment switching frequency and a first-pass Bpeak proxy.",
    ]

    for segment in segments:
        duration_s = _as_float(segment.get("duration_s")) or 0.0
        if duration_s <= 0.0:
            duration_s = _as_float(segment.get("switching_period_s")) or 0.0
        if duration_s <= 0.0:
            continue
        fsw_hz = _as_float(segment.get("fsw_hz")) or operating_point_request.fs_hz
        i_rms_a = _as_float(segment.get("irms_a")) or operating_point_request.i_rms_a
        volt_second_up_v_s = _as_float(segment.get("volt_second_up_v_s"))
        if volt_second_up_v_s is None:
            vac_eff_v = _as_float(segment.get("vac_eff_v")) or abs(operating_point_request.v_l_on_v)
            duty = _as_float(segment.get("duty")) or operating_point_request.duty
            volt_second_up_v_s = abs(vac_eff_v) * duty / max(fsw_hz, 1e-12)
        b_peak_t = abs(volt_second_up_v_s) / (ae * turns)
        segment_b_peak_values.append(b_peak_t)

        copper_energy_j = 0.0
        if design.rdc_25c_ohm is not None:
            copper_loss_w = (i_rms_a**2) * design.rdc_25c_ohm * _ac_resistance_multiplier(
                strand_diameter=strand_diameter,
                total_strands=total_strands,
                fs_hz=fsw_hz,
            )
            copper_energy_j = copper_loss_w * duration_s

        core_loss_w = _compute_operating_core_loss_w(
            design=design,
            ve_m3=ve,
            flux_peak_to_peak_t=b_peak_t,
            fs_hz=fsw_hz,
        )
        core_energy_j = (core_loss_w or 0.0) * duration_s

        total_time_s += duration_s
        total_copper_energy_j += copper_energy_j
        total_core_energy_j += core_energy_j

    if total_time_s <= 0.0:
        return (None, None, None, None, ["TCM segmented magnetic loss data was present but no valid segment timing could be evaluated."])

    copper_loss_avg_w = total_copper_energy_j / total_time_s if total_copper_energy_j else 0.0
    core_loss_avg_w = total_core_energy_j / total_time_s if total_core_energy_j else 0.0
    total_loss_avg_w = copper_loss_avg_w + core_loss_avg_w
    b_peak_t = max(segment_b_peak_values) if segment_b_peak_values else None
    return (
        copper_loss_avg_w if total_copper_energy_j or copper_loss_avg_w else None,
        core_loss_avg_w if total_core_energy_j or core_loss_avg_w else None,
        b_peak_t,
        total_loss_avg_w,
        notes,
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
    audit: dict[str, int] | None = None,
    core_offset: int = 0,
) -> list[FixedInductorDesignCandidate]:
    if database.selection_mode != "virtual":
        return _generate_catalog_candidates(request, database, core_limit=core_limit, wire_limit=wire_limit)
    cores = _select_valid_cores(database.cores, request, limit=core_limit).iloc[max(core_offset, 0) :]
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
                        audit=audit,
                    )
                )
    return candidates


def _generate_catalog_candidates(
    request: InductorDesignRequest,
    database: _DatabaseBundle,
    *,
    core_limit: int,
    wire_limit: int,
) -> list[FixedInductorDesignCandidate]:
    """Evaluate only exact catalog shape/material pairings."""
    selected = sorted(
        database.catalog_cores,
        key=lambda item: (item.effective_volume_m3 if item.effective_volume_m3 is not None else math.inf, item.catalog_core_id),
    )[: max(core_limit * 8, core_limit)]
    wires = _select_candidate_wires(database.wires, request, limit=wire_limit)
    candidates: list[FixedInductorDesignCandidate] = []
    for catalog in selected:
        core = database.cores.loc[catalog.shape_name] if catalog.shape_name in database.cores.index else None
        material = database.materials.loc[catalog.material_name] if catalog.material_name in database.materials.index else None
        if core is None or material is None:
            continue
        for wire in wires.itertuples():
            candidates.extend(_evaluate_core_material_wire_combo(request, core, material, wire, np.repeat(np.arange(8, 81, dtype=float), len(np.arange(1, 9, dtype=float))), np.tile(np.arange(1, 9, dtype=float), len(np.arange(8, 81, dtype=float))), catalog=catalog))
    return candidates


def _evaluate_core_material_wire_combo(
    request: InductorDesignRequest,
    core: Any,
    material: Any,
    wire: Any,
    turns_grid: np.ndarray,
    parallel_grid: np.ndarray,
    catalog: BoundCatalogCore | None = None,
    audit: dict[str, int] | None = None,
) -> list[FixedInductorDesignCandidate]:
    effective_volume_m3 = (
        float(catalog.effective_volume_m3)
        if catalog is not None and catalog.effective_volume_m3 is not None
        else float(core.Ve)
    )
    gap_m = (_MU0 * (turns_grid**2) * float(core.Ae)) / request.target_inductance_h
    fill_factor = turns_grid * parallel_grid * float(wire.bundle_copper_area) * _LITZ_PACKING_FACTOR / float(core.Aw)
    gap_mask = (gap_m > 0.02e-3) & (gap_m < 8.0e-3)
    fill_mask = (fill_factor > 0.01) & (fill_factor < 0.60)
    mask = gap_mask & fill_mask
    if audit is not None:
        _audit_increment(audit, "raw_grid_candidate_count", len(turns_grid))
        _audit_increment(audit, "identity_resolved_candidate_count", len(turns_grid))
        _audit_increment(audit, "gap_rejection_count", int((~gap_mask).sum()))
        _audit_increment(audit, "window_fill_rejection_count", int((gap_mask & ~fill_mask).sum()))
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
    flux_peak_to_peak_t = abs(request.v_l_on_v) * request.duty_nom / (request.fs_hz * float(core.Ae) * turns)
    flux_absolute_peak_t = request.target_inductance_h * request.i_peak_a / (turns * float(core.Ae))
    flux_dc_offset_t = request.target_inductance_h * request.i_avg_a / (turns * float(core.Ae))
    feasible = flux_absolute_peak_t < (0.85 * float(material.B_sat))
    if audit is not None:
        _audit_increment(audit, "saturation_rejection_count", int((~feasible).sum()))
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
    flux_peak_to_peak_t = flux_peak_to_peak_t[feasible]
    flux_absolute_peak_t = flux_absolute_peak_t[feasible]
    flux_dc_offset_t = flux_dc_offset_t[feasible]
    density_fn = np.vectorize(
        lambda flux_t: steinmetz_loss_density_w_per_m3(
            model=coeffs,
            frequency_hz=request.fs_hz,
            flux_ac_peak_t=float(flux_t) / 2.0,
        ),
        otypes=[float],
    )
    legacy_core_loss_w = density_fn(flux_peak_to_peak_t) * effective_volume_m3
    # Step 8 shadow adapter: the v1 search still supplies the candidate row,
    # while the shared router becomes the authoritative comparable loss value.
    routed_core_loss_w = np.empty(len(flux_peak_to_peak_t), dtype=float)
    router_statuses: list[str] = []
    router_attempt_counts: list[int] = []
    router_model_ids: list[str | None] = []
    router_model_scopes: list[str | None] = []
    for index, flux_bpp in enumerate(flux_peak_to_peak_t):
        routed = route_legacy_steinmetz_loss(
            model=coeffs,
            frequency_hz=request.fs_hz,
            flux_peak_to_peak_t=float(flux_bpp),
            effective_volume_m3=effective_volume_m3,
            material_id=str(material.Index),
            material_name=str(material.Index),
            calculation_mode="shadow_step8_generic_inductor",
        )
        if routed.core_loss_w is None or routed.volumetric_loss_w_per_m3 is None:
            # A candidate with unavailable reference loss is not comparable and
            # must not enter engineering ranking as a zero-loss candidate.
            routed_core_loss_w[index] = np.nan
        else:
            routed_core_loss_w[index] = float(routed.core_loss_w)
        router_statuses.append(routed.validity_status.value)
        router_attempt_counts.append(len(routed.routing_attempts))
        router_model_ids.append(routed.selected_model_id)
        router_model_scopes.append(routed.selected_model_scope)
    valid_router = np.isfinite(routed_core_loss_w)
    if audit is not None:
        _audit_increment(audit, "loss_model_unavailable_count", int((~valid_router).sum()))
        _audit_increment(audit, "model_compatible_candidate_count", int(valid_router.sum()))
    if not valid_router.any():
        return []
    turns = turns[valid_router]
    parallels = parallels[valid_router]
    gaps = gaps[valid_router]
    fills = fills[valid_router]
    total_strands = total_strands[valid_router]
    rdc = rdc[valid_router]
    copper_loss_w = copper_loss_w[valid_router]
    flux_peak_to_peak_t = flux_peak_to_peak_t[valid_router]
    flux_absolute_peak_t = flux_absolute_peak_t[valid_router]
    flux_dc_offset_t = flux_dc_offset_t[valid_router]
    legacy_core_loss_w = legacy_core_loss_w[valid_router]
    routed_core_loss_w = routed_core_loss_w[valid_router]
    router_statuses = [value for value, valid in zip(router_statuses, valid_router) if valid]
    router_attempt_counts = [value for value, valid in zip(router_attempt_counts, valid_router) if valid]
    router_model_ids = [value for value, valid in zip(router_model_ids, valid_router) if valid]
    router_model_scopes = [value for value, valid in zip(router_model_scopes, valid_router) if valid]
    total_loss_w = copper_loss_w + routed_core_loss_w
    winding_volume_m3 = (
        turns
        * parallels
        * float(core.mlt)
        * (math.pi * (float(wire.outer_diameter) / 2.0) ** 2)
        * _LITZ_PACKING_FACTOR
    )
    core_volume_m3 = np.full(
        len(turns),
        effective_volume_m3 if catalog is not None else float(core.gross_volume),
    )
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
            catalog_core_id=catalog.catalog_core_id if catalog is not None else None,
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
                b_peak_design_t=float(flux_absolute_peak_t[index]),
                saturation_current_a=float(saturation_current_a[index]),
                reference_copper_loss_w=float(copper_loss_w[index]),
                reference_core_loss_w=float(routed_core_loss_w[index]),
                reference_total_loss_w=float(total_loss_w[index]),
                notes=[
                    "Fixed inductor geometry synthesized from the design-point request.",
                    "Operating-point evaluation should reuse this geometry unchanged.",
                ],
                metadata={
                    "core_id": str(getattr(core, "stable_core_id", core.Index)),
                    "material_id": str(getattr(material, "stable_material_id", material.Index)),
                    "wire_id": str(getattr(wire, "stable_wire_id", wire.Index)),
                    "core_source_provenance": getattr(core, "core_source_provenance", None),
                    "material_source_provenance": getattr(material, "material_source_provenance", None),
                    "wire_source_record": getattr(wire, "source_wire_record", None),
                    "shape_label": str(getattr(core, "shape_label", core.Index)),
                    "family": str(getattr(core, "family", "")),
                    "wire_family": _derive_wire_family(str(wire.Index)),
                    "bundle_strands": int(wire.strands_per_bundle),
                    "total_strands": int(round(float(total_strands[index]))),
                    "bundle_copper_area_m2": float(wire.bundle_copper_area),
                    "strand_diameter_m": float(wire.d_strand),
                    "wire_outer_diameter_m": float(wire.outer_diameter),
                    "core_effective_area_m2": float(core.Ae),
                    "core_effective_volume_m3": effective_volume_m3,
                    "core_window_area_m2": float(core.Aw),
                    "core_path_length_m": float(core.le),
                    "mean_length_per_turn_m": float(core.mlt),
                    "gross_volume_m3": float(core.gross_volume),
                    "physical_envelope_volume_m3": _finite_or_none(
                        getattr(core, "physical_envelope_volume_m3", core.gross_volume)
                    ),
                    "solid_material_volume_m3": _finite_or_none(
                        getattr(core, "solid_material_volume_m3", None)
                    ),
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
                    "core_loss_unit_conversion_policy": "W_per_m3_times_m3_equals_W_once",
                    "core_loss_flux_input_definition": "core_loss_flux_peak_to_peak_t_is_Bpp; kernel_Bac_peak=Bpp/2",
                    "core_loss_flux_peak_to_peak_t": float(flux_peak_to_peak_t[index]),
                    "core_flux_ac_peak_t": float(flux_peak_to_peak_t[index]) / 2.0,
                    "core_flux_dc_offset_t": float(flux_dc_offset_t[index]),
                    "core_flux_absolute_peak_t": float(flux_absolute_peak_t[index]),
                    "saturation_flux_input_definition": "Babsolute=L*Ipeak/(N*Ae)",
                    "legacy_core_loss_w": float(legacy_core_loss_w[index]),
                    "kernel_core_loss_w": float(routed_core_loss_w[index]),
                    "step8_router_core_loss_w": float(routed_core_loss_w[index]),
                    "step8_router_status": router_statuses[index],
                    "step8_router_policy": "mkf_compatible_v1",
                    "step8_router_attempt_count": router_attempt_counts[index],
                    "step8_router_model_id": router_model_ids[index],
                    "step8_router_model_scope": router_model_scopes[index],
                    "core_loss_validity_status": router_statuses[index],
                    "core_loss_method": "steinmetz",
                    "core_loss_model_id": router_model_ids[index],
                    "core_loss_model_scope": router_model_scopes[index],
                    "core_loss_effective_volume_m3": effective_volume_m3,
                    "step8_legacy_core_loss_w": float(legacy_core_loss_w[index]),
                    "kernel_vs_legacy_relative_difference": (1.0 / (1e3 * (2.0 ** float(coeffs["beta"])))) - 1.0,
                    "core_loss_beta_raw": float(coeffs["beta"]),
                    "core_loss_beta_effective": float(coeffs["beta"]),
                    # The explicit names are authoritative.  ``reference_b_peak_t``
                    # remains as a compatibility alias for older stacked-loss
                    # callers, but its historical value is Bpp, not Babsolute.
                    "reference_flux_peak_to_peak_t": float(flux_peak_to_peak_t[index]),
                    "reference_flux_ac_peak_t": float(flux_peak_to_peak_t[index]) / 2.0,
                    "reference_flux_absolute_peak_t": float(flux_absolute_peak_t[index]),
                    "reference_b_peak_t": float(flux_peak_to_peak_t[index]),
                    "reference_core_loss_density_w_per_m3": float(routed_core_loss_w[index]) / max(effective_volume_m3, 1e-18),
                    "material_type": str(getattr(material, "material_type", "")),
                    "manufacturer": str(getattr(material, "manufacturer", "")),
                    "material_metric_source": str(getattr(material, "material_metric_source", "")),
                    "material_metric_source_pdf": str(getattr(material, "material_metric_source_pdf", "")),
                    "material_metric_source_page": str(getattr(material, "material_metric_source_page", "")),
                    "material_metric_notes": str(getattr(material, "material_metric_notes", "")),
                    "material_recommended_frequency_min_hz": _as_float(getattr(material, "f_min_recommended", None)),
                    "material_recommended_frequency_max_hz": _as_float(getattr(material, "f_max_recommended", None)),
                    "reference_i_rms_a": request.i_rms_a,
                    "reference_current_density_a_per_mm2": request.i_rms_a / max(float(wire.bundle_copper_area) * parallels_i * 1e6, 1e-12),
                    "tcm_segments": request.metadata.get("tcm_segments"),
                    "core_selection_mode": "virtual" if catalog is None else catalog.catalog_kind,
                    "purchasable": catalog is not None,
                    "commercial_binding_status": "virtual_shape_material_combination" if catalog is None else "bound",
                    "catalog_core_id": catalog.catalog_core_id if catalog is not None else None,
                    "catalog_kind": catalog.catalog_kind if catalog is not None else None,
                    "manufacturer_reference": catalog.manufacturer_reference if catalog is not None else None,
                    "catalog_manufacturer": catalog.manufacturer if catalog is not None else None,
                    "manufacturer_status": catalog.manufacturer_status if catalog is not None else None,
                    "catalog_shape_id": catalog.shape_id if catalog is not None else None,
                    "catalog_material_id": catalog.material_id if catalog is not None else None,
                    "catalog_number_stacks": catalog.number_stacks if catalog is not None else 1,
                    "catalog_gapping": list(catalog.gapping) if catalog is not None else [],
                    "catalog_distributor_entries": list(catalog.distributor_entries) if catalog is not None else [],
                    "core_effective_volume_source": "catalog_shape_effective_volume" if catalog is not None and catalog.effective_volume_m3 is not None else "virtual_shape_dataframe",
                    "core_mass_kg": (
                        catalog.mass_kg
                        if catalog is not None
                        else _finite_or_none(getattr(core, "core_mass_kg", None))
                    ),
                },
            )
        )
    return results


def _audit_increment(audit: dict[str, int], key: str, amount: int) -> None:
    audit[key] = audit.get(key, 0) + int(amount)


def _sort_candidates(candidates: Iterable[FixedInductorDesignCandidate]) -> list[FixedInductorDesignCandidate]:
    return sorted(
        list(candidates),
        key=lambda item: (
            0 if core_loss_is_comparable(item.metadata, item.reference_total_loss_w) else 1,
            _metric_or_inf(item.total_volume_m3),
            _metric_or_inf(item.reference_total_loss_w),
            item.candidate_id,
        ),
    )


def _best_balanced_candidate(candidates: list[FixedInductorDesignCandidate]) -> FixedInductorDesignCandidate:
    comparable = [item for item in candidates if core_loss_is_comparable(item.metadata, item.reference_total_loss_w)]
    if comparable:
        candidates = comparable
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
    flux_peak_to_peak_t: float,
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
        reference_b_peak_t = (
            _as_float(metadata.get("reference_flux_peak_to_peak_t"))
            or _as_float(metadata.get("reference_b_peak_t"))
            or design.b_peak_design_t
        )
        reference_ve_m3 = _as_float(metadata.get("core_effective_volume_m3"))
        if reference_b_peak_t is not None and reference_b_peak_t > 0.0 and reference_ve_m3 is not None and reference_ve_m3 > 0.0:
            reference_density = design.reference_core_loss_w / reference_ve_m3
            return reference_density * ((flux_peak_to_peak_t / reference_b_peak_t) ** effective_beta) * ve_m3

    coeffs = _select_steinmetz_range(steinmetz_ranges, fs_hz)
    beta = raw_beta if raw_beta is not None else coeffs["beta"]
    return steinmetz_loss_density_w_per_m3(
        model={**coeffs, "beta": beta},
        frequency_hz=fs_hz,
        flux_ac_peak_t=flux_peak_to_peak_t / 2.0,
    ) * ve_m3


def _candidate_id(
    core_name: str,
    material_name: str,
    wire_name: str,
    turns: int,
    parallel_bundles: int,
    catalog_core_id: str | None = None,
) -> str:
    raw = f"{core_name}_{material_name}_{wire_name}_N{turns}_P{parallel_bundles}"
    if catalog_core_id:
        raw = f"{catalog_core_id}_{raw}"
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
    columns = [
        "candidate_id",
        "assembly_type",
        "stack_count",
        "base_core_name",
        "core_name",
        "material_name",
        "wire_name",
        "turns",
        "parallel_bundles",
        "gap_m",
        "inductance_h",
        "rdc_25c_ohm",
        "fill_factor",
        "core_volume_m3",
        "winding_volume_m3",
        "total_volume_m3",
        "b_peak_design_t",
        "b_sat_t",
        "reference_sat_margin",
        "saturation_current_a",
        "reference_copper_loss_w",
        "reference_core_loss_w",
        "reference_total_loss_w",
    ]
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
    return pd.DataFrame(rows, columns=columns)


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


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _select_steinmetz_range(ranges: list[dict[str, float]], frequency: float) -> dict[str, float]:
    return select_steinmetz_coefficients(ranges, frequency)


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _finite_or_none(value: Any) -> float | None:
    resolved = _as_float(value)
    return resolved if resolved is not None and math.isfinite(resolved) else None


def _derive_wire_family(wire_name: str) -> str:
    if "_" in wire_name:
        return wire_name.split("_", 1)[0]
    if "-" in wire_name:
        return wire_name.split("-", 1)[0]
    return wire_name


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
