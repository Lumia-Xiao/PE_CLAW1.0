"""Selective same-core stacked magnetic competitor expansion."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable

from ...models.inductor import FixedInductorDesignCandidate, InductorDesignRequest
from .allow_profiles import MagneticAllowProfile
from .candidate_metrics import MagneticCandidateContext, MagneticCandidateEngineeringMetrics, compute_candidate_engineering_metrics
from .core_assembly import StackedCoreAssembly, build_same_core_stack_assembly
from .core_loss_audit import core_loss_is_comparable
from .core_loss_role_adapter import evaluate_candidate_core_loss

STACKED_MARGIN_NEAR_LIMIT_THRESHOLD = 1.15
STACKED_SEED_LIMIT = 20
STACKED_ALLOWED_COUNTS = (2, 3)
STACKED_CORE_LOSS_BETA_FLOOR = 1.5
_MU0 = 4.0 * math.pi * 1e-7


@dataclass(frozen=True)
class StackedExpansionResult:
    """Outcome of the selective stacked-core competitor stage."""

    executed: bool = False
    execution_reason: str = ""
    seed_count: int = 0
    generated_count: int = 0
    stack2_generated_count: int = 0
    stack3_generated_count: int = 0
    precheck_pass_count: int = 0
    expanded_candidates: list[FixedInductorDesignCandidate] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class _CoreLossComputation:
    total_loss_w: float | None
    core_loss_density_w_per_m3: float | None
    model_name: str
    raw_beta: float | None = None
    effective_beta: float | None = None
    legacy_total_loss_w: float | None = None
    validity_status: str = "loss_data_not_available"
    model_id: str | None = None
    model_scope: str | None = None
    reconstruction_method: str = "unavailable"
    flux_peak_to_peak_t: float | None = None
    flux_ac_peak_t: float | None = None
    flux_dc_offset_t: float | None = None
    flux_absolute_peak_t: float | None = None
    effective_volume_m3: float | None = None


def select_stacked_seed_candidates(
    candidates: Iterable[FixedInductorDesignCandidate],
    metrics_by_id: dict[str, MagneticCandidateEngineeringMetrics],
    limit: int = STACKED_SEED_LIMIT,
    near_limit_threshold: float = STACKED_MARGIN_NEAR_LIMIT_THRESHOLD,
) -> list[FixedInductorDesignCandidate]:
    """Select a small deterministic seed set for stacked-core competitors."""
    candidate_list = list(candidates)
    if not candidate_list:
        return []

    volumes = [_value_or_inf(candidate.total_volume_m3) for candidate in candidate_list]
    losses = [_candidate_loss(candidate, metrics_by_id) for candidate in candidate_list]
    min_volume, max_volume = min(volumes), max(volumes)
    min_loss, max_loss = min(losses), max(losses)

    def normalize(value: float, low: float, high: float) -> float:
        if high <= low:
            return 0.0
        return (value - low) / (high - low)

    # Lower is better: favor candidates that already sit near the practical frontier
    # on volume and loss while still carrying some pressure on engineering margins.
    # This keeps the selective stack_count = 2, 3 competitor set focused on plausible
    # improvements rather than expanding arbitrary seeds from the whole candidate pool.
    scored = sorted(
        candidate_list,
        key=lambda candidate: (
            0.40 * normalize(_candidate_loss(candidate, metrics_by_id), min_loss, max_loss)
            + 0.40 * normalize(_value_or_inf(candidate.total_volume_m3), min_volume, max_volume)
            + 0.20 * _margin_frontier_score(metrics_by_id.get(candidate.candidate_id), near_limit_threshold),
            candidate.candidate_id,
        ),
    )
    return scored[:limit]


def expand_stacked_same_core_candidates(
    request: InductorDesignRequest,
    seed_candidates: Iterable[FixedInductorDesignCandidate],
    allow_profile: MagneticAllowProfile,
    context: MagneticCandidateContext,
) -> StackedExpansionResult:
    """Expand selected seeds to same-core stack-count competitors 2 and 3."""
    seeds = list(seed_candidates)
    if not seeds:
        return StackedExpansionResult(notes=["No valid seed candidates were available for stacked competitor generation."])

    notes = [
        "Selective stacked-core competitor generation is first-pass only: same core, same material, same wire, stack_count 2 and 3.",
        "This path uses an idealized same-core scaling model with no mixed cores or detailed multi-interface gap/fringing model.",
    ]
    generated_count = 0
    stack2_generated_count = 0
    stack3_generated_count = 0
    precheck_pass_count = 0
    expanded_candidates: list[FixedInductorDesignCandidate] = []

    for seed in seeds:
        for stack_count in STACKED_ALLOWED_COUNTS:
            assembly = build_same_core_stack_assembly(seed, stack_count)
            if assembly is None:
                continue
            generated_count += 1
            if stack_count == 2:
                stack2_generated_count += 1
            elif stack_count == 3:
                stack3_generated_count += 1
            approximate_candidate = build_stacked_candidate(
                seed=seed,
                request=request,
                assembly=assembly,
                detailed=False,
            )
            if approximate_candidate is None:
                continue
            if not quick_check_stacked_candidate(approximate_candidate, context, allow_profile):
                continue
            detailed_candidate = build_stacked_candidate(
                seed=seed,
                request=request,
                assembly=assembly,
                detailed=True,
            )
            if detailed_candidate is None:
                continue
            if not core_loss_is_comparable(
                detailed_candidate.metadata,
                detailed_candidate.reference_total_loss_w,
            ):
                continue
            precheck_pass_count += 1
            expanded_candidates.append(detailed_candidate)

    notes.append(f"Selected {len(seeds)} seed candidates for stacked competitor generation.")
    notes.append(
        f"Generated {generated_count} stacked competitors before cheap precheck "
        f"({stack2_generated_count} with stack_count = 2, {stack3_generated_count} with stack_count = 3)."
    )
    notes.append(f"{precheck_pass_count} stacked candidates survived the cheap precheck.")
    return StackedExpansionResult(
        executed=True,
        execution_reason="Selective stacked-core competitor generation executed.",
        seed_count=len(seeds),
        generated_count=generated_count,
        stack2_generated_count=stack2_generated_count,
        stack3_generated_count=stack3_generated_count,
        precheck_pass_count=precheck_pass_count,
        expanded_candidates=expanded_candidates,
        notes=notes,
    )


def quick_check_stacked_candidate(
    candidate: FixedInductorDesignCandidate,
    context: MagneticCandidateContext,
    allow_profile: MagneticAllowProfile,
) -> bool:
    """Reject obviously poor stacked competitors before full evaluation."""
    metrics = compute_candidate_engineering_metrics(candidate, context, allow_profile)
    for margin in (
        metrics.sat_margin,
        metrics.loss_margin,
        metrics.current_density_margin,
        metrics.fill_margin,
    ):
        if margin is not None and margin < 1.0:
            return False
    seed_loss = _as_float(candidate.metadata.get("seed_total_loss_w"))
    candidate_loss = metrics.total_loss_w
    if seed_loss is not None and candidate_loss is not None and candidate_loss > 3.0 * max(seed_loss, 1e-12):
        return False
    return True


def build_stacked_candidate(
    seed: FixedInductorDesignCandidate,
    request: InductorDesignRequest,
    assembly: StackedCoreAssembly,
    detailed: bool,
) -> FixedInductorDesignCandidate | None:
    """Build an idealized same-core stacked candidate from a single-core seed."""
    effective_ae_m2 = assembly.effective_Ae_m2
    effective_ve_m3 = assembly.effective_Ve_m3
    effective_aw_m2 = assembly.effective_window_area_m2
    effective_total_volume_m3 = assembly.effective_total_volume_m3
    if effective_ae_m2 is None or effective_ve_m3 is None or effective_aw_m2 is None or effective_total_volume_m3 is None:
        return None

    turns = max(seed.turns, 1)
    corrected_v2_semantics = assembly.volume_policy.startswith("step19d_v2_")
    flux_peak_to_peak_t = (
        request.target_inductance_h * abs(request.i_peak_a - request.i_valley_a) / (turns * effective_ae_m2)
        if corrected_v2_semantics
        else abs(request.v_l_on_v) * request.duty_nom / (request.fs_hz * effective_ae_m2 * turns)
    )
    flux_absolute_peak_t = request.target_inductance_h * request.i_peak_a / (turns * effective_ae_m2)
    flux_dc_offset_t = request.target_inductance_h * request.i_avg_a / (turns * effective_ae_m2)
    gap_m = seed.gap_m * assembly.stack_count if seed.gap_m is not None else (
        _MU0 * (turns**2) * effective_ae_m2 / request.target_inductance_h
    )
    fill_factor = seed.fill_factor / assembly.stack_count if seed.fill_factor is not None else None
    rdc_ohm = seed.rdc_25c_ohm
    copper_loss_w = _resolve_copper_loss(seed)
    if copper_loss_w is None and detailed and rdc_ohm is not None:
        reference_i_rms = _as_float(seed.metadata.get("reference_i_rms_a")) or request.i_rms_a
        copper_loss_w = (reference_i_rms**2) * rdc_ohm

    if detailed:
        core_loss_result = _resolve_core_loss(
            seed,
            request,
            (
                effective_ae_m2
                if corrected_v2_semantics
                else float(seed.metadata.get("core_effective_area_m2") or effective_ae_m2)
            ),
            effective_ve_m3,
            assembly.stack_count,
        )
    else:
        approximate_core_loss = _approximate_core_loss(seed, assembly.stack_count)
        core_loss_result = _CoreLossComputation(
            total_loss_w=approximate_core_loss,
            core_loss_density_w_per_m3=(
                approximate_core_loss / effective_ve_m3
                if approximate_core_loss is not None and effective_ve_m3 > 0.0
                else None
            ),
            model_name=str(seed.metadata.get("core_loss_model") or "approximate_from_seed"),
            raw_beta=_as_float(seed.metadata.get("core_loss_beta_raw")),
            effective_beta=_as_float(seed.metadata.get("core_loss_beta_effective")),
        )
    core_loss_w = core_loss_result.total_loss_w
    if detailed and core_loss_w is None:
        return None
    total_loss_w = (
        copper_loss_w + core_loss_w
        if copper_loss_w is not None and core_loss_w is not None
        else None
    )

    winding_volume_m3 = assembly.winding_volume_m3
    core_volume_m3 = assembly.physical_envelope_volume_m3
    saturation_current_a = seed.saturation_current_a * assembly.stack_count if seed.saturation_current_a is not None else None
    candidate_id = f"{seed.candidate_id}_STACK{assembly.stack_count}"
    notes = [
        *seed.notes,
        *assembly.notes,
        "Same-core stacked competitor generated from a selected single-core seed.",
    ]
    if core_loss_result.model_name == "stacked_seed_anchored_beta_floor":
        notes.append("Legacy stacked beta-floor result is retained for A/B diagnostics only.")
    metadata = dict(seed.metadata)
    metadata.update(
        {
            "assembly_type": assembly.assembly_type,
            "stack_count": assembly.stack_count,
            "base_candidate_id": seed.candidate_id,
            "core_effective_area_m2": effective_ae_m2,
            "core_effective_volume_m3": effective_ve_m3,
            "core_window_area_m2": effective_aw_m2,
            "seed_total_loss_w": seed.reference_total_loss_w,
            "seed_total_volume_m3": seed.total_volume_m3,
            "seed_reference_core_loss_w": seed.reference_core_loss_w,
            "seed_reference_b_peak_t": seed.b_peak_design_t,
            "seed_core_effective_volume_m3": seed.metadata.get("core_effective_volume_m3"),
            "seed_core_effective_area_m2": seed.metadata.get("core_effective_area_m2"),
            "seed_core_window_area_m2": seed.metadata.get("core_window_area_m2"),
            "seed_core_physical_envelope_volume_m3": (
                seed.metadata.get("physical_envelope_volume_m3") or seed.core_volume_m3
            ),
            "seed_solid_material_volume_m3": seed.metadata.get("solid_material_volume_m3"),
            "seed_core_mass_kg": seed.metadata.get("core_mass_kg"),
            "seed_winding_volume_m3": seed.winding_volume_m3,
            "physical_envelope_volume_m3": assembly.physical_envelope_volume_m3,
            "solid_material_volume_m3": assembly.solid_material_volume_m3,
            "core_mass_kg": assembly.mass_kg,
            "gross_volume_m3": assembly.physical_envelope_volume_m3,
            "stack_volume_policy": assembly.volume_policy,
            "step19d_corrected_v2_semantics": corrected_v2_semantics,
            "core_loss_flux_peak_to_peak_t": flux_peak_to_peak_t,
            "core_flux_ac_peak_t": flux_peak_to_peak_t / 2.0,
            "core_flux_dc_offset_t": flux_dc_offset_t,
            "core_flux_absolute_peak_t": flux_absolute_peak_t,
            "saturation_flux_input_definition": "Babsolute=L*Ipeak/(N*Ae)",
        }
    )
    if core_loss_w is not None:
        raw_beta = core_loss_result.raw_beta
        effective_beta = core_loss_result.effective_beta or raw_beta
        metadata["core_loss_model"] = core_loss_result.model_name
        metadata["core_loss_unit_conversion_policy"] = "W_per_m3_times_m3_equals_W_once"
        metadata["core_loss_flux_input_definition"] = (
            "Bpp=L*(Ipeak-Ivalley)/(N*Ae_assembled); shared current reconstruction"
            if corrected_v2_semantics
            else "legacy-v1 stacked flux/loss policy retained until normalized-v2 promotion"
        )
        metadata["kernel_core_loss_w"] = core_loss_w
        metadata["step9_router_status"] = core_loss_result.validity_status
        metadata["step9_router_model_id"] = core_loss_result.model_id
        metadata["step9_router_model_scope"] = core_loss_result.model_scope
        metadata["step9_reconstruction_method"] = core_loss_result.reconstruction_method
        metadata["core_loss_validity_status"] = core_loss_result.validity_status
        metadata["core_loss_method"] = core_loss_result.model_name
        metadata["core_loss_model_id"] = core_loss_result.model_id
        metadata["core_loss_model_scope"] = core_loss_result.model_scope
        metadata["core_loss_effective_volume_m3"] = effective_ve_m3
        metadata["step19d_assembled_ae_m2"] = effective_ae_m2
        metadata["step19d_assembled_ve_m3"] = effective_ve_m3
        metadata["step19d_loss_volume_multiplier_count"] = 1
        metadata["step19d_router_flux_peak_to_peak_t"] = core_loss_result.flux_peak_to_peak_t
        metadata["step19d_router_flux_ac_peak_t"] = core_loss_result.flux_ac_peak_t
        metadata["step19d_router_flux_dc_offset_t"] = core_loss_result.flux_dc_offset_t
        metadata["step19d_router_flux_absolute_peak_t"] = core_loss_result.flux_absolute_peak_t
        if core_loss_result.legacy_total_loss_w is not None:
            metadata["legacy_core_loss_w"] = core_loss_result.legacy_total_loss_w
            metadata["kernel_vs_legacy_relative_difference"] = (core_loss_w / core_loss_result.legacy_total_loss_w) - 1.0
        # Explicit flux semantics are authoritative.  Keep the legacy alias
        # because the stacked beta-floor path still reads it for old records.
        metadata["reference_flux_peak_to_peak_t"] = flux_peak_to_peak_t
        metadata["reference_flux_ac_peak_t"] = flux_peak_to_peak_t / 2.0
        metadata["reference_flux_absolute_peak_t"] = flux_absolute_peak_t
        metadata["reference_b_peak_t"] = flux_peak_to_peak_t
        metadata["reference_core_loss_density_w_per_m3"] = (
            core_loss_result.core_loss_density_w_per_m3
            if core_loss_result.core_loss_density_w_per_m3 is not None
            else core_loss_w / max(effective_ve_m3, 1e-18)
        )
        if raw_beta is not None:
            metadata["core_loss_beta_raw"] = raw_beta
        if effective_beta is not None:
            metadata["core_loss_beta_effective"] = effective_beta
    return FixedInductorDesignCandidate(
        candidate_id=candidate_id,
        assembly_type=assembly.assembly_type,
        stack_count=assembly.stack_count,
        base_core_name=seed.base_core_name or seed.core_name,
        core_name=seed.core_name,
        material_name=seed.material_name,
        wire_name=seed.wire_name,
        turns=seed.turns,
        parallel_bundles=seed.parallel_bundles,
        gap_m=gap_m,
        inductance_h=seed.inductance_h,
        rdc_25c_ohm=rdc_ohm,
        fill_factor=fill_factor,
        core_volume_m3=core_volume_m3,
        winding_volume_m3=winding_volume_m3,
        total_volume_m3=effective_total_volume_m3,
        b_peak_design_t=flux_absolute_peak_t,
        saturation_current_a=saturation_current_a,
        reference_copper_loss_w=copper_loss_w,
        reference_core_loss_w=core_loss_w,
        reference_total_loss_w=total_loss_w,
        notes=notes,
        metadata=metadata,
    )


def _margin_frontier_score(
    metrics: MagneticCandidateEngineeringMetrics | None,
    near_limit_threshold: float,
) -> float:
    if metrics is None:
        return 0.5
    available = [
        min(max(margin - 1.0, 0.0) / max(near_limit_threshold - 1.0, 1e-9), 1.0)
        for margin in (
            metrics.sat_margin,
            metrics.loss_margin,
            metrics.current_density_margin,
            metrics.fill_margin,
        )
        if margin is not None
    ]
    if not available:
        return 0.5
    return sum(available) / len(available)


def _candidate_loss(
    candidate: FixedInductorDesignCandidate,
    metrics_by_id: dict[str, MagneticCandidateEngineeringMetrics],
) -> float:
    metrics = metrics_by_id.get(candidate.candidate_id)
    if metrics is not None and metrics.total_loss_w is not None:
        return metrics.total_loss_w
    if candidate.reference_total_loss_w is not None:
        return candidate.reference_total_loss_w
    return float("inf")


def _value_or_inf(value: float | None) -> float:
    if value is None:
        return float("inf")
    return float(value)


def _resolve_copper_loss(seed: FixedInductorDesignCandidate) -> float | None:
    if seed.reference_copper_loss_w is not None:
        return seed.reference_copper_loss_w
    if seed.reference_total_loss_w is not None and seed.reference_core_loss_w is not None:
        return max(seed.reference_total_loss_w - seed.reference_core_loss_w, 0.0)
    return None


def _resolve_core_loss(
    seed: FixedInductorDesignCandidate,
    request: InductorDesignRequest,
    effective_ae_m2: float,
    effective_ve_m3: float,
    stack_count: int,
) -> _CoreLossComputation:
    ranges = seed.metadata.get("steinmetz_ranges")
    result, built = evaluate_candidate_core_loss(
        material_id=str(seed.metadata.get("material_id") or seed.material_name or seed.candidate_id),
        material_name=seed.material_name or seed.candidate_id,
        frequency_hz=request.fs_hz,
        effective_volume_m3=effective_ve_m3,
        effective_area_m2=effective_ae_m2,
        turns=seed.turns,
        inductance_h=seed.inductance_h,
        current_min_a=float(request.i_valley_a),
        current_max_a=float(request.i_peak_a),
        steinmetz_ranges=ranges if isinstance(ranges, list) else None,
        source_role="stacked_core",
        source_component_id=f"{seed.candidate_id}_STACK{stack_count}",
    )
    total_loss_w = result.core_loss_w
    raw_beta = _as_float(seed.metadata.get("core_loss_beta_raw"))
    legacy_total_loss_w = _approximate_core_loss(seed, stack_count)
    excitation = built.excitation
    return _CoreLossComputation(
        total_loss_w=total_loss_w,
        core_loss_density_w_per_m3=result.volumetric_loss_w_per_m3,
        model_name=result.method_used or "unavailable",
        raw_beta=raw_beta,
        effective_beta=raw_beta,
        legacy_total_loss_w=legacy_total_loss_w,
        validity_status=result.validity_status.value,
        model_id=result.selected_model_id,
        model_scope=result.selected_model_scope,
        reconstruction_method=built.reconstruction_method,
        flux_peak_to_peak_t=excitation.flux_peak_to_peak_t if excitation is not None else None,
        flux_ac_peak_t=excitation.flux_ac_peak_t if excitation is not None else None,
        flux_dc_offset_t=excitation.flux_dc_offset_t if excitation is not None else None,
        flux_absolute_peak_t=excitation.flux_absolute_peak_t if excitation is not None else None,
        effective_volume_m3=excitation.effective_volume_m3 if excitation is not None else None,
    )


def _approximate_core_loss(seed: FixedInductorDesignCandidate, stack_count: int) -> float | None:
    if seed.reference_core_loss_w is None:
        return None
    beta = _as_float(seed.metadata.get("core_loss_beta_effective"))
    if beta is None:
        beta = _as_float(seed.metadata.get("steinmetz_ranges", [{}])[0].get("beta"))
    if beta is None:
        return seed.reference_core_loss_w
    if stack_count > 1 and beta <= 1.0:
        beta = max(beta, STACKED_CORE_LOSS_BETA_FLOOR)
    return seed.reference_core_loss_w * (stack_count ** (1.0 - beta))


def _as_float(value) -> float | None:
    if value is None:
        return None
    try:
        resolved = float(value)
        return resolved if math.isfinite(resolved) else None
    except (TypeError, ValueError, AttributeError):
        return None
