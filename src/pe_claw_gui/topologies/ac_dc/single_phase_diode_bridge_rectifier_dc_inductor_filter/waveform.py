"""Waveforms for the AC-DC DC-side inductor rectifier state-space simulation."""

from __future__ import annotations

from dataclasses import replace

from ....models.operating_point import OperatingPoint
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from .simulation import DCInductorBridgeSimulationResult, simulate_ac_dc_diode_bridge_dc_inductor_filter

_OPEN_LOAD_OHM = 1e12


def generate_waveforms(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
) -> WaveformSet | None:
    """Return compact final-cycle waveforms from the state-space simulation."""

    design_simulation = candidate.metadata.get("state_space_simulation")
    if not isinstance(design_simulation, dict) or not design_simulation.get("simulation_succeeded"):
        return None

    load_ratio = _clamp_load_ratio(operating_point.load_ratio if operating_point is not None else 1.0)
    if operating_point is None or abs(load_ratio - 1.0) <= 1e-12:
        waveforms = candidate.metadata.get("state_space_simulation_waveforms")
        artifact_paths = candidate.metadata.get("state_space_simulation_artifacts")
        result = None
        simulation = design_simulation
        if not isinstance(waveforms, dict) or not isinstance(artifact_paths, dict):
            return None
    else:
        result = simulate_ac_dc_dc_inductor_waveforms_for_load(candidate, load_ratio)
        if not result.succeeded:
            return None
        waveforms = result.waveforms
        artifact_paths = result.artifact_paths
        simulation = result.metrics

    time_s = waveforms["time_s"]
    return WaveformSet(
        time_s=time_s,
        switch_node_voltage_v=waveforms["vrect_v"],
        inductor_current_a=waveforms["iL_a"],
        capacitor_current_a=waveforms["iC_a"],
        output_voltage_v=waveforms["vdc_v"],
        operating_vin_v=float(candidate.metadata["vac_rms_v"]),
        operating_vout_v=float(simulation["vdc_avg_v"]),
        duty=1.0,
        load_ratio=load_ratio,
        switching_period_s=1.0 / float(candidate.metadata["f_line_hz"]),
        time_span_s=time_s[-1] - time_s[0] if len(time_s) > 1 else 0.0,
        inductor_current_min_a=float(simulation["il_min_a"]),
        inductor_current_max_a=float(simulation["il_peak_a"]),
        mode=str(simulation["ccm_dcm_status"]),
        switch_current_a=[],
        diode_current_a=waveforms["bridge_current_a"],
        input_source_current_a=waveforms["ig_a"],
        output_ripple_v=[float(value) - float(simulation["vdc_avg_v"]) for value in waveforms["vdc_v"]],
        notes=_waveform_notes(load_ratio, result),
        metadata={
            "ac_dc_dc_inductor_waveforms": waveforms,
            "ac_dc_dc_inductor_metrics": simulation,
            "artifact_paths": artifact_paths,
            "load_ratio": load_ratio,
        },
    )


def simulate_ac_dc_dc_inductor_waveforms_for_load(
    candidate: TopologyCandidate,
    load_ratio: float,
) -> DCInductorBridgeSimulationResult:
    """Regenerate state-space waveforms for a load ratio without changing Ldc/Cout."""

    clamped_load_ratio = _clamp_load_ratio(load_ratio)
    design_vdc_v = float(candidate.metadata.get("vout_achieved_v", candidate.vout_target))
    rload_nominal_ohm = float(candidate.metadata.get("rload_ohm", candidate.r_load_nom_ohm))
    rload_operating_ohm = _OPEN_LOAD_OHM if clamped_load_ratio <= 0.0 else rload_nominal_ohm / clamped_load_ratio
    result = simulate_ac_dc_diode_bridge_dc_inductor_filter(
        vac_rms_v=float(candidate.metadata["vac_rms_v"]),
        f_line_hz=float(candidate.metadata["f_line_hz"]),
        pout_w=max(float(candidate.pout_target) * clamped_load_ratio, 1e-12),
        diode_forward_drop_v=float(candidate.metadata["diode_forward_drop_v"]),
        ldc_h=float(candidate.metadata.get("selected_ldc_h", candidate.inductance_h)),
        cout_f=float(candidate.metadata.get("selected_cdc_f", candidate.capacitance_f)),
        rload_ohm=rload_operating_ohm,
        source_resistance_ohm=float(candidate.metadata.get("source_resistance_ohm", 0.0)),
        reactor_resistance_ohm=float(candidate.metadata.get("selected_reactor_rdc_ohm", 0.0)),
        initial_inductor_current_a=0.0 if clamped_load_ratio <= 0.0 else design_vdc_v / rload_operating_ohm,
        initial_vcap_v=design_vdc_v,
        artifact_suffix=f"load_{_load_ratio_suffix(clamped_load_ratio)}",
    )
    metrics = dict(result.metrics)
    metrics.update(
        {
            "load_ratio": clamped_load_ratio,
            "pout_operating_w": metrics.get("load_power_w", 0.0),
            "rload_used_ohm": rload_operating_ohm,
            "selected_cdc_f": float(candidate.metadata.get("selected_cdc_f", candidate.capacitance_f)),
            "selected_ldc_h": float(candidate.metadata.get("selected_ldc_h", candidate.inductance_h)),
            "no_load_open_load_approximation": clamped_load_ratio <= 0.0,
        }
    )
    notes = list(result.warnings)
    if clamped_load_ratio <= 0.0:
        notes.append("No-load waveform uses near-open-load approximation; PF is not meaningful when input real power is near zero.")
    return DCInductorBridgeSimulationResult(
        succeeded=result.succeeded,
        metrics=metrics,
        waveforms=result.waveforms,
        artifact_paths=result.artifact_paths,
        warnings=notes,
    )


