"""First-pass selector for AC-DC low-frequency Sendust toroid reactors."""

from __future__ import annotations

import math
import csv
from collections import Counter
from dataclasses import replace
from pathlib import Path

from ...libraries.magnetics.sendust_steinmetz import (
    estimate_sendust_core_loss_mw_per_cm3,
    get_sendust_steinmetz_material,
)
from ...libraries.magnetics.sendust_toroids import SendustToroidCore, list_sendust_toroid_cores
from ...models.ac_dc_reactor import (
    AcDcReactorCandidate,
    AcDcReactorDesignRequest,
    AcDcReactorSelectionResult,
    AcDcReactorSelectionSettings,
)

_COPPER_RESISTIVITY_25C_OHM_M = 1.724e-8


def select_ac_dc_sendust_reactor(
    request: AcDcReactorDesignRequest,
    *,
    settings: AcDcReactorSelectionSettings | None = None,
    cores: tuple[SendustToroidCore, ...] | None = None,
    output_dir: Path | str | None = None,
) -> AcDcReactorSelectionResult:
    """Select a first-pass Sendust toroid reactor for an AC-DC DC-link choke."""

    resolved_settings = settings or AcDcReactorSelectionSettings()
    _validate_request(request)
    _validate_settings(resolved_settings)

    core_list = cores if cores is not None else list_sendust_toroid_cores()
    rejection_counts: Counter[str] = Counter()
    feasible: list[AcDcReactorCandidate] = []
    rejected: list[AcDcReactorCandidate] = []

    for core in core_list:
        for parallel_core_count in range(1, resolved_settings.max_parallel_core_count + 1):
            candidate = _build_candidate(request, core, resolved_settings, parallel_core_count=parallel_core_count)
            rejection_reason = _first_rejection_reason(candidate, resolved_settings)
            if rejection_reason:
                rejection_counts[rejection_reason] += 1
                rejected.append(replace(candidate, rejection_reason=rejection_reason))
                continue
            feasible.append(candidate)

    ranked = _rank_candidates(feasible, resolved_settings)
    selected = ranked[0] if ranked else None
    selected_loss_power_ratio = (
        (selected.total_loss_w or 0.0) / request.throughput_power_w
        if selected is not None and selected.total_loss_w is not None
        else None
    )
    notes = [
        "AC-DC reactor selector uses packaged Micrometals MS Sendust toroid data.",
        "Turns use N = ceil(sqrt(L_required / (AL * dc_bias_derating))).",
        "Core loss uses the fixed Sendust Steinmetz table with ripple-frequency deltaB.",
        "Copper loss uses an equivalent copper area sized from target window utilization with current-density as a minimum.",
        "Parallel-core candidates assume ideal current sharing across identical toroid reactors.",
        "DC bias is first-pass derated by a fixed AL factor, not by vendor bias curves.",
    ]
    warnings = []
    if selected is None:
        warnings.append("No feasible Sendust toroid reactor candidate passed first-pass hard filters.")
    elif (
        selected_loss_power_ratio is not None
        and selected_loss_power_ratio > resolved_settings.loss_warning_power_ratio
    ):
        warnings.append(
            "Selected AC-DC Sendust reactor loss is high relative to throughput "
            f"({100.0 * selected_loss_power_ratio:.3g}% > {100.0 * resolved_settings.loss_warning_power_ratio:.3g}% warning threshold); "
            "review ripple target, multi-core options, and winding strategy."
        )

    artifact_paths: list[str] = []
    feasible_csv_path = ""
    top_candidates_csv_path = ""
    if output_dir is not None:
        artifact_result = export_ac_dc_reactor_selection_artifacts(
            feasible_candidates=ranked,
            top_candidates=ranked[: resolved_settings.top_candidate_count],
            rejected_candidates=rejected,
            output_dir=Path(output_dir),
        )
        artifact_paths = artifact_result["artifact_paths"]
        feasible_csv_path = artifact_result["feasible_csv_path"]
        top_candidates_csv_path = artifact_result["top_candidates_csv_path"]
        rejected_csv_path = artifact_result["rejected_csv_path"]
        if artifact_paths:
            notes.append(f"AC-DC reactor selection artifacts saved under {Path(artifact_paths[0]).parent}.")

    return AcDcReactorSelectionResult(
        request=request,
        settings=resolved_settings,
        selected_candidate=selected,
        top_candidates=ranked[: resolved_settings.top_candidate_count],
        feasible_candidates=ranked,
        rejected_candidates=rejected,
        evaluated_count=len(core_list) * resolved_settings.max_parallel_core_count,
        feasible_count=len(ranked),
        rejection_counts=dict(sorted(rejection_counts.items())),
        artifact_paths=artifact_paths,
        feasible_csv_path=feasible_csv_path,
        top_candidates_csv_path=top_candidates_csv_path,
        rejected_csv_path=rejected_csv_path if output_dir is not None else "",
        selected_loss_power_ratio=selected_loss_power_ratio,
        notes=notes,
        warnings=warnings,
    )


