"""Semiconductor reference-temperature and heatsink backsolve helpers."""

from __future__ import annotations

import math

from ...models.device_thermal import ReferenceJunctionTemperatureEstimate, SinkThermalRequirement

DEFAULT_INTERFACE_RTH_CS_K_PER_W = 1.0
DEFAULT_COOLING_MODE = "natural"

_SINK_SURFACE_MODELS: dict[str, dict[str, float | str]] = {
    # These coefficients intentionally trade fidelity for readability and tuning ease.
    # h is a first-pass effective convection coefficient referenced to the sink's exposed
    # external area. area_density is a compactness proxy for a small finned aluminum extrusion.
    "natural": {
        "h_w_per_cm2k": 0.00085,  # approx. 8.5 W/m^2-K
        "area_density_cm2_per_cm3": 6.0,
        "model_name": "surface_proxy_natural_v1",
    },
    "forced_air": {
        "h_w_per_cm2k": 0.00250,  # approx. 25 W/m^2-K with modest airflow
        "area_density_cm2_per_cm3": 10.0,
        "model_name": "surface_proxy_forced_air_v1",
    },
}


def estimate_reference_junction_temperature(
    *,
    p_total_w: float,
    rth_jc_k_per_w: float,
    rth_ja_k_per_w: float,
    ambient_temp_c: float,
    case_temp_c: float | None = None,
) -> ReferenceJunctionTemperatureEstimate:
    """Estimate bare-package junction temperature from either case or ambient."""

    if case_temp_c is not None:
        tj_est_c = case_temp_c + p_total_w * rth_jc_k_per_w
        return ReferenceJunctionTemperatureEstimate(
            tj_est_c=tj_est_c,
            method="case_based",
            label=f"Bare-package reference Tj = {tj_est_c:.3f} C via case-based estimate.",
            notes=["Reference estimate uses measured or assumed case temperature plus datasheet Rth_jc."],
        )

    tj_est_c = ambient_temp_c + p_total_w * rth_ja_k_per_w
    if p_total_w > 0.0 and tj_est_c > 1000.0 and rth_jc_k_per_w > 0.0:
        fallback_tj_est_c = ambient_temp_c + p_total_w * rth_jc_k_per_w
        return ReferenceJunctionTemperatureEstimate(
            tj_est_c=fallback_tj_est_c,
            method="rth_jc_fallback",
            label=(
                f"Bare-package reference Tj = {fallback_tj_est_c:.3f} C via Rth_jc fallback; "
                f"ambient-only Rth_ja estimate would be {tj_est_c:.3f} C."
            ),
            warnings=[
                "Case temperature not provided; ambient-only Rth_ja estimate exceeded the sanity limit and was not used.",
                "Reference estimate uses datasheet Rth_jc as a heatsink-required lower-bound fallback.",
            ],
            notes=[
                "Device requires an explicit case/sink thermal path for final junction-temperature verification.",
            ],
        )

    return ReferenceJunctionTemperatureEstimate(
        tj_est_c=tj_est_c,
        method="ambient_only",
        label=f"Bare-package reference Tj = {tj_est_c:.3f} C via ambient-only estimate.",
        warnings=["Case temperature not provided; ambient-only bare-package estimate was used."],
        notes=["Reference estimate uses datasheet Rth_ja because no case temperature was provided."],
    )


def estimate_sink_volume(
    required_sink_rth_k_per_w: float,
    *,
    cooling_mode: str = DEFAULT_COOLING_MODE,
) -> tuple[float | None, str]:
    """Estimate heatsink volume from a surface-area proxy model."""

    if required_sink_rth_k_per_w <= 0.0:
        return None, str(_SINK_SURFACE_MODELS.get(cooling_mode, _SINK_SURFACE_MODELS[DEFAULT_COOLING_MODE])["model_name"])

    model = _SINK_SURFACE_MODELS.get(cooling_mode, _SINK_SURFACE_MODELS[DEFAULT_COOLING_MODE])
    heat_transfer_coefficient = float(model["h_w_per_cm2k"])
    area_density = float(model["area_density_cm2_per_cm3"])
    model_name = str(model["model_name"])
    required_surface_area_cm2 = 1.0 / (heat_transfer_coefficient * required_sink_rth_k_per_w)
    volume_cm3 = required_surface_area_cm2 / area_density
    return volume_cm3, model_name


