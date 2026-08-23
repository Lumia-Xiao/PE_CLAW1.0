"""Stress readback for the single-phase Totem-Pole PFC topology."""

from __future__ import annotations

from ....models.stress_result import StressMetric, StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate


def extract_stress(
    candidate: TopologyCandidate,
    waveform_set: WaveformSet | None = None,
) -> StressResult:
    """Return first-pass high-frequency and line-frequency switch stress estimates."""

    metadata = candidate.metadata
    waveform_metadata = waveform_set.metadata if waveform_set is not None else {}
    vdc_target_v = float(metadata["vdc_target_v"])
    hf_current_rms_a = _metadata_float(
        waveform_metadata,
        "sizing_hf_switch_device_current_rms_a",
        fallback=candidate.il_peak * max(candidate.duty_nom, 0.0) ** 0.5,
    )
    hf_current_avg_a = _metadata_float(
        waveform_metadata,
        "sizing_hf_switch_device_current_avg_a",
        fallback=candidate.iout,
    )
    lf_current_rms_a = _metadata_float(
        waveform_metadata,
        "sizing_lf_switch_device_current_rms_a",
        fallback=float(metadata["i_line_rms_a"]) / 2.0**0.5,
    )
    lf_current_avg_a = _metadata_float(
        waveform_metadata,
        "sizing_lf_switch_device_current_avg_a",
        fallback=float(metadata["i_line_peak_a"]) / 3.141592653589793,
    )

    return StressResult(
        switch=StressMetric(
            voltage_max_v=vdc_target_v,
            current_peak_a=candidate.il_peak,
            current_rms_a=hf_current_rms_a,
            current_avg_a=hf_current_avg_a,
        ),
        rectifier=StressMetric(
            voltage_max_v=vdc_target_v,
            current_peak_a=candidate.il_peak,
            current_rms_a=lf_current_rms_a,
            current_avg_a=lf_current_avg_a,
        ),
        notes=[
            "Totem-Pole PFC stress maps switch=high-frequency Totem-Pole switch pair.",
            "Totem-Pole PFC stress maps rectifier compatibility field=line-frequency synchronous switch pair.",
            "The line-frequency synchronous switch is not a rectifier diode or boost diode.",
            "HF/LF switch currents are first-pass full-line-cycle proxies; deadtime and reverse-conduction stress are pending.",
        ],
    )


def _metadata_float(metadata: dict[str, object], key: str, *, fallback: float) -> float:
    value = metadata.get(key)
    if value is None:
        return fallback
    return float(value)
