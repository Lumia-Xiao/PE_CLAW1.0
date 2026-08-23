"""State-space simulation for the AC-DC diode bridge DC-side inductor filter."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

_MIN_POSITIVE = 1e-12
_ZERO_CURRENT_THRESHOLD_A = 1e-6
_OPEN_LOAD_OHM = 1e12
_POWER_TOLERANCE_RATIO = 0.01


@dataclass(frozen=True)
class DCInductorBridgeSimulationResult:
    """Time-domain result and summary metrics for one final line cycle."""

    succeeded: bool
    metrics: dict[str, float | int | str | bool | None]
    waveforms: dict[str, list[float]] = field(default_factory=dict)
    artifact_paths: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DCInductorLoadSolverResult:
    """Solved-load simulation result for a target output-power operating point."""

    rload_ohm: float
    simulation_result: DCInductorBridgeSimulationResult
    target_pout_w: float
    actual_pout_w: float
    relative_power_error: float
    status: str
    iterations: int
    warnings: list[str] = field(default_factory=list)


def simulate_ac_dc_diode_bridge_dc_inductor_filter(
    *,
    vac_rms_v: float,
    f_line_hz: float,
    pout_w: float,
    diode_forward_drop_v: float,
    ldc_h: float,
    cout_f: float,
    rload_ohm: float,
    source_resistance_ohm: float = 0.0,
    reactor_resistance_ohm: float = 0.0,
    initial_inductor_current_a: float | None = None,
    initial_vcap_v: float | None = None,
    cycles: int = 6,
    settling_cycles: int = 5,
    samples_per_line_cycle: int = 5000,
    max_cycles: int | None = None,
    artifact_dir: str | Path | None = None,
    artifact_suffix: str = "load_1p00",
    write_artifacts: bool = True,
) -> DCInductorBridgeSimulationResult:
    """Simulate a bridge rectifier feeding a DC choke and output capacitor."""

    validation_error = _validate_inputs(
        vac_rms_v,
        f_line_hz,
        pout_w,
        ldc_h,
        cout_f,
        rload_ohm,
        source_resistance_ohm,
        reactor_resistance_ohm,
    )
    if validation_error:
        return DCInductorBridgeSimulationResult(
            succeeded=False,
            metrics={"simulation_error": validation_error},
            warnings=[validation_error],
        )

    cycles = max(int(cycles), 6)
    settling_cycles = min(max(int(settling_cycles), 0), cycles - 1)
    samples_per_line_cycle = max(int(samples_per_line_cycle), 1000)
    minimum_cycles = max(cycles, settling_cycles + 1)
    max_cycles = max(int(max_cycles) if max_cycles is not None else 80, minimum_cycles)

    period_s = 1.0 / float(f_line_hz)
    dt_s = period_s / samples_per_line_cycle
    omega_rad_s = 2.0 * math.pi * float(f_line_hz)
    vac_peak_v = math.sqrt(2.0) * float(vac_rms_v)
    vcap_v = max(float(initial_vcap_v) if initial_vcap_v is not None else float(pout_w) ** 0.5 * float(rload_ohm) ** 0.5, 0.0)
    il_a = max(float(initial_inductor_current_a) if initial_inductor_current_a is not None else vcap_v / rload_ohm, 0.0)

    time_s: list[float] = []
    vg_v: list[float] = []
    vrect_v: list[float] = []
    vdc_v: list[float] = []
    il_series_a: list[float] = []
    ig_a: list[float] = []
    ic_a: list[float] = []
    iload_a: list[float] = []
    bridge_current_a: list[float] = []
    one_diode_a: list[float] = []
    dcm_flags: list[bool] = []
    bridge_conducting: list[float] = []
    v_l_v: list[float] = []
    final_cycle_start_step = 0
    final_cycle_end_step = 0
    vdc_start_v = vcap_v
    vdc_end_v = vcap_v
    il_start_a = il_a
    il_end_a = il_a
    e_start_j = _stored_energy_j(float(ldc_h), float(cout_f), il_a, vcap_v)
    e_end_j = e_start_j
    actual_cycles = 0

    dcm_interval_count = 0
    for cycle_index in range(max_cycles):
        cycle_start_step = cycle_index * samples_per_line_cycle
        cycle_time_s: list[float] = []
        cycle_vg_v: list[float] = []
        cycle_vrect_v: list[float] = []
        cycle_vdc_v: list[float] = []
        cycle_il_series_a: list[float] = []
        cycle_ig_a: list[float] = []
        cycle_ic_a: list[float] = []
        cycle_iload_a: list[float] = []
        cycle_bridge_current_a: list[float] = []
        cycle_one_diode_a: list[float] = []
        cycle_dcm_flags: list[bool] = []
        cycle_bridge_conducting: list[float] = []
        cycle_v_l_v: list[float] = []

        cycle_vdc_start_v = vcap_v
        cycle_il_start_a = il_a
        cycle_e_start_j = _stored_energy_j(float(ldc_h), float(cout_f), il_a, vcap_v)

        for sample_index in range(samples_per_line_cycle):
            step = cycle_start_step + sample_index
            t_s = step * dt_s
            vg = vac_peak_v * math.sin(omega_rad_s * t_s)
            vrect = abs(vg)
            total_series_resistance_ohm = float(source_resistance_ohm) + float(reactor_resistance_ohm)
            bridge_can_conduct = vrect > vcap_v + 2.0 * float(diode_forward_drop_v)
            bridge_is_conducting = il_a > _ZERO_CURRENT_THRESHOLD_A or bridge_can_conduct
            v_l_applied_v = (
                vrect
                - 2.0 * float(diode_forward_drop_v)
                - vcap_v
                - il_a * total_series_resistance_ohm
                if bridge_is_conducting
                else 0.0
            )

            if not bridge_is_conducting:
                il_next_a = 0.0
                dcm_now = True
            else:
                il_next_a = il_a + (v_l_applied_v / float(ldc_h)) * dt_s
                dcm_now = il_next_a < 0.0
                if dcm_now:
                    il_next_a = 0.0

            il_for_cap_a = 0.5 * (il_a + il_next_a) if bridge_is_conducting else 0.0
            iload = vcap_v / float(rload_ohm)
            cap_current_a = il_for_cap_a - iload
            bridge_current = il_for_cap_a if bridge_is_conducting and il_for_cap_a > _ZERO_CURRENT_THRESHOLD_A else 0.0
            vcap_next_v = max(vcap_v + (cap_current_a / float(cout_f)) * dt_s, 0.0)
            dcm_flag = dcm_now or not bridge_is_conducting or il_a <= _ZERO_CURRENT_THRESHOLD_A

            cycle_time_s.append(sample_index * dt_s)
            cycle_vg_v.append(vg)
            cycle_vrect_v.append(vrect)
            cycle_vdc_v.append(vcap_v)
            cycle_il_series_a.append(il_a)
            cycle_ig_a.append(_sign(vg) * bridge_current)
            cycle_ic_a.append(cap_current_a)
            cycle_iload_a.append(iload)
            cycle_bridge_current_a.append(bridge_current)
            cycle_one_diode_a.append(bridge_current if vg >= 0.0 else 0.0)
            cycle_dcm_flags.append(dcm_flag)
            cycle_bridge_conducting.append(1.0 if bridge_current > _ZERO_CURRENT_THRESHOLD_A else 0.0)
            cycle_v_l_v.append(v_l_applied_v if bridge_current > _ZERO_CURRENT_THRESHOLD_A else 0.0)

            if dcm_flag:
                dcm_interval_count += 1
            vcap_v = vcap_next_v
            il_a = il_next_a

        cycle_vdc_end_v = vcap_v
        cycle_il_end_a = il_a
        cycle_e_end_j = _stored_energy_j(float(ldc_h), float(cout_f), il_a, vcap_v)

        time_s = cycle_time_s
        vg_v = cycle_vg_v
        vrect_v = cycle_vrect_v
        vdc_v = cycle_vdc_v
        il_series_a = cycle_il_series_a
        ig_a = cycle_ig_a
        ic_a = cycle_ic_a
        iload_a = cycle_iload_a
        bridge_current_a = cycle_bridge_current_a
        one_diode_a = cycle_one_diode_a
        dcm_flags = cycle_dcm_flags
        bridge_conducting = cycle_bridge_conducting
        v_l_v = cycle_v_l_v
        final_cycle_start_step = cycle_start_step
        final_cycle_end_step = cycle_start_step + samples_per_line_cycle
        vdc_start_v = cycle_vdc_start_v
        vdc_end_v = cycle_vdc_end_v
        il_start_a = cycle_il_start_a
        il_end_a = cycle_il_end_a
        e_start_j = cycle_e_start_j
        e_end_j = cycle_e_end_j
        actual_cycles = cycle_index + 1

        if actual_cycles >= minimum_cycles and _cycle_boundary_is_periodic(
            cycle_vdc_v=cycle_vdc_v,
            cycle_il_a=cycle_il_series_a,
            cycle_iload_a=cycle_iload_a,
            cycle_vdc_start_v=cycle_vdc_start_v,
            cycle_vdc_end_v=cycle_vdc_end_v,
            cycle_il_start_a=cycle_il_start_a,
            cycle_il_end_a=cycle_il_end_a,
            cycle_e_start_j=cycle_e_start_j,
            cycle_e_end_j=cycle_e_end_j,
            period_s=period_s,
        ):
            break

    metrics = _build_metrics(
        vac_rms_v=float(vac_rms_v),
        vac_peak_v=vac_peak_v,
        diode_forward_drop_v=float(diode_forward_drop_v),
        ldc_h=float(ldc_h),
        cout_f=float(cout_f),
        rload_ohm=float(rload_ohm),
        source_resistance_ohm=float(source_resistance_ohm),
        reactor_resistance_ohm=float(reactor_resistance_ohm),
        cycles=actual_cycles,
        settling_cycles=max(actual_cycles - 1, 0),
        samples_per_line_cycle=samples_per_line_cycle,
        final_cycle_start_step=final_cycle_start_step,
        final_cycle_end_step=final_cycle_end_step,
        line_period_s=period_s,
        dt_s=dt_s,
        time_s=time_s,
        vg_v=vg_v,
        vdc_v=vdc_v,
        il_a=il_series_a,
        ig_a=ig_a,
        ic_a=ic_a,
        iload_a=iload_a,
        bridge_current_a=bridge_current_a,
        one_diode_a=one_diode_a,
        dcm_flags=dcm_flags,
        bridge_conducting=bridge_conducting,
        v_l_v=v_l_v,
        vdc_start_v=vdc_start_v,
        vdc_end_v=vdc_end_v,
        il_start_a=il_start_a,
        il_end_a=il_end_a,
        e_start_j=e_start_j,
        e_end_j=e_end_j,
        total_dcm_interval_count=dcm_interval_count,
    )
    if not _metrics_are_finite(metrics):
        warning = "AC-DC DC-side inductor simulation produced non-finite metrics."
        return DCInductorBridgeSimulationResult(succeeded=False, metrics=metrics, warnings=[warning])

    waveforms = {
        "time_s": time_s,
        "vg_v": vg_v,
        "vrect_v": vrect_v,
        "vdc_v": vdc_v,
        "iL_a": il_series_a,
        "ig_a": ig_a,
        "iC_a": ic_a,
        "iload_a": iload_a,
        "bridge_current_a": bridge_current_a,
        "bridge_conducting": bridge_conducting,
    }
    if write_artifacts:
        artifact_paths = _write_artifacts(artifact_dir, waveforms, metrics, artifact_suffix=artifact_suffix)
        metrics["waveform_csv_path"] = artifact_paths.get("waveform_csv", "")
        metrics["summary_json_path"] = artifact_paths.get("summary_json", "")
        metrics["waveform_png_path"] = artifact_paths.get("waveform_png", "")
    else:
        artifact_paths = {}
        metrics["waveform_csv_path"] = ""
        metrics["summary_json_path"] = ""
        metrics["waveform_png_path"] = ""
    return DCInductorBridgeSimulationResult(
        succeeded=True,
        metrics=metrics,
        waveforms=waveforms,
        artifact_paths=artifact_paths,
    )


def solve_rload_for_target_power_dc_inductor(
    *,
    vac_rms_v: float,
    f_line_hz: float,
    diode_forward_drop_v: float,
    ldc_h: float,
    cout_f: float,
    target_pout_w: float,
    initial_vdc_est_v: float,
    initial_rload_guess_ohm: float,
    cycles: int = 6,
    settling_cycles: int = 5,
    solver_samples_per_line_cycle: int = 1500,
    final_samples_per_line_cycle: int = 5000,
    max_iterations: int = 25,
    artifact_dir: str | Path | None = None,
    artifact_suffix: str = "load_1p00",
) -> DCInductorLoadSolverResult:
    """Solve Rload so final-cycle load power matches the requested target."""

    target_pout_w = max(float(target_pout_w), 0.0)
    if target_pout_w <= 0.0:
        simulation = simulate_ac_dc_diode_bridge_dc_inductor_filter(
            vac_rms_v=vac_rms_v,
            f_line_hz=f_line_hz,
            pout_w=_MIN_POSITIVE,
            diode_forward_drop_v=diode_forward_drop_v,
            ldc_h=ldc_h,
            cout_f=cout_f,
            rload_ohm=_OPEN_LOAD_OHM,
            initial_inductor_current_a=0.0,
            initial_vcap_v=initial_vdc_est_v,
            cycles=cycles,
            settling_cycles=settling_cycles,
            samples_per_line_cycle=final_samples_per_line_cycle,
            artifact_dir=artifact_dir,
            artifact_suffix=artifact_suffix,
        )
        actual_pout_w = _metric_float(simulation.metrics, "load_power_w")
        _annotate_load_solver_metrics(
            simulation.metrics,
            target_pout_w=0.0,
            actual_pout_w=actual_pout_w,
            rload_ohm=_OPEN_LOAD_OHM,
            status="no-load",
            iterations=0,
        )
        return DCInductorLoadSolverResult(
            rload_ohm=_OPEN_LOAD_OHM,
            simulation_result=simulation,
            target_pout_w=0.0,
            actual_pout_w=actual_pout_w,
            relative_power_error=0.0,
            status="no-load",
            iterations=0,
            warnings=["No-load waveform uses near-open-load approximation; PF may be not meaningful."],
        )

    tolerance_w = max(1.0, _POWER_TOLERANCE_RATIO * target_pout_w)
    r_nom_ohm = _initial_rload_guess(initial_vdc_est_v, initial_rload_guess_ohm, target_pout_w)
    r_low_ohm = max(r_nom_ohm / 10.0, _MIN_POSITIVE)
    r_high_ohm = r_nom_ohm * 10.0
    warnings: list[str] = []

    low_result = _simulate_for_solver(
        vac_rms_v=vac_rms_v,
        f_line_hz=f_line_hz,
        diode_forward_drop_v=diode_forward_drop_v,
        ldc_h=ldc_h,
        cout_f=cout_f,
        target_pout_w=target_pout_w,
        initial_vdc_est_v=initial_vdc_est_v,
        rload_ohm=r_low_ohm,
        cycles=cycles,
        settling_cycles=settling_cycles,
        samples_per_line_cycle=solver_samples_per_line_cycle,
    )
    high_result = _simulate_for_solver(
        vac_rms_v=vac_rms_v,
        f_line_hz=f_line_hz,
        diode_forward_drop_v=diode_forward_drop_v,
        ldc_h=ldc_h,
        cout_f=cout_f,
        target_pout_w=target_pout_w,
        initial_vdc_est_v=initial_vdc_est_v,
        rload_ohm=r_high_ohm,
        cycles=cycles,
        settling_cycles=settling_cycles,
        samples_per_line_cycle=solver_samples_per_line_cycle,
    )
    p_low_w = _metric_float(low_result.metrics, "load_power_w")
    p_high_w = _metric_float(high_result.metrics, "load_power_w")

    bracket_iterations = 0
    while p_low_w < target_pout_w and bracket_iterations < 12:
        r_low_ohm = max(r_low_ohm / 2.0, _MIN_POSITIVE)
        low_result = _simulate_for_solver(
            vac_rms_v=vac_rms_v,
            f_line_hz=f_line_hz,
            diode_forward_drop_v=diode_forward_drop_v,
            ldc_h=ldc_h,
            cout_f=cout_f,
            target_pout_w=target_pout_w,
            initial_vdc_est_v=initial_vdc_est_v,
            rload_ohm=r_low_ohm,
            cycles=cycles,
            settling_cycles=settling_cycles,
            samples_per_line_cycle=solver_samples_per_line_cycle,
        )
        p_low_w = _metric_float(low_result.metrics, "load_power_w")
        bracket_iterations += 1
    while p_high_w > target_pout_w and bracket_iterations < 24:
        r_high_ohm *= 2.0
        high_result = _simulate_for_solver(
            vac_rms_v=vac_rms_v,
            f_line_hz=f_line_hz,
            diode_forward_drop_v=diode_forward_drop_v,
            ldc_h=ldc_h,
            cout_f=cout_f,
            target_pout_w=target_pout_w,
            initial_vdc_est_v=initial_vdc_est_v,
            rload_ohm=r_high_ohm,
            cycles=cycles,
            settling_cycles=settling_cycles,
            samples_per_line_cycle=solver_samples_per_line_cycle,
        )
        p_high_w = _metric_float(high_result.metrics, "load_power_w")
        bracket_iterations += 1

    best_r_ohm = r_low_ohm if abs(p_low_w - target_pout_w) <= abs(p_high_w - target_pout_w) else r_high_ohm
    best_pout_w = p_low_w if best_r_ohm == r_low_ohm else p_high_w
    status = "converged"
    iterations = 0
    if not (p_low_w >= target_pout_w >= p_high_w):
        status = "failed"
        warnings.append("Load-power solver could not bracket the target output power.")
    else:
        for iteration in range(max(int(max_iterations), 1)):
            iterations = iteration + 1
            r_mid_ohm = 0.5 * (r_low_ohm + r_high_ohm)
            mid_result = _simulate_for_solver(
                vac_rms_v=vac_rms_v,
                f_line_hz=f_line_hz,
                diode_forward_drop_v=diode_forward_drop_v,
                ldc_h=ldc_h,
                cout_f=cout_f,
                target_pout_w=target_pout_w,
                initial_vdc_est_v=initial_vdc_est_v,
                rload_ohm=r_mid_ohm,
                cycles=cycles,
                settling_cycles=settling_cycles,
                samples_per_line_cycle=solver_samples_per_line_cycle,
            )
            p_mid_w = _metric_float(mid_result.metrics, "load_power_w")
            if abs(p_mid_w - target_pout_w) < abs(best_pout_w - target_pout_w):
                best_r_ohm = r_mid_ohm
                best_pout_w = p_mid_w
            if abs(p_mid_w - target_pout_w) <= tolerance_w:
                best_r_ohm = r_mid_ohm
                best_pout_w = p_mid_w
                break
            if p_mid_w >= target_pout_w:
                r_low_ohm = r_mid_ohm
            else:
                r_high_ohm = r_mid_ohm

    final_simulation = simulate_ac_dc_diode_bridge_dc_inductor_filter(
        vac_rms_v=vac_rms_v,
        f_line_hz=f_line_hz,
        pout_w=target_pout_w,
        diode_forward_drop_v=diode_forward_drop_v,
        ldc_h=ldc_h,
        cout_f=cout_f,
        rload_ohm=best_r_ohm,
        initial_inductor_current_a=target_pout_w / max(initial_vdc_est_v, _MIN_POSITIVE),
        initial_vcap_v=initial_vdc_est_v,
        cycles=cycles,
        settling_cycles=settling_cycles,
        samples_per_line_cycle=final_samples_per_line_cycle,
        artifact_dir=artifact_dir,
        artifact_suffix=artifact_suffix,
    )
    final_pout_w = _metric_float(final_simulation.metrics, "load_power_w")
    relative_error = abs(final_pout_w - target_pout_w) / max(target_pout_w, _MIN_POSITIVE)
    if status == "converged" and relative_error > _POWER_TOLERANCE_RATIO:
        status = "final-error-above-tolerance"
        warnings.append("Final high-resolution simulation load power exceeded the 1% target tolerance.")
    _annotate_load_solver_metrics(
        final_simulation.metrics,
        target_pout_w=target_pout_w,
        actual_pout_w=final_pout_w,
        rload_ohm=best_r_ohm,
        status=status,
        iterations=iterations + bracket_iterations,
    )
    return DCInductorLoadSolverResult(
        rload_ohm=best_r_ohm,
        simulation_result=final_simulation,
        target_pout_w=target_pout_w,
        actual_pout_w=final_pout_w,
        relative_power_error=relative_error,
        status=status,
        iterations=iterations + bracket_iterations,
        warnings=warnings,
    )


def _validate_inputs(
    vac_rms_v: float,
    f_line_hz: float,
    pout_w: float,
    ldc_h: float,
    cout_f: float,
    rload_ohm: float,
    source_resistance_ohm: float,
    reactor_resistance_ohm: float,
) -> str:
    for label, value in (
        ("Vac rms", vac_rms_v),
        ("Line frequency", f_line_hz),
        ("Output power", pout_w),
        ("DC-side inductance", ldc_h),
        ("Output capacitance", cout_f),
        ("Load resistance", rload_ohm),
    ):
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return f"{label} must be a finite positive number."
        if not math.isfinite(numeric) or numeric <= 0.0:
            return f"{label} must be a finite positive number."
    for label, value in (
        ("Source resistance", source_resistance_ohm),
        ("Reactor resistance", reactor_resistance_ohm),
    ):
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return f"{label} must be a finite non-negative number."
        if not math.isfinite(numeric) or numeric < 0.0:
            return f"{label} must be a finite non-negative number."
    return ""


def _build_metrics(
    *,
    vac_rms_v: float,
    vac_peak_v: float,
    diode_forward_drop_v: float,
    ldc_h: float,
    cout_f: float,
    rload_ohm: float,
    source_resistance_ohm: float,
    reactor_resistance_ohm: float,
    cycles: int,
    settling_cycles: int,
    samples_per_line_cycle: int,
    final_cycle_start_step: int,
    final_cycle_end_step: int,
    line_period_s: float,
    dt_s: float,
    time_s: list[float],
    vg_v: list[float],
    vdc_v: list[float],
    il_a: list[float],
    ig_a: list[float],
    ic_a: list[float],
    iload_a: list[float],
    bridge_current_a: list[float],
    one_diode_a: list[float],
    dcm_flags: list[bool],
    bridge_conducting: list[float],
    v_l_v: list[float],
    vdc_start_v: float,
    vdc_end_v: float,
    il_start_a: float,
    il_end_a: float,
    e_start_j: float,
    e_end_j: float,
    total_dcm_interval_count: int,
) -> dict[str, float | int | str | bool | None]:
    vdc_avg_v = _mean(vdc_v)
    vdc_min_v = min(vdc_v) if vdc_v else 0.0
    vdc_max_v = max(vdc_v) if vdc_v else 0.0
    vdc_ripple_pp_v = vdc_max_v - vdc_min_v
    il_avg_a = _mean(il_a)
    il_min_a = min(il_a) if il_a else 0.0
    il_peak_a = max(il_a) if il_a else 0.0
    il_ripple_pp_a = il_peak_a - il_min_a
    final_cycle_duration_s = samples_per_line_cycle * dt_s
    input_current_rms_a = _rms(ig_a)
    bridge_current_rms_a = _rms(bridge_current_a)
    bridge_current_peak_a = max(bridge_current_a) if bridge_current_a else 0.0
    capacitor_current_rms_a = _rms(ic_a)
    bridge_conduction_fraction = sum(1 for value in bridge_conducting if value > 0.0) / max(len(bridge_conducting), 1)
    bridge_conduction_angle_line_deg = 360.0 * bridge_conduction_fraction
    bridge_conduction_angle_half_cycle_deg = 180.0 * bridge_conduction_fraction
    bridge_pulse_count = _count_conduction_pulses(bridge_conducting)
    bridge_average_pulse_width_s = (
        bridge_conduction_fraction * final_cycle_duration_s / bridge_pulse_count
        if bridge_pulse_count > 0
        else 0.0
    )
    input_real_power_w = _mean([v * i for v, i in zip(vg_v, ig_a, strict=True)])
    prect_ac_side_w = _mean([abs(v) * i for v, i in zip(vg_v, bridge_current_a, strict=True)])
    apparent_power_va = vac_rms_v * input_current_rms_a
    dcm_fraction = sum(1 for value in dcm_flags if value) / max(len(dcm_flags), 1)
    i1_rms_a = _fundamental_rms(time_s, ig_a, 1.0 / (time_s[-1] - time_s[0] + (time_s[1] - time_s[0])) if len(time_s) > 1 else 0.0)
    thd = None
    if i1_rms_a > _MIN_POSITIVE:
        harmonic_rms_sq = max(input_current_rms_a * input_current_rms_a - i1_rms_a * i1_rms_a, 0.0)
        thd = math.sqrt(harmonic_rms_sq) / i1_rms_a
    psource_w = input_real_power_w
    pafter_diode_w = _mean([(abs(vg) - 2.0 * diode_forward_drop_v) * current for vg, current in zip(vg_v, bridge_current_a, strict=True)])
    pdiode_drop_w = _mean([2.0 * diode_forward_drop_v * current for current in bridge_current_a])
    pload_w = _mean([v * i for v, i in zip(vdc_v, iload_a, strict=True)])
    pcap_avg_w = _mean([v * i for v, i in zip(vdc_v, ic_a, strict=True)])
    pinductor_avg_w = _mean([v * i for v, i in zip(v_l_v, bridge_current_a, strict=True)])
    delta_vdc_cycle_v = vdc_end_v - vdc_start_v
    delta_il_cycle_a = il_end_a - il_start_a
    delta_energy_cycle_j = e_end_j - e_start_j
    energy_drift_power_w = delta_energy_cycle_j / max(final_cycle_duration_s, _MIN_POSITIVE)
    power_residual_w = psource_w - pdiode_drop_w - pload_w - energy_drift_power_w
    source_vs_rectifier_error_w = psource_w - prect_ac_side_w
    residual_limit_w = max(5.0, 0.05 * max(pload_w, 1.0))
    mapping_limit_w = max(2.0, 0.02 * max(abs(psource_w), 1.0))
    power_balance_status = (
        "warning"
        if abs(power_residual_w) > residual_limit_w or abs(source_vs_rectifier_error_w) > mapping_limit_w
        else "balanced"
    )
    vdc_boundary_limit_v = max(0.1, 0.01 * max(vdc_ripple_pp_v, 0.0))
    il_boundary_limit_a = max(0.01, 0.01 * max(il_ripple_pp_a, 0.0))
    energy_drift_limit_w = max(2.0, 0.02 * max(pload_w, 1.0))
    periodic_steady_state_status = (
        "warning"
        if (
            abs(delta_vdc_cycle_v) > vdc_boundary_limit_v
            or abs(delta_il_cycle_a) > il_boundary_limit_a
            or abs(energy_drift_power_w) > energy_drift_limit_w
        )
        else "converged"
    )
    return {
        "simulation_succeeded": True,
        "simulation_basis": "state-space DC-side inductor diode bridge",
        "cycles_simulated": cycles,
        "settling_cycles_discarded": settling_cycles,
        "samples_per_line_cycle": samples_per_line_cycle,
        "final_cycle_sample_count": len(time_s),
        "final_cycle_start_step": final_cycle_start_step,
        "final_cycle_end_step": final_cycle_end_step,
        "final_cycle_window_s": final_cycle_duration_s,
        "expected_line_period_s": line_period_s,
        "dt_s": dt_s,
        "ldc_used_h": ldc_h,
        "cout_used_f": cout_f,
        "rload_used_ohm": rload_ohm,
        "source_resistance_used_ohm": source_resistance_ohm,
        "reactor_resistance_used_ohm": reactor_resistance_ohm,
        "vdc_avg_v": vdc_avg_v,
        "vdc_min_v": vdc_min_v,
        "vdc_max_v": vdc_max_v,
        "vdc_ripple_pp_v": vdc_ripple_pp_v,
        "vdc_ripple_ratio": vdc_ripple_pp_v / max(vdc_avg_v, _MIN_POSITIVE),
        "il_avg_a": il_avg_a,
        "il_min_a": il_min_a,
        "il_peak_a": il_peak_a,
        "il_ripple_pp_a": il_ripple_pp_a,
        "il_ripple_ratio_pp_avg": il_ripple_pp_a / max(il_avg_a, _MIN_POSITIVE),
        "il_rms_a": _rms(il_a),
        "ccm_dcm_status": "DCM" if dcm_fraction > 0.0 or il_min_a <= _ZERO_CURRENT_THRESHOLD_A else "CCM",
        "zero_current_fraction": dcm_fraction,
        "total_dcm_interval_count": total_dcm_interval_count,
        "input_current_rms_a": input_current_rms_a,
        "input_current_peak_a": max((abs(value) for value in ig_a), default=0.0),
        "input_real_power_w": input_real_power_w,
        "apparent_power_va": apparent_power_va,
        "power_factor": input_real_power_w / apparent_power_va if apparent_power_va > _MIN_POSITIVE else 0.0,
        "input_current_fundamental_rms_a": i1_rms_a,
        "input_current_thd": thd,
        "diode_reverse_stress_v": vac_peak_v,
        "per_diode_avg_current_a": _mean(one_diode_a),
        "per_diode_rms_current_a": _rms(one_diode_a),
        "per_diode_peak_current_a": max(bridge_current_a) if bridge_current_a else 0.0,
        "bridge_current_rms_a": bridge_current_rms_a,
        "bridge_current_peak_a": bridge_current_peak_a,
        "bridge_conduction_fraction": bridge_conduction_fraction,
        "bridge_conduction_angle_line_deg": bridge_conduction_angle_line_deg,
        "bridge_conduction_angle_half_cycle_deg": bridge_conduction_angle_half_cycle_deg,
        "bridge_pulse_count_per_line_cycle": bridge_pulse_count,
        "bridge_average_pulse_width_s": bridge_average_pulse_width_s,
        "capacitor_current_rms_a": capacitor_current_rms_a,
        "capacitor_current_peak_a": max((abs(value) for value in ic_a), default=0.0),
        "load_current_avg_a": _mean(iload_a),
        "load_power_w": pload_w,
        "rectified_side_source_power_w": prect_ac_side_w,
        "after_diode_power_w": pafter_diode_w,
        "diode_drop_power_w": pdiode_drop_w,
        "capacitor_average_power_w": pcap_avg_w,
        "inductor_average_power_w": pinductor_avg_w,
        "final_cycle_vdc_start_v": vdc_start_v,
        "final_cycle_vdc_end_v": vdc_end_v,
        "final_cycle_delta_vdc_v": delta_vdc_cycle_v,
        "final_cycle_il_start_a": il_start_a,
        "final_cycle_il_end_a": il_end_a,
        "final_cycle_delta_il_a": delta_il_cycle_a,
        "final_cycle_stored_energy_start_j": e_start_j,
        "final_cycle_stored_energy_end_j": e_end_j,
        "final_cycle_delta_energy_j": delta_energy_cycle_j,
        "energy_drift_power_w": energy_drift_power_w,
        "power_residual_w": power_residual_w,
        "source_vs_rectifier_error_w": source_vs_rectifier_error_w,
        "power_balance_status": power_balance_status,
        "periodic_steady_state_status": periodic_steady_state_status,
        "power_balance_warning": (
            "Power balance residual is larger than expected; inspect bridge current and input current mapping."
            if power_balance_status == "warning"
            else ""
        ),
        "periodic_steady_state_warning": (
            "Final-cycle boundary states are not sufficiently periodic; inspect slicing or settling."
            if periodic_steady_state_status == "warning"
            else ""
        ),
        "ripple_frequency_hz": 2.0 / max(line_period_s, _MIN_POSITIVE),
        "ripple_measurement_window": "final_settled_line_cycle",
        "ripple_measurement_cycles": 1,
        "ripple_definition": "peak_to_peak",
        "output_current_avg_a": _mean(iload_a),
        "output_power_w": pload_w,
        "vout_achieved_v": vdc_avg_v,
        "iout_achieved_a": _mean(iload_a),
        "pout_achieved_w": pload_w,
        "diode_d1_avg_current_a": _mean(one_diode_a),
        "diode_d1_rms_current_a": _rms(one_diode_a),
        "diode_d1_peak_current_a": max(one_diode_a) if one_diode_a else 0.0,
        "diode_d2_avg_current_a": _mean(one_diode_a),
        "diode_d2_rms_current_a": _rms(one_diode_a),
        "diode_d2_peak_current_a": max(one_diode_a) if one_diode_a else 0.0,
        "diode_d3_avg_current_a": _mean(one_diode_a),
        "diode_d3_rms_current_a": _rms(one_diode_a),
        "diode_d3_peak_current_a": max(one_diode_a) if one_diode_a else 0.0,
        "diode_d4_avg_current_a": _mean(one_diode_a),
        "diode_d4_rms_current_a": _rms(one_diode_a),
        "diode_d4_peak_current_a": max(one_diode_a) if one_diode_a else 0.0,
    }


def _simulate_for_solver(
    *,
    vac_rms_v: float,
    f_line_hz: float,
    diode_forward_drop_v: float,
    ldc_h: float,
    cout_f: float,
    target_pout_w: float,
    initial_vdc_est_v: float,
    rload_ohm: float,
    cycles: int,
    settling_cycles: int,
    samples_per_line_cycle: int,
) -> DCInductorBridgeSimulationResult:
    return simulate_ac_dc_diode_bridge_dc_inductor_filter(
        vac_rms_v=vac_rms_v,
        f_line_hz=f_line_hz,
        pout_w=max(target_pout_w, _MIN_POSITIVE),
        diode_forward_drop_v=diode_forward_drop_v,
        ldc_h=ldc_h,
        cout_f=cout_f,
        rload_ohm=rload_ohm,
        initial_inductor_current_a=target_pout_w / max(initial_vdc_est_v, _MIN_POSITIVE),
        initial_vcap_v=initial_vdc_est_v,
        cycles=cycles,
        settling_cycles=settling_cycles,
        samples_per_line_cycle=samples_per_line_cycle,
        write_artifacts=False,
    )


def _initial_rload_guess(initial_vdc_est_v: float, initial_rload_guess_ohm: float, target_pout_w: float) -> float:
    try:
        guess = float(initial_rload_guess_ohm)
    except (TypeError, ValueError):
        guess = 0.0
    if math.isfinite(guess) and guess > 0.0:
        return guess
    return max(float(initial_vdc_est_v) * float(initial_vdc_est_v) / max(target_pout_w, _MIN_POSITIVE), _MIN_POSITIVE)


def _annotate_load_solver_metrics(
    metrics: dict[str, float | int | str | bool | None],
    *,
    target_pout_w: float,
    actual_pout_w: float,
    rload_ohm: float,
    status: str,
    iterations: int,
) -> None:
    metrics["target_output_power_w"] = target_pout_w
    metrics["simulated_load_power_w"] = actual_pout_w
    metrics["load_power_error_w"] = actual_pout_w - target_pout_w
    metrics["load_power_error_percent"] = (
        0.0 if target_pout_w <= 0.0 else 100.0 * (actual_pout_w - target_pout_w) / target_pout_w
    )
    metrics["solved_rload_ohm"] = rload_ohm
    metrics["load_solver_status"] = status
    metrics["load_solver_iterations"] = iterations


def _metric_float(metrics: dict[str, float | int | str | bool | None], key: str) -> float:
    try:
        value = float(metrics.get(key, 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0
    return value if math.isfinite(value) else 0.0


def _write_artifacts(
    artifact_dir: str | Path | None,
    waveforms: dict[str, list[float]],
    metrics: dict[str, float | int | str | bool | None],
    *,
    artifact_suffix: str,
) -> dict[str, str]:
    output_dir = Path(artifact_dir) if artifact_dir is not None else Path("outputs") / "ac_dc_rectifier_inductor_filter"
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_suffix = _safe_artifact_suffix(artifact_suffix)
    stem = f"single_phase_diode_bridge_dc_inductor_waveforms{safe_suffix}"
    waveform_path = output_dir / f"{stem}.csv"
    summary_path = output_dir / f"single_phase_diode_bridge_dc_inductor_summary{safe_suffix}.json"
    plot_path = output_dir / f"{stem}.png"

    columns = ["time_s", "vg_v", "vrect_v", "vdc_v", "iL_a", "ig_a", "iC_a", "iload_a", "bridge_current_a", "bridge_conducting"]
    with waveform_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        for row in zip(*(waveforms[column] for column in columns), strict=True):
            writer.writerow([f"{float(value):.12g}" for value in row])

    with summary_path.open("w", encoding="utf-8") as stream:
        json.dump({"metrics": metrics}, stream, indent=2, sort_keys=True)

    _write_waveform_png(plot_path, waveforms)
    return {"waveform_csv": str(waveform_path), "summary_json": str(summary_path), "waveform_png": str(plot_path)}


def _cycle_boundary_is_periodic(
    *,
    cycle_vdc_v: list[float],
    cycle_il_a: list[float],
    cycle_iload_a: list[float],
    cycle_vdc_start_v: float,
    cycle_vdc_end_v: float,
    cycle_il_start_a: float,
    cycle_il_end_a: float,
    cycle_e_start_j: float,
    cycle_e_end_j: float,
    period_s: float,
) -> bool:
    """Return True when the last cycle is close enough to periodic steady state."""

    vdc_ripple_pp_v = (max(cycle_vdc_v) - min(cycle_vdc_v)) if cycle_vdc_v else 0.0
    il_ripple_pp_a = (max(cycle_il_a) - min(cycle_il_a)) if cycle_il_a else 0.0
    pload_w = _mean([v * i for v, i in zip(cycle_vdc_v, cycle_iload_a, strict=True)])
    energy_drift_power_w = (cycle_e_end_j - cycle_e_start_j) / max(period_s, _MIN_POSITIVE)
    return (
        abs(cycle_vdc_end_v - cycle_vdc_start_v) <= max(0.1, 0.01 * max(vdc_ripple_pp_v, 0.0))
        and abs(cycle_il_end_a - cycle_il_start_a) <= max(0.01, 0.01 * max(il_ripple_pp_a, 0.0))
        and abs(energy_drift_power_w) <= max(2.0, 0.02 * max(pload_w, 1.0))
    )


def _write_waveform_png(plot_path: Path, waveforms: dict[str, list[float]]) -> None:
    time_ms = [value * 1e3 for value in waveforms["time_s"]]
    figure = Figure(figsize=(10, 7), dpi=120)
    FigureCanvasAgg(figure)
    voltage_ax = figure.add_subplot(3, 1, 1)
    current_ax = figure.add_subplot(3, 1, 2)
    ripple_ax = figure.add_subplot(3, 1, 3)

    voltage_ax.plot(time_ms, waveforms["vg_v"], linewidth=1.0, label="vg")
    voltage_ax.plot(time_ms, waveforms["vrect_v"], linewidth=1.0, label="vrect")
    voltage_ax.plot(time_ms, waveforms["vdc_v"], linewidth=1.2, label="vdc")
    voltage_ax.set_ylabel("Voltage [V]")
    voltage_ax.grid(True, alpha=0.35)
    voltage_ax.legend(loc="upper right", fontsize=8)

    current_ax.plot(time_ms, waveforms["iL_a"], linewidth=1.0, label="iL")
    current_ax.plot(time_ms, waveforms["ig_a"], linewidth=1.0, label="ig")
    current_ax.plot(time_ms, waveforms["iC_a"], linewidth=1.0, label="iC")
    current_ax.plot(time_ms, waveforms["iload_a"], linewidth=1.0, label="iload")
    current_ax.set_ylabel("Current [A]")
    current_ax.grid(True, alpha=0.35)
    current_ax.legend(loc="upper right", fontsize=8)

    vdc_avg_v = _mean(waveforms["vdc_v"])
    ripple_ax.plot(time_ms, [value - vdc_avg_v for value in waveforms["vdc_v"]], linewidth=1.0, label="vdc ripple")
    ripple_ax.set_xlabel("Time [ms]")
    ripple_ax.set_ylabel("Ripple [V]")
    ripple_ax.grid(True, alpha=0.35)
    ripple_ax.legend(loc="upper right", fontsize=8)

    if time_ms:
        for axis in (voltage_ax, current_ax, ripple_ax):
            axis.set_xlim(time_ms[0], time_ms[-1])

    figure.suptitle("Single-phase diode bridge DC-side inductor waveforms\nState-space first-pass simulation", fontsize=10)
    figure.tight_layout(rect=[0, 0, 1, 0.92])
    figure.savefig(plot_path)


def _fundamental_rms(time_s: list[float], current_a: list[float], f_line_hz: float) -> float:
    if len(time_s) < 2 or len(current_a) != len(time_s) or f_line_hz <= 0.0:
        return 0.0
    omega = 2.0 * math.pi * f_line_hz
    sin_coeff = 2.0 * _mean([i * math.sin(omega * t) for t, i in zip(time_s, current_a, strict=True)])
    cos_coeff = 2.0 * _mean([i * math.cos(omega * t) for t, i in zip(time_s, current_a, strict=True)])
    return math.sqrt(sin_coeff * sin_coeff + cos_coeff * cos_coeff) / math.sqrt(2.0)


def _safe_artifact_suffix(artifact_suffix: str) -> str:
    if not artifact_suffix:
        return ""
    safe = "".join(char if char.isalnum() else "_" for char in artifact_suffix.strip())
    return f"_{safe.strip('_')}" if safe.strip("_") else ""


def _stored_energy_j(ldc_h: float, cout_f: float, il_a: float, vcap_v: float) -> float:
    return 0.5 * ldc_h * il_a * il_a + 0.5 * cout_f * vcap_v * vcap_v


def _sign(value: float) -> float:
    if value > 0.0:
        return 1.0
    if value < 0.0:
        return -1.0
    return 0.0


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _rms(values: list[float]) -> float:
    return math.sqrt(_mean([value * value for value in values]))


def _count_conduction_pulses(conduction_flags: list[float]) -> int:
    pulse_count = 0
    was_on = False
    for value in conduction_flags:
        is_on = value > 0.0
        if is_on and not was_on:
            pulse_count += 1
        was_on = is_on
    return pulse_count


def _metrics_are_finite(metrics: dict[str, float | int | str | bool | None]) -> bool:
    for value in metrics.values():
        if isinstance(value, float) and not math.isfinite(value):
            return False
    return True
