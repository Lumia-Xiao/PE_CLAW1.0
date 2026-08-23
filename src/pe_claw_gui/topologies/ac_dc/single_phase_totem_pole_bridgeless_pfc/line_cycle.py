"""Line-cycle helpers for the single-phase Totem-Pole PFC first-pass model."""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sin, sqrt


@dataclass(frozen=True)
class TotemPolePFCLineCycle:
    """Sampled full-line-cycle Totem-Pole PFC envelope."""

    theta_deg: list[float]
    input_voltage_v: list[float]
    v_abs_v: list[float]
    input_current_a: list[float]
    i_abs_a: list[float]
    inductor_current_avg_a: list[float]
    duty: list[float]
    delta_i_allowed_a: list[float]
    line_polarity: list[str]

    @property
    def point_count(self) -> int:
        return len(self.theta_deg)

    def as_metadata(self) -> dict[str, list[float] | list[str]]:
        """Return JSON-friendly full-line-cycle arrays."""

        return {
            "theta_deg": self.theta_deg,
            "input_voltage_v": self.input_voltage_v,
            "v_abs_v": self.v_abs_v,
            "input_current_a": self.input_current_a,
            "i_abs_a": self.i_abs_a,
            "inductor_current_avg_a": self.inductor_current_avg_a,
            "duty": self.duty,
            "delta_i_allowed_a": self.delta_i_allowed_a,
            "line_polarity": self.line_polarity,
        }


def describe_planned_line_cycle_model() -> tuple[str, ...]:
    """Return the planned Totem-Pole PFC line-cycle model boundaries."""

    return (
        "Single-phase sinusoidal input-current target.",
        "Bridgeless Totem-Pole leg with high-frequency and line-frequency switch pairs.",
        "First-pass full-line-cycle average-current PFC model; detailed zero-crossing control is out of scope.",
    )


def sample_totem_pole_pfc_line_cycle(
    *,
    vac_rms_v: float,
    vdc_target_v: float,
    input_current_rms_a: float,
    ripple_current_ratio: float,
    minimum_current_fraction: float = 0.2,
    point_count: int = 361,
) -> TotemPolePFCLineCycle:
    """Sample signed line voltage/current plus absolute boost-PFC duty envelope."""

    point_count = max(int(point_count), 5)
    vac_peak_v = sqrt(2.0) * vac_rms_v
    i_line_peak_a = sqrt(2.0) * input_current_rms_a
    min_delta_current_a = max(i_line_peak_a * ripple_current_ratio * minimum_current_fraction, 1e-9)

    theta_deg: list[float] = []
    input_voltage_v: list[float] = []
    v_abs_v: list[float] = []
    input_current_a: list[float] = []
    i_abs_a: list[float] = []
    inductor_current_avg_a: list[float] = []
    duty_values: list[float] = []
    delta_i_allowed_a: list[float] = []
    line_polarity: list[str] = []

    for index in range(point_count):
        theta = 2.0 * pi * index / (point_count - 1)
        angle_deg = 360.0 * index / (point_count - 1)
        sine_value = sin(theta)
        v_ac_v = vac_peak_v * sine_value
        current_a = i_line_peak_a * sine_value
        abs_voltage_v = abs(v_ac_v)
        abs_current_a = abs(current_a)
        duty = min(max(1.0 - abs_voltage_v / max(vdc_target_v, 1e-9), 0.0), 1.0)
        delta_allowed_a = max(abs_current_a * ripple_current_ratio, min_delta_current_a)

        if v_ac_v > 1e-9:
            polarity = "positive"
        elif v_ac_v < -1e-9:
            polarity = "negative"
        else:
            polarity = "zero_crossing"

        theta_deg.append(angle_deg)
        input_voltage_v.append(v_ac_v)
        v_abs_v.append(abs_voltage_v)
        input_current_a.append(current_a)
        i_abs_a.append(abs_current_a)
        inductor_current_avg_a.append(abs_current_a)
        duty_values.append(duty)
        delta_i_allowed_a.append(delta_allowed_a)
        line_polarity.append(polarity)

    return TotemPolePFCLineCycle(
        theta_deg=theta_deg,
        input_voltage_v=input_voltage_v,
        v_abs_v=v_abs_v,
        input_current_a=input_current_a,
        i_abs_a=i_abs_a,
        inductor_current_avg_a=inductor_current_avg_a,
        duty=duty_values,
        delta_i_allowed_a=delta_i_allowed_a,
        line_polarity=line_polarity,
    )
