"""LLC synchronous-rectifier stress entry point."""

from __future__ import annotations

from ....models.stress_result import StressMetric, StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from .input_schema import SYNCHRONOUS_RECTIFIER_TIMING_MODE_INPUT_KEY
from .stress_readback import build_llc_sr_stress_readback


def extract_stress(
    candidate: TopologyCandidate,
    waveform_set: WaveformSet | None = None,
) -> StressResult:
    """Build first-pass FHA-level stress estimates for LLC SR roles."""

    llc_fha = candidate.metadata.get("llc_fha", {})
    if not isinstance(llc_fha, dict):
        raise ValueError("LLC SR stress extraction requires llc_fha candidate metadata.")
    timing_mode = str(
        candidate.metadata.get("llc_sr", {})
        .get("timing_readback", {})
        .get("timing_mode", llc_fha.get(SYNCHRONOUS_RECTIFIER_TIMING_MODE_INPUT_KEY, "ideal_complementary_first_pass"))
        if isinstance(candidate.metadata.get("llc_sr", {}), dict)
        else "ideal_complementary_first_pass"
    )
    stress_readback = build_llc_sr_stress_readback(llc_fha, timing_mode=timing_mode)
    role_stresses = stress_readback["role_stresses"]
    primary = role_stresses["main_switch"]
    secondary = role_stresses["secondary_sync_switch"]
    notes = [
        "First-pass FHA sinusoidal current stress estimates are used for LLC SR semiconductor screening.",
        "Primary switch stress maps to main_switch; secondary rectifier stress maps to secondary_sync_switch.",
        "No rectifier_diode role is required for the full-bridge synchronous-rectifier LLC MVP.",
        "SR stress is remapped from diode LLC FHA current estimates; reverse conduction, deadtime overlap, Coss/Eoss, and current sharing are not signed off.",
    ]
    return StressResult(
        switch=StressMetric(
            voltage_max_v=_float_or_default(primary.get("v_block_v"), candidate.vin_max),
            current_peak_a=_float_or_default(primary.get("i_peak_a"), candidate.iout),
            current_rms_a=_float_or_none(primary.get("i_rms_a")),
            current_avg_a=_float_or_none(primary.get("i_avg_a")),
        ),
        rectifier=StressMetric(
            voltage_max_v=_float_or_default(secondary.get("v_block_v"), candidate.vout_target),
            current_peak_a=_float_or_default(secondary.get("i_peak_a"), candidate.iout),
            current_rms_a=_float_or_none(secondary.get("i_rms_a")),
            current_avg_a=_float_or_none(secondary.get("i_avg_a")),
        ),
        notes=notes,
    )


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _float_or_default(value: object, fallback: float) -> float:
    if value is None:
        return fallback
    return float(value)
