"""Waveforms for the Phase 2 AC-DC rectifier pulse-current estimate."""

from __future__ import annotations

from dataclasses import replace

from ....models.operating_point import OperatingPoint
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from .simulation import DiodeBridgeSimulationResult, simulate_diode_bridge_capacitor_input

_OPEN_LOAD_OHM = 1e12


def generate_waveforms(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
) -> WaveformSet | None:
    """Return compact final-cycle waveforms from the stored pulse simulation artifact."""

    design_simulation = candidate.metadata.get("pulse_simulation")
    if not isinstance(design_simulation, dict) or not design_simulation.get("simulation_succeeded"):
        return None

    load_ratio = _clamp_load_ratio(operating_point.load_ratio if operating_point is not None else 1.0)
    if operating_point is None or abs(load_ratio - 1.0) <= 1e-12:
        waveforms = candidate.metadata.get("pulse_simulation_waveforms")
        artifact_paths = candidate.metadata.get("pulse_simulation_artifacts")
        result = None
        simulation = design_simulation
        if not isinstance(waveforms, dict) or not isinstance(artifact_paths, dict):
            return None
    else:
        result = simulate_ac_dc_waveforms_for_load(candidate, load_ratio)
        if not result.succeeded:
            return None
        waveforms = result.waveforms
        artifact_paths = result.artifact_paths
        simulation = result.metrics

    time_s = waveforms["time_s"]
    return WaveformSet(
        time_s=time_s,
        switch_node_voltage_v=waveforms["vrect_v"],
        inductor_current_a=waveforms["ibridge_a"],
        capacitor_current_a=waveforms["icap_a"],
        output_voltage_v=waveforms["vdc_v"],
        operating_vin_v=float(candidate.metadata["vac_rms_v"]),
        operating_vout_v=float(simulation["vdc_avg_v"]),
        duty=float(simulation["conduction_duty"]),
        load_ratio=load_ratio,
        switching_period_s=1.0 / float(candidate.metadata["f_line_hz"]),
        time_span_s=time_s[-1] - time_s[0] if len(time_s) > 1 else 0.0,
        inductor_current_min_a=min(waveforms["ibridge_a"]),
        inductor_current_max_a=max(waveforms["ibridge_a"]),
        mode="Rs pulse-current",
        switch_current_a=[],
        diode_current_a=waveforms["ibridge_a"],
        input_source_current_a=waveforms["iac_a"],
        notes=_waveform_notes(load_ratio, result),
        metadata={
            "ac_dc_rectifier_waveforms": waveforms,
            "ac_dc_rectifier_metrics": simulation,
            "artifact_paths": artifact_paths,
            "load_ratio": load_ratio,
        },
    )


def simulate_ac_dc_waveforms_for_load(candidate: TopologyCandidate, load_ratio: float) -> DiodeBridgeSimulationResult:
    """Regenerate AC-DC waveforms for a load ratio without changing design Cdc."""

    clamped_load_ratio = _clamp_load_ratio(load_ratio)
    design_vdc_v = float(candidate.metadata["vdc_est_v"])
    pout_nom_w = float(candidate.metadata.get("pout_request_w", candidate.pout_target))
    pout_op_w = pout_nom_w * clamped_load_ratio
    if clamped_load_ratio <= 0.0:
        rload_ohm = _OPEN_LOAD_OHM
    else:
        nominal_rload_ohm = float(candidate.metadata.get("rload_ohm", candidate.r_load_nom_ohm))
        rload_ohm = nominal_rload_ohm / clamped_load_ratio

    result = simulate_diode_bridge_capacitor_input(
        vac_rms_v=float(candidate.metadata["vac_rms_v"]),
        f_line_hz=float(candidate.metadata["f_line_hz"]),
        pout_w=max(pout_op_w, 1e-12),
        diode_forward_drop_v=float(candidate.metadata["diode_forward_drop_v"]),
        source_resistance_ohm=float(candidate.metadata["source_resistance_ohm"]),
        cdc_f=float(candidate.metadata.get("selected_cdc_f", candidate.metadata["cdc_required_f"])),
        rload_ohm=rload_ohm,
        initial_vcap_v=design_vdc_v,
        artifact_suffix=f"load_{_load_ratio_suffix(clamped_load_ratio)}",
    )
    metrics = dict(result.metrics)
    metrics.update(
        {
            "load_ratio": clamped_load_ratio,
            "pout_requested_operating_w": pout_op_w,
            "pout_operating_w": metrics.get("output_power_w"),
            "no_load_open_load_approximation": clamped_load_ratio <= 0.0,
        }
    )
    notes = list(result.warnings)
    if clamped_load_ratio <= 0.0:
        notes.append("No-load waveform uses near-open-load approximation; PF is not meaningful when input real power is near zero.")
    return DiodeBridgeSimulationResult(
        succeeded=result.succeeded,
        metrics=metrics,
        waveforms=result.waveforms,
        artifact_paths=result.artifact_paths,
        warnings=notes,
    )