def required_sink_thermal_resistance(
    *,
    p_total_w: float,
    ambient_temp_c: float,
    target_junction_temp_c: float,
    rth_jc_k_per_w: float,
    rth_cs_k_per_w: float = DEFAULT_INTERFACE_RTH_CS_K_PER_W,
    cooling_mode: str = DEFAULT_COOLING_MODE,
) -> SinkThermalRequirement:
    """Backsolve the required sink-to-ambient thermal resistance."""

    warnings: list[str] = []
    notes: list[str] = []

    if target_junction_temp_c <= ambient_temp_c:
        warnings.append("Target junction temperature must be above ambient temperature.")
        return SinkThermalRequirement(
            target_junction_temp_c=target_junction_temp_c,
            ambient_temp_c=ambient_temp_c,
            p_total_w=p_total_w,
            rth_jc_k_per_w=rth_jc_k_per_w,
            rth_cs_k_per_w=rth_cs_k_per_w,
            required_total_rth_k_per_w=None,
            required_sink_rth_k_per_w=None,
            estimated_sink_volume_cm3=None,
            sink_volume_model=str(_SINK_SURFACE_MODELS.get(cooling_mode, _SINK_SURFACE_MODELS[DEFAULT_COOLING_MODE])["model_name"]),
            cooling_mode_assumed=cooling_mode,
            feasible=False,
            classification="invalid_target",
            sink_requirement_label="Target-junction backsolve is invalid because the requested junction temperature is not above ambient.",
            sink_volume_estimate_label="No sink volume estimate was produced.",
            sink_estimate_model_label="First-pass sink model was not applied.",
            thermal_interpretation_label="Cooling requirement: invalid thermal target.",
            warnings=warnings,
            notes=notes,
        )

    if p_total_w <= 0.0:
        notes.append("Nonpositive device loss; no sink is required under the current operating point.")
        return SinkThermalRequirement(
            target_junction_temp_c=target_junction_temp_c,
            ambient_temp_c=ambient_temp_c,
            p_total_w=p_total_w,
            rth_jc_k_per_w=rth_jc_k_per_w,
            rth_cs_k_per_w=rth_cs_k_per_w,
            required_total_rth_k_per_w=0.0,
            required_sink_rth_k_per_w=0.0,
            estimated_sink_volume_cm3=0.0,
            sink_volume_model=str(_SINK_SURFACE_MODELS.get(cooling_mode, _SINK_SURFACE_MODELS[DEFAULT_COOLING_MODE])["model_name"]),
            cooling_mode_assumed=cooling_mode,
            feasible=True,
            classification="no_sink_required",
            sink_requirement_label="Target-junction backsolve indicates no additional sink is required at this loss level.",
            sink_volume_estimate_label="First-pass sink volume estimate: 0 cm^3.",
            sink_estimate_model_label="Surface-area proxy model was bypassed because device loss is nonpositive.",
            thermal_interpretation_label="Cooling requirement: no sink required for this operating point.",
            warnings=warnings,
            notes=notes,
        )

    required_total_rth_k_per_w = (target_junction_temp_c - ambient_temp_c) / p_total_w
    required_sink_rth_k_per_w = required_total_rth_k_per_w - rth_jc_k_per_w - rth_cs_k_per_w

    if required_sink_rth_k_per_w <= 0.0:
        warnings.append("No feasible passive sink under the current assumptions; target is tighter than package plus interface allow.")
        return SinkThermalRequirement(
            target_junction_temp_c=target_junction_temp_c,
            ambient_temp_c=ambient_temp_c,
            p_total_w=p_total_w,
            rth_jc_k_per_w=rth_jc_k_per_w,
            rth_cs_k_per_w=rth_cs_k_per_w,
            required_total_rth_k_per_w=required_total_rth_k_per_w,
            required_sink_rth_k_per_w=required_sink_rth_k_per_w,
            estimated_sink_volume_cm3=None,
            sink_volume_model=str(_SINK_SURFACE_MODELS.get(cooling_mode, _SINK_SURFACE_MODELS[DEFAULT_COOLING_MODE])["model_name"]),
            cooling_mode_assumed=cooling_mode,
            feasible=False,
            classification="not_feasible",
            sink_requirement_label=(
                "Target-junction backsolve indicates the package plus interface path already exceeds the requested thermal budget."
            ),
            sink_volume_estimate_label="No feasible passive-sink volume estimate was produced.",
            sink_estimate_model_label="Surface-area proxy model was not applied because required Rth_sa is nonpositive.",
            thermal_interpretation_label="Cooling requirement: target is too strict for the current package/interface assumptions.",
            warnings=warnings,
            notes=notes,
        )

    estimated_sink_volume_cm3, sink_volume_model = estimate_sink_volume(
        required_sink_rth_k_per_w,
        cooling_mode=cooling_mode,
    )
    classification = classify_sink_requirement(required_sink_rth_k_per_w)
    notes.append(
        f"To limit junction temperature to {target_junction_temp_c:.3f} C at {ambient_temp_c:.3f} C ambient, "
        f"required sink Rth_sa <= {required_sink_rth_k_per_w:.3f} K/W."
    )
    if estimated_sink_volume_cm3 is not None:
        notes.append(
            f"First-pass {cooling_mode.replace('_', ' ')} heatsink volume estimate: {estimated_sink_volume_cm3:.3f} cm^3."
        )
        notes.append("This sink volume is an empirical comparison proxy and not a final mechanical design guarantee.")
    return SinkThermalRequirement(
        target_junction_temp_c=target_junction_temp_c,
        ambient_temp_c=ambient_temp_c,
        p_total_w=p_total_w,
        rth_jc_k_per_w=rth_jc_k_per_w,
        rth_cs_k_per_w=rth_cs_k_per_w,
        required_total_rth_k_per_w=required_total_rth_k_per_w,
        required_sink_rth_k_per_w=required_sink_rth_k_per_w,
        estimated_sink_volume_cm3=estimated_sink_volume_cm3,
        sink_volume_model=sink_volume_model,
        cooling_mode_assumed=cooling_mode,
        feasible=True,
        classification=classification,
        sink_requirement_label=(
            f"Target-junction backsolve: required sink-to-ambient thermal resistance <= {required_sink_rth_k_per_w:.3f} K/W."
        ),
        sink_volume_estimate_label=(
            f"First-pass {cooling_mode.replace('_', ' ')} heatsink volume estimate: {estimated_sink_volume_cm3:.3f} cm^3."
        ),
        sink_estimate_model_label=(
            f"Sink estimate model: {sink_volume_model} "
            "(surface-area proxy using effective convection and sink compactness assumptions)."
        ),
        thermal_interpretation_label=f"Cooling requirement: {classification}.",
        warnings=warnings,
        notes=notes,
    )


