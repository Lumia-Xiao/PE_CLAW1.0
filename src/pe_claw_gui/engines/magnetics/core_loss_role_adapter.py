"""Role adapters for migrating legacy candidate records to the shared router."""

from __future__ import annotations

from typing import Any, Mapping

from ...models.magnetic_loss_contract import CoreLossResult, CoreLossExcitationBuildResult
from .core_loss_excitation_builder import build_core_loss_excitation
from .core_loss_router import legacy_material_v2, route_core_loss_from_build_result


def evaluate_candidate_core_loss(
    *,
    material_id: str,
    material_name: str,
    frequency_hz: float,
    effective_volume_m3: float,
    effective_area_m2: float,
    turns: int,
    inductance_h: float | None,
    b_peak_t: float | None = None,
    current_min_a: float | None = None,
    current_max_a: float | None = None,
    steinmetz_ranges: list[Mapping[str, Any]] | None = None,
    proxy_coefficients: Mapping[str, float] | None = None,
    source_role: str,
    source_component_id: str,
    dc_offset_policy: str | None = None,
    requested_sample_count: int = 1001,
) -> tuple[CoreLossResult, CoreLossExcitationBuildResult]:
    """Build a scalar role excitation and route it through normalized-v2 logic.

    Candidate-generation APIs currently expose scalar design data rather than
    complete switch-cycle waveforms.  The builder therefore emits an explicit
    scalar-template record, preserving the distinction from measured data.
    """

    if current_min_a is not None or current_max_a is not None:
        if current_min_a is None or current_max_a is None:
            raise ValueError("Both current_min_a and current_max_a are required.")
        template = "piecewise_linear_current"
        current_a = (float(current_min_a), float(current_max_a))
        declared_peak = None
        declared_bpp = None
        declared_offset = None
    else:
        if b_peak_t is None:
            raise ValueError("b_peak_t is required when no current template is supplied.")
        template = "bipolar_triangular"
        current_a = ()
        declared_peak = float(b_peak_t)
        declared_bpp = 2.0 * float(b_peak_t)
        declared_offset = 0.0

    request = _build_request(
        frequency_hz=frequency_hz,
        source_role=source_role,
        source_component_id=source_component_id,
        effective_area_m2=effective_area_m2,
        effective_volume_m3=effective_volume_m3,
        turns=turns,
        inductance_h=inductance_h,
        current_a=current_a,
        template=template,
        declared_peak=declared_peak,
        declared_bpp=declared_bpp,
        declared_offset=declared_offset,
        dc_offset_policy=dc_offset_policy,
        requested_sample_count=requested_sample_count,
    )
    built = build_core_loss_excitation(request)
    material = legacy_material_v2(
        material_id=material_id,
        material_name=material_name,
        steinmetz_ranges=steinmetz_ranges,
        proxy_coefficients=proxy_coefficients,
        source_reference=f"step9:{source_role}",
    )
    result = route_core_loss_from_build_result(
        material=material,
        build_result=built,
        calculation_mode="production_step9",
    )
    return result, built


def _build_request(
    *, frequency_hz: float, source_role: str, source_component_id: str,
    effective_area_m2: float, effective_volume_m3: float, turns: int,
    inductance_h: float | None, current_a: tuple[float, ...], template: str,
    declared_peak: float | None, declared_bpp: float | None,
    declared_offset: float | None, dc_offset_policy: str | None,
    requested_sample_count: int,
):
    from ...models.magnetic_loss_contract import CoreLossExcitationBuildRequest

    return CoreLossExcitationBuildRequest(
        frequency_hz=float(frequency_hz), temperature_c=25.0,
        source_topology="candidate_generation", source_role=source_role,
        source_component_id=source_component_id, effective_area_m2=float(effective_area_m2),
        effective_volume_m3=float(effective_volume_m3), turns=int(turns),
        inductance_h=inductance_h, current_a=current_a,
        scalar_waveform_template=template,
        declared_flux_ac_peak_t=declared_peak,
        declared_flux_peak_to_peak_t=declared_bpp,
        declared_flux_dc_offset_t=declared_offset,
        declared_flux_absolute_peak_t=declared_peak,
        dc_offset_policy=dc_offset_policy,
        requested_sample_count=requested_sample_count,
        source_fields=("candidate scalar design fields", "step9 shared role adapter"),
    )


__all__ = ["evaluate_candidate_core_loss"]
