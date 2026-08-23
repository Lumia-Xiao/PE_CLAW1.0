"""First-pass transformer and output-inductor search for the planned PSFB topology."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from ....models.inductor import FixedInductorDesignCandidate
from ....engines.magnetics.core_loss_role_adapter import evaluate_candidate_core_loss
from ...base.candidate import TopologyCandidate


_MU0_H_PER_M = 4.0 * math.pi * 1e-7


@dataclass(frozen=True)
class PSFBMagneticCore:
    """Packaged first-pass core option used by PSFB transformer/inductor search."""

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


@dataclass(frozen=True)
class PSFBMagneticWire:
    """Copper option used by the first-pass PSFB magnetic search."""

    wire_name: str
    copper_area_m2: float
    resistance_ohm_per_m_25c: float


@dataclass(frozen=True)
class PSFBMagneticSearchResult:
    """Structured first-pass PSFB transformer/output-inductor search result."""

    design_requirements: dict[str, float | str | bool | None]
    evaluated_count: int = 0
    feasible_candidates: list[FixedInductorDesignCandidate] = field(default_factory=list)
    chosen_candidates: list[FixedInductorDesignCandidate] = field(default_factory=list)
    recommended_candidate: FixedInductorDesignCandidate | None = None
    output_inductor_candidate: FixedInductorDesignCandidate | None = None
    output_inductor_feasible_count: int = 0
    rejection_counts: dict[str, int] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def generate_psfb_transformer_output_inductor_candidates(
    candidate: TopologyCandidate,
    *,
    transformer_fill_limit: float = 0.45,
    output_inductor_b_limit_t: float = 0.22,
    output_inductor_fill_limit: float = 0.50,
    current_density_limit_a_per_mm2: float = 6.0,
    insulation_window_reserve_ratio: float = 0.20,
) -> PSFBMagneticSearchResult:
    """Search deterministic first-pass PSFB transformer plus output-inductor candidates."""

    psfb = _psfb_metadata(candidate)
    fs_hz = _positive_float_from_mapping(psfb, "fs_hz", candidate.fs_hz)
    turns_ratio_np_ns = _positive_float_from_mapping(psfb, "turns_ratio_np_ns")
    b_limit_t = _positive_float_from_mapping(psfb, "target_bmax_t")
    max_command_duty = _positive_float_from_mapping(psfb, "max_command_duty")
    primary_rms_a = _positive_float_from_mapping(psfb, "primary_rms_current_a")
    primary_peak_a = _positive_float_from_mapping(psfb, "primary_peak_current_a")
    secondary_rms_a = max(
        _positive_float_from_mapping(psfb, "rectifier_rms_current_a"),
        candidate.iout * math.sqrt(max(float(psfb.get("command_duty_nom", candidate.duty_nom)), 0.05)),
    )
    secondary_peak_a = candidate.il_peak
    output_inductor_rms_a = math.sqrt(candidate.iout * candidate.iout + candidate.delta_il * candidate.delta_il / 12.0)
    output_inductor_peak_a = candidate.il_peak

    output_inductor_candidates, output_evaluated, output_rejections = _generate_output_inductor_candidates(
        candidate,
        b_limit_t=output_inductor_b_limit_t,
        fill_limit=output_inductor_fill_limit,
        current_density_limit_a_per_mm2=current_density_limit_a_per_mm2,
    )
    output_selected = output_inductor_candidates[0] if output_inductor_candidates else None

    design_requirements = {
        "topology_id": candidate.topology_id,
        "design_type": "psfb_transformer_and_output_inductor_first_pass",
        "transformer_design_type": "isolated_psfb_transformer",
        "output_inductor_design_type": "psfb_output_filter_inductor",
        "vin_max_v": candidate.vin_max,
        "vout_v": candidate.vout_target,
        "pout_w": candidate.pout_target,
        "fs_hz": fs_hz,
        "turns_ratio_np_ns_target": turns_ratio_np_ns,
        "max_command_duty": max_command_duty,
        "b_limit_t": b_limit_t,
        "transformer_fill_limit": transformer_fill_limit,
        "primary_rms_current_a": primary_rms_a,
        "primary_peak_current_a": primary_peak_a,
        "secondary_rms_current_a": secondary_rms_a,
        "secondary_peak_current_a": secondary_peak_a,
        "magnetizing_inductance_h": float(psfb.get("magnetizing_inductance_h", 0.0)),
        "leakage_inductance_target_h": float(psfb.get("leakage_inductance_target_h", 0.0)),
        "output_inductor_inductance_h": candidate.inductance_h,
        "output_inductor_current_rms_a": output_inductor_rms_a,
        "output_inductor_current_peak_a": output_inductor_peak_a,
        "output_inductor_delta_i_pp_a": candidate.delta_il,
        "output_inductor_b_limit_t": output_inductor_b_limit_t,
        "output_inductor_fill_limit": output_inductor_fill_limit,
        "throughput_power_w": candidate.pout_target,
        "mode": candidate.mode_capable,
        "current_density_limit_a_per_mm2": current_density_limit_a_per_mm2,
        "insulation_window_reserve_ratio": insulation_window_reserve_ratio,
        "output_inductor_evaluated_count": output_evaluated,
        "output_inductor_feasible_count": len(output_inductor_candidates),
    }

    feasible: list[FixedInductorDesignCandidate] = []
    rejection_counts = dict(output_rejections)
    evaluated_count = output_evaluated
    if output_selected is not None:
        for core in _default_core_options():
            for primary_wire in _default_wire_options():
                for secondary_wire in _default_wire_options():
                    evaluated_count += 1
                    row, rejection_reason = _build_transformer_candidate(
                        core=core,
                        primary_wire=primary_wire,
                        secondary_wire=secondary_wire,
                        candidate=candidate,
                        psfb=psfb,
                        fs_hz=fs_hz,
                        turns_ratio_np_ns=turns_ratio_np_ns,
                        b_limit_t=b_limit_t,
                        max_command_duty=max_command_duty,
                        primary_rms_a=primary_rms_a,
                        primary_peak_a=primary_peak_a,
                        secondary_rms_a=secondary_rms_a,
                        secondary_peak_a=secondary_peak_a,
                        output_inductor=output_selected,
                        fill_limit=transformer_fill_limit,
                        current_density_limit_a_per_mm2=current_density_limit_a_per_mm2,
                        insulation_window_reserve_ratio=insulation_window_reserve_ratio,
                        sequence=evaluated_count,
                    )
                    if rejection_reason:
                        rejection_counts[rejection_reason] = rejection_counts.get(rejection_reason, 0) + 1
                        continue
                    feasible.append(row)

    feasible.sort(key=_candidate_score)
    chosen = _choose_representative_candidates(feasible)
    recommended = chosen[0] if chosen else None
    notes = [
        "PSFB magnetic search uses a deterministic first-pass transformer and output-inductor table.",
        "Transformer turns use Np >= Vin_max * Dcmd_max / (4 * Bmax * Ae * fsw), with Ns rounded from Np/Ns.",
        "Output inductor turns use N >= Lout * Ipk / (Blimit * Ae) and a first-pass gapped-core estimate.",
        "PSFB magnetic readback preserves duty loss and ZVS evidence from electrical synthesis; detailed leakage, proximity, winding construction, creepage, clearance, and manufacturability remain follow-up work.",
    ]
    warnings: list[str] = []
    if output_selected is None:
        warnings.append("No first-pass PSFB output-inductor candidate satisfied Bpeak, gap, turns, and fill constraints.")
    if recommended is None:
        warnings.append("No first-pass PSFB transformer candidate satisfied Bpeak, turns-ratio, and fill constraints.")

    return PSFBMagneticSearchResult(
        design_requirements=design_requirements,
        evaluated_count=evaluated_count,
        feasible_candidates=feasible,
        chosen_candidates=chosen,
        recommended_candidate=recommended,
        output_inductor_candidate=output_selected,
        output_inductor_feasible_count=len(output_inductor_candidates),
        rejection_counts=rejection_counts,
        notes=notes,
        warnings=warnings,
    )


def _build_transformer_candidate(
    *,
    core: PSFBMagneticCore,
    primary_wire: PSFBMagneticWire,
    secondary_wire: PSFBMagneticWire,
    candidate: TopologyCandidate,
    psfb: dict[str, object],
    fs_hz: float,
    turns_ratio_np_ns: float,
    b_limit_t: float,
    max_command_duty: float,
    primary_rms_a: float,
    primary_peak_a: float,
    secondary_rms_a: float,
    secondary_peak_a: float,
    output_inductor: FixedInductorDesignCandidate,
    fill_limit: float,
    current_density_limit_a_per_mm2: float,
    insulation_window_reserve_ratio: float,
    sequence: int,
) -> tuple[FixedInductorDesignCandidate, str]:
    np_turns = max(
        1,
        math.ceil(
            candidate.vin_max
            * max_command_duty
            / max(4.0 * b_limit_t * core.effective_area_m2 * fs_hz, 1e-18)
        ),
    )
    ns_turns = max(1, round(np_turns / max(turns_ratio_np_ns, 1e-12)))
    if np_turns > 160 or ns_turns > 160:
        return _empty_candidate("psfb-tx", sequence), "transformer_turns_exceed_first_pass_limit"

    actual_ratio = np_turns / max(ns_turns, 1)
    ratio_error_percent = abs(actual_ratio - turns_ratio_np_ns) / max(turns_ratio_np_ns, 1e-12) * 100.0
    if ratio_error_percent > 5.0:
        return _empty_candidate("psfb-tx", sequence), "transformer_turns_ratio_error_exceeds_limit"

    b_peak_t = candidate.vin_max * max_command_duty / max(4.0 * np_turns * core.effective_area_m2 * fs_hz, 1e-18)
    if b_peak_t > b_limit_t:
        return _empty_candidate("psfb-tx", sequence), "transformer_bpeak_exceeds_limit"

    primary_parallel = _parallel_count(primary_rms_a, primary_wire, current_density_limit_a_per_mm2)
    secondary_parallel = _parallel_count(secondary_rms_a, secondary_wire, current_density_limit_a_per_mm2)
    primary_copper_area_m2 = primary_wire.copper_area_m2 * primary_parallel
    secondary_copper_area_m2 = secondary_wire.copper_area_m2 * secondary_parallel
    winding_fill_area_m2 = 1.65 * (
        np_turns * primary_copper_area_m2 + ns_turns * secondary_copper_area_m2
    )
    primary_fill_area_m2 = 1.65 * np_turns * primary_copper_area_m2
    secondary_fill_area_m2 = 1.65 * ns_turns * secondary_copper_area_m2
    insulation_reserved_area_m2 = insulation_window_reserve_ratio * core.window_area_m2
    fill_factor = (winding_fill_area_m2 + insulation_reserved_area_m2) / max(core.window_area_m2, 1e-18)
    if fill_factor > fill_limit:
        return _empty_candidate("psfb-tx", sequence), "transformer_fill_factor_exceeds_limit"

    primary_resistance_ohm = (
        primary_wire.resistance_ohm_per_m_25c * core.mean_turn_length_m * np_turns / primary_parallel
    )
    secondary_resistance_ohm = (
        secondary_wire.resistance_ohm_per_m_25c * core.mean_turn_length_m * ns_turns / secondary_parallel
    )
    temperature_resistance_factor = 1.25
    copper_loss_w = temperature_resistance_factor * (
        primary_rms_a * primary_rms_a * primary_resistance_ohm
        + secondary_rms_a * secondary_rms_a * secondary_resistance_ohm
    )
    lm_h = float(psfb.get("magnetizing_inductance_h", 0.0))
    core_loss_w = _shared_core_loss_w(core, fs_hz=fs_hz, b_peak_t=b_peak_t, turns=np_turns, inductance_h=lm_h, component_id=f"psfb-tx-{sequence:03d}", role="psfb_transformer_core")
    transformer_loss_w = copper_loss_w + core_loss_w
    output_copper_loss_w = output_inductor.reference_copper_loss_w or 0.0
    output_core_loss_w = output_inductor.reference_core_loss_w or 0.0
    output_loss_w = output_inductor.reference_total_loss_w or (output_copper_loss_w + output_core_loss_w)
    total_copper_loss_w = copper_loss_w + output_copper_loss_w
    total_core_loss_w = core_loss_w + output_core_loss_w
    total_loss_w = transformer_loss_w + output_loss_w
    winding_volume_m3 = 1.65 * core.mean_turn_length_m * (
        np_turns * primary_copper_area_m2 + ns_turns * secondary_copper_area_m2
    )
    total_volume_m3 = core.effective_volume_m3 + winding_volume_m3 + (output_inductor.total_volume_m3 or 0.0)
    magnetizing_current_at_b_limit_a = (
        b_limit_t * np_turns * core.effective_area_m2 / max(lm_h, 1e-18)
        if lm_h > 0.0
        else None
    )

    output_metadata = output_inductor.metadata if isinstance(output_inductor.metadata, dict) else {}
    metadata = {
        "component_role": "psfb_transformer",
        "primary_turns": np_turns,
        "secondary_turns": ns_turns,
        "turns_ratio_np_ns_target": turns_ratio_np_ns,
        "turns_ratio_np_ns_actual": actual_ratio,
        "turns_ratio_error_percent": ratio_error_percent,
        "b_limit_t": b_limit_t,
        "fill_limit": fill_limit,
        "primary_wire_name": primary_wire.wire_name,
        "secondary_wire_name": secondary_wire.wire_name,
        "primary_parallel_bundles": primary_parallel,
        "secondary_parallel_bundles": secondary_parallel,
        "primary_current_density_a_per_mm2": primary_rms_a / max(primary_copper_area_m2 * 1e6, 1e-12),
        "secondary_current_density_a_per_mm2": secondary_rms_a / max(secondary_copper_area_m2 * 1e6, 1e-12),
        "primary_rms_current_a": primary_rms_a,
        "primary_peak_current_a": primary_peak_a,
        "secondary_rms_current_a": secondary_rms_a,
        "secondary_peak_current_a": secondary_peak_a,
        "magnetizing_inductance_h": lm_h,
        "inductance_role": "transformer_magnetizing_inductance",
        "magnetizing_current_at_b_limit_a": magnetizing_current_at_b_limit_a,
        "magnetizing_current_limit_basis": "Blimit * Np * Ae / Lm",
        "leakage_inductance_target_h": float(psfb.get("leakage_inductance_target_h", 0.0)),
        "max_command_duty": max_command_duty,
        "command_duty_nom": float(psfb.get("command_duty_nom", candidate.duty_nom)),
        "duty_loss_nom": float(psfb.get("duty_loss_nom", 0.0)),
        "zvs_energy_margin": _optional_float_from_mapping(
            psfb.get("zvs") if isinstance(psfb.get("zvs"), dict) else {},
            "energy_margin",
        ),
        "core_width_m": core.core_width_m,
        "core_height_m": core.core_height_m,
        "core_depth_m": core.core_depth_m,
        "core_effective_area_m2": core.effective_area_m2,
        "core_window_area_m2": core.window_area_m2,
        "core_magnetic_path_length_m": core.magnetic_path_length_m,
        "primary_fill_area_m2": primary_fill_area_m2,
        "secondary_fill_area_m2": secondary_fill_area_m2,
        "insulation_reserved_area_m2": insulation_reserved_area_m2,
        "total_fill_area_m2": primary_fill_area_m2 + secondary_fill_area_m2 + insulation_reserved_area_m2,
        "transformer_copper_loss_w": copper_loss_w,
        "transformer_core_loss_w": core_loss_w,
        "transformer_total_loss_w": transformer_loss_w,
        "output_inductor_selected_design_id": output_inductor.candidate_id,
        "output_inductor_core_name": output_inductor.core_name,
        "output_inductor_wire_name": output_inductor.wire_name,
        "output_inductor_turns": output_inductor.turns,
        "output_inductor_gap_m": output_inductor.gap_m,
        "output_inductor_inductance_h": output_inductor.inductance_h,
        "output_inductor_core_effective_area_m2": output_metadata.get("core_effective_area_m2"),
        "output_inductor_core_effective_volume_m3": output_inductor.core_volume_m3,
        "output_inductor_b_peak_t": output_inductor.b_peak_design_t,
        "output_inductor_b_limit_t": output_metadata.get("b_limit_t"),
        "output_inductor_fill_factor": output_inductor.fill_factor,
        "output_inductor_fill_limit": output_metadata.get("fill_limit"),
        "output_inductor_copper_loss_w": output_copper_loss_w,
        "output_inductor_core_loss_w": output_core_loss_w,
        "output_inductor_total_loss_w": output_loss_w,
        "psfb_magnetic_copper_loss_w": total_copper_loss_w,
        "psfb_magnetic_core_loss_w": total_core_loss_w,
        "psfb_magnetic_total_loss_w": total_loss_w,
        "search_basis": "first_pass_psfb_transformer_and_output_filter_inductor",
        "family": "psfb",
    }
    return (
        FixedInductorDesignCandidate(
            candidate_id=f"psfb-tx-{sequence:03d}",
            assembly_type="isolated_transformer_plus_output_inductor",
            stack_count=1,
            base_core_name=core.core_name,
            core_name=core.core_name,
            material_name=core.material_name,
            wire_name=f"{primary_wire.wire_name} / {secondary_wire.wire_name}",
            turns=np_turns,
            parallel_bundles=primary_parallel,
            gap_m=None,
            inductance_h=lm_h,
            rdc_25c_ohm=primary_resistance_ohm,
            fill_factor=fill_factor,
            core_volume_m3=core.effective_volume_m3,
            winding_volume_m3=winding_volume_m3,
            total_volume_m3=total_volume_m3,
            b_peak_design_t=b_peak_t,
            saturation_current_a=None,
            reference_copper_loss_w=total_copper_loss_w,
            reference_core_loss_w=total_core_loss_w,
            reference_total_loss_w=total_loss_w,
            notes=[
                "First-pass PSFB isolated transformer candidate.",
                "Candidate metadata includes the paired first-pass output-inductor recommendation.",
            ],
            metadata=metadata,
        ),
        "",
    )


def _generate_output_inductor_candidates(
    candidate: TopologyCandidate,
    *,
    b_limit_t: float,
    fill_limit: float,
    current_density_limit_a_per_mm2: float,
) -> tuple[list[FixedInductorDesignCandidate], int, dict[str, int]]:
    feasible: list[FixedInductorDesignCandidate] = []
    rejection_counts: dict[str, int] = {}
    evaluated_count = 0
    for core in _default_core_options():
        for wire in _default_wire_options():
            evaluated_count += 1
            row, rejection_reason = _build_output_inductor_candidate(
                core=core,
                wire=wire,
                candidate=candidate,
                b_limit_t=b_limit_t,
                fill_limit=fill_limit,
                current_density_limit_a_per_mm2=current_density_limit_a_per_mm2,
                sequence=evaluated_count,
            )
            if rejection_reason:
                rejection_counts[rejection_reason] = rejection_counts.get(rejection_reason, 0) + 1
                continue
            feasible.append(row)
    feasible.sort(key=_candidate_score)
    return feasible, evaluated_count, rejection_counts


def _build_output_inductor_candidate(
    *,
    core: PSFBMagneticCore,
    wire: PSFBMagneticWire,
    candidate: TopologyCandidate,
    b_limit_t: float,
    fill_limit: float,
    current_density_limit_a_per_mm2: float,
    sequence: int,
) -> tuple[FixedInductorDesignCandidate, str]:
    inductance_h = candidate.inductance_h
    peak_current_a = candidate.il_peak
    rms_current_a = math.sqrt(candidate.iout * candidate.iout + candidate.delta_il * candidate.delta_il / 12.0)
    turns = max(1, math.ceil(inductance_h * peak_current_a / max(b_limit_t * core.effective_area_m2, 1e-18)))
    if turns > 220:
        return _empty_candidate("psfb-lout", sequence), "output_inductor_turns_exceed_first_pass_limit"

    gap_m = _MU0_H_PER_M * turns * turns * core.effective_area_m2 / max(inductance_h, 1e-18)
    if gap_m < 0.05e-3:
        return _empty_candidate("psfb-lout", sequence), "output_inductor_gap_below_practical_limit"
    if gap_m > 7.0e-3:
        return _empty_candidate("psfb-lout", sequence), "output_inductor_gap_exceeds_first_pass_limit"

    b_peak_t = inductance_h * peak_current_a / max(turns * core.effective_area_m2, 1e-18)
    if b_peak_t > b_limit_t:
        return _empty_candidate("psfb-lout", sequence), "output_inductor_bpeak_exceeds_limit"

    parallel = _parallel_count(rms_current_a, wire, current_density_limit_a_per_mm2)
    copper_area_m2 = wire.copper_area_m2 * parallel
    insulation_reserved_area_m2 = 0.10 * core.window_area_m2
    winding_fill_area_m2 = 1.45 * turns * copper_area_m2
    fill_factor = (winding_fill_area_m2 + insulation_reserved_area_m2) / max(core.window_area_m2, 1e-18)
    if fill_factor > fill_limit:
        return _empty_candidate("psfb-lout", sequence), "output_inductor_fill_factor_exceeds_limit"

    resistance_ohm = wire.resistance_ohm_per_m_25c * core.mean_turn_length_m * turns / parallel
    copper_loss_w = 1.25 * rms_current_a * rms_current_a * resistance_ohm
    core_loss_w = _shared_core_loss_w(core, fs_hz=candidate.fs_hz, b_peak_t=b_peak_t, turns=turns, inductance_h=inductance_h, component_id=f"psfb-lout-{sequence:03d}", role="psfb_output_inductor_core")
    total_loss_w = copper_loss_w + core_loss_w
    winding_volume_m3 = 1.45 * core.mean_turn_length_m * turns * copper_area_m2
    total_volume_m3 = core.effective_volume_m3 + winding_volume_m3
    metadata = {
        "component_role": "psfb_output_inductor",
        "b_limit_t": b_limit_t,
        "fill_limit": fill_limit,
        "current_density_limit_a_per_mm2": current_density_limit_a_per_mm2,
        "current_density_a_per_mm2": rms_current_a / max(copper_area_m2 * 1e6, 1e-12),
        "rms_current_a": rms_current_a,
        "peak_current_a": peak_current_a,
        "delta_i_pp_a": candidate.delta_il,
        "core_effective_area_m2": core.effective_area_m2,
        "core_window_area_m2": core.window_area_m2,
        "core_width_m": core.core_width_m,
        "core_height_m": core.core_height_m,
        "core_depth_m": core.core_depth_m,
        "search_basis": "first_pass_psfb_output_filter_inductor",
        "family": "psfb",
    }
    return (
        FixedInductorDesignCandidate(
            candidate_id=f"psfb-lout-{sequence:03d}",
            assembly_type="gapped_output_inductor",
            stack_count=1,
            base_core_name=core.core_name,
            core_name=core.core_name,
            material_name=core.material_name,
            wire_name=wire.wire_name,
            turns=turns,
            parallel_bundles=parallel,
            gap_m=gap_m,
            inductance_h=inductance_h,
            rdc_25c_ohm=resistance_ohm,
            fill_factor=fill_factor,
            core_volume_m3=core.effective_volume_m3,
            winding_volume_m3=winding_volume_m3,
            total_volume_m3=total_volume_m3,
            b_peak_design_t=b_peak_t,
            saturation_current_a=b_limit_t * turns * core.effective_area_m2 / max(inductance_h, 1e-18),
            reference_copper_loss_w=copper_loss_w,
            reference_core_loss_w=core_loss_w,
            reference_total_loss_w=total_loss_w,
            notes=["First-pass PSFB output-filter inductor candidate."],
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
    return (loss_w + 0.012 * volume_cm3, volume_cm3, candidate.candidate_id)


def _shared_core_loss_w(
    core: PSFBMagneticCore,
    *, fs_hz: float,
    b_peak_t: float,
    turns: int,
    inductance_h: float,
    component_id: str,
    role: str,
) -> float:
    result, _ = evaluate_candidate_core_loss(
        material_id=core.material_name,
        material_name=core.material_name,
        frequency_hz=fs_hz,
        effective_volume_m3=core.effective_volume_m3,
        effective_area_m2=core.effective_area_m2,
        turns=turns,
        inductance_h=inductance_h,
        b_peak_t=b_peak_t,
        proxy_coefficients={
            "density_reference_w_per_m3": 45_000.0,
            "reference_frequency_hz": 100_000.0,
            "reference_flux_t": 0.18,
            "frequency_exponent": 1.35,
            "flux_exponent": 2.4,
        },
        source_role=role,
        source_component_id=component_id,
    )
    if result.core_loss_w is None:
        raise ValueError(f"Shared PSFB core-loss route unavailable: {result.validity_status.value}")
    return result.core_loss_w


def _parallel_count(
    current_rms_a: float,
    wire: PSFBMagneticWire,
    current_density_limit_a_per_mm2: float,
) -> int:
    wire_area_mm2 = wire.copper_area_m2 * 1e6
    return max(1, math.ceil(current_rms_a / max(current_density_limit_a_per_mm2 * wire_area_mm2, 1e-12)))


def _psfb_metadata(candidate: TopologyCandidate) -> dict[str, object]:
    metadata = candidate.metadata.get("psfb") if isinstance(candidate.metadata, dict) else None
    if not isinstance(metadata, dict):
        raise ValueError("PSFB candidate metadata is missing.")
    return metadata


def _positive_float_from_mapping(
    mapping: dict[str, object],
    key: str,
    default: float | None = None,
) -> float:
    value = mapping.get(key, default)
    if value is None:
        raise ValueError(f"{key} is required.")
    number = float(value)
    if number <= 0.0:
        raise ValueError(f"{key} must be positive.")
    return number


def _optional_float_from_mapping(
    mapping: dict[str, object],
    key: str,
    default: float | None = None,
) -> float | None:
    value = mapping.get(key, default)
    if value is None:
        return None
    return float(value)


def _empty_candidate(prefix: str, sequence: int) -> FixedInductorDesignCandidate:
    return FixedInductorDesignCandidate(candidate_id=f"{prefix}-{sequence:03d}")


def _default_core_options() -> tuple[PSFBMagneticCore, ...]:
    mm2 = 1e-6
    cm3 = 1e-6
    return (
        PSFBMagneticCore(
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
        PSFBMagneticCore(
            core_name="ETD59",
            material_name="Ferrite first-pass 100 kHz",
            effective_area_m2=368.0 * mm2,
            window_area_m2=436.0 * mm2,
            magnetic_path_length_m=0.136,
            effective_volume_m3=50.0 * cm3,
            mean_turn_length_m=0.152,
            core_width_m=0.059,
            core_height_m=0.045,
            core_depth_m=0.045,
        ),
        PSFBMagneticCore(
            core_name="E65/32/27",
            material_name="Ferrite first-pass 100 kHz",
            effective_area_m2=540.0 * mm2,
            window_area_m2=530.0 * mm2,
            magnetic_path_length_m=0.147,
            effective_volume_m3=79.4 * cm3,
            mean_turn_length_m=0.166,
            core_width_m=0.065,
            core_height_m=0.053,
            core_depth_m=0.052,
        ),
        PSFBMagneticCore(
            core_name="E70/33/32",
            material_name="Ferrite first-pass 100 kHz",
            effective_area_m2=683.0 * mm2,
            window_area_m2=610.0 * mm2,
            magnetic_path_length_m=0.160,
            effective_volume_m3=109.0 * cm3,
            mean_turn_length_m=0.182,
            core_width_m=0.070,
            core_height_m=0.058,
            core_depth_m=0.058,
        ),
    )


def _default_wire_options() -> tuple[PSFBMagneticWire, ...]:
    mm2 = 1e-6
    return (
        PSFBMagneticWire("litz_100x0.10", 0.785 * mm2, 0.0220),
        PSFBMagneticWire("litz_160x0.10", 1.257 * mm2, 0.0137),
        PSFBMagneticWire("litz_250x0.10", 1.963 * mm2, 0.0088),
        PSFBMagneticWire("foil_equiv_4mm2", 4.000 * mm2, 0.0043),
    )
