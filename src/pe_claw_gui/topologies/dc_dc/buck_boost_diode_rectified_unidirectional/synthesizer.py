"""Inverting diode Buck-Boost synthesis logic used by the runtime plugin."""

from __future__ import annotations

from ...base.candidate import TopologyCandidate
from ...base.spec import TopologySpec


def _clamp_duty(value: float) -> float:
    return min(max(value, 1e-6), 0.95)


def synthesize(spec: TopologySpec) -> TopologyCandidate:
    """Synthesize the nominal inverting Buck-Boost hardware design."""
    vin_nom = 0.5 * (spec.vin_min + spec.vin_max)
    fs_hz = spec.fs_khz * 1e3
    vout_mag = abs(spec.vout)
    iout = spec.pout / vout_mag
    duty_nom = _clamp_duty(vout_mag / (vout_mag + vin_nom))

    i_l_nom = iout / max(1.0 - duty_nom, 1e-6)
    delta_il = spec.ripple_current_ratio * i_l_nom
    inductance_h = vin_nom * duty_nom / (delta_il * fs_hz)

    delta_vo = spec.ripple_voltage_ratio_percent / 100.0 * vout_mag
    capacitance_f = iout * duty_nom / (fs_hz * delta_vo)

    r_load_nom_ohm = vout_mag / max(iout, 1e-9)
    r_crit_nom_ohm = 2.0 * inductance_h * fs_hz / max((1.0 - duty_nom) ** 2, 1e-9)
    i_boundary_nom_a = vout_mag / max(r_crit_nom_ohm, 1e-9)
    boundary_load_ratio = i_boundary_nom_a / max(iout, 1e-9)

    il_peak = i_l_nom + 0.5 * delta_il
    il_valley = i_l_nom - 0.5 * delta_il

    return TopologyCandidate(
        topology_id=spec.topology_id,
        display_name=spec.display_name,
        vin_min=spec.vin_min,
        vin_max=spec.vin_max,
        vin_nom=vin_nom,
        vout_target=vout_mag,
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
        ccm_valid=il_valley > 0.0,
        mode_capable="ccm_dcm",
        r_load_nom_ohm=r_load_nom_ohm,
        r_crit_nom_ohm=r_crit_nom_ohm,
        boundary_load_ratio=boundary_load_ratio,
        i_boundary_nom_a=i_boundary_nom_a,
        notes=[
            "Inverting Buck-Boost diode rectified unidirectional.",
            "Nominal CCM/DCM-capable operating model.",
            "Output polarity is inverted; design uses output-voltage magnitude.",
        ],
        metadata={
            "legacy_key": spec.metadata.get("legacy_key"),
            "output_polarity": "inverted",
        },
    )
