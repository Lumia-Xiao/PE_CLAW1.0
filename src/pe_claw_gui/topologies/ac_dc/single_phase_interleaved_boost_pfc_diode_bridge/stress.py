"""Phase-level and shared stress adapters for interleaved Boost PFC."""

from __future__ import annotations

from dataclasses import dataclass

from ....models.stress_result import StressMetric, StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from .waveform import generate_waveforms


@dataclass(frozen=True)
class PhaseStress:
    """Switch and Boost-diode stress for one physical interleaved phase."""

    main_switch: StressMetric
    boost_diode: StressMetric


@dataclass(frozen=True)
class InterleavedPFCStress:
    """Typed phase and shared-bridge stress readback."""

    phase_stress: dict[str, PhaseStress]
    input_bridge_rectifier: StressMetric
    shared_result: StressResult


def extract_phase_stress(
    candidate: TopologyCandidate,
    waveform_set: WaveformSet | None = None,
) -> InterleavedPFCStress:
    """Build auditable phase-level device and shared bridge stresses."""

    resolved_waveform = waveform_set or generate_waveforms(candidate)
    phase_metrics = resolved_waveform.metadata.get("phase_device_metrics")
    bridge_metrics = resolved_waveform.metadata.get("bridge_metrics")
    if not isinstance(phase_metrics, dict) or not isinstance(bridge_metrics, dict):
        raise ValueError("Interleaved Boost PFC waveform is missing phase or bridge stress metrics.")

    phase_stress: dict[str, PhaseStress] = {}
    for phase in ("phase_1", "phase_2"):
        metrics = phase_metrics.get(phase)
        if not isinstance(metrics, dict):
            raise ValueError(f"Interleaved Boost PFC waveform is missing {phase} stress metrics.")
        phase_stress[phase] = PhaseStress(
            main_switch=StressMetric(
                voltage_max_v=float(candidate.vout_target),
                current_peak_a=float(metrics["switch_current_peak_a"]),
                current_rms_a=float(metrics["switch_current_rms_a"]),
                current_avg_a=float(metrics["switch_current_avg_a"]),
            ),
            boost_diode=StressMetric(
                voltage_max_v=float(candidate.vout_target),
                current_peak_a=float(metrics["boost_diode_current_peak_a"]),
                current_rms_a=float(metrics["boost_diode_current_rms_a"]),
                current_avg_a=float(metrics["boost_diode_current_avg_a"]),
            ),
        )

    bridge_stress = StressMetric(
        voltage_max_v=float(candidate.metadata["bridge_reverse_stress_v"]),
        current_peak_a=float(bridge_metrics["input_bridge_current_peak_a"]),
        current_rms_a=float(bridge_metrics["input_bridge_current_rms_a"]),
        current_avg_a=float(bridge_metrics["input_bridge_current_avg_a"]),
    )
    shared_result = StressResult(
        switch=phase_stress["phase_1"].main_switch,
        rectifier=phase_stress["phase_1"].boost_diode,
        notes=[
            "Shared switch and rectifier slots represent phase_1; phase_1 and phase_2 are equal under ideal sharing.",
            "Input bridge stress is returned separately by the interleaved phase-stress adapter.",
        ],
    )
    return InterleavedPFCStress(
        phase_stress=phase_stress,
        input_bridge_rectifier=bridge_stress,
        shared_result=shared_result,
    )


def extract_stress(
    candidate: TopologyCandidate,
    waveform_set: WaveformSet | None = None,
) -> StressResult:
    """Return the compatibility StressResult with representative per-phase slots."""

    return extract_phase_stress(candidate, waveform_set=waveform_set).shared_result
