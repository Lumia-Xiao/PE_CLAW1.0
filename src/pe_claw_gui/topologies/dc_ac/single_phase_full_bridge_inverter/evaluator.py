"""Evaluation/report assembly for the single-phase full-bridge inverter."""

from __future__ import annotations

from dataclasses import replace

from ....models.design_report import DesignReport
from ....models.operating_point import OperatingPoint
from ....models.stress_result import StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from ...base.result import TopologyResult
from ...base.spec import TopologySpec


def evaluate(
    candidate: TopologyCandidate,
    waveform_set: WaveformSet | None = None,
    stress_result: StressResult | None = None,
) -> TopologyResult:
    """Build compact first-pass inverter evaluation lines."""

    metadata = candidate.metadata
    is_tcm = str(candidate.mode_capable).startswith("tcm_")
    if is_tcm:
        summary_lines = [
            "First-pass TCM triangular-current full-bridge inverter estimate completed.",
            f"Modulation index = {_fmt(metadata.get('modulation_index'))} (limit {_fmt(metadata.get('modulation_limit'))}).",
            f"Output inductor = {_fmt(candidate.inductance_h * 1e6)} uH from TCM segmented frequency window.",
            f"TCM valley current target = {_fmt(metadata.get('tcm_valley_current_target_a'))} A.",
            f"TCM peak current max = {_fmt(metadata.get('tcm_i_peak_max_a'))} A.",
            (
                "TCM design-segment switching frequency range = "
                f"{_fmt(metadata.get('tcm_fsw_min_actual_hz'))} to {_fmt(metadata.get('tcm_fsw_max_actual_hz'))} Hz."
            ),
            f"TCM feasible frequency-window intersection = {bool(metadata.get('tcm_feasible'))}.",
            (
                f"DC-link capacitor = {_fmt(candidate.capacitance_f * 1e6)} uF from twice-line "
                "energy balance using Vdc ripple peak-to-peak target."
            ),
        ]
    else:
        summary_lines = [
            "First-pass CCM unipolar-SPWM full-bridge inverter estimate completed.",
            f"Modulation index = {_fmt(metadata.get('modulation_index'))} (limit {_fmt(metadata.get('modulation_limit'))}).",
            f"Output inductor = {_fmt(candidate.inductance_h * 1e6)} uH from current-ripple target.",
            (
                f"DC-link capacitor = {_fmt(candidate.capacitance_f * 1e6)} uF from twice-line "
                "energy balance using Vdc ripple peak-to-peak target."
            ),
        ]
    if waveform_set is not None:
        summary_lines.extend(
            [
                f"Integrated v_dc ripple pp = {_fmt(waveform_set.metadata.get('dc_link_voltage_ripple_pp_v'))} V.",
                f"i_Cdc rms = {_fmt(waveform_set.metadata.get('dc_link_capacitor_current_rms_a'))} A.",
            ]
        )
        refined_sample_count = waveform_set.metadata.get("refined_pwm_sample_count")
        if refined_sample_count:
            summary_lines.extend(
                [
                    f"Refined unipolar-SPWM preview samples = {int(refined_sample_count)}.",
                    f"Refined inductor PWM ripple pp = {_fmt(waveform_set.metadata.get('refined_inductor_pwm_ripple_pp_a'))} A.",
                ]
            )
        if waveform_set.metadata.get("single_phase_inverter_tcm_envelope"):
            summary_lines.extend(
                [
                    (
                        "TCM reconstructed waveform fsw range = "
                        f"{_fmt(waveform_set.metadata.get('tcm_detail_fsw_min_hz'))} to "
                        f"{_fmt(waveform_set.metadata.get('tcm_detail_fsw_max_hz'))} Hz."
                    ),
                    "TCM detailed current is a first-pass triangular reconstruction; transitions and parasitics are not modeled.",
                ]
            )
            if waveform_set.metadata.get("tcm_low_slope_region_detected"):
                summary_lines.append(
                    "TCM low-slope guard: reconstructed fsw falls below "
                    f"{_fmt(waveform_set.metadata.get('tcm_low_slope_fsw_min_limit_hz'))} Hz "
                    f"(minimum {_fmt(waveform_set.metadata.get('tcm_low_slope_min_fsw_hz'))} Hz); "
                    "mixed-mode fallback clamps fsw to the requested minimum."
                )
                summary_lines.append(
                    "TCM mixed-mode cycle fraction = "
                    f"{_fmt_percent(waveform_set.metadata.get('tcm_mixed_mode_cycle_fraction'))}."
                )
    return TopologyResult(
        topology_id=candidate.topology_id,
        display_name=candidate.display_name,
        candidate=candidate,
        feasible=bool(metadata.get("modulation_valid", False)) and (not is_tcm or bool(metadata.get("tcm_feasible", False))),
        summary_lines=summary_lines,
        notes=[
            "DC-link capacitance uses single-phase twice-line-frequency energy balance.",
            "Semiconductor loss uses a 20-segment line-cycle quasi-static model when device selection has run.",
            "Electrolytic capacitor bank selection is available through Run Capacitor.",
        ],
    )


def build_report(
    spec: TopologySpec,
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
    waveform_set: WaveformSet | None = None,
    stress_result: StressResult | None = None,
    topology_result: TopologyResult | None = None,
) -> DesignReport:
    """Build the design report for first-pass inverter synthesis."""

    is_tcm = str(candidate.mode_capable).startswith("tcm_")
    design_note = (
        "Output inductor is selected from a 20-segment TCM triangular-current frequency-window envelope."
        if is_tcm
        else "Output inductor is sized from unipolar-SPWM current ripple in CCM."
    )
    waveform_note = (
        "TCM waveform output includes a first-pass triangular current reconstruction; transitions and parasitics are not modeled."
        if is_tcm
        else "Efficiency Sweep reuses the selected switch, DC-link capacitor bank, and output-inductor realization over the fixed-hardware load grid."
    )
    if operating_point is not None and waveform_set is not None:
        operating_point = replace(
            operating_point,
            vout_v=float(waveform_set.metadata.get("achieved_output_voltage_fundamental_rms_v", waveform_set.operating_vout_v)),
            power_factor=float(
                waveform_set.metadata.get(
                    "achieved_load_displacement_power_factor",
                    operating_point.power_factor if operating_point.power_factor is not None else 1.0,
                )
            ),
        )
    return DesignReport(
        spec=spec,
        candidate=candidate,
        operating_point=operating_point,
        waveform=waveform_set,
        stress=stress_result,
        topology_result=topology_result,
        notes=[
            design_note,
            "DC-link electrolytic capacitor is sized from single-phase twice-line energy storage.",
            "Semiconductor loss uses a 20-segment line-cycle quasi-static model; ZVS direction classification is diagnostic only.",
            waveform_note,
        ],
    )


def _fmt(value) -> str:
    try:
        return f"{float(value):.6g}"
    except (TypeError, ValueError):
        return "-"


def _fmt_percent(value) -> str:
    try:
        return f"{100.0 * float(value):.3g}%"
    except (TypeError, ValueError):
        return "-"
