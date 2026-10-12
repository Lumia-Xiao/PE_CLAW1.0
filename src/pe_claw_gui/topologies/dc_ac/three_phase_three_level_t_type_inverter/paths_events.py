"""Ideal IGBT-reference conduction and commutation for a common-emitter T-type.

Negative local current denotes the antiparallel diode reference path. This
decomposition does not establish a MOSFET third-quadrant model or event energy.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .topology_contract import CONVENTIONAL_T_TYPE_CONTRACT, PHASES


ROLES = CONVENTIONAL_T_TYPE_CONTRACT.gate_order
STATE_NAMES = {1: "P", 0: "O", -1: "N"}


class IllegalTransitionError(ValueError):
    """A solved sequence violated the T-type adjacent-level contract."""


def state_name(state: float) -> str:
    if state not in STATE_NAMES:
        raise ValueError(f"T-type illegal state {state!r}; expected P/O/N as +1/0/-1.")
    return STATE_NAMES[state]


def gate_vector(state: float) -> tuple[int, int, int, int]:
    return CONVENTIONAL_T_TYPE_CONTRACT.gate_states[state_name(state)]


@dataclass(frozen=True)
class PositionCurrent:
    """One instantaneous C-to-E current and its IGBT reference decomposition."""

    signed_a: float

    @property
    def channel_a(self) -> float:
        return max(self.signed_a, 0.0)

    @property
    def diode_a(self) -> float:
        return max(-self.signed_a, 0.0)

    @property
    def path(self) -> str:
        return "channel" if self.signed_a > 0 else "antiparallel_diode" if self.signed_a < 0 else "no_current"


def conduction_currents(state: float, phase_current_a: float) -> dict[str, PositionCurrent]:
    """Apply circuit KCL in each stable state, independent of gate-enabled count."""

    name = state_name(state)
    if not math.isfinite(phase_current_a):
        raise ValueError("T-type phase current must be finite.")
    values = {role: 0.0 for role in ROLES}
    if name == "P":
        values["QP"] = phase_current_a
    elif name == "N":
        values["QN"] = -phase_current_a
    else:
        values["QA"] = -phase_current_a
        values["QO"] = phase_current_a
    return {role: PositionCurrent(value) for role, value in values.items()}


def blocking_voltages(state: float, vdc_v: float) -> dict[str, float]:
    """Stable-state terminal voltage magnitudes for the balanced ideal bus."""

    name = state_name(state)
    if not math.isfinite(vdc_v) or vdc_v <= 0:
        raise ValueError("T-type event bus voltage must be finite and positive.")
    half = vdc_v / 2
    values = {"P": (0, vdc_v, half, 0), "O": (half, half, 0, 0), "N": (vdc_v, 0, 0, half)}
    return dict(zip(ROLES, values[name], strict=True))


def build_positions(phases: dict[str, dict[str, object]], vdc_v: float) -> dict[str, dict[str, object]]:
    """Produce all 12 sampled current/voltage paths on the waveform time axis."""

    positions = {}
    for phase in PHASES:
        states = phases[phase]["state"]
        currents = phases[phase]["current_a"]
        samples = [conduction_currents(state, current) for state, current in zip(states, currents, strict=True)]
        volts = [blocking_voltages(state, vdc_v) for state in states]
        for role in ROLES:
            positions[f"{phase}_{role}"] = {
                "phase": phase,
                "role": "t_type_main_switch" if role in {"QP", "QN"} else "t_type_midpoint_switch",
                "current_positive_direction": "collector_to_emitter_reference",
                "signed_current_a": [sample[role].signed_a for sample in samples],
                "channel_current_a": [sample[role].channel_a for sample in samples],
                "antiparallel_diode_current_a": [sample[role].diode_a for sample in samples],
                "reference_path": [sample[role].path for sample in samples],
                "static_blocking_voltage_v": [value[role] for value in volts],
                "reference_model": "ideal_igbt_with_antiparallel_diode",
            }
    return positions


def commutation_event(
    *, phase: str, from_state: float, to_state: float, time_s: float,
    phase_current_a: float, vdc_v: float,
) -> dict[str, object]:
    """Describe one adjacent-level transition; energy and ZVS are unavailable."""

    before_name, after_name = state_name(from_state), state_name(to_state)
    if phase not in PHASES or not math.isfinite(time_s) or time_s < 0:
        raise ValueError("T-type event requires a valid phase and finite non-negative time.")
    if abs(from_state - to_state) != 1:
        raise IllegalTransitionError(
            f"T-type illegal transition {before_name}->{after_name} at {time_s:.12g} s "
            f"in phase {phase}; adjacent P/O or O/N required."
        )
    before = conduction_currents(from_state, phase_current_a)
    after = conduction_currents(to_state, phase_current_a)
    before_voltage = blocking_voltages(from_state, vdc_v)
    after_voltage = blocking_voltages(to_state, vdc_v)
    before_gates, after_gates = gate_vector(from_state), gate_vector(to_state)
    positive = phase_current_a > 0
    # Table 7: the gate transition alone does not imply a loaded transistor edge.
    loaded = {
        ("P", "O", True): ("QP", "off", None),
        ("P", "O", False): ("QA", "on", "QP"),
        ("O", "P", True): ("QP", "on", "QA"),
        ("O", "P", False): ("QA", "off", None),
        ("O", "N", True): ("QO", "off", None),
        ("O", "N", False): ("QN", "on", "QO"),
        ("N", "O", True): ("QO", "on", "QN"),
        ("N", "O", False): ("QN", "off", None),
    }
    loaded_role, loaded_action, recovery_role = loaded[(before_name, after_name, positive)]
    changes = []
    for role, old_gate, new_gate in zip(ROLES, before_gates, after_gates, strict=True):
        if old_gate == new_gate:
            continue
        action = "on" if new_gate else "off"
        if phase_current_a == 0:
            category = "no_current"
        elif role == loaded_role:
            category = "ideal_loaded_turn_on" if action == "on" else "ideal_loaded_turn_off"
        else:
            category = "ideal_clamped_gate_on" if action == "on" else "gate_off_antiparallel_path"
        changes.append({
            "position": f"{phase}_{role}", "action": action, "category": category,
            "local_current_before_a": before[role].signed_a,
            "local_current_after_a": after[role].signed_a,
            "reference_path_before": before[role].path,
            "reference_path_after": after[role].path,
            "blocking_before_v": before_voltage[role],
            "blocking_after_v": after_voltage[role],
        })
    return {
        "time_s": time_s, "phase": phase, "from_state": before_name, "to_state": after_name,
        "phase_current_a": phase_current_a,
        "current_direction": "positive" if positive else "negative" if phase_current_a < 0 else "zero",
        "level_step_v": (to_state - from_state) * vdc_v / 2,
        "commutation_voltage_v": vdc_v / 2,
        "gate_changes": changes,
        "loaded_position": f"{phase}_{loaded_role}" if phase_current_a != 0 else None,
        "loaded_action": loaded_action if phase_current_a != 0 else None,
        "possible_recovery_diode_position": f"{phase}_{recovery_role}" if recovery_role and phase_current_a != 0 else None,
        "category": "ideal_adjacent_level" if phase_current_a != 0 else "no_current",
        "current_source": "exact_integrated_segment_boundary",
        "voltage_source": "balanced_operating_split_bus",
        "reference_model": "ideal_igbt_with_antiparallel_diode_zero_deadtime",
    }


def extract_events(segments: list[dict[str, object]], vdc_v: float) -> list[dict[str, object]]:
    """Read real state changes at continuous segment boundaries, once per phase.

    Zero-duration records are excluded, but cannot serve as an artificial O
    dwell that legitimizes a P-to-N jump. No periodic seam is invented here.
    """

    if not segments:
        raise ValueError("T-type event extraction requires integrated segments.")
    positive_segments = []
    for segment in segments:
        start, end = float(segment["start_time_s"]), float(segment["end_time_s"])
        if not math.isfinite(start) or not math.isfinite(end) or end < start or start < 0:
            raise ValueError("T-type segment time interval is invalid.")
        if end == start:
            continue
        for key in ("states", "start_currents_a", "end_currents_a"):
            if len(segment[key]) != 3:
                raise ValueError(f"T-type segment {key} must contain three phases.")
        for state in segment["states"]:
            state_name(state)
        for key in ("start_currents_a", "end_currents_a"):
            if not all(math.isfinite(value) for value in segment[key]):
                raise ValueError("T-type segment currents must be finite.")
        positive_segments.append(segment)
    if not positive_segments:
        raise ValueError("T-type event extraction requires positive-duration segments.")
    events = []
    for before, after in zip(positive_segments, positive_segments[1:]):
        if abs(before["end_time_s"] - after["start_time_s"]) > 1e-12:
            raise ValueError("T-type segment timeline is discontinuous.")
        for index, phase in enumerate(PHASES):
            current = before["end_currents_a"][index]
            if abs(current - after["start_currents_a"][index]) > 1e-7:
                raise ValueError(f"T-type {phase} segment current is discontinuous.")
            old, new = before["states"][index], after["states"][index]
            if old != new:
                events.append(commutation_event(
                    phase=phase, from_state=old, to_state=new,
                    time_s=float(after["start_time_s"]), phase_current_a=current, vdc_v=vdc_v,
                ))
    return events
