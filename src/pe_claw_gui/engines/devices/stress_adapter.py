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


def _series_rms(values: list[float]) -> float:
    return _rms([abs(value) for value in values])


def _series_avg(values: list[float]) -> float:
    return _mean([abs(value) for value in values])


def _series_peak(values: list[float]) -> float:
    return max((abs(value) for value in values), default=0.0)


def _series_duty(values: list[float]) -> float:
    if not values:
        return 0.0
    active_samples = sum(1 for value in values if abs(value) > 1e-12)
    return active_samples / len(values)


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


def _fallback_case(report: DesignReport, *, case_id: str, label: str, operating_point: OperatingPoint) -> SwitchStressCase | None:
    if report.candidate is None or report.stress is None:
        return None

    switching_period_s = 1.0 / max(report.candidate.fs_hz, 1e-9)
    duty = report.candidate.duty_nom
    mode = report.waveform.mode if report.waveform is not None else report.candidate.mode_capable.upper()
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
            f"{label}: Vin={operating_point.vin_v:.6g} V, load={operating_point.load_ratio:.6g}, mode={mode}.",
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
    if topology_id in {
        "buck_diode_rectified_unidirectional",
        "boost_diode_rectified_unidirectional",
        "buck_boost_diode_rectified_unidirectional",
    }:
        stresses = [
            _infer_main_switch_stress(report, waveform),
            _infer_rectifier_diode_stress(report, waveform),
        ]
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
    else:
        stresses = [_infer_main_switch_stress(report, waveform)]

    return SwitchStressCase(
        case_id=case_id,
        label=label,
        operating_point=operating_point,
        mode=waveform.mode,
        stresses=tuple(stresses),
        notes=[
            f"{label}: Vin={operating_point.vin_v:.6g} V, load={operating_point.load_ratio:.6g}, mode={waveform.mode}.",
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
