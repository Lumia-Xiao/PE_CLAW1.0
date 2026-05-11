"""Mode scheduling and operating-state resolution for the four-switch Buck-Boost topology."""

from __future__ import annotations

from dataclasses import dataclass

from ....models.operating_point import OperatingPoint
from ...base.candidate import TopologyCandidate

PURE_BUCK = "PURE_BUCK"
EXTENDED_BUCK = "EXTENDED_BUCK"
EXTENDED_BOOST = "EXTENDED_BOOST"
PURE_BOOST = "PURE_BOOST"


def _clamp_ratio(value: float) -> float:
    return min(max(value, 1e-6), 0.999999)


@dataclass(frozen=True)
class SegmentDefinition:
    """One piecewise-linear segment of the simplified switching period."""

    name: str
    duration_ratio: float
    inductor_voltage_v: float
    switch_node_voltage_v: float
    primary_path_active: bool
    secondary_path_active: bool
    output_path_active: bool
    input_source_active: bool


@dataclass(frozen=True)
class FourSwitchBuckBoostOperatingState:
    """Resolved operating state used for four-switch Buck-Boost waveforms."""

    vin: float
    vout: float
    load_ratio: float
    iout: float
    duty_clamp: float
    transition_band_ratio: float
    d2: float
    d3: float
    mode: str
    switching_period_s: float
    iL_avg: float
    delta_il: float
    il_min: float
    il_max: float


def classify_mode(vin: float, vout: float, transition_band_ratio: float) -> str:
    """Classify the requested operating point into one of the four scheduler modes."""
    if vin >= vout * (1.0 + transition_band_ratio):
        return PURE_BUCK
    if vout < vin < vout * (1.0 + transition_band_ratio):
        return EXTENDED_BUCK
    if vout * (1.0 - transition_band_ratio) < vin <= vout:
        return EXTENDED_BOOST
    return PURE_BOOST


def compute_duties(vin: float, vout: float, mode: str, duty_clamp: float) -> tuple[float, float]:
    """Compute simplified four-mode duties for the requested operating point."""
    if mode == PURE_BUCK:
        return _clamp_ratio(1.0 - vout / vin), 0.0
    if mode == EXTENDED_BUCK:
        return _clamp_ratio(1.0 - (1.0 - duty_clamp) * vout / vin), duty_clamp
    if mode == EXTENDED_BOOST:
        return duty_clamp, _clamp_ratio(1.0 - (1.0 - duty_clamp) * vin / vout)
    if mode == PURE_BOOST:
        return 0.0, _clamp_ratio(1.0 - vin / vout)
    raise ValueError(f"Unsupported four-mode operating state: {mode}")


def build_segment_plan(vin: float, vout: float, mode: str, d2: float, d3: float) -> tuple[SegmentDefinition, ...]:
    """Build a waveform-friendly piecewise segment plan for one switching period."""
    buck_transfer_ratio = max(1.0 - d2, 0.0)
    boost_transfer_ratio = max(1.0 - d3, 0.0)

    if mode == PURE_BUCK:
        return (
            SegmentDefinition("buck_active", buck_transfer_ratio, vin - vout, vin, True, False, True, True),
            SegmentDefinition("buck_freewheel", d2, -vout, 0.0, False, True, True, False),
        )

    if mode == PURE_BOOST:
        return (
            SegmentDefinition("boost_charge", d3, vin, 0.0, True, False, False, True),
            SegmentDefinition("boost_transfer", boost_transfer_ratio, vin - vout, vout, False, True, True, True),
        )

    if mode == EXTENDED_BUCK:
        positive_half = 0.5 * buck_transfer_ratio
        negative_ratio = max(boost_transfer_ratio - buck_transfer_ratio, 0.0)
        zero_ratio = max(1.0 - boost_transfer_ratio, 0.0)
        return (
            SegmentDefinition("extended_buck_active", positive_half, vin - vout, vin, True, False, True, True),
            SegmentDefinition("extended_buck_common", positive_half, vin - vout, vin, True, True, True, True),
            SegmentDefinition("extended_buck_clamped", negative_ratio, -vout, 0.0, False, True, True, False),
            SegmentDefinition("extended_buck_recovery", zero_ratio, 0.0, 0.0, False, False, False, False),
        )

    positive_half = 0.5 * max(buck_transfer_ratio - boost_transfer_ratio, 0.0)
    negative_ratio = boost_transfer_ratio
    zero_ratio = max(1.0 - buck_transfer_ratio, 0.0)
    return (
        SegmentDefinition("extended_boost_charge", positive_half, vin, 0.0, True, False, False, True),
        SegmentDefinition("extended_boost_common", positive_half, vin, 0.0, True, True, False, True),
        SegmentDefinition("extended_boost_transfer", negative_ratio, vin - vout, vout, False, True, True, True),
        SegmentDefinition("extended_boost_recovery", zero_ratio, 0.0, 0.0, False, False, False, False),
    )


def estimate_delta_il(inductance_h: float, switching_period_s: float, segments: tuple[SegmentDefinition, ...]) -> float:
    """Estimate ripple from the total positive inductor-voltage segments."""
    positive_volt_seconds = sum(
        max(segment.inductor_voltage_v, 0.0) * segment.duration_ratio * switching_period_s
        for segment in segments
    )
    return positive_volt_seconds / max(inductance_h, 1e-12)


def build_operating_state(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
) -> FourSwitchBuckBoostOperatingState:
    """Resolve the simplified four-mode operating state for the requested point."""
    vin = operating_point.vin_v if operating_point is not None else candidate.vin_nom
    load_ratio = operating_point.load_ratio if operating_point is not None else 1.0
    if vin <= 0.0:
        raise ValueError("Operating Vin must be positive.")

    vout = candidate.vout_target
    duty_clamp = float(candidate.metadata.get("duty_clamp", 0.10))
    transition_band_ratio = float(candidate.metadata.get("transition_band_ratio", 0.10))
    mode = classify_mode(vin, vout, transition_band_ratio)
    d2, d3 = compute_duties(vin, vout, mode, duty_clamp)
    switching_period_s = 1.0 / candidate.fs_hz
    iout = candidate.iout * max(load_ratio, 0.0)

    if mode in {PURE_BUCK, EXTENDED_BUCK}:
        i_l_avg = iout
    else:
        i_l_avg = iout / max(1.0 - d3, 1e-6)

    segments = build_segment_plan(vin, vout, mode, d2, d3)
    delta_il = estimate_delta_il(candidate.inductance_h, switching_period_s, segments)
    il_min = i_l_avg - 0.5 * delta_il
    il_max = i_l_avg + 0.5 * delta_il

    return FourSwitchBuckBoostOperatingState(
        vin=vin,
        vout=vout,
        load_ratio=max(load_ratio, 0.0),
        iout=iout,
        duty_clamp=duty_clamp,
        transition_band_ratio=transition_band_ratio,
        d2=d2,
        d3=d3,
        mode=mode,
        switching_period_s=switching_period_s,
        iL_avg=i_l_avg,
        delta_il=delta_il,
        il_min=il_min,
        il_max=il_max,
    )


__all__ = [
    "EXTENDED_BOOST",
    "EXTENDED_BUCK",
    "PURE_BOOST",
    "PURE_BUCK",
    "FourSwitchBuckBoostOperatingState",
    "SegmentDefinition",
    "build_operating_state",
    "build_segment_plan",
    "classify_mode",
    "compute_duties",
    "estimate_delta_il",
]
