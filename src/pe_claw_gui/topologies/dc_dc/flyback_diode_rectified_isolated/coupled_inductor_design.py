"""First-pass coupled-inductor target and search helpers for Flyback."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping

from ....models.inductor import FixedInductorDesignCandidate
from ....engines.magnetics.core_loss_role_adapter import evaluate_candidate_core_loss
from ....engines.magnetics.winding_evidence import build_winding_electrical_evidence
from ...base.candidate import TopologyCandidate


_MU0_H_PER_M = 4.0 * math.pi * 1e-7
_DEFAULT_AMBIENT_C = 40.0
_DEFAULT_HOTSPOT_LIMIT_C = 120.0


@dataclass(frozen=True)
class FlybackCoupledInductorCore:
    """Small packaged core option used by the first-pass Flyback search."""

    core_name: str
    material_name: str
    effective_area_m2: float
    window_area_m2: float
    magnetic_path_length_m: float
    effective_volume_m3: float
    mean_turn_length_m: float
    core_width_m: float
    core_height_m: float
    core_depth_m: float
    steinmetz_ranges: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class FlybackCoupledInductorWire:
    """Copper option used by the first-pass Flyback coupled-inductor search."""

    wire_name: str
    copper_area_m2: float
    resistance_ohm_per_m_25c: float
    wire_id: str = ""
    source_wire_record: Mapping[str, Any] = field(default_factory=dict)
    area_basis: str = "first_pass_declared_copper_area"
    strand_diameter_m: float | None = None
    strand_count: int = 1


@dataclass(frozen=True)
class FlybackCoupledInductorSearchResult:
    """Structured result for the first-pass Flyback coupled-inductor search."""

    design_requirements: dict[str, float | str | bool | None]
    evaluated_count: int = 0
    feasible_candidates: list[FixedInductorDesignCandidate] = field(default_factory=list)
    chosen_candidates: list[FixedInductorDesignCandidate] = field(default_factory=list)
    recommended_candidate: FixedInductorDesignCandidate | None = None
    rejection_counts: dict[str, int] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

def build_coupled_inductor_target(
    *,
    magnetizing_inductance_h: float,
    primary_peak_current_a: float,
    switching_frequency_hz: float,
    turns_ratio_ns_np: float,
) -> dict[str, float | str]:
    """Return the target values that a later gapped-core search must satisfy."""

    stored_energy_j = 0.5 * magnetizing_inductance_h * primary_peak_current_a * primary_peak_current_a
    return {
        "target_type": "gapped_flyback_coupled_inductor",
        "magnetizing_inductance_h": magnetizing_inductance_h,
        "primary_peak_current_a": primary_peak_current_a,
        "turns_ratio_ns_np": turns_ratio_ns_np,
        "switching_frequency_hz": switching_frequency_hz,
        "stored_energy_j": stored_energy_j,
        "stored_energy_uj": stored_energy_j * 1e6,
    }


def generate_flyback_coupled_inductor_candidates(
    candidate: TopologyCandidate,
    *,
    b_limit_t: float = 0.22,
    fill_limit: float = 0.45,
    current_density_limit_a_per_mm2: float = 6.0,
    insulation_window_reserve_ratio: float = 0.18,
    material_limit: int | None = 16,
    backend_bundle: Any | None = None,
) -> FlybackCoupledInductorSearchResult:
    """Search a deterministic first-pass gapped coupled-inductor candidate set."""

    flyback = _flyback_metadata(candidate)
    target = _target_metadata(flyback)
    lm_h = _positive_float(target, "magnetizing_inductance_h")
    primary_peak_a = _positive_float(target, "primary_peak_current_a")
    primary_valley_a = _nonnegative_float_or_default(
        flyback,
        "sizing_primary_valley_current_a",
        _nonnegative_float_or_default(flyback, "primary_valley_current_a", 0.0),
    )
    if primary_valley_a >= primary_peak_a:
        raise ValueError("Flyback primary valley current must be below primary peak current.")
    turns_ratio_ns_np = _positive_float(target, "turns_ratio_ns_np")
    fs_hz = _positive_float(target, "switching_frequency_hz")
    stored_energy_j = _positive_float(target, "stored_energy_j")
    primary_rms_a = _positive_float_or_default(
        flyback,
        "sizing_primary_switch_rms_current_a",
        _positive_float_or_default(flyback, "primary_switch_rms_current_a", primary_peak_a / math.sqrt(3.0)),
    )
    secondary_rms_a = _positive_float_or_default(
        flyback,
        "sizing_secondary_rms_current_a",
        _positive_float_or_default(flyback, "secondary_rms_current_a", candidate.iout),
    )
    secondary_peak_a = _positive_float_or_default(
        flyback,
        "sizing_secondary_peak_current_a",
        primary_peak_a / max(turns_ratio_ns_np, 1e-12),
    )

    design_requirements = {
        "topology_id": candidate.topology_id,
        "design_type": "gapped_flyback_coupled_inductor",
        "magnetizing_inductance_h": lm_h,
        "lm_target_h": lm_h,
        "primary_peak_current_a": primary_peak_a,
        "primary_valley_current_a": primary_valley_a,
        "primary_rms_current_a": primary_rms_a,
        "secondary_peak_current_a": secondary_peak_a,
        "secondary_rms_current_a": secondary_rms_a,
        "turns_ratio_ns_np": turns_ratio_ns_np,
        "fs_hz": fs_hz,
        "stored_energy_j": stored_energy_j,
        "b_limit_t": b_limit_t,
        "fill_limit": fill_limit,
        "current_density_limit_a_per_mm2": current_density_limit_a_per_mm2,
        "insulation_window_reserve_ratio": insulation_window_reserve_ratio,
    }

    feasible: list[FixedInductorDesignCandidate] = []
    rejection_counts: dict[str, int] = {}
    evaluated_count = 0
    if backend_bundle is None:
        # Keep standalone callers on the same central production resolver as
        # the pipeline; static first-pass tables are reserved for explicit
        # fixtures passed through the private conversion helpers.
        from ....engines.magnetics.data_backend import resolve_magnetic_data_backend

        backend_bundle = resolve_magnetic_data_backend()
    core_options = _backend_core_options(backend_bundle, material_limit=material_limit)
    wire_options = _backend_wire_options(backend_bundle)
    for core in core_options:
        for primary_wire in wire_options:
            for secondary_wire in wire_options:
                evaluated_count += 1
                candidate_row, rejection_reason = _build_candidate(
                    core=core,
                    primary_wire=primary_wire,
                    secondary_wire=secondary_wire,
                    lm_h=lm_h,
                    primary_peak_a=primary_peak_a,
                    primary_valley_a=primary_valley_a,
                    primary_rms_a=primary_rms_a,
                    secondary_peak_a=secondary_peak_a,
                    secondary_rms_a=secondary_rms_a,
                    turns_ratio_ns_np=turns_ratio_ns_np,
                    fs_hz=fs_hz,
                    stored_energy_j=stored_energy_j,
                    b_limit_t=b_limit_t,
                    fill_limit=fill_limit,
                    current_density_limit_a_per_mm2=current_density_limit_a_per_mm2,
                    insulation_window_reserve_ratio=insulation_window_reserve_ratio,
                    sequence=evaluated_count,
                )
                if rejection_reason:
                    rejection_counts[rejection_reason] = rejection_counts.get(rejection_reason, 0) + 1
                    continue
                feasible.append(candidate_row)

    feasible.sort(key=_candidate_score)
    chosen = _choose_representative_candidates(feasible)
    recommended = chosen[0] if chosen else None
    notes = [
        "Flyback coupled-inductor search uses a deterministic first-pass gapped-core table.",
        "Primary turns use Np >= Lm * Ipk / (Blimit * Ae); air gap uses gap = mu0 * Np^2 * Ae / Lm.",
        "Secondary turns are rounded from the synthesized Ns/Np ratio and checked against a ratio-error limit.",
        "Window fill includes a reserved insulation area proxy, but creepage, clearance, hi-pot, bobbin, and safety-standard checks are not final.",
        "Leakage inductance, clamp/snubber dynamics, proximity loss, EMI, and detailed winding-stack optimization remain follow-up work.",
    ]
    notes.append(
        f"Magnetic backend: {backend_bundle.backend} ({backend_bundle.mode}); "
        "central normalized resolver supplied core/material/wire records."
    )
    warnings: list[str] = []
    if recommended is None:
        warnings.append("No first-pass Flyback coupled-inductor candidate satisfied Bpeak, gap, turns, and fill constraints.")

    return FlybackCoupledInductorSearchResult(
        design_requirements=design_requirements,
        evaluated_count=evaluated_count,
        feasible_candidates=feasible,
        chosen_candidates=chosen,
        recommended_candidate=recommended,
        rejection_counts=rejection_counts,
        notes=notes,
        warnings=warnings,
    )


def _build_candidate(
    *,
    core: FlybackCoupledInductorCore,
    primary_wire: FlybackCoupledInductorWire,
    secondary_wire: FlybackCoupledInductorWire,
    lm_h: float,
    primary_peak_a: float,
    primary_valley_a: float,
    primary_rms_a: float,
    secondary_peak_a: float,
    secondary_rms_a: float,
    turns_ratio_ns_np: float,
    fs_hz: float,
    stored_energy_j: float,
    b_limit_t: float,
    fill_limit: float,
    current_density_limit_a_per_mm2: float,
    insulation_window_reserve_ratio: float,
    sequence: int,
) -> tuple[FixedInductorDesignCandidate, str]:
    np_turns = max(1, math.ceil(lm_h * primary_peak_a / max(b_limit_t * core.effective_area_m2, 1e-18)))
    ns_turns = max(1, round(np_turns * turns_ratio_ns_np))
    if np_turns > 180 or ns_turns > 180:
        return _empty_candidate(sequence), "turns_exceed_first_pass_limit"

    actual_ratio = ns_turns / max(np_turns, 1)
    ratio_error_percent = abs(actual_ratio - turns_ratio_ns_np) / max(turns_ratio_ns_np, 1e-12) * 100.0
    if ratio_error_percent > 5.0:
        return _empty_candidate(sequence), "turns_ratio_error_exceeds_limit"

    gap_m = _MU0_H_PER_M * np_turns * np_turns * core.effective_area_m2 / max(lm_h, 1e-18)
    if gap_m < 0.05e-3:
        return _empty_candidate(sequence), "gap_below_practical_limit"
    if gap_m > 3.5e-3:
        return _empty_candidate(sequence), "gap_exceeds_first_pass_limit"

    b_peak_t = lm_h * primary_peak_a / max(np_turns * core.effective_area_m2, 1e-18)
    if b_peak_t > b_limit_t:
        return _empty_candidate(sequence), "bpeak_exceeds_limit"

    primary_parallel = _parallel_count(primary_rms_a, primary_wire, current_density_limit_a_per_mm2)
    secondary_parallel = _parallel_count(secondary_rms_a, secondary_wire, current_density_limit_a_per_mm2)
    primary_copper_area_m2 = primary_wire.copper_area_m2 * primary_parallel
    secondary_copper_area_m2 = secondary_wire.copper_area_m2 * secondary_parallel
    winding_fill_area_m2 = 1.75 * (
        np_turns * primary_copper_area_m2 + ns_turns * secondary_copper_area_m2
    )
    insulation_reserved_area_m2 = insulation_window_reserve_ratio * core.window_area_m2
    fill_factor = (winding_fill_area_m2 + insulation_reserved_area_m2) / max(core.window_area_m2, 1e-18)
    if fill_factor > fill_limit:
        return _empty_candidate(sequence), "fill_factor_exceeds_limit"

    temperature_resistance_factor = 1.25
    resistance_temperature_c = 25.0 + (temperature_resistance_factor - 1.0) / 0.00393
    primary_winding_evidence = build_winding_electrical_evidence(
        wire_id=primary_wire.wire_id or primary_wire.wire_name,
        wire_name=primary_wire.wire_name,
        source_wire_record=_wire_source_record(primary_wire),
        conducting_area_m2=primary_wire.copper_area_m2,
        area_basis=primary_wire.area_basis,
        strand_diameter_m=_wire_strand_diameter(primary_wire),
        strand_count=primary_wire.strand_count,
        parallel_winding_count=primary_parallel,
        turns=np_turns,
        mean_length_per_turn_m=core.mean_turn_length_m,
        resistance_temperature_c=resistance_temperature_c,
        resistance_temperature_factor=temperature_resistance_factor,
        rac_multiplier=1.0,
        rms_current_a=primary_rms_a,
        fill_area_m2=1.75 * np_turns * primary_copper_area_m2,
        resistance_ohm_per_m_25c=primary_wire.resistance_ohm_per_m_25c,
    )
    secondary_winding_evidence = build_winding_electrical_evidence(
        wire_id=secondary_wire.wire_id or secondary_wire.wire_name,
        wire_name=secondary_wire.wire_name,
        source_wire_record=_wire_source_record(secondary_wire),
        conducting_area_m2=secondary_wire.copper_area_m2,
        area_basis=secondary_wire.area_basis,
        strand_diameter_m=_wire_strand_diameter(secondary_wire),
        strand_count=secondary_wire.strand_count,
        parallel_winding_count=secondary_parallel,
        turns=ns_turns,
        mean_length_per_turn_m=core.mean_turn_length_m,
        resistance_temperature_c=resistance_temperature_c,
        resistance_temperature_factor=temperature_resistance_factor,
        rac_multiplier=1.0,
        rms_current_a=secondary_rms_a,
        fill_area_m2=1.75 * ns_turns * secondary_copper_area_m2,
        resistance_ohm_per_m_25c=secondary_wire.resistance_ohm_per_m_25c,
    )
    primary_resistance_ohm = primary_winding_evidence.rdc_25c_ohm
    secondary_resistance_ohm = secondary_winding_evidence.rdc_25c_ohm
    copper_loss_w = (
        primary_winding_evidence.total_copper_loss_w
        + secondary_winding_evidence.total_copper_loss_w
    )
    core_loss_w, core_loss_audit = _shared_core_loss(
        core,
        fs_hz=fs_hz,
        primary_valley_a=primary_valley_a,
        primary_peak_a=primary_peak_a,
        turns=np_turns,
        inductance_h=lm_h,
        component_id=f"flyback-ci-{sequence:03d}",
    )
    total_loss_w = copper_loss_w + core_loss_w
    winding_volume_m3 = 1.75 * core.mean_turn_length_m * (
        np_turns * primary_copper_area_m2 + ns_turns * secondary_copper_area_m2
    )
    total_volume_m3 = core.effective_volume_m3 + winding_volume_m3
    thermal_resistance_k_per_w = _first_pass_thermal_resistance_k_per_w(total_volume_m3)
    hotspot_c = _DEFAULT_AMBIENT_C + total_loss_w * thermal_resistance_k_per_w
    if hotspot_c > _DEFAULT_HOTSPOT_LIMIT_C:
        return _empty_candidate(sequence), "thermal_limit"
    saturation_current_a = b_limit_t * np_turns * core.effective_area_m2 / max(lm_h, 1e-18)

    metadata = {
        "primary_turns": np_turns,
        "secondary_turns": ns_turns,
        "turns_ratio_ns_np_target": turns_ratio_ns_np,
        "turns_ratio_ns_np_actual": actual_ratio,
        "turns_ratio_error_percent": ratio_error_percent,
        "b_limit_t": b_limit_t,
        "fill_limit": fill_limit,
        "stored_energy_j": stored_energy_j,
        "stored_energy_uj": stored_energy_j * 1e6,
        "primary_wire_name": primary_wire.wire_name,
        "secondary_wire_name": secondary_wire.wire_name,
        "primary_parallel_bundles": primary_parallel,
        "secondary_parallel_bundles": secondary_parallel,
        "primary_current_density_a_per_mm2": primary_rms_a / max(primary_copper_area_m2 * 1e6, 1e-12),
        "secondary_current_density_a_per_mm2": secondary_rms_a / max(secondary_copper_area_m2 * 1e6, 1e-12),
        "primary_rms_current_a": primary_rms_a,
        "secondary_rms_current_a": secondary_rms_a,
        "primary_peak_current_a": primary_peak_a,
        "primary_valley_current_a": primary_valley_a,
        "primary_delta_current_a": primary_peak_a - primary_valley_a,
        "secondary_peak_current_a": secondary_peak_a,
        **core_loss_audit,
        "thermal_model": "first_pass_volume_proxy_lumped",
        "thermal_resistance_k_per_w": thermal_resistance_k_per_w,
        "ambient_c": _DEFAULT_AMBIENT_C,
        "hotspot_c": hotspot_c,
        "hotspot_limit_c": _DEFAULT_HOTSPOT_LIMIT_C,
        "thermal_status": "pass",
        "winding_evidence_contract_version": primary_winding_evidence.contract_version,
        "winding_evidence": {
            "primary": primary_winding_evidence.to_dict(),
            "secondary": secondary_winding_evidence.to_dict(),
        },
        "winding_current_basis": {
            "primary": "flyback primary magnetizing/switch RMS current",
            "secondary": "flyback secondary rectifier RMS current",
        },
        "core_width_m": core.core_width_m,
        "core_height_m": core.core_height_m,
        "core_depth_m": core.core_depth_m,
        "core_effective_area_m2": core.effective_area_m2,
        "core_window_area_m2": core.window_area_m2,
        "core_magnetic_path_length_m": core.magnetic_path_length_m,
        "insulation_reserved_area_m2": insulation_reserved_area_m2,
        "search_basis": "first_pass_energy_storage_gapped_flyback_coupled_inductor",
        "family": "flyback",
    }
    return (
        FixedInductorDesignCandidate(
            candidate_id=f"flyback-ci-{sequence:03d}",
            assembly_type="gapped_coupled_inductor",
            stack_count=1,
            base_core_name=core.core_name,
            core_name=core.core_name,
            material_name=core.material_name,
            wire_name=f"{primary_wire.wire_name} / {secondary_wire.wire_name}",
            turns=np_turns,
            parallel_bundles=primary_parallel,
            gap_m=gap_m,
            inductance_h=lm_h,
            rdc_25c_ohm=primary_resistance_ohm,
            fill_factor=fill_factor,
            core_volume_m3=core.effective_volume_m3,
            winding_volume_m3=winding_volume_m3,
            total_volume_m3=total_volume_m3,
            b_peak_design_t=b_peak_t,
            saturation_current_a=saturation_current_a,
            reference_copper_loss_w=copper_loss_w,
            reference_core_loss_w=core_loss_w,
            reference_total_loss_w=total_loss_w,
            notes=[
                "First-pass Flyback gapped coupled-inductor candidate.",
                "Np realizes Lm energy storage; Ns realizes the synthesized output/input turns ratio.",
            ],
            metadata=metadata,
        ),
        "",
    )


def _choose_representative_candidates(
    feasible: list[FixedInductorDesignCandidate],
    *,
    limit: int = 5,
) -> list[FixedInductorDesignCandidate]:
    if not feasible:
        return []
    selected: list[FixedInductorDesignCandidate] = []
    for row in (
        min(feasible, key=lambda item: item.reference_total_loss_w or float("inf")),
        min(feasible, key=lambda item: item.total_volume_m3 or float("inf")),
        feasible[0],
    ):
        if row.candidate_id not in {item.candidate_id for item in selected}:
            selected.append(row)
    for row in feasible:
        if len(selected) >= limit:
            break
        if row.candidate_id not in {item.candidate_id for item in selected}:
            selected.append(row)
    selected.sort(key=_candidate_score)
    return selected


def _candidate_score(candidate: FixedInductorDesignCandidate) -> tuple[float, float, str]:
    loss_w = candidate.reference_total_loss_w or float("inf")
    volume_cm3 = (candidate.total_volume_m3 or float("inf")) * 1e6
    return (loss_w + 0.015 * volume_cm3, volume_cm3, candidate.candidate_id)


def _shared_core_loss(
    core: FlybackCoupledInductorCore,
    *,
    fs_hz: float,
    primary_valley_a: float,
    primary_peak_a: float,
    turns: int,
    inductance_h: float,
    component_id: str,
) -> tuple[float, dict[str, float | str]]:
    result, built = evaluate_candidate_core_loss(
        material_id=core.material_name,
        material_name=core.material_name,
        frequency_hz=fs_hz,
        effective_volume_m3=core.effective_volume_m3,
        effective_area_m2=core.effective_area_m2,
        turns=turns,
        inductance_h=inductance_h,
        current_min_a=primary_valley_a,
        current_max_a=primary_peak_a,
        steinmetz_ranges=list(core.steinmetz_ranges) or None,
        proxy_coefficients=(None if core.steinmetz_ranges else {
            "density_reference_w_per_m3": 40_000.0,
            "reference_frequency_hz": 100_000.0,
            "reference_flux_t": 0.20,
            "frequency_exponent": 1.35,
            "flux_exponent": 2.4,
        }),
        source_role="flyback_coupled_inductor_core",
        source_component_id=component_id,
    )
    if result.core_loss_w is None:
        raise ValueError(f"Shared Flyback core-loss route unavailable: {result.validity_status.value}")
    if built.excitation is None:
        raise ValueError(f"Shared Flyback excitation unavailable: {built.status.value}")
    excitation = built.excitation
    return result.core_loss_w, {
        "core_loss_excitation_status": built.status.value,
        "core_loss_reconstruction_method": built.reconstruction_method,
        "core_loss_flux_peak_to_peak_t": excitation.flux_peak_to_peak_t,
        "core_loss_flux_ac_peak_t": excitation.flux_ac_peak_t,
        "core_loss_flux_dc_offset_t": excitation.flux_dc_offset_t,
        "core_loss_flux_absolute_peak_t": excitation.flux_absolute_peak_t,
        "core_loss_method": result.method_used,
        "core_loss_validity_status": result.validity_status.value,
        "core_loss_input_policy": "primary magnetizing current valley-to-peak; Bpp for loss and Babsolute for saturation",
    }


def _first_pass_thermal_resistance_k_per_w(total_volume_m3: float) -> float:
    volume_cm3 = max(total_volume_m3 * 1.0e6, 1.0e-9)
    return min(80.0, max(4.0, 18.0 / (volume_cm3 ** (1.0 / 3.0))))


def _parallel_count(
    current_rms_a: float,
    wire: FlybackCoupledInductorWire,
    current_density_limit_a_per_mm2: float,
) -> int:
    wire_area_mm2 = wire.copper_area_m2 * 1e6
    return max(1, math.ceil(current_rms_a / max(current_density_limit_a_per_mm2 * wire_area_mm2, 1e-12)))


def _flyback_metadata(candidate: TopologyCandidate) -> dict[str, object]:
    metadata = candidate.metadata.get("flyback") if isinstance(candidate.metadata, dict) else None
    if not isinstance(metadata, dict):
        raise ValueError("Flyback candidate metadata is missing.")
    return metadata


def _target_metadata(flyback: dict[str, object]) -> dict[str, object]:
    target = flyback.get("coupled_inductor_target")
    if not isinstance(target, dict):
        raise ValueError("Flyback coupled-inductor target metadata is missing.")
    return target


def _positive_float(mapping: dict[str, object], key: str) -> float:
    value = float(mapping[key])
    if value <= 0.0:
        raise ValueError(f"{key} must be positive.")
    return value


def _positive_float_or_default(mapping: dict[str, object], key: str, default: float) -> float:
    try:
        value = float(mapping.get(key, default))
    except (TypeError, ValueError):
        return default
    return value if value > 0.0 else default


def _nonnegative_float_or_default(mapping: dict[str, object], key: str, default: float) -> float:
    try:
        value = float(mapping.get(key, default))
    except (TypeError, ValueError):
        return default
    return value if value >= 0.0 else default


def _empty_candidate(sequence: int) -> FixedInductorDesignCandidate:
    return FixedInductorDesignCandidate(candidate_id=f"flyback-ci-{sequence:03d}")


def _backend_core_options(
    bundle: Any,
    *,
    material_limit: int | None = 16,
) -> tuple[FlybackCoupledInductorCore, ...]:
    cores = bundle.cores.sort_values(["Ae", "Aw"], ascending=False).head(16)
    materials = bundle.materials.sort_values("B_sat", ascending=False)
    if material_limit is not None and material_limit > 0:
        materials = materials.head(material_limit)
    options: list[FlybackCoupledInductorCore] = []
    for core in cores.itertuples():
        for material in materials.itertuples():
            options.append(
                FlybackCoupledInductorCore(
                    core_name=str(core.Index),
                    material_name=str(material.Index),
                    effective_area_m2=float(core.Ae),
                    window_area_m2=float(core.Aw),
                    magnetic_path_length_m=float(core.le),
                    effective_volume_m3=float(core.Ve),
                    mean_turn_length_m=float(core.mlt),
                    core_width_m=float(core.width),
                    core_height_m=float(core.height),
                    core_depth_m=float(core.depth),
                    steinmetz_ranges=tuple(material.steinmetz_ranges or ()),
                )
            )
    if not options:
        raise ValueError("Explicit magnetic backend supplied no Flyback-compatible core/material records.")
    return tuple(options)


def _backend_wire_options(bundle: Any) -> tuple[FlybackCoupledInductorWire, ...]:
    wires = bundle.wires.sort_values("bundle_copper_area", ascending=False).head(6)
    options = tuple(
        FlybackCoupledInductorWire(
            wire_name=str(row.Index),
            copper_area_m2=float(row.bundle_copper_area),
            resistance_ohm_per_m_25c=1.724e-8 / float(row.bundle_copper_area),
            wire_id=str(getattr(row, "stable_wire_id", row.Index)),
            source_wire_record=dict(getattr(row, "source_wire_record", {}) or {}),
            area_basis=str(getattr(row, "conducting_area_basis", "engine_bundle_copper_area")),
            strand_diameter_m=float(row.d_strand),
            strand_count=int(row.strands_per_bundle),
        )
        for row in wires.itertuples()
        if float(row.bundle_copper_area) > 0.0
    )
    if not options:
        raise ValueError("Explicit magnetic backend supplied no Flyback-compatible Litz records.")
    return options


def _default_core_options() -> tuple[FlybackCoupledInductorCore, ...]:
    mm2 = 1e-6
    cm3 = 1e-6
    return (
        FlybackCoupledInductorCore(
            core_name="PQ32/30",
            material_name="Ferrite first-pass 100 kHz",
            effective_area_m2=161.0 * mm2,
            window_area_m2=134.0 * mm2,
            magnetic_path_length_m=0.074,
            effective_volume_m3=11.9 * cm3,
            mean_turn_length_m=0.085,
            core_width_m=0.032,
            core_height_m=0.030,
            core_depth_m=0.024,
        ),
        FlybackCoupledInductorCore(
            core_name="ETD44",
            material_name="Ferrite first-pass 100 kHz",
            effective_area_m2=173.0 * mm2,
            window_area_m2=172.0 * mm2,
            magnetic_path_length_m=0.103,
            effective_volume_m3=17.8 * cm3,
            mean_turn_length_m=0.102,
            core_width_m=0.044,
            core_height_m=0.033,
            core_depth_m=0.035,
        ),
        FlybackCoupledInductorCore(
            core_name="ETD49",
            material_name="Ferrite first-pass 100 kHz",
            effective_area_m2=211.0 * mm2,
            window_area_m2=250.0 * mm2,
            magnetic_path_length_m=0.115,
            effective_volume_m3=24.2 * cm3,
            mean_turn_length_m=0.118,
            core_width_m=0.049,
            core_height_m=0.038,
            core_depth_m=0.039,
        ),
        FlybackCoupledInductorCore(
            core_name="E55/28/21",
            material_name="Ferrite first-pass 100 kHz",
            effective_area_m2=354.0 * mm2,
            window_area_m2=315.0 * mm2,
            magnetic_path_length_m=0.124,
            effective_volume_m3=43.9 * cm3,
            mean_turn_length_m=0.135,
            core_width_m=0.055,
            core_height_m=0.044,
            core_depth_m=0.042,
        ),
    )


def _default_wire_options() -> tuple[FlybackCoupledInductorWire, ...]:
    mm2 = 1e-6
    return (
        _default_wire("litz_60x0.10", 0.471 * mm2, 0.10e-3, 60),
        _default_wire("litz_100x0.10", 0.785 * mm2, 0.10e-3, 100),
        _default_wire("litz_160x0.10", 1.257 * mm2, 0.10e-3, 160),
    )


def _default_wire(name: str, area_m2: float, strand_diameter_m: float, strand_count: int) -> FlybackCoupledInductorWire:
    return FlybackCoupledInductorWire(
        wire_name=name,
        copper_area_m2=area_m2,
        resistance_ohm_per_m_25c=1.724e-8 / area_m2,
        wire_id=f"static:{name}",
        source_wire_record={"source_kind": "flyback_first_pass_static_wire", "wire_name": name},
        area_basis="declared_bundle_copper_area",
        strand_diameter_m=strand_diameter_m,
        strand_count=strand_count,
    )


def _wire_source_record(wire: FlybackCoupledInductorWire) -> Mapping[str, Any]:
    return wire.source_wire_record or {
        "source_kind": "caller_supplied_flyback_wire",
        "wire_id": wire.wire_id or wire.wire_name,
        "wire_name": wire.wire_name,
    }


def _wire_strand_diameter(wire: FlybackCoupledInductorWire) -> float:
    if wire.strand_diameter_m is not None and wire.strand_diameter_m > 0.0:
        return wire.strand_diameter_m
    return 2.0 * math.sqrt(wire.copper_area_m2 / (math.pi * max(wire.strand_count, 1)))