def classify_sink_requirement(required_sink_rth_k_per_w: float) -> str:
    """Classify the sink requirement into a simple engineering bucket."""

    if required_sink_rth_k_per_w <= 0.0:
        return "not_feasible"
    if required_sink_rth_k_per_w > 20.0:
        return "easy passive cooling"
    if required_sink_rth_k_per_w > 8.0:
        return "moderate passive sink"
    if required_sink_rth_k_per_w > 3.0:
        return "large passive sink / weak airflow may help"
    return "forced air likely required"


def summarize_semiconductor_thermal_design(
    *,
    reference_estimate: ReferenceJunctionTemperatureEstimate,
    sink_requirement: SinkThermalRequirement,
    datasheet_tj_max_c: float,
) -> list[str]:
    """Create short human-readable thermal notes for the device stage."""

    notes = [
        reference_estimate.label,
    ]
    notes.extend(reference_estimate.notes)
    notes.extend(reference_estimate.warnings)

    if reference_estimate.tj_est_c > datasheet_tj_max_c:
        notes.append(
            f"Device exceeds datasheet Tj,max ({datasheet_tj_max_c:.3f} C) in the bare-package reference case."
        )

    if (
        sink_requirement.required_sink_rth_k_per_w is not None
        and math.isfinite(sink_requirement.required_sink_rth_k_per_w)
        and sink_requirement.required_sink_rth_k_per_w > 0.0
    ):
        notes.append(sink_requirement.sink_requirement_label)
        notes.append("This sink resistance is a first-pass thermal sizing target.")
    if sink_requirement.sink_volume_estimate_label:
        notes.append(sink_requirement.sink_volume_estimate_label)
    if sink_requirement.sink_estimate_model_label:
        notes.append(sink_requirement.sink_estimate_model_label)
    if sink_requirement.thermal_interpretation_label:
        notes.append(sink_requirement.thermal_interpretation_label)
    notes.extend(sink_requirement.notes)
    notes.extend(sink_requirement.warnings)
    return notes
