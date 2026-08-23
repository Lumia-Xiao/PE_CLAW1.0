"""Phase 1 synthesis for a three-phase diode bridge capacitor-filter rectifier."""

from __future__ import annotations

from math import sqrt

from ...base.candidate import TopologyCandidate
from ...base.spec import TopologySpec
from .simulation import power_factor_requirement_status
from .waveform import build_three_phase_diode_bridge_waveform_preview


def calculate_three_phase_diode_bridge_capacitor_filter_phase1(
    *,
    vll_rms_v: float,
    f_line_hz: float,
    vout_target_v: float,
    pout_w: float,
    dc_link_ripple_ratio: float,
    diode_forward_drop_v: float,
    diode_voltage_margin: float,
    ambient_temp_c: float | None = None,
    target_junction_temp_c: float | None = None,
) -> dict[str, float | None]:
    """Return first-pass six-pulse rectifier estimates for line-to-line RMS input."""

    if vll_rms_v <= 0.0:
        raise ValueError("VLL rms must be positive.")
    if f_line_hz <= 0.0:
        raise ValueError("Line frequency must be positive.")
    if pout_w <= 0.0:
        raise ValueError("Output power must be positive.")
    if dc_link_ripple_ratio <= 0.0:
        raise ValueError("DC-link ripple ratio must be positive.")
    if diode_forward_drop_v < 0.0:
        raise ValueError("Diode forward drop estimate cannot be negative.")
    if diode_voltage_margin <= 0.0:
        raise ValueError("Diode voltage margin must be positive.")

    vll_peak_v = sqrt(2.0) * vll_rms_v
    ripple_frequency_hz = 6.0 * f_line_hz
    vdc_six_pulse_average_reference_v = 1.35 * vll_rms_v - 2.0 * diode_forward_drop_v
    vdc_peak_charge_limit_v = sqrt(2.0) * vll_rms_v - 2.0 * diode_forward_drop_v
    if vdc_peak_charge_limit_v <= 0.0:
        raise ValueError("Estimated Vdc must be positive; check VLL rms and diode forward drop.")

    rload_ohm = vout_target_v * vout_target_v / pout_w
    idc_reference_a = vdc_peak_charge_limit_v / rload_ohm
    design_target_ripple_vpp = dc_link_ripple_ratio * vout_target_v
    cdc_required_f = idc_reference_a / (ripple_frequency_hz * design_target_ripple_vpp)
    diode_reverse_stress_v = vll_peak_v
    diode_vrrm_required_v = diode_voltage_margin * diode_reverse_stress_v
    per_diode_average_current_est_a = idc_reference_a / 3.0
    per_diode_rms_current_est_a = idc_reference_a / sqrt(3.0)
    bridge_conduction_loss_est_w = 2.0 * diode_forward_drop_v * idc_reference_a
    capacitor_voltage_requirement_v = vdc_peak_charge_limit_v

    return {
        "vll_peak_v": vll_peak_v,
        "ripple_frequency_hz": ripple_frequency_hz,
        "vdc_est_v": vdc_six_pulse_average_reference_v,
        "vdc_six_pulse_average_reference_v": vdc_six_pulse_average_reference_v,
        "vdc_peak_charge_limit_v": vdc_peak_charge_limit_v,
        "vout_target_v": vout_target_v,
        "idc_a": idc_reference_a,
        "rload_ohm": rload_ohm,
        "delta_vdc_pp_v": design_target_ripple_vpp,
        "design_target_ripple_vpp": design_target_ripple_vpp,
        "cdc_required_f": cdc_required_f,
        "diode_reverse_stress_v": diode_reverse_stress_v,
        "diode_vrrm_required_v": diode_vrrm_required_v,
        "per_diode_average_current_est_a": per_diode_average_current_est_a,
        "per_diode_rms_current_est_a": per_diode_rms_current_est_a,
        "per_diode_peak_current_est_a": None,
        "per_diode_peak_current_placeholder_a": idc_reference_a,
        "bridge_conduction_loss_est_w": bridge_conduction_loss_est_w,
        "capacitor_voltage_requirement_v": capacitor_voltage_requirement_v,
        "ambient_temp_c": ambient_temp_c,
        "target_junction_temp_c": target_junction_temp_c,
    }


