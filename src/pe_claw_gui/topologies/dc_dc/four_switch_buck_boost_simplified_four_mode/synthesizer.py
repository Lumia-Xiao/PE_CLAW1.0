"""Simplified four-mode four-switch Buck-Boost synthesis logic."""

from __future__ import annotations

from ...base.candidate import TopologyCandidate
from ...base.spec import TopologySpec
from .mode import build_segment_plan, classify_mode, compute_duties, estimate_delta_il


def synthesize(spec: TopologySpec) -> TopologyCandidate:
    """Synthesize the nominal four-switch Buck-Boost passive design."""
    vin_nom = 0.5 * (spec.vin_min + spec.vin_max)
    fs_hz = spec.fs_khz * 1e3
    iout = spec.pout / spec.vout
    duty_clamp = float(spec.metadata.get("duty_clamp", 0.10))
    transition_band_ratio = float(spec.metadata.get("transition_band_ratio", 0.10))

    delta_il_buck = spec.ripple_current_ratio * iout
    if spec.vin_max > spec.vout:
        d_buck = spec.vout / spec.vin_max
        l_buck = (spec.vin_max - spec.vout) * d_buck / max(delta_il_buck * fs_hz, 1e-12)
    else:
        l_buck = 0.0

    if spec.vout > spec.vin_min:
        d_boost = 1.0 - spec.vin_min / spec.vout
        iin_min = spec.pout / max(spec.vin_min, 1e-6)
        delta_il_boost = spec.ripple_current_ratio * iin_min
        l_boost = spec.vin_min * d_boost / max(delta_il_boost * fs_hz, 1e-12)
    else:
        d_boost = 0.0
        l_boost = 0.0

    if l_buck <= 0.0 and l_boost <= 0.0:
        l_transition = spec.vout * 0.5 / max(delta_il_buck * fs_hz, 1e-12)
        inductance_h = l_transition
    else:
        inductance_h = max(l_buck, l_boost)

    delta_vo = spec.ripple_voltage_ratio_percent / 100.0 * spec.vout
    c_buck = delta_il_buck / max(8.0 * fs_hz * delta_vo, 1e-12)
    c_boost = iout * d_boost / max(fs_hz * delta_vo, 1e-12)
    if c_buck <= 0.0 and c_boost <= 0.0:
        capacitance_f = iout * 0.5 / max(fs_hz * delta_vo, 1e-12)
    else:
        capacitance_f = max(c_buck, c_boost)

    nominal_mode = classify_mode(vin_nom, spec.vout, transition_band_ratio)
    d2_nom, d3_nom = compute_duties(vin_nom, spec.vout, nominal_mode, duty_clamp)
    segments = build_segment_plan(vin_nom, spec.vout, nominal_mode, d2_nom, d3_nom)
    delta_il_nom = estimate_delta_il(inductance_h, 1.0 / fs_hz, segments)
    nominal_i_l_avg = iout if nominal_mode in {"PURE_BUCK", "EXTENDED_BUCK"} else iout / max(1.0 - d3_nom, 1e-6)
    il_peak = nominal_i_l_avg + 0.5 * delta_il_nom
    il_valley = nominal_i_l_avg - 0.5 * delta_il_nom

    return TopologyCandidate(
        topology_id=spec.topology_id,
        display_name=spec.display_name,
        vin_min=spec.vin_min,
        vin_max=spec.vin_max,
        vin_nom=vin_nom,
        vout_target=spec.vout,
        pout_target=spec.pout,
        duty_nom=max(d2_nom, d3_nom),
        iout=iout,
        fs_hz=fs_hz,
        inductance_h=inductance_h,
        capacitance_f=capacitance_f,
        delta_il=delta_il_nom,
        delta_vo=delta_vo,
        il_peak=il_peak,
        il_valley=il_valley,
        ccm_valid=il_valley > 0.0,
        mode_capable="simplified_four_mode_ccm",
        notes=[
            "Non-inverting four-switch buck-boost.",
            "Simplified fixed-frequency four-mode control.",
            "Passive design based on worst-case Buck/Boost region approximations.",
        ],
        metadata={
            "legacy_key": spec.metadata.get("legacy_key"),
            "duty_clamp": duty_clamp,
            "transition_band_ratio": transition_band_ratio,
            "nominal_mode": nominal_mode,
            "d2_nom": d2_nom,
            "d3_nom": d3_nom,
        },
    )
