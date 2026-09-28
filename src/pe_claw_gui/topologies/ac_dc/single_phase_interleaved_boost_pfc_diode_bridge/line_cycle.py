"""Rectified line-cycle sampling for the independent two-phase PFC core."""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sin, sqrt


@dataclass(frozen=True)
class InterleavedBoostPFCLineCycle:
    """Sampled total and per-phase CCM PFC envelopes."""

    theta_deg: list[float]
    v_rectified_v: list[float]
    total_input_current_a: list[float]
    phase_current_a: list[float]
    duty: list[float]
    delta_i_allowed_a: list[float]

    @property
    def point_count(self) -> int:
        return len(self.theta_deg)

    def as_metadata(self) -> dict[str, list[float]]:
        """Return JSON-friendly total and per-phase arrays."""

        return {
            "theta_deg": list(self.theta_deg),
            "v_rectified_v": list(self.v_rectified_v),
            "total_input_current_a": list(self.total_input_current_a),
            "phase_current_a": list(self.phase_current_a),
            "duty": list(self.duty),
            "delta_i_allowed_a": list(self.delta_i_allowed_a),
        }


def describe_line_cycle_model() -> tuple[str, ...]:
    """Return the explicit first-pass line-cycle model boundaries."""

    return (
        "Single-phase diode bridge followed by two identical Boost phases.",
        "Total input current is a sinusoidal rectified-envelope target.",
        "Ideal equal sharing assigns one half of the total current to each phase.",
        "CCM duty is D(theta) = 1 - Vrect(theta)/Vdc, clamped to [0, 1].",
    )


def sample_interleaved_boost_pfc_line_cycle(
    *,
    vac_rms_v: float,
    vdc_target_v: float,
    input_current_rms_a: float,
    ripple_current_ratio: float,
    phase_count: int = 2,
    point_count: int = 181,
) -> InterleavedBoostPFCLineCycle:
    """Sample a rectified half-line cycle and split its current equally."""

    if phase_count != 2:
        raise ValueError("The first-pass interleaved Boost PFC core requires exactly two phases.")
    if vac_rms_v <= 0.0 or vdc_target_v <= 0.0 or input_current_rms_a <= 0.0:
        raise ValueError("Line-cycle voltage, bus voltage, and current must be positive.")
    if ripple_current_ratio <= 0.0:
        raise ValueError("Inductor current ripple ratio must be positive.")

    point_count = max(int(point_count), 3)
    vac_peak_v = sqrt(2.0) * vac_rms_v
    total_current_peak_a = sqrt(2.0) * input_current_rms_a
    phase_current_peak_a = total_current_peak_a / phase_count
    delta_i_design_a = phase_current_peak_a * ripple_current_ratio

    theta_deg: list[float] = []
    v_rectified_v: list[float] = []
    total_input_current_a: list[float] = []
    phase_current_a: list[float] = []
    duty_values: list[float] = []
    delta_i_allowed_a: list[float] = []
    for index in range(point_count):
        theta = pi * index / (point_count - 1)
        sine_value = max(sin(theta), 0.0)
        v_rectified = vac_peak_v * sine_value
        total_current = total_current_peak_a * sine_value
        duty = min(max(1.0 - v_rectified / max(vdc_target_v, 1e-12), 0.0), 1.0)

        theta_deg.append(180.0 * index / (point_count - 1))
        v_rectified_v.append(v_rectified)
        total_input_current_a.append(total_current)
        phase_current_a.append(total_current / phase_count)
        duty_values.append(duty)
        delta_i_allowed_a.append(delta_i_design_a)

    return InterleavedBoostPFCLineCycle(
        theta_deg=theta_deg,
        v_rectified_v=v_rectified_v,
        total_input_current_a=total_input_current_a,
        phase_current_a=phase_current_a,
        duty=duty_values,
        delta_i_allowed_a=delta_i_allowed_a,
    )
