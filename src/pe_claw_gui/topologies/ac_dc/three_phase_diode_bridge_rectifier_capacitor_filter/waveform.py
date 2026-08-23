"""Ideal six-pulse waveform preview for the Phase 2 three-phase diode bridge."""

from __future__ import annotations

import csv
import math
from dataclasses import replace
from dataclasses import dataclass, field
from pathlib import Path

from matplotlib import pyplot as plt
from matplotlib.ticker import FixedLocator, MaxNLocator

from ....models.operating_point import OperatingPoint
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from .simulation import (
    ThreePhaseRectifierSimulationResult,
    power_factor_requirement_status,
    simulate_three_phase_capacitor_rectifier,
)

_PHASE_LABELS = ("A", "B", "C")
_MIN_POSITIVE = 1e-12


@dataclass(frozen=True)
class ThreePhaseDiodeBridgeWaveformPreview:
    """Sampled ideal six-pulse preview waveforms and diagnostics."""

    metrics: dict[str, float | int | str | bool | None]
    waveforms: dict[str, list[float] | list[str]]
    artifact_paths: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def build_three_phase_diode_bridge_waveform_preview(
    *,
    vll_rms_v: float,
    f_line_hz: float,
    pout_w: float,
    dc_link_ripple_ratio: float,
    diode_forward_drop_v: float,
    phase1_vdc_est_v: float,
    idc_a: float,
    diode_reverse_stress_v: float,
    source_resistance_per_phase_ohm: float = 0.05,
    rload_ohm: float | None = None,
    cout_f: float | None = None,
    cycles: int = 2,
    samples_per_line_cycle: int = 1440,
    artifact_dir: str | Path | None = None,
    artifact_suffix: str = "load_1p00",
) -> ThreePhaseDiodeBridgeWaveformPreview:
    """Build a deterministic ideal six-pulse bridge waveform preview."""

    _validate_positive("VLL rms", vll_rms_v)
    _validate_positive("Line frequency", f_line_hz)
    _validate_positive("Output power", pout_w)
    _validate_positive("Phase 1 Vdc estimate", phase1_vdc_est_v)
    if diode_forward_drop_v < 0.0:
        raise ValueError("Diode forward drop estimate cannot be negative.")
    _validate_positive("DC-link ripple ratio", dc_link_ripple_ratio)
    _validate_positive("Idc", idc_a)

    resolved_rload_ohm = rload_ohm or phase1_vdc_est_v / idc_a
    target_ripple_pp_v = dc_link_ripple_ratio * phase1_vdc_est_v
    resolved_cout_f = cout_f or idc_a / (6.0 * f_line_hz * target_ripple_pp_v)
    result = simulate_three_phase_capacitor_rectifier(
        vll_rms_v=vll_rms_v,
        f_line_hz=f_line_hz,
        diode_forward_drop_v=diode_forward_drop_v,
        source_resistance_per_phase_ohm=source_resistance_per_phase_ohm,
        cout_f=resolved_cout_f,
        rload_ohm=resolved_rload_ohm,
        initial_vdc_v=math.sqrt(2.0) * vll_rms_v - 2.0 * diode_forward_drop_v,
        samples_per_line_cycle=10_000,
    )
    if not result.succeeded:
        return ThreePhaseDiodeBridgeWaveformPreview(result.metrics, {}, warnings=result.warnings)
    waveforms = _preview_waveform_aliases(result.waveforms)
    metrics = dict(result.metrics)
    metrics.update(
        {
            "idc_a": metrics["output_current_avg_a"],
            "cdc_required_f": resolved_cout_f,
            "dc_link_capacitor_current_model": "bridge charging current minus fixed-resistive load current",
            "dc_link_capacitor_current_rms_a": metrics["capacitor_current_rms_a"],
            "dc_link_capacitor_current_pp_a": _peak_to_peak(_numeric_series(waveforms, "icap_proxy_a")),
            "current_model": "three-phase source-resistance-limited charging pulses",
            "diode_reverse_stress_v": diode_reverse_stress_v,
        }
    )
    artifact_paths = _write_artifacts(artifact_dir, waveforms, metrics, artifact_suffix=artifact_suffix)
    metrics["waveform_csv_path"] = artifact_paths.get("waveform_csv", "")
    metrics["waveform_png_path"] = artifact_paths.get("waveform_png", "")
    return ThreePhaseDiodeBridgeWaveformPreview(
        metrics=metrics,
        waveforms=waveforms,
        artifact_paths=artifact_paths,
        warnings=[
            "First-stage charging-pulse model includes per-phase source resistance and fixed resistive load.",
            "Source inductance, diode recovery, commutation overlap, and capacitor ESR dynamics remain out of scope.",
        ],
    )

    cycles = max(int(cycles), 1)
    samples_per_line_cycle = max(int(samples_per_line_cycle), 360)
    sample_count = cycles * samples_per_line_cycle
    line_period_s = 1.0 / f_line_hz
    dt_s = line_period_s / samples_per_line_cycle
    omega_rad_s = 2.0 * math.pi * f_line_hz
    vphase_rms_v = vll_rms_v / math.sqrt(3.0)
    vphase_peak_v = math.sqrt(2.0) * vphase_rms_v
    ripple_frequency_hz = 6.0 * f_line_hz

    time_s: list[float] = []
    va_v: list[float] = []
    vb_v: list[float] = []
    vc_v: list[float] = []
    vab_v: list[float] = []
    vbc_v: list[float] = []
    vca_v: list[float] = []
    vba_v: list[float] = []
    vcb_v: list[float] = []
    vac_v: list[float] = []
    vrect_ideal_v: list[float] = []
    vdc_ideal_v: list[float] = []
    vdc_smooth_v: list[float] = []
    ia_a: list[float] = []
    ib_a: list[float] = []
    ic_a: list[float] = []
    capacitor_current_a: list[float] = []
    upper_phase: list[str] = []
    lower_phase: list[str] = []
    upper_phase_index: list[float] = []
    lower_phase_index: list[float] = []

    target_ripple_pp_v = dc_link_ripple_ratio * phase1_vdc_est_v
    cdc_required_f = idc_a / (ripple_frequency_hz * target_ripple_pp_v)
    for step in range(sample_count + 1):
        t_s = step * dt_s
        angle = omega_rad_s * t_s
        phases = (
            vphase_peak_v * math.sin(angle),
            vphase_peak_v * math.sin(angle - 2.0 * math.pi / 3.0),
            vphase_peak_v * math.sin(angle + 2.0 * math.pi / 3.0),
        )
        high_index = max(range(3), key=lambda index: phases[index])
        low_index = min(range(3), key=lambda index: phases[index])
        currents = [0.0, 0.0, 0.0]
        currents[high_index] = idc_a
        currents[low_index] = -idc_a
        vrect_v = phases[high_index] - phases[low_index]
        vdc_ideal = max(vrect_v - 2.0 * diode_forward_drop_v, 0.0)
        vdc_smooth = phase1_vdc_est_v + 0.5 * target_ripple_pp_v * math.cos(6.0 * angle)
        cap_current = -cdc_required_f * 0.5 * target_ripple_pp_v * 6.0 * omega_rad_s * math.sin(6.0 * angle)

        time_s.append(t_s)
        va_v.append(phases[0])
        vb_v.append(phases[1])
        vc_v.append(phases[2])
        vab_v.append(phases[0] - phases[1])
        vbc_v.append(phases[1] - phases[2])
        vca_v.append(phases[2] - phases[0])
        vba_v.append(phases[1] - phases[0])
        vcb_v.append(phases[2] - phases[1])
        vac_v.append(phases[0] - phases[2])
        vrect_ideal_v.append(vrect_v)
        vdc_ideal_v.append(vdc_ideal)
        vdc_smooth_v.append(vdc_smooth)
        ia_a.append(currents[0])
        ib_a.append(currents[1])
        ic_a.append(currents[2])
        capacitor_current_a.append(cap_current)
        upper_phase.append(_PHASE_LABELS[high_index])
        lower_phase.append(_PHASE_LABELS[low_index])
        upper_phase_index.append(float(high_index))
        lower_phase_index.append(float(low_index))

    vdc_avg_v = _mean(vdc_ideal_v)
    vdc_min_v = min(vdc_ideal_v)
    vdc_max_v = max(vdc_ideal_v)
    vdc_ripple_pp_v = vdc_max_v - vdc_min_v
    ia_rms_a = _rms(ia_a)
    ib_rms_a = _rms(ib_a)
    ic_rms_a = _rms(ic_a)
    capacitor_current_rms_a = _rms(capacitor_current_a)
    line_current_rms_a = _rms([*ia_a, *ib_a, *ic_a])
    input_real_power_w = _mean(
        [
            va * ia + vb * ib + vc * ic
            for va, vb, vc, ia, ib, ic in zip(va_v, vb_v, vc_v, ia_a, ib_a, ic_a, strict=True)
        ]
    )
    apparent_power_va = 3.0 * vphase_rms_v * line_current_rms_a
    power_factor = input_real_power_w / apparent_power_va if apparent_power_va > _MIN_POSITIVE else 0.0
    average_error_v = vdc_avg_v - phase1_vdc_est_v

    metrics: dict[str, float | int | str | bool | None] = {
        "simulation_succeeded": True,
        "simulation_basis": "ideal six-pulse bridge waveform preview",
        "vll_rms_v": vll_rms_v,
        "vphase_rms_v": vphase_rms_v,
        "vphase_peak_v": vphase_peak_v,
        "f_line_hz": f_line_hz,
        "ripple_frequency_hz": ripple_frequency_hz,
        "cycles_shown": cycles,
        "samples_per_line_cycle": samples_per_line_cycle,
        "sample_count": len(time_s),
        "idc_a": idc_a,
        "cdc_required_f": cdc_required_f,
        "representative_smooth_ripple_ratio": dc_link_ripple_ratio,
        "representative_smooth_ripple_pp_v": target_ripple_pp_v,
        "dc_link_capacitor_current_model": "Cdc*dVdc_smooth/dt six-pulse ripple proxy",
        "dc_link_capacitor_current_rms_a": capacitor_current_rms_a,
        "dc_link_capacitor_current_pp_a": max(capacitor_current_a) - min(capacitor_current_a) if capacitor_current_a else 0.0,
        "vdc_avg_v": vdc_avg_v,
        "vdc_min_v": vdc_min_v,
        "vdc_max_v": vdc_max_v,
        "vdc_ripple_pp_v": vdc_ripple_pp_v,
        "vdc_ripple_ratio": vdc_ripple_pp_v / max(vdc_avg_v, _MIN_POSITIVE),
        "phase1_vdc_est_v": phase1_vdc_est_v,
        "average_error_vs_phase1_v": average_error_v,
        "average_error_vs_phase1_percent": 100.0 * average_error_v / max(phase1_vdc_est_v, _MIN_POSITIVE),
        "line_current_rms_a": line_current_rms_a,
        "ia_rms_a": ia_rms_a,
        "ib_rms_a": ib_rms_a,
        "ic_rms_a": ic_rms_a,
        "input_real_power_w": input_real_power_w,
        "apparent_power_va": apparent_power_va,
        "power_factor": power_factor,
        "input_current_thd": None,
        "per_diode_avg_current_a": idc_a / 3.0,
        "per_diode_rms_current_a": idc_a / math.sqrt(3.0),
        "per_diode_peak_current_a": idc_a,
        "diode_reverse_stress_v": diode_reverse_stress_v,
        "current_model": "six-step continuous-DC-current approximation",
    }
    waveforms: dict[str, list[float] | list[str]] = {
        "time_s": time_s,
        "va_v": va_v,
        "vb_v": vb_v,
        "vc_v": vc_v,
        "vab_v": vab_v,
        "vbc_v": vbc_v,
        "vca_v": vca_v,
        "vba_v": vba_v,
        "vcb_v": vcb_v,
        "vac_v": vac_v,
        "vrect_ideal_v": vrect_ideal_v,
        "vdc_ideal_v": vdc_ideal_v,
        "vdc_smooth_v": vdc_smooth_v,
        "ia_a": ia_a,
        "ib_a": ib_a,
        "ic_a": ic_a,
        "icap_proxy_a": capacitor_current_a,
        "upper_phase": upper_phase,
        "lower_phase": lower_phase,
        "upper_phase_index": upper_phase_index,
        "lower_phase_index": lower_phase_index,
    }
    artifact_paths = _write_artifacts(artifact_dir, waveforms, metrics, artifact_suffix=artifact_suffix)
    metrics["waveform_csv_path"] = artifact_paths.get("waveform_csv", "")
    metrics["waveform_png_path"] = artifact_paths.get("waveform_png", "")
    return ThreePhaseDiodeBridgeWaveformPreview(
        metrics=metrics,
        waveforms=waveforms,
        artifact_paths=artifact_paths,
        warnings=[
            "Ideal six-pulse bridge output before detailed capacitor pulse-current simulation.",
            "DC-link capacitor current uses a C*dV/dt six-pulse ripple proxy for first-pass capacitor selection.",
            "Capacitor charging pulse current, source impedance, and commutation overlap are not included.",
        ],
    )


