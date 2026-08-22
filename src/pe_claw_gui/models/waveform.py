"""Waveform result model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WaveformSet:
    """Steady-state waveform bundle for the active topology.

    `diode_current_a` may also be used as a compatibility placeholder for the
    secondary freewheel-path current when that path is not literally a diode.
    """

    time_s: list[float]
    switch_node_voltage_v: list[float]
    inductor_current_a: list[float]
    capacitor_current_a: list[float]
    output_voltage_v: list[float]
    operating_vin_v: float
    operating_vout_v: float
    duty: float
    load_ratio: float
    switching_period_s: float
    time_span_s: float
    inductor_current_min_a: float
    inductor_current_max_a: float
    mode: str = "CCM"
    switch_current_a: list[float] = field(default_factory=list)
    diode_current_a: list[float] = field(default_factory=list)
    input_source_current_a: list[float] = field(default_factory=list)
    inductor_voltage_v: list[float] = field(default_factory=list)
    vox_voltage_v: list[float] = field(default_factory=list)
    output_ripple_v: list[float] = field(default_factory=list)
    gate_s1: list[float] = field(default_factory=list)
    gate_s2: list[float] = field(default_factory=list)
    gate_s3: list[float] = field(default_factory=list)
    gate_s4: list[float] = field(default_factory=list)
    t_zero_current_s: float | None = None
    notes: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)