def export_ac_dc_reactor_selection_artifacts(
    *,
    feasible_candidates: list[AcDcReactorCandidate],
    top_candidates: list[AcDcReactorCandidate],
    rejected_candidates: list[AcDcReactorCandidate],
    output_dir: Path,
) -> dict[str, object]:
    """Write AC-DC reactor selection CSV artifacts."""

    output_dir.mkdir(parents=True, exist_ok=True)
    feasible_csv_path = output_dir / "feasible_candidates.csv"
    top_candidates_csv_path = output_dir / "top_candidates.csv"
    rejected_csv_path = output_dir / "rejected_candidates.csv"
    _write_candidates_csv(feasible_csv_path, feasible_candidates)
    _write_candidates_csv(top_candidates_csv_path, top_candidates)
    _write_candidates_csv(rejected_csv_path, rejected_candidates)
    return {
        "artifact_paths": [str(feasible_csv_path), str(top_candidates_csv_path), str(rejected_csv_path)],
        "feasible_csv_path": str(feasible_csv_path),
        "top_candidates_csv_path": str(top_candidates_csv_path),
        "rejected_csv_path": str(rejected_csv_path),
    }


def _build_candidate(
    request: AcDcReactorDesignRequest,
    core: SendustToroidCore,
    settings: AcDcReactorSelectionSettings,
    *,
    parallel_core_count: int,
) -> AcDcReactorCandidate:
    material_id = _material_id_from_permeability(core.relative_permeability)
    material = get_sendust_steinmetz_material(material_id)
    derated_al_h = core.al_h_per_turn2 * settings.al_dc_derating_factor
    per_core_required_inductance_h = request.required_inductance_h * parallel_core_count
    turns = max(1, math.ceil(math.sqrt(per_core_required_inductance_h / derated_al_h)))
    per_core_inductance_h = core.al_h_per_turn2 * turns * turns
    per_core_effective_inductance_h = per_core_inductance_h * settings.al_dc_derating_factor
    inductance_h = per_core_inductance_h / parallel_core_count
    effective_inductance_h = per_core_effective_inductance_h / parallel_core_count
    per_core_i_rms_a = request.i_rms_a / parallel_core_count
    per_core_idc_a = request.idc_a / parallel_core_count
    per_core_i_peak_a = request.i_peak_a / parallel_core_count
    per_core_delta_i_pp_a = request.delta_i_pp_a / parallel_core_count
    minimum_copper_area_mm2 = per_core_i_rms_a / settings.target_current_density_a_per_mm2
    target_window_copper_area_mm2 = (
        settings.target_window_utilization
        * core.window_area_mm2
        / max(turns * settings.winding_pack_factor, 1e-12)
    )
    max_copper_area_mm2 = (
        settings.max_fill_factor
        * core.window_area_mm2
        / max(turns * settings.winding_pack_factor, 1e-12)
    )
    target_copper_area_mm2 = min(target_window_copper_area_mm2, max_copper_area_mm2)
    copper_area_mm2 = max(minimum_copper_area_mm2, target_copper_area_mm2)
    copper_area_m2 = copper_area_mm2 * 1e-6
    actual_current_density_a_per_mm2 = per_core_i_rms_a / max(copper_area_mm2, 1e-12)
    equivalent_wire_diameter_mm = math.sqrt(4.0 * copper_area_mm2 / math.pi)
    fill_factor = (
        turns
        * copper_area_mm2
        * settings.winding_pack_factor
        / max(core.window_area_mm2, 1e-12)
    )
    rdc_25c_ohm = _COPPER_RESISTIVITY_25C_OHM_M * turns * core.mean_length_per_turn_m / max(copper_area_m2, 1e-18)
    per_core_copper_loss_w = per_core_i_rms_a * per_core_i_rms_a * rdc_25c_ohm * settings.copper_temperature_factor
    copper_loss_w = per_core_copper_loss_w * parallel_core_count
    b_dc_t = per_core_effective_inductance_h * per_core_idc_a / max(turns * core.ae_m2, 1e-18)
    delta_b_t = per_core_effective_inductance_h * per_core_delta_i_pp_a / max(turns * core.ae_m2, 1e-18)
    b_peak_t = max(
        b_dc_t + 0.5 * delta_b_t,
        per_core_effective_inductance_h * per_core_i_peak_a / max(turns * core.ae_m2, 1e-18),
    )
    core_loss_density_mw_per_cm3 = estimate_sendust_core_loss_mw_per_cm3(
        material,
        frequency_hz=request.ripple_frequency_hz,
        delta_b_t=delta_b_t,
    )
    per_core_core_loss_w = core_loss_density_mw_per_cm3 * core.ve_cm3 / 1000.0
    core_loss_w = per_core_core_loss_w * parallel_core_count
    winding_volume_cm3 = turns * core.mean_length_per_turn_m * copper_area_m2 * settings.winding_pack_factor * 1e6
    estimated_volume_cm3 = (core.ve_cm3 + winding_volume_cm3) * parallel_core_count

    return AcDcReactorCandidate(
        candidate_id=f"{core.part_number}_P{parallel_core_count}_N{turns}",
        core_part_number=core.part_number,
        material_id=material.material_id,
        material_name=material.display_name,
        relative_permeability=core.relative_permeability,
        parallel_core_count=parallel_core_count,
        per_core_turns=turns,
        turns=turns,
        per_core_inductance_h=per_core_inductance_h,
        per_core_effective_inductance_h=per_core_effective_inductance_h,
        inductance_h=inductance_h,
        effective_inductance_h=effective_inductance_h,
        al_dc_derating_factor=settings.al_dc_derating_factor,
        od_mm=core.od_mm,
        id_mm=core.id_mm,
        ht_mm=core.ht_mm,
        ae_cm2=core.ae_cm2,
        le_cm=core.le_cm,
        ve_cm3=core.ve_cm3,
        mean_length_per_turn_m=core.mean_length_per_turn_m,
        window_area_mm2=core.window_area_mm2,
        fill_factor=fill_factor,
        copper_area_mm2=copper_area_mm2,
        equivalent_wire_diameter_mm=equivalent_wire_diameter_mm,
        current_density_a_per_mm2=actual_current_density_a_per_mm2,
        rdc_25c_ohm=rdc_25c_ohm,
        b_dc_t=b_dc_t,
        delta_b_t=delta_b_t,
        b_peak_t=b_peak_t,
        core_loss_w=core_loss_w,
        copper_loss_w=copper_loss_w,
        total_loss_w=core_loss_w + copper_loss_w,
        estimated_volume_cm3=estimated_volume_cm3,
        notes=[
            "First-pass Sendust toroid reactor candidate.",
            "AL is derated with a fixed DC-bias factor; vendor bias curve fitting is not implemented.",
        ],
        metadata={
            "core_loss_density_mw_per_cm3": core_loss_density_mw_per_cm3,
            "al_nh_per_turn2": core.al_nh_per_turn2,
            "stock_qty": core.stock_qty,
            "analyzer_url": core.analyzer_url,
            "winding_pack_factor": settings.winding_pack_factor,
            "copper_temperature_factor": settings.copper_temperature_factor,
            "target_current_density_a_per_mm2": settings.target_current_density_a_per_mm2,
            "target_window_utilization": settings.target_window_utilization,
            "minimum_copper_area_mm2": minimum_copper_area_mm2,
            "target_window_copper_area_mm2": target_window_copper_area_mm2,
            "max_copper_area_mm2": max_copper_area_mm2,
            "selected_target_copper_area_mm2": target_copper_area_mm2,
            "per_core_i_rms_a": per_core_i_rms_a,
            "per_core_idc_a": per_core_idc_a,
            "per_core_delta_i_pp_a": per_core_delta_i_pp_a,
            "per_core_copper_loss_w": per_core_copper_loss_w,
            "per_core_core_loss_w": per_core_core_loss_w,
        },
    )


