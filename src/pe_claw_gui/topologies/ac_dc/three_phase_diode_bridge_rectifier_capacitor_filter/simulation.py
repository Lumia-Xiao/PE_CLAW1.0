"""Time-domain model for a three-phase diode bridge capacitor-input rectifier."""

from __future__ import annotations

import math
from dataclasses import dataclass, field


_MIN_POSITIVE = 1e-12


def power_factor_requirement_status(
    achieved_pf: float,
    target_pf: float | None,
) -> str:
    """Classify an explicitly requested PF target without inventing one."""

    if target_pf is None:
        return "not_specified"
    return "pass" if achieved_pf >= target_pf else "infeasible_for_passive_topology"


@dataclass(frozen=True)
class ThreePhaseRectifierSimulationResult:
    """Final settled line-cycle waveforms and electrical metrics."""

    succeeded: bool
    metrics: dict[str, float | int | str | bool | None]
    waveforms: dict[str, list[float] | list[str]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def simulate_three_phase_capacitor_rectifier(
    *,
    vll_rms_v: float,
    f_line_hz: float,
    diode_forward_drop_v: float,
    source_resistance_per_phase_ohm: float,
    cout_f: float,
    rload_ohm: float,
    initial_vdc_v: float | None = None,
    minimum_cycles: int = 6,
    maximum_cycles: int = 40,
    samples_per_line_cycle: int = 10_000,
) -> ThreePhaseRectifierSimulationResult:
    """Simulate bridge charging pulses through two per-phase source resistances."""

    error = _validate_inputs(
        vll_rms_v,
        f_line_hz,
        diode_forward_drop_v,
        source_resistance_per_phase_ohm,
        cout_f,
        rload_ohm,
    )
    if error:
        return ThreePhaseRectifierSimulationResult(False, {"simulation_error": error}, warnings=[error])

    samples_per_line_cycle = max(int(samples_per_line_cycle), 3_000)
    minimum_cycles = max(int(minimum_cycles), 2)
    maximum_cycles = max(int(maximum_cycles), minimum_cycles)
    line_period_s = 1.0 / f_line_hz
    dt_s = line_period_s / samples_per_line_cycle
    omega_rad_s = 2.0 * math.pi * f_line_hz
    phase_peak_v = math.sqrt(2.0) * vll_rms_v / math.sqrt(3.0)
    peak_charge_limit_v = math.sqrt(2.0) * vll_rms_v - 2.0 * diode_forward_drop_v
    vdc_v = max(float(initial_vdc_v) if initial_vdc_v is not None else peak_charge_limit_v, 0.0)
    loop_resistance_ohm = 2.0 * source_resistance_per_phase_ohm

    final: dict[str, list[float] | list[str]] = {}
    cycle_start_v = vdc_v
    actual_cycles = 0
    for cycle_index in range(maximum_cycles):
        cycle = _empty_waveforms()
        cycle_start_v = vdc_v
        for sample_index in range(samples_per_line_cycle):
            t_local_s = sample_index * dt_s
            angle = omega_rad_s * t_local_s
            phases = (
                phase_peak_v * math.sin(angle),
                phase_peak_v * math.sin(angle - 2.0 * math.pi / 3.0),
                phase_peak_v * math.sin(angle + 2.0 * math.pi / 3.0),
            )
            high_index = max(range(3), key=lambda index: phases[index])
            low_index = min(range(3), key=lambda index: phases[index])
            rectified_open_v = phases[high_index] - phases[low_index] - 2.0 * diode_forward_drop_v
            bridge_current_a = max((rectified_open_v - vdc_v) / loop_resistance_ohm, 0.0)
            load_current_a = vdc_v / rload_ohm
            capacitor_current_a = bridge_current_a - load_current_a

            phase_currents = [0.0, 0.0, 0.0]
            diode_currents = [0.0] * 6
            if bridge_current_a > 0.0:
                phase_currents[high_index] = bridge_current_a
                phase_currents[low_index] = -bridge_current_a
                diode_currents[high_index] = bridge_current_a
                diode_currents[3 + low_index] = bridge_current_a

            _append_sample(
                cycle,
                t_local_s=t_local_s,
                phases=phases,
                phase_currents=phase_currents,
                diode_currents=diode_currents,
                high_index=high_index,
                low_index=low_index,
                rectified_open_v=rectified_open_v,
                vdc_v=vdc_v,
                bridge_current_a=bridge_current_a,
                load_current_a=load_current_a,
                capacitor_current_a=capacitor_current_a,
            )
            vdc_v = max(vdc_v + capacitor_current_a / cout_f * dt_s, 0.0)

        final = cycle
        actual_cycles = cycle_index + 1
        ripple_vpp = _peak_to_peak(_numeric(cycle, "vdc_v"))
        if actual_cycles >= minimum_cycles and abs(vdc_v - cycle_start_v) <= max(0.01, 1e-3 * ripple_vpp):
            break

    metrics = _build_metrics(
        final,
        vll_rms_v=vll_rms_v,
        f_line_hz=f_line_hz,
        diode_forward_drop_v=diode_forward_drop_v,
        source_resistance_per_phase_ohm=source_resistance_per_phase_ohm,
        cout_f=cout_f,
        rload_ohm=rload_ohm,
        dt_s=dt_s,
        cycles_simulated=actual_cycles,
        cycle_start_v=cycle_start_v,
        cycle_end_v=vdc_v,
    )
    return ThreePhaseRectifierSimulationResult(True, metrics, final)


def _empty_waveforms() -> dict[str, list[float] | list[str]]:
    return {
        key: []
        for key in (
            "time_s", "va_v", "vb_v", "vc_v", "vab_v", "vbc_v", "vca_v",
            "vrect_open_v", "vdc_v", "ia_a", "ib_a", "ic_a", "bridge_dc_current_a",
            "load_current_a", "capacitor_current_a", "d1_current_a", "d2_current_a",
            "d3_current_a", "d4_current_a", "d5_current_a", "d6_current_a",
            "upper_phase", "lower_phase",
        )
    }


def _append_sample(
    waveforms: dict[str, list[float] | list[str]],
    *,
    t_local_s: float,
    phases: tuple[float, float, float],
    phase_currents: list[float],
    diode_currents: list[float],
    high_index: int,
    low_index: int,
    rectified_open_v: float,
    vdc_v: float,
    bridge_current_a: float,
    load_current_a: float,
    capacitor_current_a: float,
) -> None:
    labels = ("A", "B", "C")
    values = {
        "time_s": t_local_s,
        "va_v": phases[0], "vb_v": phases[1], "vc_v": phases[2],
        "vab_v": phases[0] - phases[1], "vbc_v": phases[1] - phases[2], "vca_v": phases[2] - phases[0],
        "vrect_open_v": rectified_open_v, "vdc_v": vdc_v,
        "ia_a": phase_currents[0], "ib_a": phase_currents[1], "ic_a": phase_currents[2],
        "bridge_dc_current_a": bridge_current_a, "load_current_a": load_current_a,
        "capacitor_current_a": capacitor_current_a,
        "upper_phase": labels[high_index], "lower_phase": labels[low_index],
    }
    for index, current in enumerate(diode_currents, start=1):
        values[f"d{index}_current_a"] = current
    for key, value in values.items():
        waveforms[key].append(value)


def _build_metrics(
    waveforms: dict[str, list[float] | list[str]],
    *,
    vll_rms_v: float,
    f_line_hz: float,
    diode_forward_drop_v: float,
    source_resistance_per_phase_ohm: float,
    cout_f: float,
    rload_ohm: float,
    dt_s: float,
    cycles_simulated: int,
    cycle_start_v: float,
    cycle_end_v: float,
) -> dict[str, float | int | str | bool | None]:
    vdc = _numeric(waveforms, "vdc_v")
    ia, ib, ic = (_numeric(waveforms, key) for key in ("ia_a", "ib_a", "ic_a"))
    va, vb, vc = (_numeric(waveforms, key) for key in ("va_v", "vb_v", "vc_v"))
    bridge = _numeric(waveforms, "bridge_dc_current_a")
    load = _numeric(waveforms, "load_current_a")
    capacitor = _numeric(waveforms, "capacitor_current_a")
    input_power_w = _mean([a * x + b * y + c * z for a, b, c, x, y, z in zip(va, vb, vc, ia, ib, ic, strict=True)])
    phase_current_rms = _mean([_rms(ia), _rms(ib), _rms(ic)])
    apparent_power_va = math.sqrt(3.0) * vll_rms_v * phase_current_rms
    output_power_w = _mean([v * i for v, i in zip(vdc, load, strict=True)])
    source_loss_w = source_resistance_per_phase_ohm * _mean(
        [a * a + b * b + c * c for a, b, c in zip(ia, ib, ic, strict=True)]
    )
    diode_loss_w = 2.0 * diode_forward_drop_v * _mean(bridge)
    metrics: dict[str, float | int | str | bool | None] = {
        "simulation_succeeded": True,
        "simulation_basis": "three-phase capacitor charging-pulse state model",
        "cycles_simulated": cycles_simulated,
        "samples_per_line_cycle": len(vdc),
        "dt_s": dt_s,
        "vll_rms_v": vll_rms_v,
        "f_line_hz": f_line_hz,
        "ripple_frequency_hz": 6.0 * f_line_hz,
        "ripple_measurement_window": "final_settled_line_cycle",
        "ripple_measurement_cycles": 1,
        "ripple_definition": "peak_to_peak",
        "source_resistance_per_phase_ohm": source_resistance_per_phase_ohm,
        "source_resistance_definition": "per_phase; two phases conduct in each bridge pulse",
        "cdc_used_f": cout_f,
        "rload_used_ohm": rload_ohm,
        "vdc_avg_v": _mean(vdc),
        "vdc_min_v": min(vdc),
        "vdc_max_v": max(vdc),
        "vdc_ripple_pp_v": _peak_to_peak(vdc),
        "output_current_avg_a": _mean(load),
        "output_power_w": output_power_w,
        "input_real_power_w": input_power_w,
        "input_apparent_power_va": apparent_power_va,
        "power_factor": input_power_w / apparent_power_va if apparent_power_va > _MIN_POSITIVE else 0.0,
        "phase_a_current_rms_a": _rms(ia),
        "phase_b_current_rms_a": _rms(ib),
        "phase_c_current_rms_a": _rms(ic),
        "phase_current_rms_a": phase_current_rms,
        "phase_current_peak_a": max((abs(value) for value in [*ia, *ib, *ic]), default=0.0),
        "phase_current_sum_max_abs_a": max((abs(a + b + c) for a, b, c in zip(ia, ib, ic, strict=True)), default=0.0),
        "bridge_dc_current_avg_a": _mean(bridge),
        "bridge_dc_current_rms_a": _rms(bridge),
        "bridge_dc_current_peak_a": max(bridge, default=0.0),
        "capacitor_current_rms_a": _rms(capacitor),
        "capacitor_current_peak_a": max((abs(value) for value in capacitor), default=0.0),
        "capacitor_kcl_max_abs_error_a": max((abs(cap - (dc - load_i)) for cap, dc, load_i in zip(capacitor, bridge, load, strict=True)), default=0.0),
        "source_resistor_loss_w": source_loss_w,
        "diode_drop_loss_w": diode_loss_w,
        "power_balance_residual_w": input_power_w - source_loss_w - diode_loss_w - output_power_w,
        "final_cycle_vdc_start_v": cycle_start_v,
        "final_cycle_vdc_end_v": cycle_end_v,
        "final_cycle_delta_vdc_v": cycle_end_v - cycle_start_v,
        "periodic_steady_state_status": "converged" if abs(cycle_end_v - cycle_start_v) <= max(0.01, 1e-3 * _peak_to_peak(vdc)) else "warning",
    }
    for index in range(1, 7):
        current = _numeric(waveforms, f"d{index}_current_a")
        metrics[f"diode_d{index}_avg_current_a"] = _mean(current)
        metrics[f"diode_d{index}_rms_current_a"] = _rms(current)
        metrics[f"diode_d{index}_peak_current_a"] = max(current, default=0.0)
    return metrics


def _validate_inputs(
    vll_rms_v: float,
    f_line_hz: float,
    diode_forward_drop_v: float,
    source_resistance_per_phase_ohm: float,
    cout_f: float,
    rload_ohm: float,
) -> str:
    for label, value in (
        ("VLL rms", vll_rms_v), ("Line frequency", f_line_hz),
        ("Source resistance per phase", source_resistance_per_phase_ohm),
        ("Output capacitance", cout_f), ("Load resistance", rload_ohm),
    ):
        if not math.isfinite(float(value)) or float(value) <= 0.0:
            return f"{label} must be a finite positive number."
    if not math.isfinite(float(diode_forward_drop_v)) or diode_forward_drop_v < 0.0:
        return "Diode forward drop must be a finite non-negative number."
    return ""


def _numeric(waveforms: dict[str, list[float] | list[str]], key: str) -> list[float]:
    return [float(value) for value in waveforms.get(key, [])]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _rms(values: list[float]) -> float:
    return math.sqrt(_mean([value * value for value in values]))


def _peak_to_peak(values: list[float]) -> float:
    return max(values) - min(values) if values else 0.0