def synthesize(spec: TopologySpec) -> TopologyCandidate:
    """Build first-pass three-phase diode bridge electrical estimates."""

    metadata = dict(spec.metadata)
    estimates = calculate_three_phase_diode_bridge_capacitor_filter_phase1(
        vll_rms_v=float(metadata["vll_rms_v"]),
        f_line_hz=float(metadata["f_line_hz"]),
        vout_target_v=float(spec.vout),
        pout_w=spec.pout,
        dc_link_ripple_ratio=float(metadata["dc_link_ripple_ratio"]),
        diode_forward_drop_v=float(metadata["diode_forward_drop_v"]),
        diode_voltage_margin=float(metadata["diode_voltage_margin"]),
        ambient_temp_c=_optional_float(metadata.get("ambient_temp_c")),
        target_junction_temp_c=_optional_float(metadata.get("target_junction_temp_c")),
    )
    vdc_est_v = float(estimates["vdc_six_pulse_average_reference_v"])
    idc_a = float(estimates["idc_a"])
    delta_vdc_pp_v = float(estimates["design_target_ripple_vpp"])
    cdc_required_f = float(estimates["cdc_required_f"])
    ripple_frequency_hz = float(estimates["ripple_frequency_hz"])
    rload_ohm = float(estimates["rload_ohm"])

    candidate_metadata = {
        **metadata,
        **estimates,
        "ripple_ratio": float(metadata["dc_link_ripple_ratio"]),
        "diode_vrrm_stress_v": estimates["diode_reverse_stress_v"],
        "recommended_diode_vrrm_v": estimates["diode_vrrm_required_v"],
        "per_diode_avg_current_a": estimates["per_diode_average_current_est_a"],
        "per_diode_rms_current_a": estimates["per_diode_rms_current_est_a"],
        "per_diode_peak_current_a": None,
        "bridge_conduction_loss_w": estimates["bridge_conduction_loss_est_w"],
        "phase1_basis": "fixed passive load with three-phase capacitor charging-pulse simulation",
        "cdc_required_f": cdc_required_f,
        "selected_cdc_f": cdc_required_f,
    }
    waveform_preview = build_three_phase_diode_bridge_waveform_preview(
        vll_rms_v=float(metadata["vll_rms_v"]),
        f_line_hz=float(metadata["f_line_hz"]),
        pout_w=spec.pout,
        dc_link_ripple_ratio=float(metadata["dc_link_ripple_ratio"]),
        diode_forward_drop_v=float(metadata["diode_forward_drop_v"]),
        phase1_vdc_est_v=vdc_est_v,
        idc_a=idc_a,
        diode_reverse_stress_v=float(estimates["diode_reverse_stress_v"]),
        source_resistance_per_phase_ohm=float(metadata["source_resistance_per_phase_ohm"]),
        rload_ohm=float(metadata["rload_ohm"]),
        cout_f=cdc_required_f,
        artifact_suffix="load_1p00",
    )
    candidate_metadata["six_pulse_waveform_preview"] = waveform_preview.metrics
    candidate_metadata["six_pulse_waveform_preview_waveforms"] = waveform_preview.waveforms
    candidate_metadata["six_pulse_waveform_preview_artifacts"] = waveform_preview.artifact_paths
    candidate_metadata["six_pulse_waveform_preview_warnings"] = waveform_preview.warnings
    simulation = waveform_preview.metrics
    candidate_metadata.update(
        {
            "three_phase_pulse_simulation": simulation,
            "vout_achieved_v": simulation["vdc_avg_v"],
            "iout_achieved_a": simulation["output_current_avg_a"],
            "pout_achieved_w": simulation["output_power_w"],
            "power_factor_achieved": simulation["power_factor"],
            "power_factor_requirement_status": power_factor_requirement_status(
                float(simulation["power_factor"]),
                _optional_float(metadata.get("power_factor_target")),
            ),
        }
    )
    return TopologyCandidate(
        topology_id=spec.topology_id,
        display_name=spec.display_name,
        vin_min=float(metadata["vll_rms_v"]),
        vin_max=float(metadata["vll_rms_v"]),
        vin_nom=float(metadata["vll_rms_v"]),
        vout_target=float(simulation["vdc_avg_v"]),
        pout_target=spec.pout,
        duty_nom=1.0,
        iout=float(simulation["output_current_avg_a"]),
        fs_hz=ripple_frequency_hz,
        inductance_h=0.0,
        capacitance_f=cdc_required_f,
        delta_il=0.0,
        delta_vo=float(simulation["vdc_ripple_pp_v"]),
        il_peak=float(simulation["phase_current_peak_a"]),
        il_valley=0.0,
        ccm_valid=True,
        mode_capable="phase1_three_phase_six_pulse_estimate",
        output_ripple_vpp_v=float(simulation["vdc_ripple_pp_v"]),
        r_load_nom_ohm=float(metadata["rload_ohm"]),
        notes=[
            "Phase 1 three-phase diode bridge capacitor-filter estimate.",
            "Vdc estimate uses line-to-line RMS voltage, not single-phase Vac peak voltage.",
            "Three-phase capacitor charging-pulse state simulation completed.",
            "Bridge module selection, capacitor selection, and final loss remain separate pipeline stages.",
        ],
        metadata=candidate_metadata,
    )


def _optional_float(value: object) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None