def generate_waveforms(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
) -> WaveformSet | None:
    """Return the ideal six-pulse preview as a waveform set when requested."""

    load_ratio = _clamp_load_ratio(operating_point.load_ratio if operating_point is not None else 1.0)
    result = simulate_three_phase_rectifier_for_load(candidate, load_ratio)
    if not result.succeeded:
        return None
    preview = result.metrics
    waveforms = _preview_waveform_aliases(result.waveforms)
    time_s = _numeric_series(waveforms, "time_s")
    ia_a = _numeric_series(waveforms, "ia_a")
    ib_a = _numeric_series(waveforms, "ib_a")
    ic_a = _numeric_series(waveforms, "ic_a")
    capacitor_current_a = _numeric_series(waveforms, "icap_proxy_a")
    output_voltage_v = _numeric_series(waveforms, "vdc_smooth_v")
    display_waveforms = waveforms
    current_values = [*ia_a, *ib_a, *ic_a]
    return WaveformSet(
        time_s=time_s,
        switch_node_voltage_v=[float(value) for value in waveforms["vrect_ideal_v"]],
        inductor_current_a=ia_a,
        capacitor_current_a=capacitor_current_a,
        output_voltage_v=output_voltage_v,
        operating_vin_v=float(preview["vll_rms_v"]),
        operating_vout_v=float(preview["vdc_avg_v"]),
        duty=1.0,
        load_ratio=load_ratio,
        switching_period_s=1.0 / float(preview["ripple_frequency_hz"]),
        time_span_s=time_s[-1] - time_s[0] if len(time_s) > 1 else 0.0,
        inductor_current_min_a=min(current_values) if current_values else 0.0,
        inductor_current_max_a=max(current_values) if current_values else 0.0,
        mode="three-phase capacitor charging pulses",
        diode_current_a=ia_a,
        input_source_current_a=ia_a,
        notes=[
            "Three-phase capacitor charging-pulse state simulation.",
            "Per-phase source resistance and fixed passive load are included.",
        ],
        metadata={
            "ac_dc_three_phase_rectifier_waveforms": display_waveforms,
            "ac_dc_three_phase_rectifier_design_waveforms": waveforms,
            "ac_dc_three_phase_rectifier_metrics": preview,
            "artifact_paths": {},
            "load_ratio": load_ratio,
            "rload_used_ohm": preview["rload_used_ohm"],
            "selected_cdc_f": preview["cdc_used_f"],
        },
    )