def _first_rejection_reason(
    candidate: AcDcReactorCandidate,
    settings: AcDcReactorSelectionSettings,
) -> str:
    if candidate.turns > settings.max_turns:
        return "turns_limit"
    if candidate.effective_inductance_h <= 0.0:
        return "inductance"
    if candidate.fill_factor is None or candidate.fill_factor > settings.max_fill_factor:
        return "fill_factor"
    if candidate.b_peak_t is None or candidate.b_peak_t > settings.max_b_peak_t:
        return "b_peak"
    if candidate.delta_b_t is None or candidate.delta_b_t > settings.max_delta_b_t:
        return "delta_b"
    if candidate.total_loss_w is None or not math.isfinite(candidate.total_loss_w):
        return "loss"
    return ""


def _rank_candidates(
    candidates: list[AcDcReactorCandidate],
    settings: AcDcReactorSelectionSettings,
) -> list[AcDcReactorCandidate]:
    if not candidates:
        return []
    losses = [float(candidate.total_loss_w or math.inf) for candidate in candidates]
    volumes = [float(candidate.estimated_volume_cm3 or math.inf) for candidate in candidates]
    fills = [float(candidate.fill_factor or math.inf) for candidate in candidates]
    fluxes = [float(candidate.b_peak_t or math.inf) / settings.max_b_peak_t for candidate in candidates]
    turns_values = [float(candidate.turns) for candidate in candidates]

    ranked: list[AcDcReactorCandidate] = []
    for candidate in candidates:
        loss_score = _normalize(float(candidate.total_loss_w or math.inf), losses)
        volume_score = _normalize(float(candidate.estimated_volume_cm3 or math.inf), volumes)
        fill_score = _normalize(float(candidate.fill_factor or math.inf), fills)
        flux_score = _normalize(float(candidate.b_peak_t or math.inf) / settings.max_b_peak_t, fluxes)
        turns_score = _normalize(float(candidate.turns), turns_values)
        score = (
            0.35 * loss_score
            + 0.25 * volume_score
            + 0.20 * fill_score
            + 0.15 * flux_score
            + 0.05 * turns_score
        )
        ranked.append(
            replace(
                candidate,
                score=score,
                metadata={
                    **candidate.metadata,
                    "ranking_breakdown": {
                        "loss": loss_score,
                        "volume": volume_score,
                        "fill": fill_score,
                        "flux": flux_score,
                        "turns": turns_score,
                    },
                },
            )
        )
    return sorted(
        ranked,
        key=lambda item: (
            float(item.score if item.score is not None else math.inf),
            float(item.total_loss_w if item.total_loss_w is not None else math.inf),
            float(item.estimated_volume_cm3 if item.estimated_volume_cm3 is not None else math.inf),
            item.candidate_id,
        ),
    )