def refresh_selected_capacitor_candidate(
    candidate: TopologyCandidate,
    selected_cdc_f: float,
    *,
    load_ratio: float = 1.0,
) -> tuple[TopologyCandidate, DiodeBridgeSimulationResult]:
    """Re-run the rectifier at the selected hardware capacitor and fixed load."""

    if selected_cdc_f <= 0.0:
        raise ValueError("Selected DC-link capacitance must be positive.")
    nominal_rload_ohm = float(candidate.metadata.get("rload_ohm", candidate.r_load_nom_ohm))
    clamped_load_ratio = _clamp_load_ratio(load_ratio)
    rload_ohm = _OPEN_LOAD_OHM if clamped_load_ratio <= 0.0 else nominal_rload_ohm / clamped_load_ratio
    result = simulate_diode_bridge_capacitor_input(
        vac_rms_v=float(candidate.metadata["vac_rms_v"]),
        f_line_hz=float(candidate.metadata["f_line_hz"]),
        pout_w=max(float(candidate.metadata.get("pout_request_w", candidate.pout_target)), 1e-12),
        diode_forward_drop_v=float(candidate.metadata["diode_forward_drop_v"]),
        source_resistance_ohm=float(candidate.metadata["source_resistance_ohm"]),
        cdc_f=selected_cdc_f,
        rload_ohm=rload_ohm,
        initial_vcap_v=float(candidate.metadata["vdc_est_v"]),
        artifact_suffix=f"selected_load_{_load_ratio_suffix(clamped_load_ratio)}",
    )
    metrics = dict(result.metrics)
    metrics.update(
        {
            "selected_cdc_f": selected_cdc_f,
            "load_ratio": _clamp_load_ratio(load_ratio),
            "pout_operating_w": metrics.get("output_power_w"),
            "ripple_definition": "peak_to_peak",
            "ripple_measurement_window": "final_settled_line_cycle",
            "ripple_measurement_cycles": 1,
        }
    )
    metadata = {
        **candidate.metadata,
        "selected_cdc_f": selected_cdc_f,
        "pulse_simulation": metrics,
        "pulse_simulation_waveforms": result.waveforms,
        "pulse_simulation_artifacts": result.artifact_paths,
        "pulse_simulation_warnings": result.warnings,
        "selected_operating_point": metrics,
    }
    refreshed = replace(candidate, metadata=metadata)
    return refreshed, result


def _clamp_load_ratio(value: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 1.0
    return min(max(numeric, 0.0), 1.0)


def _load_ratio_suffix(load_ratio: float) -> str:
    return f"{load_ratio:.2f}".replace(".", "p")


def _waveform_notes(load_ratio: float, result: DiodeBridgeSimulationResult | None) -> list[str]:
    notes = ["Phase 2 Rs-based first-pass waveform simulation."]
    if result is not None:
        notes.extend(result.warnings)
    if load_ratio <= 0.0:
        notes.append("No-load waveform uses near-open-load approximation; PF is not meaningful when input real power is near zero.")
    return notes
