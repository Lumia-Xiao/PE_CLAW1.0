"""First-pass stress estimates for the three-phase three-level NPC inverter."""

from __future__ import annotations

import math

from ....models.stress_result import StressMetric, StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate


def extract_stress(candidate: TopologyCandidate, waveform_set: WaveformSet | None = None) -> StressResult:
    """Return first-pass active switch and clamp diode stress for the NPC bridge."""

    metadata = candidate.metadata
    operating_metadata = waveform_set.metadata if waveform_set is not None and isinstance(waveform_set.metadata, dict) else {}
    i_phase_rms_a = _metadata_float(operating_metadata, "operating_i_phase_rms_a", float(metadata["i_phase_rms_a"]))
    i_phase_peak_a = _metadata_float(operating_metadata, "operating_i_phase_peak_a", float(metadata["i_phase_peak_a"]))
    current_peak_a = i_phase_peak_a
    active_switch_rms_a = i_phase_rms_a / math.sqrt(2.0)
    active_switch_avg_a = 0.0
    clamp_diode_rms_a = i_phase_rms_a / math.sqrt(6.0)
    clamp_diode_avg_a = 0.0
    device_currents = operating_metadata.get("three_phase_npc_device_currents")
    roles = device_currents.get("roles") if isinstance(device_currents, dict) else None
    if isinstance(roles, dict):
        outer = roles.get("outer_switch") if isinstance(roles.get("outer_switch"), dict) else {}
        inner = roles.get("inner_switch") if isinstance(roles.get("inner_switch"), dict) else {}
        clamp = roles.get("clamp_diode") if isinstance(roles.get("clamp_diode"), dict) else {}
        active_switch_rms_a = max(
            _dict_float(outer, "rms_current_a", active_switch_rms_a),
            _dict_float(inner, "rms_current_a", active_switch_rms_a),
        )
        active_switch_avg_a = max(
            _dict_float(outer, "average_absolute_current_a", 0.0),
            _dict_float(inner, "average_absolute_current_a", 0.0),
        )
        current_peak_a = max(
            _dict_float(outer, "peak_absolute_current_a", current_peak_a),
            _dict_float(inner, "peak_absolute_current_a", current_peak_a),
        )
        clamp_diode_rms_a = _dict_float(clamp, "rms_current_a", clamp_diode_rms_a)
        clamp_diode_avg_a = _dict_float(clamp, "average_absolute_current_a", 0.0)
    blocking_voltage_v = float(metadata["npc_half_bus_voltage_v"])
    switch_metric = StressMetric(
        voltage_max_v=blocking_voltage_v,
        current_peak_a=current_peak_a,
        current_rms_a=active_switch_rms_a,
        current_avg_a=active_switch_avg_a,
    )
    clamp_metric = StressMetric(
        voltage_max_v=blocking_voltage_v,
        current_peak_a=current_peak_a,
        current_rms_a=clamp_diode_rms_a,
        current_avg_a=clamp_diode_avg_a,
    )
    return StressResult(
        switch=switch_metric,
        rectifier=clamp_metric,
        notes=[
            f"NPC topology contract: {metadata.get('npc_topology_contract', {}).get('topology_family', 'conventional_diode_clamped_npc')} with 12 active switch positions and 6 clamp diode positions.",
            "Role stress mapping: outer S1/S4, inner S2/S3, clamp diodes DNP+/DNP- in the zero state.",
            "First-pass three-phase three-level NPC stress uses Vdc/2 device blocking voltage.",
            "Outer and inner switch branches are resolved separately in waveform metadata; the shared switch metric is the conservative role maximum.",
            "Clamp diode current is resolved from zero-state phase-current direction and does not include neutral-point balancing dynamics.",
            "No dead-time, Coss, commutation overlap, or parasitic transient model is included.",
            *(
                ["Operating-point waveform current refreshed NPC first-pass stress."]
                if waveform_set is not None
                else []
            ),
        ],
    )


def _metadata_float(metadata: dict[str, object], key: str, fallback: float) -> float:
    try:
        return float(metadata.get(key, fallback))
    except (TypeError, ValueError):
        return fallback


def _dict_float(metadata: dict[str, object], key: str, fallback: float) -> float:
    try:
        return float(metadata.get(key, fallback))
    except (TypeError, ValueError):
        return fallback
