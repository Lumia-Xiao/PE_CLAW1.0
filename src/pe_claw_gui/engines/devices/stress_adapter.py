"""Adapters from topology report outputs to normalized switch-stress cases."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import math

from ...models.design_report import DesignReport
from ...models.device_loss import SwitchStress
from ...models.operating_point import OperatingPoint
from ...models.waveform import WaveformSet
from ...libraries.semiconductors.topology_roles import get_active_topology_ids
from ...topologies.base.interface import TopologyPlugin
from ...utils.ambient_temperature import TARGET_JUNCTION_TEMP_INPUT_KEY


_LLC_DIODE_RECTIFIER_TOPOLOGY_ID = "llc_resonant_converter_diode_rectifier"
_LLC_SR_TOPOLOGY_ID = "llc_resonant_converter_synchronous_rectifier"
_PSFB_DIODE_RECTIFIER_TOPOLOGY_ID = "phase_shifted_full_bridge_diode_rectifier_isolated"
_SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID = "single_phase_boost_pfc_diode_bridge"
_SINGLE_PHASE_TOTEM_POLE_PFC_TOPOLOGY_ID = "single_phase_totem_pole_bridgeless_pfc"


@dataclass(frozen=True)
class SwitchStressCase:
    """One operating case and all normalized switch stresses derived from it."""

    case_id: str
    label: str
    operating_point: OperatingPoint
    mode: str
    stresses: tuple[SwitchStress, ...]
    notes: list[str] = field(default_factory=list)


def _rms(values: list[float]) -> float:
    if not values:
        return 0.0
    return math.sqrt(sum(value * value for value in values) / len(values))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _ambient_temp_c(report: DesignReport) -> float | None:
    ambient = report.spec.metadata.get("ambient_temp_c")
    return float(ambient) if ambient is not None else None


def _target_junction_temp_c(report: DesignReport) -> float | None:
    target = report.spec.metadata.get(TARGET_JUNCTION_TEMP_INPUT_KEY)
    return float(target) if target is not None else None


def _maximum_device_selection_voltage_v(report: DesignReport, fallback_v: float) -> float:
    """Return the highest DC-bus voltage that device selection must cover."""

    raw_input = report.spec.raw_input if isinstance(report.spec.raw_input, dict) else {}
    metadata = report.spec.metadata if isinstance(report.spec.metadata, dict) else {}
    for source in (raw_input, metadata):
        for key in ("device_selection_voltage_v", "vdc_max_v", "vdc_max", "vin_max_v"):
            try:
                candidate_v = float(source.get(key))
            except (TypeError, ValueError):
                continue
            if candidate_v > 0.0:
                return max(float(fallback_v), candidate_v)
    return float(fallback_v)


def _infer_main_switch_stress(report: DesignReport, waveform: WaveformSet) -> SwitchStress:
    stress = report.stress
    if stress is None:
        raise ValueError("Stress result is required to build switch stress.")
    switching_period_s = waveform.switching_period_s
    return SwitchStress(
        role="main_switch",
        mode=waveform.mode,
        v_block_V=stress.switch.voltage_max_v,
        i_rms_A=_rms(waveform.switch_current_a),
        i_avg_A=_mean(waveform.switch_current_a),
        i_turn_on_A=max(waveform.inductor_current_min_a, 0.0),
        i_turn_off_A=waveform.inductor_current_max_a,
        fsw_Hz=1.0 / switching_period_s,
        duty=waveform.duty,
        conduction_time_s=waveform.duty * switching_period_s,
        ambient_temp_C=_ambient_temp_c(report),
        target_junction_temp_C=_target_junction_temp_c(report),
    )


def _infer_low_side_switch_stress(report: DesignReport, waveform: WaveformSet) -> SwitchStress:
    stress = report.stress
    if stress is None:
        raise ValueError("Stress result is required to build switch stress.")
    low_side_current_a = waveform.diode_current_a
    switching_period_s = waveform.switching_period_s
    return SwitchStress(
        role="sync_switch",
        mode=waveform.mode,
        v_block_V=stress.rectifier.voltage_max_v,
        i_rms_A=_rms(low_side_current_a),
        i_avg_A=_mean(low_side_current_a),
        i_turn_on_A=waveform.inductor_current_max_a,
        i_turn_off_A=waveform.inductor_current_min_a,
        fsw_Hz=1.0 / switching_period_s,
        duty=max(0.0, 1.0 - waveform.duty),
        conduction_time_s=max(0.0, 1.0 - waveform.duty) * switching_period_s,
        ambient_temp_C=_ambient_temp_c(report),
        target_junction_temp_C=_target_junction_temp_c(report),
    )


def _infer_rectifier_diode_stress(report: DesignReport, waveform: WaveformSet) -> SwitchStress:
    stress = report.stress
    if stress is None:
        raise ValueError("Stress result is required to build switch stress.")
    diode_current_a = waveform.diode_current_a
    switching_period_s = waveform.switching_period_s
    return SwitchStress(
        role="rectifier_diode",
        mode=waveform.mode,
        v_block_V=stress.rectifier.voltage_max_v,
        i_rms_A=_rms(diode_current_a),
        i_avg_A=_mean(diode_current_a),
        i_turn_on_A=waveform.inductor_current_max_a,
        i_turn_off_A=0.0,
        fsw_Hz=1.0 / switching_period_s,
        duty=max(0.0, 1.0 - waveform.duty),
        conduction_time_s=max(0.0, 1.0 - waveform.duty) * switching_period_s,
        ambient_temp_C=_ambient_temp_c(report),
        target_junction_temp_C=_target_junction_temp_c(report),
    )


def _infer_flyback_rectifier_diode_stress(report: DesignReport, waveform: WaveformSet) -> SwitchStress:
    stress = report.stress
    if stress is None:
        raise ValueError("Stress result is required to build switch stress.")
    diode_current_a = waveform.diode_current_a
    switching_period_s = waveform.switching_period_s
    active_duty = _series_duty(diode_current_a)
    return SwitchStress(
        role="rectifier_diode",
        mode=waveform.mode,
        v_block_V=stress.rectifier.voltage_max_v,
        i_rms_A=_rms(diode_current_a),
        i_avg_A=_mean(diode_current_a),
        i_turn_on_A=_series_peak(diode_current_a),
        i_turn_off_A=_series_min_positive(diode_current_a) if waveform.mode == "CCM" else 0.0,
        fsw_Hz=1.0 / switching_period_s,
        duty=active_duty,
        conduction_time_s=active_duty * switching_period_s,
        ambient_temp_C=_ambient_temp_c(report),
        target_junction_temp_C=_target_junction_temp_c(report),
    )


def _build_flyback_stresses(
    report: DesignReport,
    waveform: WaveformSet,
    *,
    use_sizing_currents: bool,
) -> tuple[SwitchStress, SwitchStress]:
    if not use_sizing_currents:
        return (
            _infer_main_switch_stress(report, waveform),
            _infer_flyback_rectifier_diode_stress(report, waveform),
        )
    stress = report.stress
    candidate = report.candidate
    if stress is None or candidate is None:
        raise ValueError("Flyback stress and candidate are required for sizing-current mapping.")
    flyback = candidate.metadata.get("flyback") if isinstance(candidate.metadata, dict) else None
    if not isinstance(flyback, dict):
        return (
            _infer_main_switch_stress(report, waveform),
            _infer_flyback_rectifier_diode_stress(report, waveform),
        )
    duty = waveform.duty
    secondary_duty = float(flyback.get("secondary_decay_fraction", max(0.0, 1.0 - duty)))
    primary_peak_a = float(flyback.get("sizing_primary_peak_current_a", stress.switch.current_peak_a))
    primary_valley_a = float(flyback.get("sizing_primary_valley_current_a", 0.0))
    primary_rms_a = float(
        flyback.get("sizing_primary_switch_rms_current_a", stress.switch.current_rms_a or 0.0)
    )
    secondary_peak_a = float(flyback.get("sizing_secondary_peak_current_a", stress.rectifier.current_peak_a))
    secondary_valley_a = float(flyback.get("sizing_secondary_valley_current_a", 0.0))
    secondary_rms_a = float(
        flyback.get("sizing_secondary_rms_current_a", stress.rectifier.current_rms_a or 0.0)
    )
    switching_period_s = waveform.switching_period_s
    common = {
        "mode": waveform.mode,
        "fsw_Hz": 1.0 / switching_period_s,
        "ambient_temp_C": _ambient_temp_c(report),
        "target_junction_temp_C": _target_junction_temp_c(report),
    }
    return (
        SwitchStress(
            role="main_switch",
            v_block_V=stress.switch.voltage_max_v,
            i_rms_A=primary_rms_a,
            i_avg_A=duty * (primary_peak_a + primary_valley_a) / 2.0,
            i_turn_on_A=primary_valley_a,
            i_turn_off_A=primary_peak_a,
            duty=duty,
            conduction_time_s=duty * switching_period_s,
            **common,
        ),
        SwitchStress(
            role="rectifier_diode",
            v_block_V=stress.rectifier.voltage_max_v,
            i_rms_A=secondary_rms_a,
            i_avg_A=secondary_duty * (secondary_peak_a + secondary_valley_a) / 2.0,
            i_turn_on_A=secondary_peak_a,
            i_turn_off_A=secondary_valley_a if waveform.mode == "CCM" else 0.0,
            duty=secondary_duty,
            conduction_time_s=secondary_duty * switching_period_s,
            **common,
        ),
    )


def _series_rms(values: list[float]) -> float:
    return _rms([abs(value) for value in values])


def _series_avg(values: list[float]) -> float:
    return _mean([abs(value) for value in values])


def _series_peak(values: list[float]) -> float:
    return max((abs(value) for value in values), default=0.0)


def _series_min_positive(values: list[float]) -> float:
    return min((abs(value) for value in values if abs(value) > 1e-12), default=0.0)


def _series_duty(values: list[float]) -> float:
    if not values:
        return 0.0
    active_samples = sum(1 for value in values if abs(value) > 1e-12)
    return active_samples / len(values)


def _metadata_float(metadata: dict[str, object], key: str, *, fallback: float) -> float:
    value = metadata.get(key)
    if value is None:
        return fallback
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _build_series_stress(
    report: DesignReport,
    waveform: WaveformSet,
    *,
    role: str,
    current_series_a: list[float],
    blocking_voltage_v: float,
) -> SwitchStress:
    switching_period_s = waveform.switching_period_s
    duty = _series_duty(current_series_a)
    return SwitchStress(
        role=role,
        mode=waveform.mode,
        v_block_V=blocking_voltage_v,
        i_rms_A=_series_rms(current_series_a),
        i_avg_A=_series_avg(current_series_a),
        i_turn_on_A=_series_peak(current_series_a),
        i_turn_off_A=_series_peak(current_series_a),
        fsw_Hz=1.0 / switching_period_s,
        duty=duty,
        conduction_time_s=duty * switching_period_s,
        ambient_temp_C=_ambient_temp_c(report),
        target_junction_temp_C=_target_junction_temp_c(report),
    )


def _build_four_switch_stresses(report: DesignReport, waveform: WaveformSet) -> tuple[SwitchStress, ...]:
    stress = report.stress
    if stress is None:
        raise ValueError("Stress result is required to build four-switch stresses.")
    high_path = waveform.switch_current_a or []
    low_path = waveform.diode_current_a or []
    blocking_voltage_v = max(stress.switch.voltage_max_v, stress.rectifier.voltage_max_v)
    return (
        _build_series_stress(report, waveform, role="switch_a_high", current_series_a=high_path, blocking_voltage_v=blocking_voltage_v),
        _build_series_stress(report, waveform, role="switch_a_low", current_series_a=low_path, blocking_voltage_v=blocking_voltage_v),
        _build_series_stress(report, waveform, role="switch_b_high", current_series_a=high_path, blocking_voltage_v=blocking_voltage_v),
        _build_series_stress(report, waveform, role="switch_b_low", current_series_a=low_path, blocking_voltage_v=blocking_voltage_v),
    )


def _gated_current_series(current_series: list[float], gate_series: list[float]) -> list[float]:
    count = min(len(current_series), len(gate_series))
    return [
        abs(current_series[index]) if gate_series[index] > 0.5 else 0.0
        for index in range(count)
    ]


def _build_three_level_stresses(report: DesignReport, waveform: WaveformSet) -> tuple[SwitchStress, ...]:
    stress = report.stress
    if stress is None:
        raise ValueError("Stress result is required to build three-level switch stresses.")
    inductor_current = waveform.inductor_current_a or waveform.switch_current_a or []
    blocking_voltage_v = max(stress.switch.voltage_max_v, stress.rectifier.voltage_max_v)
    gate_sets = (
        ("S1", waveform.gate_s1),
        ("S2", waveform.gate_s2),
        ("S3", waveform.gate_s3),
        ("S4", waveform.gate_s4),
    )
    if not all(gate for _, gate in gate_sets):
        high_path = waveform.switch_current_a or inductor_current
        low_path = waveform.diode_current_a or inductor_current
        return (
            _build_series_stress(report, waveform, role="S1", current_series_a=high_path, blocking_voltage_v=blocking_voltage_v),
            _build_series_stress(report, waveform, role="S2", current_series_a=low_path, blocking_voltage_v=blocking_voltage_v),
            _build_series_stress(report, waveform, role="S3", current_series_a=low_path, blocking_voltage_v=blocking_voltage_v),
            _build_series_stress(report, waveform, role="S4", current_series_a=high_path, blocking_voltage_v=blocking_voltage_v),
        )
    return tuple(
        _build_series_stress(
            report,
            waveform,
            role=role_name,
            current_series_a=_gated_current_series(inductor_current, gate_series),
            blocking_voltage_v=blocking_voltage_v,
        )
        for role_name, gate_series in gate_sets
    )


def _build_single_phase_full_bridge_inverter_stress(report: DesignReport, waveform: WaveformSet) -> SwitchStress:
    """Return the first-pass per-position switch stress for the full bridge."""

    stress = report.stress
    candidate = report.candidate
    if stress is None or candidate is None:
        raise ValueError("Candidate and stress result are required to build inverter switch stress.")
    switching_period_s = 1.0 / max(candidate.fs_hz, 1e-9)
    is_tcm = str(candidate.mode_capable).startswith("tcm_")
    current_series = waveform.inductor_current_a or waveform.switch_current_a or []
    current_rms_a = stress.switch.current_rms_a or 0.0 if is_tcm else (
        _series_rms(current_series) / math.sqrt(2.0) if current_series else (stress.switch.current_rms_a or 0.0) / math.sqrt(2.0)
    )
    current_avg_a = 0.5 * _series_avg(current_series) if current_series else 0.0
    turn_current_a = stress.switch.current_peak_a if is_tcm else (_series_peak(current_series) or stress.switch.current_peak_a)
    return SwitchStress(
        role="main_switch",
        mode="full_bridge_tcm_design_point" if is_tcm else "full_bridge_unipolar_spwm_design_point",
        v_block_V=_maximum_device_selection_voltage_v(report, stress.switch.voltage_max_v),
        i_rms_A=current_rms_a,
        i_avg_A=current_avg_a,
        i_turn_on_A=turn_current_a,
        i_turn_off_A=turn_current_a,
        fsw_Hz=candidate.fs_hz,
        duty=0.5,
        conduction_time_s=0.5 * switching_period_s,
        ambient_temp_C=_ambient_temp_c(report),
        target_junction_temp_C=_target_junction_temp_c(report),
    )


def _build_three_phase_two_level_inverter_stress(report: DesignReport) -> SwitchStress:
    """Return the Step1 first-pass per-position switch stress for the six-switch bridge."""

    stress = report.stress
    candidate = report.candidate
    if stress is None or candidate is None:
        raise ValueError("Candidate and stress result are required to build three-phase inverter switch stress.")
    switching_period_s = 1.0 / max(candidate.fs_hz, 1e-9)
    return SwitchStress(
        role="main_switch",
        mode="three_phase_two_level_spwm_first_pass_design_point",
        v_block_V=stress.switch.voltage_max_v,
        i_rms_A=stress.switch.current_rms_a or 0.0,
        i_avg_A=0.0,
        i_turn_on_A=stress.switch.current_peak_a,
        i_turn_off_A=stress.switch.current_peak_a,
        fsw_Hz=candidate.fs_hz,
        duty=0.5,
        conduction_time_s=0.5 * switching_period_s,
        ambient_temp_C=_ambient_temp_c(report),
        target_junction_temp_C=_target_junction_temp_c(report),
    )


def _build_three_phase_npc_inverter_stresses(report: DesignReport) -> tuple[SwitchStress, SwitchStress, SwitchStress]:
    """Return waveform-backed per-position stress for NPC switches and clamp diodes."""

    stress = report.stress
    candidate = report.candidate
    if stress is None or candidate is None:
        raise ValueError("Candidate and stress result are required to build three-phase NPC inverter switch stress.")
    switching_period_s = 1.0 / max(candidate.fs_hz, 1e-9)
    waveform_metadata = report.waveform.metadata if report.waveform is not None else {}
    device_currents = waveform_metadata.get("three_phase_npc_device_currents") if isinstance(waveform_metadata, dict) else None
    roles = device_currents.get("roles") if isinstance(device_currents, dict) else None

    def role_metric(role: str, key: str, fallback: float) -> float:
        role_values = roles.get(role) if isinstance(roles, dict) else None
        return _metadata_float(role_values, key, fallback=fallback) if isinstance(role_values, dict) else fallback

    def role_events(role: str, key: str) -> tuple[float, ...]:
        role_values = roles.get(role) if isinstance(roles, dict) else None
        if not isinstance(role_values, dict):
            return ()
        values = role_values.get(key, ())
        if not isinstance(values, (list, tuple)):
            return ()
        return tuple(float(value) for value in values)

    def role_event_window(role: str) -> float:
        return role_metric(role, "event_window_s", 0.0)

    def role_event_positions(role: str) -> int:
        return max(1, int(role_metric(role, "event_position_count", 1.0)))

    common = {
        "mode": "three_phase_three_level_npc_pd_spwm_waveform_backed_design_point",
        "fsw_Hz": candidate.fs_hz,
        "ambient_temp_C": _ambient_temp_c(report),
        "target_junction_temp_C": _target_junction_temp_c(report),
        "dead_time_s": _npc_metadata_float(report, "npc_dead_time_s") or 0.0,
        "v_drive_on_V": _npc_metadata_float(report, "npc_gate_drive_v") or 15.0,
        "v_drive_off_V": 0.0,
        "voltage_margin_ratio": _npc_voltage_margin_ratio(report),
        "static_voltage_basis_V": _npc_static_voltage_basis(report),
        "neutral_point_stress_factor": _npc_metadata_float(report, "npc_neutral_point_stress_factor"),
        "dynamic_overvoltage_V": _npc_metadata_float(report, "npc_switching_overvoltage_v") or 0.0,
        "overvoltage_source": _npc_metadata_text(report, "npc_switching_overvoltage_source"),
        "overvoltage_validation_status": _npc_metadata_text(report, "npc_switching_overvoltage_validation_status"),
    }
    outer_duty = role_metric("outer_switch", "conduction_duty", 0.5)
    inner_duty = role_metric("inner_switch", "conduction_duty", 0.5)
    clamp_duty = role_metric("clamp_diode", "conduction_duty", 0.0)
    outer = SwitchStress(
        role="npc_outer_switch",
        v_block_V=stress.switch.voltage_max_v,
        i_rms_A=role_metric("outer_switch", "rms_current_a", stress.switch.current_rms_a or 0.0),
        i_avg_A=role_metric("outer_switch", "average_absolute_current_a", stress.switch.current_avg_a or 0.0),
        i_turn_on_A=role_metric("outer_switch", "peak_absolute_current_a", stress.switch.current_peak_a),
        i_turn_off_A=role_metric("outer_switch", "peak_absolute_current_a", stress.switch.current_peak_a),
        duty=outer_duty,
        conduction_time_s=outer_duty * switching_period_s,
        turn_on_event_currents_A=role_events("outer_switch", "turn_on_event_currents_a"),
        turn_off_event_currents_A=role_events("outer_switch", "turn_off_event_currents_a"),
        turn_on_event_voltages_V=role_events("outer_switch", "turn_on_event_voltages_v"),
        turn_off_event_voltages_V=role_events("outer_switch", "turn_off_event_voltages_v"),
        event_window_s=role_event_window("outer_switch"),
        event_position_count=role_event_positions("outer_switch"),
        **common,
    )
    inner_peak_a = role_metric("inner_switch", "peak_absolute_current_a", stress.switch.current_peak_a)
    inner = SwitchStress(
        role="npc_inner_switch",
        v_block_V=stress.switch.voltage_max_v,
        i_rms_A=role_metric("inner_switch", "rms_current_a", stress.switch.current_rms_a or 0.0),
        i_avg_A=role_metric("inner_switch", "average_absolute_current_a", stress.switch.current_avg_a or 0.0),
        i_turn_on_A=inner_peak_a,
        i_turn_off_A=inner_peak_a,
        duty=inner_duty,
        conduction_time_s=inner_duty * switching_period_s,
        turn_on_event_currents_A=role_events("inner_switch", "turn_on_event_currents_a"),
        turn_off_event_currents_A=role_events("inner_switch", "turn_off_event_currents_a"),
        turn_on_event_voltages_V=role_events("inner_switch", "turn_on_event_voltages_v"),
        turn_off_event_voltages_V=role_events("inner_switch", "turn_off_event_voltages_v"),
        event_window_s=role_event_window("inner_switch"),
        event_position_count=role_event_positions("inner_switch"),
        **common,
    )
    clamp_peak_a = role_metric("clamp_diode", "peak_absolute_current_a", stress.rectifier.current_peak_a)
    clamp = SwitchStress(
        role="npc_clamp_diode",
        v_block_V=stress.rectifier.voltage_max_v,
        i_rms_A=role_metric("clamp_diode", "rms_current_a", stress.rectifier.current_rms_a or 0.0),
        i_avg_A=role_metric("clamp_diode", "average_absolute_current_a", stress.rectifier.current_avg_a or 0.0),
        i_turn_on_A=clamp_peak_a,
        i_turn_off_A=0.0,
        duty=clamp_duty,
        conduction_time_s=clamp_duty * switching_period_s,
        **common,
    )
    return outer, inner, clamp


def _npc_metadata_float(report: DesignReport, key: str) -> float | None:
    if report.spec.topology_id != "three_phase_three_level_npc_inverter":
        return None
    try:
        return float(report.candidate.metadata[key]) if report.candidate is not None else None
    except (KeyError, TypeError, ValueError):
        return None


def _npc_metadata_text(report: DesignReport, key: str) -> str:
    if report.spec.topology_id != "three_phase_three_level_npc_inverter" or report.candidate is None:
        return "not_applicable"
    return str(report.candidate.metadata.get(key, "unverified_assumption"))


def _npc_voltage_margin_ratio(report: DesignReport) -> float:
    value = _npc_metadata_float(report, "npc_static_voltage_margin_ratio")
    return 0.20 if value is None else value


def _npc_static_voltage_basis(report: DesignReport) -> float | None:
    value = _npc_metadata_float(report, "npc_static_blocking_voltage_v")
    return value


def _build_psfb_diode_rectifier_stresses(report: DesignReport) -> tuple[SwitchStress, SwitchStress]:
    """Return first-pass per-position stress for PSFB primary switches and secondary diodes."""

    stress = report.stress
    candidate = report.candidate
    if stress is None or candidate is None:
        raise ValueError("Candidate and stress result are required to build PSFB switch stress.")
    switching_period_s = 1.0 / max(candidate.fs_hz, 1e-9)
    psfb_metadata = candidate.metadata.get("psfb") if isinstance(candidate.metadata, dict) else None
    command_duty = (
        float(psfb_metadata.get("command_duty_nom", candidate.duty_nom))
        if isinstance(psfb_metadata, dict)
        else candidate.duty_nom
    )
    secondary_duty = (
        float(psfb_metadata.get("effective_duty_nom", candidate.duty_nom))
        if isinstance(psfb_metadata, dict)
        else candidate.duty_nom
    )
    primary = SwitchStress(
        role="main_switch",
        mode="psfb_phase_shift_first_pass_design_point",
        v_block_V=stress.switch.voltage_max_v,
        i_rms_A=stress.switch.current_rms_a or 0.0,
        i_avg_A=stress.switch.current_avg_a or 0.0,
        i_turn_on_A=stress.switch.current_peak_a,
        i_turn_off_A=stress.switch.current_peak_a,
        fsw_Hz=candidate.fs_hz,
        duty=max(0.0, min(command_duty, 1.0)),
        conduction_time_s=max(0.0, min(command_duty, 1.0)) * switching_period_s,
        ambient_temp_C=_ambient_temp_c(report),
        target_junction_temp_C=_target_junction_temp_c(report),
    )
    rectifier = SwitchStress(
        role="rectifier_diode",
        mode="psfb_secondary_full_bridge_diode_first_pass_design_point",
        v_block_V=stress.rectifier.voltage_max_v,
        i_rms_A=stress.rectifier.current_rms_a or 0.0,
        i_avg_A=stress.rectifier.current_avg_a or candidate.iout,
        i_turn_on_A=stress.rectifier.current_peak_a,
        i_turn_off_A=0.0,
        fsw_Hz=candidate.fs_hz,
        duty=max(0.0, min(secondary_duty, 1.0)),
        conduction_time_s=max(0.0, min(secondary_duty, 1.0)) * switching_period_s,
        ambient_temp_C=_ambient_temp_c(report),
        target_junction_temp_C=_target_junction_temp_c(report),
    )
    return primary, rectifier


def _build_llc_sr_stresses(report: DesignReport) -> tuple[SwitchStress, SwitchStress]:
    """Return first-pass per-position stress for LLC primary switches and secondary SR switches."""

    stress = report.stress
    candidate = report.candidate
    if stress is None or candidate is None:
        raise ValueError("Candidate and stress result are required to build LLC SR switch stress.")
    switching_period_s = 1.0 / max(candidate.fs_hz, 1e-9)
    mode = report.waveform.mode if report.waveform is not None else candidate.mode_capable.upper()
    primary = SwitchStress(
        role="main_switch",
        mode=mode,
        v_block_V=stress.switch.voltage_max_v,
        i_rms_A=stress.switch.current_rms_a or 0.0,
        i_avg_A=stress.switch.current_avg_a or 0.0,
        i_turn_on_A=stress.switch.current_peak_a,
        i_turn_off_A=stress.switch.current_peak_a,
        fsw_Hz=candidate.fs_hz,
        duty=0.5,
        conduction_time_s=0.5 * switching_period_s,
        ambient_temp_C=_ambient_temp_c(report),
        target_junction_temp_C=_target_junction_temp_c(report),
    )
    secondary = SwitchStress(
        role="secondary_sync_switch",
        mode=mode,
        v_block_V=stress.rectifier.voltage_max_v,
        i_rms_A=stress.rectifier.current_rms_a or 0.0,
        i_avg_A=stress.rectifier.current_avg_a or 0.0,
        i_turn_on_A=stress.rectifier.current_peak_a,
        i_turn_off_A=stress.rectifier.current_peak_a,
        fsw_Hz=candidate.fs_hz,
        duty=0.5,
        conduction_time_s=0.5 * switching_period_s,
        ambient_temp_C=_ambient_temp_c(report),
        target_junction_temp_C=_target_junction_temp_c(report),
    )
    return primary, secondary


def _build_single_phase_boost_pfc_stresses(report: DesignReport) -> tuple[SwitchStress, SwitchStress]:
    """Return first-pass stress for the PFC boost switch and independent boost diode."""

    stress = report.stress
    candidate = report.candidate
    if stress is None or candidate is None:
        raise ValueError("Candidate and stress result are required to build PFC switch stresses.")
    waveform_metadata = report.waveform.metadata if report.waveform is not None else {}
    switching_period_s = 1.0 / max(candidate.fs_hz, 1e-9)
    mode = report.waveform.mode if report.waveform is not None else candidate.mode_capable.upper()
    boost_switch = SwitchStress(
        role="main_switch",
        mode=mode,
        v_block_V=stress.switch.voltage_max_v,
        i_rms_A=_metadata_float(
            waveform_metadata,
            "sizing_boost_switch_current_rms_a",
            fallback=stress.switch.current_rms_a or 0.0,
        ),
        i_avg_A=_metadata_float(
            waveform_metadata,
            "sizing_boost_switch_current_avg_a",
            fallback=stress.switch.current_avg_a or 0.0,
        ),
        i_turn_on_A=stress.switch.current_peak_a,
        i_turn_off_A=stress.switch.current_peak_a,
        fsw_Hz=candidate.fs_hz,
        duty=max(0.0, min(candidate.duty_nom, 1.0)),
        conduction_time_s=max(0.0, min(candidate.duty_nom, 1.0)) * switching_period_s,
        ambient_temp_C=_ambient_temp_c(report),
        target_junction_temp_C=_target_junction_temp_c(report),
    )
    diode_duty = max(0.0, min(1.0 - candidate.duty_nom, 1.0))
    boost_diode = SwitchStress(
        role="rectifier_diode",
        mode=mode,
        v_block_V=stress.rectifier.voltage_max_v,
        i_rms_A=_metadata_float(
            waveform_metadata,
            "sizing_boost_diode_current_rms_a",
            fallback=stress.rectifier.current_rms_a or 0.0,
        ),
        i_avg_A=_metadata_float(
            waveform_metadata,
            "sizing_boost_diode_current_avg_a",
            fallback=candidate.iout,
        ),
        i_turn_on_A=stress.rectifier.current_peak_a,
        i_turn_off_A=0.0,
        fsw_Hz=candidate.fs_hz,
        duty=diode_duty,
        conduction_time_s=diode_duty * switching_period_s,
        ambient_temp_C=_ambient_temp_c(report),
        target_junction_temp_C=_target_junction_temp_c(report),
    )
    return boost_switch, boost_diode


def _build_single_phase_totem_pole_pfc_stresses(report: DesignReport) -> tuple[SwitchStress, SwitchStress]:
    """Return first-pass stress for Totem-Pole high-frequency and line-frequency switch pairs."""

    stress = report.stress
    candidate = report.candidate
    if stress is None or candidate is None:
        raise ValueError("Candidate and stress result are required to build Totem-Pole PFC switch stresses.")
    waveform_metadata = report.waveform.metadata if report.waveform is not None else {}
    switching_period_s = 1.0 / max(candidate.fs_hz, 1e-9)
    mode = report.waveform.mode if report.waveform is not None else candidate.mode_capable.upper()
    hf_duty = max(0.0, min(candidate.duty_nom, 1.0))
    lf_duty = 0.5
    hf_switch = SwitchStress(
        role="totem_pole_hf_switch",
        mode=mode,
        v_block_V=stress.switch.voltage_max_v,
        i_rms_A=_metadata_float(
            waveform_metadata,
            "sizing_hf_switch_device_current_rms_a",
            fallback=stress.switch.current_rms_a or 0.0,
        ),
        i_avg_A=_metadata_float(
            waveform_metadata,
            "sizing_hf_switch_device_current_avg_a",
            fallback=stress.switch.current_avg_a or 0.0,
        ),
        i_turn_on_A=stress.switch.current_peak_a,
        i_turn_off_A=stress.switch.current_peak_a,
        fsw_Hz=candidate.fs_hz,
        duty=hf_duty,
        conduction_time_s=hf_duty * switching_period_s,
        ambient_temp_C=_ambient_temp_c(report),
        target_junction_temp_C=_target_junction_temp_c(report),
    )
    lf_switch = SwitchStress(
        role="totem_pole_lf_switch",
        mode=mode,
        v_block_V=stress.rectifier.voltage_max_v,
        i_rms_A=_metadata_float(
            waveform_metadata,
            "sizing_lf_switch_device_current_rms_a",
            fallback=stress.rectifier.current_rms_a or 0.0,
        ),
        i_avg_A=_metadata_float(
            waveform_metadata,
            "sizing_lf_switch_device_current_avg_a",
            fallback=stress.rectifier.current_avg_a or 0.0,
        ),
        i_turn_on_A=stress.rectifier.current_peak_a,
        i_turn_off_A=stress.rectifier.current_peak_a,
        fsw_Hz=float(candidate.metadata["f_line_hz"]),
        duty=lf_duty,
        conduction_time_s=lf_duty / float(candidate.metadata["f_line_hz"]),
        ambient_temp_C=_ambient_temp_c(report),
        target_junction_temp_C=_target_junction_temp_c(report),
    )
    return hf_switch, lf_switch


def _fallback_case(report: DesignReport, *, case_id: str, label: str, operating_point: OperatingPoint) -> SwitchStressCase | None:
    if report.candidate is None or report.stress is None:
        return None

    switching_period_s = 1.0 / max(report.candidate.fs_hz, 1e-9)
    duty = report.candidate.duty_nom
    mode = report.waveform.mode if report.waveform is not None else report.candidate.mode_capable.upper()
    if report.spec.topology_id == "three_phase_three_level_npc_inverter":
        return SwitchStressCase(
            case_id=case_id,
            label=label,
            operating_point=operating_point,
            mode=mode,
            stresses=_build_three_phase_npc_inverter_stresses(report),
            notes=[
                _format_operating_point_note(label, operating_point, mode),
                "Three-phase NPC inverter Step1 stress maps 12 active switch positions and 6 clamp diode positions.",
                "NPC fallback stress uses Vdc/2 blocking voltage and first-pass PD-SPWM current approximations.",
            ],
        )
    if report.spec.topology_id == _PSFB_DIODE_RECTIFIER_TOPOLOGY_ID:
        return SwitchStressCase(
            case_id=case_id,
            label=label,
            operating_point=operating_point,
            mode=mode,
            stresses=_build_psfb_diode_rectifier_stresses(report),
            notes=[
                _format_operating_point_note(label, operating_point, mode),
                "PSFB fallback stress maps four primary bridge switch positions and four secondary diode positions.",
                "Detailed resonant-transition and transformer parasitic stress mapping is pending.",
            ],
        )
    if report.spec.topology_id == _LLC_SR_TOPOLOGY_ID:
        return SwitchStressCase(
            case_id=case_id,
            label=label,
            operating_point=operating_point,
            mode=mode,
            stresses=_build_llc_sr_stresses(report),
            notes=[
                _format_operating_point_note(label, operating_point, mode),
                "LLC SR fallback stress adapter maps four primary switch positions and four secondary_sync_switch positions.",
                "Detailed LLC SR time-domain gate timing, reverse conduction, and current sharing are not implemented.",
            ],
        )
    if report.spec.topology_id == _SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID:
        return SwitchStressCase(
            case_id=case_id,
            label=label,
            operating_point=operating_point,
            mode=mode,
            stresses=_build_single_phase_boost_pfc_stresses(report),
            notes=[
                _format_operating_point_note(label, operating_point, mode),
                "Boost PFC fallback stress maps one boost main_switch and one independent boost rectifier_diode.",
                "Input bridge rectifier selection uses the AC-DC bridge selector rather than the generic semiconductor role map.",
            ],
        )
    if report.spec.topology_id == _SINGLE_PHASE_TOTEM_POLE_PFC_TOPOLOGY_ID:
        return SwitchStressCase(
            case_id=case_id,
            label=label,
            operating_point=operating_point,
            mode=mode,
            stresses=_build_single_phase_totem_pole_pfc_stresses(report),
            notes=[
                _format_operating_point_note(label, operating_point, mode),
                "Totem-Pole PFC fallback stress maps two high-frequency and two line-frequency active switch positions.",
                "No input bridge rectifier, rectifier diode, or boost diode role is emitted by this adapter.",
            ],
        )
    if report.spec.topology_id == _LLC_DIODE_RECTIFIER_TOPOLOGY_ID:
        rectifier_current_a = report.stress.rectifier.current_rms_a or report.stress.rectifier.current_avg_a or 0.0
        switch_current_rms_a = report.stress.switch.current_rms_a or 0.0
        switch_current_peak_a = report.stress.switch.current_peak_a or switch_current_rms_a
        return SwitchStressCase(
            case_id=case_id,
            label=label,
            operating_point=operating_point,
            mode=mode,
            stresses=(
                SwitchStress(
                    role="main_switch",
                    mode=mode,
                    v_block_V=report.stress.switch.voltage_max_v,
                    i_rms_A=switch_current_rms_a,
                    i_avg_A=report.stress.switch.current_avg_a or 0.0,
                    i_turn_on_A=switch_current_peak_a,
                    i_turn_off_A=switch_current_peak_a,
                    fsw_Hz=report.candidate.fs_hz,
                    duty=0.5,
                    conduction_time_s=0.5 * switching_period_s,
                    ambient_temp_C=_ambient_temp_c(report),
                    target_junction_temp_C=_target_junction_temp_c(report),
                ),
                SwitchStress(
                    role="rectifier_diode",
                    mode=mode,
                    v_block_V=report.stress.rectifier.voltage_max_v,
                    i_rms_A=rectifier_current_a,
                    i_avg_A=report.stress.rectifier.current_avg_a or rectifier_current_a,
                    i_turn_on_A=report.stress.rectifier.current_peak_a or rectifier_current_a,
                    i_turn_off_A=0.0,
                    fsw_Hz=report.candidate.fs_hz,
                    duty=0.5,
                    conduction_time_s=0.5 * switching_period_s,
                    ambient_temp_C=_ambient_temp_c(report),
                    target_junction_temp_C=_target_junction_temp_c(report),
                ),
            ),
            notes=[
                _format_operating_point_note(label, operating_point, mode),
                "LLC fallback stress adapter used worst-case first-pass FHA corner current estimates.",
                "Detailed LLC time-domain waveform stress mapping is not implemented.",
            ],
        )
    return SwitchStressCase(
        case_id=case_id,
        label=label,
        operating_point=operating_point,
        mode=mode,
        stresses=(
            SwitchStress(
                role="main_switch",
                mode=mode,
                v_block_V=report.stress.switch.voltage_max_v,
                i_rms_A=report.stress.switch.current_rms_a or 0.0,
                i_avg_A=report.stress.switch.current_avg_a or 0.0,
                i_turn_on_A=report.stress.switch.current_peak_a,
                i_turn_off_A=report.stress.switch.current_peak_a,
                fsw_Hz=report.candidate.fs_hz,
                duty=duty,
                conduction_time_s=duty * switching_period_s,
                ambient_temp_C=_ambient_temp_c(report),
                target_junction_temp_C=_target_junction_temp_c(report),
            ),
        ),
        notes=[
            _format_operating_point_note(label, operating_point, mode),
            "Fallback stress adapter used nominal stress metrics because waveform-specific mapping was unavailable.",
        ],
    )


def _design_operating_point(report: DesignReport) -> OperatingPoint:
    candidate = report.candidate
    if candidate is None:
        raise ValueError("Candidate is required to resolve the semiconductor design point.")
    return OperatingPoint(vin_v=candidate.vin_nom, load_ratio=1.0)


def _build_case(report: DesignReport, waveform: WaveformSet, operating_point: OperatingPoint, case_id: str, label: str) -> SwitchStressCase:
    topology_id = report.spec.topology_id
    if topology_id in {_LLC_DIODE_RECTIFIER_TOPOLOGY_ID, _LLC_SR_TOPOLOGY_ID}:
        fallback = _fallback_case(report, case_id=case_id, label=label, operating_point=operating_point)
        if fallback is None:
            raise ValueError("Stress result is required to build LLC switch stresses.")
        return fallback
    if topology_id in {
        "buck_diode_rectified_unidirectional",
        "boost_diode_rectified_unidirectional",
        "buck_boost_diode_rectified_unidirectional",
    }:
        stresses = [
            _infer_main_switch_stress(report, waveform),
            _infer_rectifier_diode_stress(report, waveform),
        ]
    elif topology_id == "flyback_diode_rectified_isolated":
        stresses = list(
            _build_flyback_stresses(
                report,
                waveform,
                use_sizing_currents=case_id == "design_point",
            )
        )
    elif topology_id in {
        "buck_synchronous_rectified_unidirectional",
        "boost_synchronous_rectified_unidirectional",
    }:
        stresses = [
            _infer_main_switch_stress(report, waveform),
            _infer_low_side_switch_stress(report, waveform),
        ]
    elif topology_id == "four_switch_buck_boost_simplified_four_mode":
        stresses = list(_build_four_switch_stresses(report, waveform))
    elif topology_id == "three_level_tzcm_fixed_frequency":
        stresses = list(_build_three_level_stresses(report, waveform))
    elif topology_id == "single_phase_full_bridge_inverter":
        stresses = [_build_single_phase_full_bridge_inverter_stress(report, waveform)]
    elif topology_id == "three_phase_two_level_voltage_source_inverter":
        stresses = [_build_three_phase_two_level_inverter_stress(report)]
    elif topology_id == "three_phase_three_level_npc_inverter":
        stresses = list(_build_three_phase_npc_inverter_stresses(report))
    elif topology_id == _PSFB_DIODE_RECTIFIER_TOPOLOGY_ID:
        stresses = list(_build_psfb_diode_rectifier_stresses(report))
    elif topology_id == _SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID:
        stresses = list(_build_single_phase_boost_pfc_stresses(report))
    elif topology_id == _SINGLE_PHASE_TOTEM_POLE_PFC_TOPOLOGY_ID:
        stresses = list(_build_single_phase_totem_pole_pfc_stresses(report))
    else:
        stresses = [_infer_main_switch_stress(report, waveform)]

    return SwitchStressCase(
        case_id=case_id,
        label=label,
        operating_point=operating_point,
        mode=waveform.mode,
        stresses=tuple(stresses),
        notes=[
            _format_operating_point_note(label, operating_point, waveform.mode),
            *(
                [
                    "Flyback design-point semiconductor selection uses efficiency-adjusted sizing currents; operating-point readback uses ideal charge-balance currents.",
                ]
                if topology_id == "flyback_diode_rectified_isolated"
                else []
            ),
            *(
                [
                    "PSFB design-point stress selects one primary switch repeated across four bridge positions.",
                    "Secondary full-bridge rectifier stress selects one independent diode repeated across four positions.",
                ]
                if topology_id == _PSFB_DIODE_RECTIFIER_TOPOLOGY_ID
                else []
            ),
            *(
                [
                    "Single-phase full-bridge inverter design-point stress selects one switch for four bridge positions.",
                    "Line-cycle segmented loss reports ZVS direction diagnostics while keeping turn-on loss from the device evaluator.",
                ]
                if topology_id == "single_phase_full_bridge_inverter"
                else []
            ),
            *(
                [
                    "Three-phase two-level inverter design-point stress selects one switch for six bridge positions.",
                    "SPWM waveform preview is not used as a high-fidelity switching stress model.",
                ]
                if topology_id == "three_phase_two_level_voltage_source_inverter"
                else []
            ),
            *(
                [
                    "Three-phase NPC inverter Step1 stress maps 12 active switch positions and 6 clamp diode positions.",
                    "NPC switching loss uses signed gate-edge currents and actual half-link event voltages; negative turn-on current is treated as soft switching.",
                ]
                if topology_id == "three_phase_three_level_npc_inverter"
                else []
            ),
        ],
    )


def build_design_point_switch_stress_cases(report: DesignReport, plugin: TopologyPlugin | None = None) -> list[SwitchStressCase]:
    """Build the 100% load semiconductor design-point stress cases."""

    if report.candidate is None or report.stress is None:
        return []

    design_operating_point = _design_operating_point(report)
    if plugin is None or report.spec.topology_id not in set(get_active_topology_ids()):
        fallback = _fallback_case(report, case_id="design_point", label="Design Point", operating_point=design_operating_point)
        return [] if fallback is None else [fallback]

    waveform = plugin.generate_waveforms(report.candidate, operating_point=design_operating_point)
    if waveform is None:
        fallback = _fallback_case(report, case_id="design_point", label="Design Point", operating_point=design_operating_point)
        return [] if fallback is None else [fallback]
    case_report = replace(
        report,
        operating_point=design_operating_point,
        waveform=waveform,
        stress=plugin.extract_stress(report.candidate, waveform_set=waveform),
    )
    return [_build_case(case_report, waveform, design_operating_point, "design_point", "Design Point")]


def build_current_operating_switch_stress_case(report: DesignReport, plugin: TopologyPlugin | None = None) -> SwitchStressCase | None:
    """Build the current operating-point semiconductor stress case."""

    if report.candidate is None or report.stress is None:
        return None

    operating_point = report.operating_point or _design_operating_point(report)
    if report.waveform is not None:
        return _build_case(report, report.waveform, operating_point, "current", "Current Operating Point")

    if plugin is None or report.spec.topology_id not in set(get_active_topology_ids()):
        return _fallback_case(report, case_id="current", label="Current Operating Point", operating_point=operating_point)

    waveform = plugin.generate_waveforms(report.candidate, operating_point=operating_point)
    if waveform is None:
        return _fallback_case(report, case_id="current", label="Current Operating Point", operating_point=operating_point)
    case_report = replace(
        report,
        operating_point=operating_point,
        waveform=waveform,
        stress=plugin.extract_stress(report.candidate, waveform_set=waveform),
    )
    return _build_case(case_report, waveform, operating_point, "current", "Current Operating Point")


def build_switch_stress_cases(report: DesignReport, plugin: TopologyPlugin | None = None) -> list[SwitchStressCase]:
    """Compatibility wrapper for callers that still expect design-point semiconductor cases."""

    return build_design_point_switch_stress_cases(report, plugin=plugin)


def _format_operating_point_note(label: str, operating_point: OperatingPoint, mode: str) -> str:
    power_factor = getattr(operating_point, "power_factor", None)
    pf_text = f", PF={float(power_factor):.6g}" if power_factor is not None else ""
    return f"{label}: Vin={operating_point.vin_v:.6g} V, load={operating_point.load_ratio:.6g}{pf_text}, mode={mode}."
