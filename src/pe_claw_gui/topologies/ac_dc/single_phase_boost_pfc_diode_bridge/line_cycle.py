"""Line-cycle helpers for the single-phase boost PFC first-pass model."""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sin, sqrt


@dataclass(frozen=True)
class BoostPFCLineCycle:
    """Sampled half-line-cycle PFC envelope."""

    theta_deg: list[float]
    v_rectified_v: list[float]
    input_current_a: list[float]
    inductor_current_avg_a: list[float]
    duty: list[float]
    delta_i_allowed_a: list[float]

    @property
    def point_count(self) -> int:
        return len(self.theta_deg)

    def as_metadata(self) -> dict[str, list[float]]:
        """Return JSON-friendly line-cycle arrays."""

        return {
            "theta_deg": self.theta_deg,
            "v_rectified_v": self.v_rectified_v,
            "input_current_a": self.input_current_a,
            "inductor_current_avg_a": self.inductor_current_avg_a,
            "duty": self.duty,
            "delta_i_allowed_a": self.delta_i_allowed_a,
        }


def describe_planned_line_cycle_model() -> tuple[str, ...]:
    """Return the planned line-cycle model boundaries for documentation/readback."""

    return (
        "Single-phase sinusoidal input current target.",
        "Diode bridge followed by boost inductor and active boost switch.",
        "First-pass average-current PFC model with sampled half-line-cycle duty/current readback.",
    )


def sample_boost_pfc_half_line_cycle(
    *,
    vac_rms_v: float,
    vdc_target_v: float,
    input_current_rms_a: float,
    ripple_current_ratio: float,
    minimum_current_fraction: float = 0.2,
    point_count: int = 181,
) -> BoostPFCLineCycle:
    """Sample rectified voltage, sinusoidal current target, and boost duty."""

    point_count = max(int(point_count), 3)
    vac_peak_v = sqrt(2.0) * vac_rms_v
    i_line_peak_a = sqrt(2.0) * input_current_rms_a
    # Define switching ripple against the rated line-current peak. Scaling the
    # allowance with instantaneous sine current makes it collapse near the
    # zero crossing and greatly oversizes the Boost inductance.
    del minimum_current_fraction  # Retained only for API compatibility.
    delta_i_design_a = max(i_line_peak_a * ripple_current_ratio, 1e-9)

    theta_deg: list[float] = []
    v_rectified_v: list[float] = []
    input_current_a: list[float] = []
    inductor_current_avg_a: list[float] = []
    duty_values: list[float] = []
    delta_i_allowed_a: list[float] = []

    for index in range(point_count):
        theta = pi * index / (point_count - 1)
        angle_deg = 180.0 * index / (point_count - 1)
        sine_value = max(sin(theta), 0.0)
        v_rec_v = vac_peak_v * sine_value
        current_a = i_line_peak_a * sine_value
        duty = min(max(1.0 - v_rec_v / max(vdc_target_v, 1e-9), 0.0), 1.0)
        delta_allowed_a = delta_i_design_a

        theta_deg.append(angle_deg)
        v_rectified_v.append(v_rec_v)
        input_current_a.append(current_a)
        inductor_current_avg_a.append(current_a)
        duty_values.append(duty)
        delta_i_allowed_a.append(delta_allowed_a)

    return BoostPFCLineCycle(
        theta_deg=theta_deg,
        v_rectified_v=v_rectified_v,
        input_current_a=input_current_a,
        inductor_current_avg_a=inductor_current_avg_a,
        duty=duty_values,
        delta_i_allowed_a=delta_i_allowed_a,
    )
