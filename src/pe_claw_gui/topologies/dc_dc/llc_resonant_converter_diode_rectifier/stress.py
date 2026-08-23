"""LLC diode-rectifier first-pass stress entry point."""

from __future__ import annotations

from ....models.stress_result import StressMetric, StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate


def extract_stress(
    candidate: TopologyCandidate,
    waveform_set: WaveformSet | None = None,
) -> StressResult:
    """Build first-pass FHA-level LLC stress estimates."""

    llc_fha = candidate.metadata.get("llc_fha", {})
    vout_nom_v = float(llc_fha.get("vout_nom_v", candidate.vout_target)) if isinstance(llc_fha, dict) else candidate.vout_target
    vout_max_v = float(llc_fha.get("vout_max_v", candidate.vout_target)) if isinstance(llc_fha, dict) else candidate.vout_target
    pout_max_w = float(llc_fha.get("pout_max_w", candidate.pout_target)) if isinstance(llc_fha, dict) else candidate.pout_target
    nominal_current_estimate = (
        llc_fha.get("current_estimates_nominal_full_load", {})
        if isinstance(llc_fha, dict)
        else {}
    )
    worst_case_current_stress = (
        llc_fha.get("worst_case_current_stress", {})
        if isinstance(llc_fha, dict)
        else {}
    )
    stress_basis = (
        worst_case_current_stress
        if isinstance(worst_case_current_stress, dict) and worst_case_current_stress
        else nominal_current_estimate
    )
    waveform_metadata = (
        waveform_set.metadata.get("llc_fha_waveforms", {})
        if waveform_set is not None and isinstance(waveform_set.metadata, dict)
        else {}
    )
    operating_currents = (
        waveform_metadata.get("operating_point_currents", {})
        if isinstance(waveform_metadata, dict)
        else {}
    )
    primary_switch_rows = operating_currents.get("primary_switches", {}) if isinstance(operating_currents, dict) else {}
    diode_rows = operating_currents.get("secondary_diodes", {}) if isinstance(operating_currents, dict) else {}
    secondary_rectifier_type = (
        str(llc_fha.get("secondary_rectifier_type", "full_bridge_rectifier"))
        if isinstance(llc_fha, dict)
        else "full_bridge_rectifier"
    )
    primary_switch_voltage_stress_v = _read_estimate(stress_basis, "primary_switch_voltage_stress_v", candidate.vin_max)
    rectifier_reverse_voltage_v = _read_estimate(
        stress_basis,
        "rectifier_reverse_voltage_stress_v",
        vout_max_v if secondary_rectifier_type == "full_bridge_rectifier" else 2.0 * vout_max_v,
    )
    full_load_output_current_a = pout_max_w / max(vout_nom_v, 1e-12)
    primary_switch_peak_a = _read_estimate(stress_basis, "primary_switch_peak_a")
    primary_switch_rms_a = _read_estimate(stress_basis, "primary_switch_rms_a")
    rectifier_diode_peak_a = _read_estimate(stress_basis, "rectifier_diode_peak_a", full_load_output_current_a)
    rectifier_diode_rms_a = _read_estimate(stress_basis, "rectifier_diode_rms_a", full_load_output_current_a)
    rectifier_diode_avg_a = _read_estimate(stress_basis, "rectifier_diode_avg_a", full_load_output_current_a / 2.0)
    if isinstance(primary_switch_rows, dict) and primary_switch_rows:
        primary_switch_rms_a = max(float(row.get("rms_a", 0.0)) for row in primary_switch_rows.values())
        primary_switch_peak_a = max(float(row.get("peak_a", 0.0)) for row in primary_switch_rows.values())
    if isinstance(diode_rows, dict) and diode_rows:
        rectifier_diode_avg_a = max(float(row.get("avg_a", 0.0)) for row in diode_rows.values())
        rectifier_diode_rms_a = max(float(row.get("rms_a", 0.0)) for row in diode_rows.values())
        rectifier_diode_peak_a = max(float(row.get("peak_a", 0.0)) for row in diode_rows.values())
    notes = [
        "First-pass FHA sinusoidal current stress estimates are used for diode LLC semiconductor screening.",
        "Worst-case current stress is selected from feasible FHA coverage corners.",
        "Primary switch RMS assumes each primary switch conducts for approximately half a switching period.",
        "Rectifier diode average/RMS currents are output-side first-pass estimates, not conduction-angle-integrated waveform results.",
        "Rectifier peak current is estimated from the reflected FHA tank-current peak.",
        "Detailed LLC time-domain waveforms, dead-time commutation, ZVS current, harmonics, diode conduction angle, and device-level current sharing are not implemented yet.",
        f"Rectifier diode reverse voltage stress is approximated from secondary_rectifier_type={secondary_rectifier_type}.",
        f"Full-load output current is {full_load_output_current_a:.6g} A and is not used as primary switch current.",
    ]
    return StressResult(
        switch=StressMetric(
            voltage_max_v=primary_switch_voltage_stress_v,
            current_peak_a=primary_switch_peak_a,
            current_rms_a=primary_switch_rms_a,
            current_avg_a=0.0,
        ),
        rectifier=StressMetric(
            voltage_max_v=rectifier_reverse_voltage_v,
            current_peak_a=rectifier_diode_peak_a,
            current_rms_a=rectifier_diode_rms_a,
            current_avg_a=rectifier_diode_avg_a,
        ),
        notes=notes,
    )


def _read_estimate(estimates: object, key: str, fallback: float | None = None) -> float | None:
    if not isinstance(estimates, dict):
        return fallback
    value = estimates.get(key, fallback)
    if value is None:
        return fallback
    return float(value)