def _normalize(value: float, population: list[float]) -> float:
    finite_values = [item for item in population if math.isfinite(item)]
    if not finite_values or not math.isfinite(value):
        return 1.0
    low = min(finite_values)
    high = max(finite_values)
    if high <= low:
        return 0.0
    return (value - low) / (high - low)


def _validate_request(request: AcDcReactorDesignRequest) -> None:
    positive_fields = {
        "required_inductance_h": request.required_inductance_h,
        "f_line_hz": request.f_line_hz,
        "ripple_frequency_hz": request.ripple_frequency_hz,
        "idc_a": request.idc_a,
        "i_rms_a": request.i_rms_a,
        "i_peak_a": request.i_peak_a,
        "delta_i_pp_a": request.delta_i_pp_a,
        "vdc_est_v": request.vdc_est_v,
        "throughput_power_w": request.throughput_power_w,
    }
    for name, value in positive_fields.items():
        if value <= 0.0:
            raise ValueError(f"{name} must be positive for AC-DC reactor selection.")
    if request.i_valley_a < 0.0:
        raise ValueError("i_valley_a must be non-negative for the first-pass choke selector.")
    if request.material_family != "sendust":
        raise ValueError("Only Sendust AC-DC reactor material_family is implemented.")
    if request.core_shape != "toroid":
        raise ValueError("Only toroid AC-DC reactor core_shape is implemented.")


