"""Stress readback for the single-phase boost PFC topology."""

from __future__ import annotations

from ....models.stress_result import StressMetric, StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate


def extract_stress(
    candidate: TopologyCandidate,
    waveform_set: WaveformSet | None = None,
) -> StressResult:
    """Return first-pass boost switch and boost diode stress estimates."""

    metadata = candidate.metadata
    waveform_metadata = waveform_set.metadata if waveform_set is not None else {}
    vdc_target_v = float(metadata["vdc_target_v"])
    switch_current_rms_a = _metadata_float(
        waveform_metadata,
        "sizing_boost_switch_current_rms_a",
        fallback=candidate.il_peak * max(candidate.duty_nom, 0.0) ** 0.5,
    )
    switch_current_avg_a = _metadata_float(
        waveform_metadata,
        "sizing_boost_switch_current_avg_a",
        fallback=candidate.iout,
    )
    diode_current_rms_a = _metadata_float(
        waveform_metadata,
        "sizing_boost_diode_current_rms_a",
        fallback=max(candidate.iout, 0.0),
    )
    diode_current_avg_a = _metadata_float(
        waveform_metadata,
        "sizing_boost_diode_current_avg_a",
        fallback=candidate.iout,
    )
    bridge_rms_a = _metadata_float(
        waveform_metadata,
        "sizing_bridge_rectifier_current_rms_a",
        fallback=float(metadata["sizing_input_current_rms_a"]),
    )
    bridge_peak_a = _metadata_float(
        waveform_metadata,
        "sizing_bridge_rectifier_current_peak_a",
        fallback=float(metadata["sizing_input_current_peak_a"]),
    )

    return StressResult(
        switch=StressMetric(
            voltage_max_v=vdc_target_v,
            current_peak_a=_metadata_float(
                waveform_metadata,
                "sizing_boost_switch_current_peak_a",
                fallback=candidate.il_peak,
            ),
            current_rms_a=switch_current_rms_a,
            current_avg_a=switch_current_avg_a,
        ),
        rectifier=StressMetric(
            voltage_max_v=vdc_target_v,
            current_peak_a=_metadata_float(
                waveform_metadata,
                "sizing_boost_diode_current_peak_a",
                fallback=candidate.il_peak,
            ),
            current_rms_a=diode_current_rms_a,
            current_avg_a=diode_current_avg_a,
        ),
        notes=[
            "Boost PFC stress maps switch=boost switch and rectifier=independent boost diode.",
            "Boost switch and boost diode RMS currents include line-cycle integrated triangular switching ripple.",
            "Boost diode average current is derived from the off-state conduction interval and should equal DC output current within sampling tolerance.",
            (
                "Input bridge rectifier first-pass stress readback: "
                f"VRRM ~= {float(metadata['vac_peak_max_v']):.6g} V, "
                f"Irms ~= {bridge_rms_a:.6g} A, Ipk ~= {bridge_peak_a:.6g} A."
            ),
            "Input bridge rectifier selection is wired through the AC-DC bridge-rectifier pipeline.",
        ],
    )


def _metadata_float(metadata: dict[str, object], key: str, *, fallback: float) -> float:
    value = metadata.get(key)
    if value is None:
        return fallback
    return float(value)
