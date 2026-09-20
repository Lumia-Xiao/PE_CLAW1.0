"""Evaluation/report assembly for the three-phase three-level NPC inverter."""

from __future__ import annotations

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
    """Build compact first-pass three-phase NPC inverter evaluation lines."""

    metadata = candidate.metadata
    waveform_metadata = waveform_set.metadata if waveform_set is not None and isinstance(waveform_set.metadata, dict) else {}
    waveform_lines = _waveform_summary_lines(waveform_metadata)
    summary_lines = [
        "Three-phase three-level NPC PD level-shifted SPWM first-pass estimate completed.",
        f"Topology ID = {candidate.topology_id}.",
        f"Vdc min/nom/max = {_fmt(metadata.get('vdc_min_v'))} / {_fmt(metadata.get('vdc_nom_v'))} / {_fmt(metadata.get('vdc_max_v'))} V.",
        f"Vac line-line rms = {_fmt(metadata.get('vac_ll_rms_v'))} V.",
        f"Vac phase rms = {_fmt(metadata.get('vac_phase_rms_v'))} V.",
        f"Pout = {_fmt(candidate.pout_target)} W.",
        f"PF = {_fmt(metadata.get('power_factor'))}.",
        f"fsw = {_fmt(candidate.fs_hz)} Hz; f_line = {_fmt(metadata.get('f_line_hz'))} Hz.",
        f"Modulation scheme = {metadata.get('modulation_scheme', 'unspecified')}.",
        f"Modulation index = {_fmt(metadata.get('modulation_index'))} (limit {_fmt(metadata.get('modulation_limit'))}).",
        f"Output inductor per phase = {_fmt(candidate.inductance_h * 1e6)} uH from conservative NPC ripple target.",
        f"Cdc series-equivalent minimum = {_fmt(metadata.get('dc_link_series_equivalent_capacitance_f', 0.0) * 1e6)} uF.",
        f"Cdc minimum per physical split bank = {_fmt(candidate.capacitance_f * 1e6)} uF.",
        f"I_phase_rms = {_fmt(metadata.get('i_phase_rms_a'))} A.",
        f"I_phase_peak = {_fmt(metadata.get('i_phase_peak_a'))} A.",
        f"Delta iL pp sizing target = {_fmt(metadata.get('delta_il_pp_a'))} A.",
        f"Synthesized target-based I_L peak/valley = {_fmt(candidate.il_peak)} A / {_fmt(candidate.il_valley)} A.",
        f"Sizing-target CCM valid = {bool(candidate.ccm_valid)}.",
        f"Switch positions = {int(metadata.get('switch_position_count', 0))}.",
        f"Clamp diode positions = {int(metadata.get('clamp_diode_count', 0))}.",
        f"Device worst-case blocking basis = Vdc_max/2 x Kneutral + Vovershoot = {_fmt(metadata.get('npc_worst_case_blocking_voltage_v'))} V; required rating = {_fmt(float(metadata.get('npc_worst_case_blocking_voltage_v', 0.0)) * (1.0 + float(metadata.get('npc_static_voltage_margin_ratio', 0.20))))} V.",
        *waveform_lines,
        "Split upper/lower DC-link capacitor bank selection is available through Run Capacitor.",
        "Loss stage available: NPC outer/inner switches, clamp diodes, split DC-link capacitors, and 3x output-inductor first-pass operating loss.",
        "Efficiency sweep available: fixed-hardware load and PF diagnostics.",
    ]
    return TopologyResult(
        topology_id=candidate.topology_id,
        display_name=candidate.display_name,
        candidate=candidate,
        feasible=bool(metadata.get("modulation_valid", False)),
        summary_lines=summary_lines,
        notes=[
            "Run Design completed for first-pass NPC CCM synthesis.",
            "Output inductor is per phase.",
            "DC-link capacitor is a split upper/lower structure; RMS bank selection is available through Run Capacitor.",
            "Neutral-point balancing is not modeled in the first-pass NPC preview.",
            *(
                ["NPC PD-SPWM waveform preview generated; downstream loss and efficiency stages reuse the selected fixed hardware."]
                if waveform_set is not None
                else ["NPC PD-SPWM waveform generation is available through Generate Waveforms."]
            ),
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
    """Build the design report for first-pass three-phase NPC synthesis."""

    return DesignReport(
        spec=spec,
        candidate=candidate,
        operating_point=operating_point,
        waveform=waveform_set,
        stress=stress_result,
        topology_result=topology_result,
        notes=[
            "Output inductor is sized as a per-phase CCM NPC PD-SPWM first-pass estimate.",
            "DC-link capacitance is a split half-link proxy; upper/lower capacitor bank RMS selection is available through Run Capacitor.",
            "Semiconductor stress uses Vdc/2 first-pass blocking voltage for NPC active switches and clamp diodes.",
            "First-pass loss, efficiency sweep, geometry, and Hardware Overview closure are available after running the corresponding GUI stages.",
            "Neutral-point balancing dynamics, dead-time, Coss, commutation overlap, and parasitic transient models are not included.",
        ],
    )


def _fmt(value) -> str:
    try:
        return f"{float(value):.6g}"
    except (TypeError, ValueError):
        return "-"


def _waveform_summary_lines(metadata: dict[str, object]) -> list[str]:
    if not metadata.get("three_phase_npc_pd_spwm_waveforms"):
        return ["NPC PD-SPWM waveform generation is available through Generate Waveforms."]
    return [
        "NPC PD-SPWM waveform preview generated.",
        f"Operating load ratio = {_fmt(metadata.get('three_phase_npc_pd_spwm_operating', {}).get('load_ratio') if isinstance(metadata.get('three_phase_npc_pd_spwm_operating'), dict) else metadata.get('load_ratio'))}.",
        f"Operating PF = {_fmt(metadata.get('operating_power_factor'))}.",
        f"I_phase_rms operating = {_fmt(metadata.get('operating_i_phase_rms_a'))} A.",
        f"I_phase total RMS operating = {_fmt(metadata.get('operating_i_phase_total_rms_a'))} A.",
        f"Maximum local PWM-period phase-current ripple = {_fmt(metadata.get('phase_inductor_ripple_max_local_pp_a'))} A pp.",
        f"Waveform-predicted CCM valid = {bool(metadata.get('operating_ccm_valid'))}.",
        f"Neutral-point current RMS proxy = {_fmt(metadata.get('npc_neutral_point_current_rms_a'))} A.",
        (
            "Upper/lower split DC-link capacitor current RMS proxies = "
            f"{_fmt(metadata.get('upper_dc_link_capacitor_current_rms_pwm_a'))} A / "
            f"{_fmt(metadata.get('lower_dc_link_capacitor_current_rms_pwm_a'))} A."
        ),
        "First-pass PD-SPWM only; neutral-point balancing, dead-time, Coss, and parasitic transients are not modeled.",
        "Split-link capacitor, magnetic, loss, efficiency, geometry, and Hardware Overview stages reuse this operating-point waveform when available.",
    ]