def _validate_settings(settings: AcDcReactorSelectionSettings) -> None:
    for name in (
        "al_dc_derating_factor",
        "target_current_density_a_per_mm2",
        "target_window_utilization",
        "max_fill_factor",
        "max_b_peak_t",
        "max_delta_b_t",
        "winding_pack_factor",
        "copper_temperature_factor",
        "loss_warning_power_ratio",
    ):
        if getattr(settings, name) <= 0.0:
            raise ValueError(f"{name} must be positive.")
    if settings.max_turns <= 0:
        raise ValueError("max_turns must be positive.")
    if settings.max_parallel_core_count <= 0:
        raise ValueError("max_parallel_core_count must be positive.")
    if settings.top_candidate_count <= 0:
        raise ValueError("top_candidate_count must be positive.")


def _material_id_from_permeability(relative_permeability: float) -> str:
    mu = int(round(relative_permeability))
    return f"ms_{mu}"


def _write_candidates_csv(path: Path, candidates: list[AcDcReactorCandidate]) -> None:
    fieldnames = [
        "rank",
        "candidate_id",
        "core_part_number",
        "material_name",
        "relative_permeability",
        "parallel_core_count",
        "turns",
        "per_core_turns",
        "per_core_inductance_h",
        "per_core_effective_inductance_h",
        "inductance_h",
        "effective_inductance_h",
        "od_mm",
        "id_mm",
        "ht_mm",
        "ae_cm2",
        "ve_cm3",
        "fill_factor",
        "current_density_a_per_mm2",
        "equivalent_wire_diameter_mm",
        "rdc_25c_ohm",
        "b_dc_t",
        "delta_b_t",
        "b_peak_t",
        "copper_loss_w",
        "core_loss_w",
        "total_loss_w",
        "estimated_volume_cm3",
        "score",
        "rejection_reason",
        "loss_score",
        "volume_score",
        "fill_score",
        "flux_score",
        "turns_score",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for rank, candidate in enumerate(candidates, start=1):
            breakdown = candidate.metadata.get("ranking_breakdown", {})
            writer.writerow(
                {
                    "rank": rank,
                    "candidate_id": candidate.candidate_id,
                    "core_part_number": candidate.core_part_number,
                    "material_name": candidate.material_name,
                    "relative_permeability": candidate.relative_permeability,
                    "parallel_core_count": candidate.parallel_core_count,
                    "turns": candidate.turns,
                    "per_core_turns": candidate.per_core_turns,
                    "per_core_inductance_h": candidate.per_core_inductance_h,
                    "per_core_effective_inductance_h": candidate.per_core_effective_inductance_h,
                    "inductance_h": candidate.inductance_h,
                    "effective_inductance_h": candidate.effective_inductance_h,
                    "od_mm": candidate.od_mm,
                    "id_mm": candidate.id_mm,
                    "ht_mm": candidate.ht_mm,
                    "ae_cm2": candidate.ae_cm2,
                    "ve_cm3": candidate.ve_cm3,
                    "fill_factor": candidate.fill_factor,
                    "current_density_a_per_mm2": candidate.current_density_a_per_mm2,
                    "equivalent_wire_diameter_mm": candidate.equivalent_wire_diameter_mm,
                    "rdc_25c_ohm": candidate.rdc_25c_ohm,
                    "b_dc_t": candidate.b_dc_t,
                    "delta_b_t": candidate.delta_b_t,
                    "b_peak_t": candidate.b_peak_t,
                    "copper_loss_w": candidate.copper_loss_w,
                    "core_loss_w": candidate.core_loss_w,
                    "total_loss_w": candidate.total_loss_w,
                    "estimated_volume_cm3": candidate.estimated_volume_cm3,
                    "score": candidate.score,
                    "rejection_reason": candidate.rejection_reason,
                    "loss_score": breakdown.get("loss"),
                    "volume_score": breakdown.get("volume"),
                    "fill_score": breakdown.get("fill"),
                    "flux_score": breakdown.get("flux"),
                    "turns_score": breakdown.get("turns"),
                }
            )