def simulate_three_phase_rectifier_for_load(
    candidate: TopologyCandidate,
    load_ratio: float,
) -> ThreePhaseRectifierSimulationResult:
    """Regenerate the physical waveform at a fixed-resistance load ratio."""

    ratio = _clamp_load_ratio(load_ratio)
    nominal_rload_ohm = float(candidate.metadata.get("rload_ohm", candidate.r_load_nom_ohm))
    rload_ohm = 1e12 if ratio <= 0.0 else nominal_rload_ohm / ratio
    return simulate_three_phase_capacitor_rectifier(
        vll_rms_v=float(candidate.metadata["vll_rms_v"]),
        f_line_hz=float(candidate.metadata["f_line_hz"]),
        diode_forward_drop_v=float(candidate.metadata["diode_forward_drop_v"]),
        source_resistance_per_phase_ohm=float(candidate.metadata["source_resistance_per_phase_ohm"]),
        cout_f=float(candidate.metadata.get("selected_cdc_f", candidate.capacitance_f)),
        rload_ohm=rload_ohm,
        initial_vdc_v=float(candidate.metadata.get("vout_achieved_v", candidate.vout_target)),
    )


def refresh_selected_capacitor_candidate(
    candidate: TopologyCandidate,
    selected_cdc_f: float,
    *,
    load_ratio: float = 1.0,
) -> tuple[TopologyCandidate, ThreePhaseRectifierSimulationResult]:
    """Refresh candidate electrical values with the selected capacitor bank."""

    metadata = {**candidate.metadata, "selected_cdc_f": float(selected_cdc_f)}
    provisional = replace(candidate, metadata=metadata)
    result = simulate_three_phase_rectifier_for_load(provisional, load_ratio)
    if not result.succeeded:
        return provisional, result
    metrics = dict(result.metrics)
    pf_target = metadata.get("power_factor_target")
    pf_target = None if pf_target in (None, "") else float(pf_target)
    metadata.update(
        {
            "three_phase_pulse_simulation": metrics,
            "six_pulse_waveform_preview": metrics,
            "six_pulse_waveform_preview_waveforms": _preview_waveform_aliases(result.waveforms),
            "vout_achieved_v": metrics["vdc_avg_v"],
            "iout_achieved_a": metrics["output_current_avg_a"],
            "pout_achieved_w": metrics["output_power_w"],
            "power_factor_achieved": metrics["power_factor"],
            "power_factor_requirement_status": power_factor_requirement_status(
                float(metrics["power_factor"]), pf_target
            ),
        }
    )
    return (
        replace(
            candidate,
            vout_target=float(metrics["vdc_avg_v"]),
            iout=float(metrics["output_current_avg_a"]),
            delta_vo=float(metrics["vdc_ripple_pp_v"]),
            il_peak=float(metrics["phase_current_peak_a"]),
            output_ripple_vpp_v=float(metrics["vdc_ripple_pp_v"]),
            metadata=metadata,
        ),
        result,
    )


