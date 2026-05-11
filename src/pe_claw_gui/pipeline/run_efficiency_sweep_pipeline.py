"""Fixed-hardware efficiency sweep orchestration."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from collections.abc import Sequence

from matplotlib.figure import Figure

from ..models.design_report import DesignReport
from ..models.efficiency_sweep import EfficiencySweepPoint, EfficiencySweepResult
from ..models.operating_point import OperatingPoint
from ..topologies.base import TopologyPlugin
from .options import PipelineOptions
from .run_capacitor_pipeline import run_capacitor_operating_point_refresh
from .run_device_pipeline import run_device_operating_point_refresh
from .run_loss_pipeline import run_loss_pipeline
from .run_thermal_pipeline import run_thermal_pipeline

DEFAULT_LOAD_POINTS: tuple[float, ...] = tuple(round(index / 10.0, 1) for index in range(1, 11))


def run_efficiency_sweep(
    report: DesignReport,
    plugin: TopologyPlugin | None = None,
    load_points: Sequence[float] | None = None,
    output_dir: str | Path | None = None,
) -> EfficiencySweepResult:
    """Evaluate efficiency over load using the existing selected hardware."""

    load_grid = _normalize_load_grid(load_points)
    warnings: list[str] = []
    signature = _build_signature(report, load_grid)
    if report.efficiency_sweep is not None and report.efficiency_sweep.signature == signature:
        return report.efficiency_sweep

    blocking_warning = _blocking_warning(report, plugin)
    if blocking_warning is not None:
        return EfficiencySweepResult(load_grid=load_grid, warnings=(blocking_warning,), signature=signature)

    if report.capacitor is None:
        warnings.append("Capacitor design has not been run; capacitor loss is omitted.")
    if report.magnetic is None or not report.magnetic.chosen_designs:
        warnings.append("Magnetic design has not been run; magnetic loss is omitted.")

    points: list[EfficiencySweepPoint] = []
    for load_pu in load_grid:
        point, point_warnings = _evaluate_load_point(report, plugin, load_pu)
        points.append(point)
        warnings.extend(point_warnings)

    result = _build_result(points, load_grid, warnings, signature)
    artifacts = _write_artifacts(result, output_dir)
    return replace(result, artifact_paths=artifacts)


def _evaluate_load_point(
    base_report: DesignReport,
    plugin: TopologyPlugin,
    load_pu: float,
) -> tuple[EfficiencySweepPoint, list[str]]:
    point_warnings: list[str] = []
    operating_point = OperatingPoint(vin_v=_operating_vin_v(base_report), load_ratio=load_pu)
    waveform_set = plugin.generate_waveforms(base_report.candidate, operating_point=operating_point)
    if waveform_set is None:
        warning = f"Waveform generation returned no data at {load_pu:.1f} p.u.; point omitted."
        return (
            EfficiencySweepPoint(
                load_pu=load_pu,
                output_power_w=0.0,
                total_loss_w=None,
                efficiency=None,
                semiconductor_loss_w=None,
                magnetic_loss_w=None,
                capacitor_loss_w=None,
                other_loss_w=None,
                warnings=(warning,),
            ),
            [warning],
        )

    stress_result = plugin.extract_stress(base_report.candidate, waveform_set=waveform_set)
    topology_result = plugin.evaluate(base_report.candidate, waveform_set=waveform_set, stress_result=stress_result)
    refreshed = replace(
        base_report,
        operating_point=operating_point,
        waveform=waveform_set,
        stress=stress_result,
        topology_result=topology_result,
    )
    refreshed = run_device_operating_point_refresh(refreshed, plugin=plugin)
    if refreshed.magnetic is not None and refreshed.magnetic.chosen_designs:
        magnetic_options = PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=refreshed.capacitor is not None)
        refreshed = run_loss_pipeline(
            refreshed,
            preserve_selected_design_id=True,
            refresh_plot_artifact=False,
            pipeline_options=magnetic_options,
        )
        refreshed = run_thermal_pipeline(refreshed, pipeline_options=magnetic_options)
    refreshed = run_capacitor_operating_point_refresh(refreshed)

    semiconductor_loss_w = _semiconductor_loss_w(refreshed)
    magnetic_loss_w = _magnetic_loss_w(refreshed)
    capacitor_loss_w = _capacitor_loss_w(refreshed)
    available_losses = [semiconductor_loss_w, magnetic_loss_w, capacitor_loss_w]
    total_loss_w = sum(loss for loss in available_losses if loss is not None)
    if not any(loss is not None for loss in available_losses):
        total_loss_w = None
        point_warnings.append(f"No loss components were available at {load_pu:.1f} p.u.")

    output_power_w, power_warning = _output_power_w(refreshed, load_pu)
    if power_warning:
        point_warnings.append(power_warning)
    efficiency = None
    if total_loss_w is not None and output_power_w > 0.0:
        efficiency = output_power_w / (output_power_w + total_loss_w)

    return (
        EfficiencySweepPoint(
            load_pu=load_pu,
            output_power_w=output_power_w,
            total_loss_w=total_loss_w,
            efficiency=efficiency,
            semiconductor_loss_w=semiconductor_loss_w,
            magnetic_loss_w=magnetic_loss_w,
            capacitor_loss_w=capacitor_loss_w,
            other_loss_w=0.0,
            warnings=tuple(point_warnings),
        ),
        point_warnings,
    )


def _blocking_warning(report: DesignReport, plugin: TopologyPlugin | None) -> str | None:
    if report is None or report.candidate is None:
        return "Run Design before running Efficiency Sweep."
    if plugin is None:
        return "Efficiency sweep requires the active topology plugin."
    device = report.device
    if device is None or (not device.selected_devices and not device.design_point_losses and not device.scheme_results):
        return "Efficiency sweep requires selected semiconductor hardware from Run Design."
    return None


def _normalize_load_grid(load_points: Sequence[float] | None) -> tuple[float, ...]:
    values = load_points if load_points is not None else DEFAULT_LOAD_POINTS
    normalized = tuple(round(float(value), 6) for value in values)
    if not normalized:
        raise ValueError("Efficiency sweep load grid must contain at least one point.")
    return normalized


def _operating_vin_v(report: DesignReport) -> float:
    if report.operating_point is not None:
        return float(report.operating_point.vin_v)
    if report.candidate is not None:
        return float(report.candidate.vin_nom)
    return float(report.spec.vin_min)


def _output_power_w(report: DesignReport, load_pu: float) -> tuple[float, str | None]:
    if report.waveform is not None and report.candidate is not None:
        try:
            power_w = abs(float(report.waveform.operating_vout_v) * float(report.candidate.iout) * float(report.waveform.load_ratio))
            if power_w > 0.0:
                return power_w, None
        except (AttributeError, TypeError, ValueError):
            pass
    design_power_w = _design_power_w(report)
    if design_power_w is None:
        return 0.0, f"Output power unavailable at {load_pu:.1f} p.u.; efficiency omitted."
    return max(float(design_power_w) * load_pu, 0.0), (
        f"Used load_pu * design output power fallback at {load_pu:.1f} p.u."
    )


def _design_power_w(report: DesignReport) -> float | None:
    if report.candidate is not None:
        return getattr(report.candidate, "pout_target", None)
    return report.spec.pout


def _semiconductor_loss_w(report: DesignReport) -> float | None:
    device = report.device
    if device is None:
        return None
    if device.current_operating_losses:
        total = 0.0
        for key, loss_result in device.current_operating_losses.items():
            role_name = key.split(":", 1)[1] if ":" in key else loss_result.role
            total += _role_parallel_count(device, role_name) * float(loss_result.p_total_W)
        return total
    active_scheme = _active_scheme(device)
    if active_scheme is not None:
        return active_scheme.total_scheme_loss_w
    if device.design_point_losses:
        return sum(loss.p_total_W for loss in device.design_point_losses.values())
    return None


def _active_scheme(device):
    active_scheme_id = device.active_scheme_id or device.recommended_scheme_id
    for scheme in device.scheme_results:
        if scheme.scheme_id == active_scheme_id:
            return scheme
    return None


def _role_parallel_count(device, role_name: str) -> int:
    active_scheme = _active_scheme(device)
    if active_scheme is None:
        return max(int(getattr(device, "active_parallel_count", 1) or 1), 1)
    for role_result in active_scheme.role_results:
        if role_result.role == role_name:
            return max(int(role_result.parallel_count or 1), 1)
    return max(int(getattr(device, "active_parallel_count", 1) or 1), 1)


def _magnetic_loss_w(report: DesignReport) -> float | None:
    if report.loss is None:
        return None
    return report.loss.total_loss_w


def _capacitor_loss_w(report: DesignReport) -> float | None:
    if report.capacitor is None:
        return None
    total = 0.0
    found = False
    for side_result in (report.capacitor.current_operating_input, report.capacitor.current_operating_output):
        if side_result is not None and side_result.recommended is not None:
            total += side_result.recommended.p_total_w
            found = True
    return total if found else None


def _build_result(
    points: list[EfficiencySweepPoint],
    load_grid: tuple[float, ...],
    warnings: list[str],
    signature: str,
) -> EfficiencySweepResult:
    complete_points = [point for point in points if point.efficiency is not None]
    peak = max(complete_points, key=lambda point: point.efficiency or 0.0) if complete_points else None
    return EfficiencySweepResult(
        points=tuple(points),
        load_grid=load_grid,
        peak_efficiency=peak.efficiency if peak is not None else None,
        peak_efficiency_load_pu=peak.load_pu if peak is not None else None,
        full_load_efficiency=_efficiency_at(points, 1.0),
        light_load_efficiency=_efficiency_at(points, 0.1),
        warnings=tuple(_dedupe(warnings)),
        signature=signature,
    )


def _efficiency_at(points: list[EfficiencySweepPoint], load_pu: float) -> float | None:
    for point in points:
        if abs(point.load_pu - load_pu) < 1.0e-9:
            return point.efficiency
    return None


def _write_artifacts(result: EfficiencySweepResult, output_dir: str | Path | None) -> dict[str, str]:
    directory = Path(output_dir) if output_dir is not None else _project_root() / "outputs" / "efficiency_sweep"
    directory.mkdir(parents=True, exist_ok=True)
    efficiency_path = directory / "efficiency_curve.png"
    loss_path = directory / "loss_breakdown_stacked.png"
    _write_efficiency_curve(result, efficiency_path)
    _write_loss_breakdown(result, loss_path)
    return {"efficiency_curve": str(efficiency_path), "loss_breakdown_stacked": str(loss_path)}


def _write_efficiency_curve(result: EfficiencySweepResult, path: Path) -> None:
    figure = Figure(figsize=(5.8, 3.2), dpi=120)
    axis = figure.add_subplot(111)
    x_values = [point.load_pu for point in result.points if point.efficiency is not None]
    y_values = [100.0 * (point.efficiency or 0.0) for point in result.points if point.efficiency is not None]
    axis.plot(x_values, y_values, marker="o", color="#1f77b4")
    axis.set_xlabel("Load [p.u.]")
    axis.set_ylabel("Efficiency [%]")
    axis.grid(True, alpha=0.3)
    axis.set_xlim(0.1, 1.0)
    figure.tight_layout()
    figure.savefig(path)
    figure.clear()


def _write_loss_breakdown(result: EfficiencySweepResult, path: Path) -> None:
    figure = Figure(figsize=(5.8, 3.2), dpi=120)
    axis = figure.add_subplot(111)
    x_values = [point.load_pu for point in result.points]
    components = (
        ("Semiconductor", [point.semiconductor_loss_w or 0.0 for point in result.points], "#4c78a8"),
        ("Magnetic", [point.magnetic_loss_w or 0.0 for point in result.points], "#f58518"),
        ("Capacitor", [point.capacitor_loss_w or 0.0 for point in result.points], "#54a24b"),
        ("Other / unavailable", [point.other_loss_w or 0.0 for point in result.points], "#b279a2"),
    )
    bottoms = [0.0 for _ in result.points]
    width = 0.065
    for label, values, color in components:
        axis.bar(x_values, values, width=width, bottom=bottoms, label=label, color=color)
        bottoms = [bottom + value for bottom, value in zip(bottoms, values)]
    axis.set_xlabel("Load [p.u.]")
    axis.set_ylabel("Loss [W]")
    axis.grid(True, axis="y", alpha=0.3)
    axis.legend(loc="best", fontsize=8)
    figure.tight_layout()
    figure.savefig(path)
    figure.clear()


def _build_signature(report: DesignReport, load_grid: tuple[float, ...]) -> str:
    device = report.device
    capacitor = report.capacitor
    magnetic = report.magnetic
    payload = {
        "topology_id": report.spec.topology_id,
        "raw_input": report.spec.raw_input,
        "candidate": {
            "vin_nom": getattr(report.candidate, "vin_nom", None),
            "vout_target": getattr(report.candidate, "vout_target", None),
            "pout_target": getattr(report.candidate, "pout_target", None),
            "fs_hz": getattr(report.candidate, "fs_hz", None),
        },
        "semiconductor_scheme": getattr(device, "active_scheme_id", None) or getattr(device, "recommended_scheme_id", None),
        "selected_devices": getattr(device, "selected_devices", {}),
        "capacitor_parts": _capacitor_signature(capacitor),
        "magnetic_design_id": getattr(magnetic, "selected_design_id", None),
        "load_grid": load_grid,
        "operating_vin": report.operating_point.vin_v if report.operating_point is not None else None,
    }
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _capacitor_signature(capacitor) -> dict[str, str | None]:
    if capacitor is None:
        return {}
    return {
        "input": _capacitor_part(capacitor.input_selection),
        "output": _capacitor_part(capacitor.output_selection),
    }


def _capacitor_part(side_result) -> str | None:
    if side_result is None or side_result.recommended is None:
        return None
    return side_result.recommended.candidate.part_number


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]