def refresh_selected_hardware_candidate(
    candidate: TopologyCandidate,
    *,
    selected_cdc_f: float | None = None,
    selected_ldc_h: float | None = None,
    selected_reactor_rdc_ohm: float | None = None,
    load_ratio: float = 1.0,
) -> tuple[TopologyCandidate, DCInductorBridgeSimulationResult]:
    """Refresh electrical results using the selected capacitor and reactor hardware."""

    metadata = dict(candidate.metadata)
    if selected_cdc_f is not None and selected_cdc_f > 0.0:
        metadata["selected_cdc_f"] = float(selected_cdc_f)
    if selected_ldc_h is not None and selected_ldc_h > 0.0:
        metadata["selected_ldc_h"] = float(selected_ldc_h)
    if selected_reactor_rdc_ohm is not None and selected_reactor_rdc_ohm >= 0.0:
        metadata["selected_reactor_rdc_ohm"] = float(selected_reactor_rdc_ohm)
    provisional = replace(candidate, metadata=metadata)
    result = simulate_ac_dc_dc_inductor_waveforms_for_load(provisional, load_ratio)
    if not result.succeeded:
        return provisional, result
    metrics = dict(result.metrics)
    metadata.update(
        {
            "state_space_simulation": metrics,
            "state_space_simulation_waveforms": result.waveforms,
            "state_space_simulation_artifacts": result.artifact_paths,
            "vout_achieved_v": metrics["vdc_avg_v"],
            "iout_achieved_a": metrics["load_current_avg_a"],
            "pout_achieved_w": metrics["load_power_w"],
            "simulation_primary_vdc_avg_v": metrics["vdc_avg_v"],
            "simulation_primary_idc_a": metrics["load_current_avg_a"],
            "simulation_primary_il_avg_a": metrics["il_avg_a"],
            "simulation_primary_il_rms_a": metrics["il_rms_a"],
            "simulation_primary_il_peak_a": metrics["il_peak_a"],
            "simulation_primary_il_min_a": metrics["il_min_a"],
            "simulation_primary_delta_il_pp_a": metrics["il_ripple_pp_a"],
            "simulation_primary_vdc_ripple_pp_v": metrics["vdc_ripple_pp_v"],
            "simulation_primary_bridge_current_rms_a": metrics["bridge_current_rms_a"],
            "simulation_primary_bridge_current_peak_a": metrics["bridge_current_peak_a"],
            "simulation_primary_capacitor_current_rms_a": metrics["capacitor_current_rms_a"],
        }
    )
    refreshed = replace(
        candidate,
        vout_target=float(metrics["vdc_avg_v"]),
        iout=float(metrics["load_current_avg_a"]),
        delta_il=float(metrics["il_ripple_pp_a"]),
        delta_vo=float(metrics["vdc_ripple_pp_v"]),
        il_peak=float(metrics["il_peak_a"]),
        il_valley=float(metrics["il_min_a"]),
        output_ripple_vpp_v=float(metrics["vdc_ripple_pp_v"]),
        metadata=metadata,
    )
    return refreshed, result


def _clamp_load_ratio(value: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 1.0
    return min(max(numeric, 0.0), 1.0)


def _load_ratio_suffix(load_ratio: float) -> str:
    return f"{load_ratio:.2f}".replace(".", "p")


def _waveform_notes(load_ratio: float, result: DCInductorBridgeSimulationResult | None) -> list[str]:
    notes = ["Phase 2 state-space DC-side inductor simulation."]
    if result is not None:
        notes.extend(result.warnings)
    if load_ratio <= 0.0:
        notes.append("No-load waveform uses near-open-load approximation; PF is not meaningful when input real power is near zero.")
    return notes