def _preview_waveform_aliases(
    source: dict[str, list[float] | list[str]],
) -> dict[str, list[float] | list[str]]:
    waveforms = {key: list(values) for key, values in source.items()}
    waveforms["vrect_ideal_v"] = list(source.get("vrect_open_v", []))
    waveforms["vdc_ideal_v"] = list(source.get("vrect_open_v", []))
    waveforms["vdc_smooth_v"] = list(source.get("vdc_v", []))
    waveforms["icap_proxy_a"] = list(source.get("capacitor_current_a", []))
    return waveforms


def _write_artifacts(
    artifact_dir: str | Path | None,
    waveforms: dict[str, list[float] | list[str]],
    metrics: dict[str, float | int | str | bool | None],
    *,
    artifact_suffix: str,
) -> dict[str, str]:
    output_dir = Path(artifact_dir) if artifact_dir is not None else Path("outputs") / "ac_dc_three_phase_rectifier"
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_suffix = _safe_artifact_suffix(artifact_suffix)
    stem = f"three_phase_diode_bridge_rectifier_waveforms{safe_suffix}"
    csv_path = output_dir / f"{stem}.csv"
    png_path = output_dir / f"{stem}.png"

    columns = [
        "time_s",
        "va_v",
        "vb_v",
        "vc_v",
        "vab_v",
        "vbc_v",
        "vca_v",
        "vrect_ideal_v",
        "vdc_ideal_v",
        "ia_a",
        "ib_a",
        "ic_a",
        "icap_proxy_a",
        "upper_phase",
        "lower_phase",
        "vdc_smooth_v",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        for row in zip(*(waveforms[column] for column in columns), strict=True):
            writer.writerow([_csv_value(value) for value in row])

    _write_waveform_png(png_path, waveforms, metrics)
    return {"waveform_csv": str(csv_path), "waveform_png": str(png_path)}


def _write_waveform_png(
    png_path: Path,
    waveforms: dict[str, list[float] | list[str]],
    metrics: dict[str, float | int | str | bool | None],
) -> None:
    time_ms = [float(value) * 1e3 for value in waveforms["time_s"]]
    figure, axes = plt.subplots(
        3,
        1,
        figsize=(14, 9),
        sharex=True,
        constrained_layout=True,
    )
    phase_ax, rectifier_ax, current_ax = axes

    phase_ax.plot(time_ms, waveforms["va_v"], linewidth=1.0, label="va")
    phase_ax.plot(time_ms, waveforms["vb_v"], linewidth=1.0, label="vb")
    phase_ax.plot(time_ms, waveforms["vc_v"], linewidth=1.0, label="vc")
    phase_ax.set_ylabel("Phase voltage [V]")
    phase_ax.grid(True, alpha=0.28)
    phase_ax.legend(loc="upper right", fontsize=8, framealpha=0.9)

    rectifier_ax.plot(time_ms, waveforms["vrect_ideal_v"], linewidth=1.0, label="vrect ideal")
    rectifier_ax.plot(time_ms, waveforms["vdc_ideal_v"], linewidth=1.1, label="vdc ideal")
    rectifier_ax.plot(time_ms, waveforms["vdc_smooth_v"], linewidth=0.9, label="vdc representative smooth")
    rectifier_ax.set_ylabel("DC voltage [V]")
    rectifier_ax.grid(True, alpha=0.28)
    rectifier_ax.legend(loc="upper right", fontsize=8, framealpha=0.9)

    current_ax.step(time_ms, waveforms["ia_a"], where="post", linewidth=1.0, label="ia")
    current_ax.step(time_ms, waveforms["ib_a"], where="post", linewidth=1.0, label="ib")
    current_ax.step(time_ms, waveforms["ic_a"], where="post", linewidth=1.0, label="ic")
    if waveforms.get("icap_proxy_a"):
        current_ax.plot(time_ms, waveforms["icap_proxy_a"], linewidth=1.0, label="iC proxy")
    current_ax.set_xlabel("Time [ms]")
    current_ax.set_ylabel("Line current [A]")
    current_ax.grid(True, alpha=0.28)
    current_ax.legend(loc="upper right", fontsize=8, framealpha=0.9)

    _set_axis_limits_and_ticks(
        phase_ax=phase_ax,
        rectifier_ax=rectifier_ax,
        current_ax=current_ax,
        time_ms=time_ms,
        waveforms=waveforms,
        idc_a=_metric_float(metrics, "idc_a"),
    )
    _format_preview_axes(
        axes=[phase_ax, rectifier_ax, current_ax],
        time_ms=time_ms,
    )

    figure.suptitle(
        "Three-phase diode bridge ideal six-pulse waveform preview\n"
        "Not a detailed capacitor charging-pulse simulation",
        fontsize=12,
    )
    figure.savefig(png_path, dpi=120)
    plt.close(figure)


def _set_axis_limits_and_ticks(
    *,
    phase_ax,
    rectifier_ax,
    current_ax,
    time_ms: list[float],
    waveforms: dict[str, list[float] | list[str]],
    idc_a: float,
) -> None:
    """Keep the saved preview plot readable without changing waveform data."""

    phase_values = [
        *_numeric_series(waveforms, "va_v"),
        *_numeric_series(waveforms, "vb_v"),
        *_numeric_series(waveforms, "vc_v"),
    ]
    dc_values = [
        *_numeric_series(waveforms, "vrect_ideal_v"),
        *_numeric_series(waveforms, "vdc_ideal_v"),
        *_numeric_series(waveforms, "vdc_smooth_v"),
    ]
    current_values = [
        *_numeric_series(waveforms, "ia_a"),
        *_numeric_series(waveforms, "ib_a"),
        *_numeric_series(waveforms, "ic_a"),
        *_numeric_series(waveforms, "icap_proxy_a"),
    ]
    _set_margin_ylim(phase_ax, phase_values, margin_ratio=0.08)
    _set_margin_ylim(rectifier_ax, dc_values, margin_ratio=0.06)
    current_limit_a = max(abs(value) for value in current_values) * 1.2 if current_values else 0.0
    current_limit_a = max(current_limit_a, abs(idc_a) * 1.2)
    if current_limit_a > _MIN_POSITIVE:
        current_ax.set_ylim(-current_limit_a, current_limit_a)
    else:
        _set_margin_ylim(current_ax, current_values, margin_ratio=0.10)
    if time_ms:
        current_ax.set_xlim(time_ms[0], time_ms[-1])


def _format_preview_axes(*, axes, time_ms: list[float]) -> None:
    if time_ms:
        start_ms = _floor_to_tick(time_ms[0], 5.0)
        stop_ms = _ceil_to_tick(time_ms[-1], 5.0)
        ticks_ms = _fixed_time_ticks(start_ms, stop_ms, 5.0)
    else:
        start_ms = 0.0
        stop_ms = 40.0
        ticks_ms = _fixed_time_ticks(start_ms, stop_ms, 5.0)
    for axis in axes:
        axis.set_xlim(start_ms, stop_ms)
        axis.set_xticks(ticks_ms)
        axis.xaxis.set_major_locator(FixedLocator(ticks_ms))
        axis.yaxis.set_major_locator(MaxNLocator(nbins=5))
        axis.ticklabel_format(axis="y", style="plain", useOffset=False)
        axis.minorticks_off()
        axis.tick_params(
            top=False,
            right=False,
            labeltop=False,
            labelright=False,
        )
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
    axes[0].tick_params(labelbottom=False)
    axes[1].tick_params(labelbottom=False)
    axes[2].set_xlabel("Time [ms]")


def _fixed_time_ticks(start_ms: float, stop_ms: float, step_ms: float) -> list[float]:
    tick_count = int(round((stop_ms - start_ms) / step_ms))
    return [start_ms + step_ms * index for index in range(tick_count + 1)]


def _floor_to_tick(value: float, step: float) -> float:
    return math.floor(value / step) * step


def _ceil_to_tick(value: float, step: float) -> float:
    return math.ceil(value / step) * step


def _set_margin_ylim(axis, values: list[float], *, margin_ratio: float) -> None:
    if not values:
        return
    ymin = min(values)
    ymax = max(values)
    value_range = ymax - ymin
    if value_range <= _MIN_POSITIVE:
        margin = max(abs(ymax), 1.0) * margin_ratio
    else:
        margin = value_range * margin_ratio
    axis.set_ylim(ymin - margin, ymax + margin)


def _numeric_series(waveforms: dict[str, list[float] | list[str]], key: str) -> list[float]:
    values = waveforms.get(key, [])
    return [float(value) for value in values if isinstance(value, (int, float))]


def _peak_to_peak(values: list[float]) -> float:
    return max(values) - min(values) if values else 0.0


def _scaled_numeric_series(waveforms: dict[str, list[float] | list[str]], key: str, scale: float) -> list[float]:
    return [value * scale for value in _numeric_series(waveforms, key)]


def _load_scaled_dc_voltage(
    waveforms: dict[str, list[float] | list[str]],
    preview: dict[str, object],
    load_ratio: float,
) -> list[float]:
    baseline = _numeric_series(waveforms, "vdc_smooth_v")
    center = _preview_float(preview, "phase1_vdc_est_v", _mean(baseline) if baseline else 0.0)
    return [center + (value - center) * load_ratio for value in baseline]


def _load_scaled_display_waveforms(
    waveforms: dict[str, list[float] | list[str]],
    *,
    ia_a: list[float],
    ib_a: list[float],
    ic_a: list[float],
    capacitor_current_a: list[float],
    output_voltage_v: list[float],
) -> dict[str, list[float] | list[str]]:
    display = {key: list(value) for key, value in waveforms.items()}
    display["ia_a"] = ia_a
    display["ib_a"] = ib_a
    display["ic_a"] = ic_a
    display["icap_proxy_a"] = capacitor_current_a
    display["vdc_smooth_v"] = output_voltage_v
    return display


def _preview_float(preview: dict[str, object], key: str, fallback: float) -> float:
    try:
        return float(preview.get(key, fallback))
    except (TypeError, ValueError):
        return fallback


def _metric_float(metrics: dict[str, float | int | str | bool | None], key: str) -> float:
    try:
        return float(metrics.get(key) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _validate_positive(label: str, value: float) -> None:
    if not math.isfinite(float(value)) or float(value) <= 0.0:
        raise ValueError(f"{label} must be a finite positive number.")


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _rms(values: list[float]) -> float:
    return math.sqrt(_mean([value * value for value in values]))


def _safe_artifact_suffix(value: str) -> str:
    if not value:
        return ""
    safe = "".join(char if char.isalnum() else "_" for char in value.strip())
    return f"_{safe.strip('_')}" if safe.strip("_") else ""


def _csv_value(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value):.12g}"
    return str(value)


def _clamp_load_ratio(value: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 1.0
    return min(max(numeric, 0.0), 1.0)
