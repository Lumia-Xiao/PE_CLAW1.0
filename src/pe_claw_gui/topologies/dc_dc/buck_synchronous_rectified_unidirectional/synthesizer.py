"""Synchronous Buck synthesis logic used by the runtime plugin."""

from __future__ import annotations

from ...base.candidate import TopologyCandidate
from ...base.spec import TopologySpec


def synthesize(spec: TopologySpec) -> TopologyCandidate:
    """Synthesize the nominal synchronous Buck hardware design."""
    vin_nom = 0.5 * (spec.vin_min + spec.vin_max)
    fs_hz = spec.fs_khz * 1e3
    iout = spec.pout / spec.vout
    duty_nom = spec.vout / vin_nom

    delta_il = spec.ripple_current_ratio * iout
    inductance_h = (vin_nom - spec.vout) * duty_nom / (delta_il * fs_hz)

    delta_vo = spec.ripple_voltage_ratio_percent / 100.0 * spec.vout
    capacitance_f = delta_il / (8.0 * fs_hz * delta_vo)

    il_peak = iout + 0.5 * delta_il
    il_valley = iout - 0.5 * delta_il

    return TopologyCandidate(
        topology_id=spec.topology_id,
        display_name=spec.display_name,
        vin_min=spec.vin_min,
        vin_max=spec.vin_max,
        vin_nom=vin_nom,
        vout_target=spec.vout,
        pout_target=spec.pout,
        duty_nom=duty_nom,
        iout=iout,
        fs_hz=fs_hz,
        inductance_h=inductance_h,
        capacitance_f=capacitance_f,
        delta_il=delta_il,
        delta_vo=delta_vo,
        il_peak=il_peak,
        il_valley=il_valley,
        ccm_valid=True,
        mode_capable="ccm_negative_current_allowed",
        r_load_nom_ohm=0.0,
        r_crit_nom_ohm=0.0,
        boundary_load_ratio=0.0,
        i_boundary_nom_a=0.0,
        notes=[
            "Synchronous rectified Buck.",
            "Continuous-current treatment.",
            "Negative inductor current allowed.",
        ],
        metadata={"legacy_key": spec.metadata.get("legacy_key")},
    )
