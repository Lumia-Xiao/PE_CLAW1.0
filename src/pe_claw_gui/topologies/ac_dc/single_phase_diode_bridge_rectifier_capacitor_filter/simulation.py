"""Rs-based pulse-current simulation for the AC-DC capacitor-input bridge."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

_SAFE_RS_OHM = 1e-6
_MIN_POSITIVE = 1e-12


@dataclass(frozen=True)
class DiodeBridgeSimulationResult:
    """Time-domain result and summary metrics for one final line cycle."""

    succeeded: bool
    metrics: dict[str, float | int | str | bool | None]
    waveforms: dict[str, list[float]] = field(default_factory=dict)
    artifact_paths: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def simulate_diode_bridge_capacitor_input(
    *,
    vac_rms_v: float,
    f_line_hz: float,
    pout_w: float,
    diode_forward_drop_v: float,
    source_resistance_ohm: float,
    cdc_f: float,
    rload_ohm: float,
    initial_vcap_v: float,
    cycles: int = 6,
    settling_cycles: int = 5,
    samples_per_line_cycle: int = 5000,
    artifact_dir: str | Path | None = None,
    artifact_suffix: str = "",
) -> DiodeBridgeSimulationResult:
    """Simulate a full-bridge rectifier charging a DC-link capacitor through Rs."""

    warnings: list[str] = []
    validation_error = _validate_inputs(vac_rms_v, f_line_hz, pout_w, cdc_f, rload_ohm)
    if validation_error:
        return DiodeBridgeSimulationResult(
            succeeded=False,
            metrics={"simulation_error": validation_error},
            warnings=[validation_error],
        )

    rs_ohm = float(source_resistance_ohm)
    if rs_ohm <= 0.0:
        warnings.append(f"Equivalent source resistance Rs <= 0; clamped to {_SAFE_RS_OHM:g} ohm.")
        rs_ohm = _SAFE_RS_OHM

    cycles = max(int(cycles), 2)
    settling_cycles = min(max(int(settling_cycles), 0), cycles - 1)
    samples_per_line_cycle = max(int(samples_per_line_cycle), 1000)
    total_steps = cycles * samples_per_line_cycle
    final_start_step = settling_cycles * samples_per_line_cycle
    final_steps = total_steps - final_start_step

    period_s = 1.0 / float(f_line_hz)
    dt_s = period_s / samples_per_line_cycle
    omega_rad_s = 2.0 * math.pi * float(f_line_hz)
    vac_peak_v = math.sqrt(2.0) * float(vac_rms_v)
    vcap_v = max(float(initial_vcap_v), 0.0)

    time_s: list[float] = []
    vac_v: list[float] = []
    vrect_v: list[float] = []
    vdc_v: list[float] = []
    iac_a: list[float] = []
    ibridge_a: list[float] = []
    icap_a: list[float] = []
    iload_a: list[float] = []
    one_diode_a: list[float] = []
    diode_d1_a: list[float] = []
    diode_d2_a: list[float] = []
    diode_d3_a: list[float] = []
    diode_d4_a: list[float] = []

    for step in range(total_steps):
        t_s = step * dt_s
        vac = vac_peak_v * math.sin(omega_rad_s * t_s)
        vrect = abs(vac)
        iload = vcap_v / rload_ohm
        available_v = vrect - vcap_v - 2.0 * float(diode_forward_drop_v)
        bridge_current_a = max(available_v / rs_ohm, 0.0)
        cap_current_a = bridge_current_a - iload

        if step >= final_start_step:
            time_s.append((step - final_start_step) * dt_s)
            vac_v.append(vac)
            vrect_v.append(vrect)
            vdc_v.append(vcap_v)
            iac_a.append(bridge_current_a if vac >= 0.0 else -bridge_current_a)
            ibridge_a.append(bridge_current_a)
            icap_a.append(cap_current_a)
            iload_a.append(iload)
            one_diode_a.append(bridge_current_a if vac >= 0.0 else 0.0)
            diode_d1_a.append(bridge_current_a if vac >= 0.0 else 0.0)
            diode_d4_a.append(bridge_current_a if vac >= 0.0 else 0.0)
            diode_d2_a.append(bridge_current_a if vac < 0.0 else 0.0)
            diode_d3_a.append(bridge_current_a if vac < 0.0 else 0.0)

        vcap_v = max(vcap_v + (cap_current_a / cdc_f) * dt_s, 0.0)

    metrics = _build_metrics(
        vac_rms_v=float(vac_rms_v),
        f_line_hz=float(f_line_hz),
        rs_ohm=rs_ohm,
        cdc_f=float(cdc_f),
        rload_ohm=float(rload_ohm),
        cycles=cycles,
        settling_cycles=settling_cycles,
        samples_per_line_cycle=samples_per_line_cycle,
        final_steps=final_steps,
        time_s=time_s,
        vac_v=vac_v,
        vdc_v=vdc_v,
        iac_a=iac_a,
        ibridge_a=ibridge_a,
        icap_a=icap_a,
        iload_a=iload_a,
        one_diode_a=one_diode_a,
        diode_currents=(diode_d1_a, diode_d2_a, diode_d3_a, diode_d4_a),
    )
    if not _metrics_are_finite(metrics):
        warning = "AC-DC pulse-current simulation produced non-finite metrics."
        return DiodeBridgeSimulationResult(succeeded=False, metrics=metrics, warnings=[*warnings, warning])

    waveforms = {
        "time_s": time_s,
        "vac_v": vac_v,
        "vrect_v": vrect_v,
        "vdc_v": vdc_v,
        "iac_a": iac_a,
        "ibridge_a": ibridge_a,
        "icap_a": icap_a,
        "iload_a": iload_a,
        "diode_d1_a": diode_d1_a,
        "diode_d2_a": diode_d2_a,
        "diode_d3_a": diode_d3_a,
        "diode_d4_a": diode_d4_a,
    }
    artifact_paths = _write_artifacts(artifact_dir, waveforms, metrics, warnings, artifact_suffix=artifact_suffix)
    metrics["waveform_csv_path"] = artifact_paths.get("waveform_csv", "")
    metrics["summary_json_path"] = artifact_paths.get("summary_json", "")
    metrics["waveform_png_path"] = artifact_paths.get("waveform_png", "")
    return DiodeBridgeSimulationResult(
        succeeded=True,
        metrics=metrics,
        waveforms=waveforms,
        artifact_paths=artifact_paths,
        warnings=warnings,
    )


def _validate_inputs(vac_rms_v: float, f_line_hz: float, pout_w: float, cdc_f: float, rload_ohm: float) -> str:
    for label, value in (
        ("Vac rms", vac_rms_v),
        ("Line frequency", f_line_hz),
        ("Output power", pout_w),
        ("DC-link capacitance", cdc_f),
        ("Load resistance", rload_ohm),
    ):
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return f"{label} must be a finite positive number."
        if not math.isfinite(numeric) or numeric <= 0.0:
            return f"{label} must be a finite positive number."
    return ""


def _build_metrics(
    *,
    vac_rms_v: float,
    f_line_hz: float,
    rs_ohm: float,
    cdc_f: float,
    rload_ohm: float,
    cycles: int,
    settling_cycles: int,
    samples_per_line_cycle: int,
    final_steps: int,
    time_s: list[float],
    vac_v: list[float],
    vdc_v: list[float],
    iac_a: list[float],
    ibridge_a: list[float],
    icap_a: list[float],
    iload_a: list[float],
    one_diode_a: list[float],
    diode_currents: tuple[list[float], list[float], list[float], list[float]],
) -> dict[str, float | int | str | bool | None]:
    vdc_avg_v = _mean(vdc_v)
    vdc_min_v = min(vdc_v) if vdc_v else 0.0
    vdc_max_v = max(vdc_v) if vdc_v else 0.0
    vdc_ripple_pp_v = vdc_max_v - vdc_min_v
    iac_rms_a = _rms(iac_a)
    input_real_power_w = _mean([v * i for v, i in zip(vac_v, iac_a, strict=True)])
    output_power_w = _mean([v * i for v, i in zip(vdc_v, iload_a, strict=True)])
    apparent_power_va = vac_rms_v * iac_rms_a
    conduction_fraction = sum(1 for current in ibridge_a if current > _MIN_POSITIVE) / max(len(ibridge_a), 1)
    diode_metrics: dict[str, float] = {}
    for index, current in enumerate(diode_currents, start=1):
        diode_metrics.update(
            {
                f"diode_d{index}_avg_current_a": _mean(current),
                f"diode_d{index}_rms_current_a": _rms(current),
                f"diode_d{index}_peak_current_a": max(current) if current else 0.0,
            }
        )
    return {
        "simulation_succeeded": True,
        "simulation_basis": "Rs-based capacitor-input diode bridge",
        "cycles_simulated": cycles,
        "settling_cycles_discarded": settling_cycles,
        "samples_per_line_cycle": samples_per_line_cycle,
        "final_cycle_sample_count": final_steps,
        "rs_used_ohm": rs_ohm,
        "cdc_used_f": cdc_f,
        "rload_used_ohm": rload_ohm,
        "vdc_avg_v": vdc_avg_v,
        "vdc_min_v": vdc_min_v,
        "vdc_max_v": vdc_max_v,
        "vdc_ripple_pp_v": vdc_ripple_pp_v,
        "vdc_ripple_ratio": vdc_ripple_pp_v / max(vdc_avg_v, _MIN_POSITIVE),
        "idc_avg_a": _mean(iload_a),
        "output_current_avg_a": _mean(iload_a),
        "output_current_peak_a": max(iload_a) if iload_a else 0.0,
        "output_power_w": output_power_w,
        "i_bridge_peak_a": max(ibridge_a) if ibridge_a else 0.0,
        "i_bridge_rms_a": _rms(ibridge_a),
        "per_diode_avg_current_a": _mean(one_diode_a),
        "per_diode_rms_current_a": _rms(one_diode_a),
        "per_diode_peak_current_a": max(ibridge_a) if ibridge_a else 0.0,
        "input_current_rms_a": iac_rms_a,
        "input_current_peak_a": max((abs(value) for value in iac_a), default=0.0),
        "input_real_power_w": input_real_power_w,
        "apparent_power_va": apparent_power_va,
        "power_factor": input_real_power_w / apparent_power_va if apparent_power_va > _MIN_POSITIVE else 0.0,
        "capacitor_current_rms_a": _rms(icap_a),
        "capacitor_current_peak_a": max((abs(value) for value in icap_a), default=0.0),
        "conduction_duty": conduction_fraction,
        "conduction_angle_deg_per_half_cycle": conduction_fraction * 180.0,
        "ripple_frequency_hz": 2.0 * f_line_hz,
        **diode_metrics,
    }


def _write_artifacts(
    artifact_dir: str | Path | None,
    waveforms: dict[str, list[float]],
    metrics: dict[str, float | int | str | bool | None],
    warnings: list[str],
    *,
    artifact_suffix: str = "",
) -> dict[str, str]:
    if artifact_dir is None:
        from ....models.design_run_context import get_active_run_output_dir

        artifact_dir = get_active_run_output_dir()
    output_dir = Path(artifact_dir) if artifact_dir is not None else Path("outputs") / "ac_dc_rectifier"
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_suffix = _safe_artifact_suffix(artifact_suffix)
    stem = f"single_phase_diode_bridge_rectifier_waveforms{safe_suffix}"
    waveform_path = output_dir / f"{stem}.csv"
    summary_path = output_dir / f"single_phase_diode_bridge_rectifier_summary{safe_suffix}.json"
    plot_path = output_dir / f"{stem}.png"

    columns = ["time_s", "vac_v", "vrect_v", "vdc_v", "iac_a", "ibridge_a", "icap_a", "iload_a"]
    with waveform_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        for row in zip(*(waveforms[column] for column in columns), strict=True):
            writer.writerow([f"{float(value):.12g}" for value in row])

    with summary_path.open("w", encoding="utf-8") as stream:
        json.dump({"metrics": metrics, "warnings": warnings}, stream, indent=2, sort_keys=True)

    _write_waveform_png(plot_path, waveforms, metrics)

    if safe_suffix:
        _write_compatibility_artifacts(output_dir, waveform_path, summary_path, plot_path)

    return {"waveform_csv": str(waveform_path), "summary_json": str(summary_path), "waveform_png": str(plot_path)}


def _write_waveform_png(
    plot_path: Path,
    waveforms: dict[str, list[float]],
    metrics: dict[str, float | int | str | bool | None],
) -> None:
    time_ms = [value * 1e3 for value in waveforms["time_s"]]
    figure = Figure(figsize=(10, 6), dpi=120)
    FigureCanvasAgg(figure)
    voltage_ax = figure.add_subplot(2, 1, 1)
    current_ax = figure.add_subplot(2, 1, 2)

    voltage_ax.plot(time_ms, waveforms["vac_v"], linewidth=1.0, label="vac")
    voltage_ax.plot(time_ms, waveforms["vrect_v"], linewidth=1.0, label="vrect = |vac|")
    voltage_ax.plot(time_ms, waveforms["vdc_v"], linewidth=1.2, label="vdc")
    voltage_ax.set_ylabel("Voltage [V]")
    voltage_ax.grid(True, alpha=0.35)
    voltage_ax.legend(loc="upper right", fontsize=8)

    current_ax.plot(time_ms, waveforms["iac_a"], linewidth=1.0, label="iac")
    current_ax.plot(time_ms, waveforms["ibridge_a"], linewidth=1.0, label="ibridge")
    current_ax.plot(time_ms, waveforms["icap_a"], linewidth=1.0, label="icap")
    current_ax.plot(time_ms, waveforms["iload_a"], linewidth=1.0, label="iload")
    current_ax.set_xlabel("Time [ms]")
    current_ax.set_ylabel("Current [A]")
    current_ax.grid(True, alpha=0.35)
    current_ax.legend(loc="upper right", fontsize=8)

    if time_ms:
        voltage_ax.set_xlim(time_ms[0], time_ms[-1])
        current_ax.set_xlim(time_ms[0], time_ms[-1])

    figure.suptitle(
        "Single-phase diode bridge capacitor-filter waveforms\n"
        "Phase 2 Rs-based first-pass simulation, final settled line cycle",
        fontsize=10,
    )
    figure.tight_layout(rect=[0, 0, 1, 0.9])
    figure.savefig(plot_path)


def _safe_artifact_suffix(artifact_suffix: str) -> str:
    if not artifact_suffix:
        return ""
    safe = "".join(char if char.isalnum() else "_" for char in artifact_suffix.strip())
    return f"_{safe.strip('_')}" if safe.strip("_") else ""


def _write_compatibility_artifacts(output_dir: Path, waveform_path: Path, summary_path: Path, plot_path: Path) -> None:
    for source, target_name in (
        (waveform_path, "single_phase_diode_bridge_rectifier_waveforms.csv"),
        (summary_path, "single_phase_diode_bridge_rectifier_summary.json"),
        (plot_path, "single_phase_diode_bridge_rectifier_waveforms.png"),
    ):
        target = output_dir / target_name
        target.write_bytes(source.read_bytes())


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _rms(values: list[float]) -> float:
    return math.sqrt(_mean([value * value for value in values]))


def _metrics_are_finite(metrics: dict[str, float | int | str | bool | None]) -> bool:
    for value in metrics.values():
        if isinstance(value, float) and not math.isfinite(value):
            return False
    return True
