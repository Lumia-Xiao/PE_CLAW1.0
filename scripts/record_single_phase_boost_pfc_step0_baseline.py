"""Record the step-0 baseline for the existing single-phase Boost PFC."""

from __future__ import annotations

import argparse
import json
from importlib import import_module
from pathlib import Path
import tempfile
from typing import Any

from pe_claw_gui.pipeline import run_efficiency_sweep
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry


TOPOLOGY_ID = "single_phase_boost_pfc_diode_bridge"
CASE_INPUTS = {
    "nominal": "230",
    "low_line": "180",
    "high_line": "265",
}
RAW_INPUT_KEYS = (
    "vac_rms",
    "vac_rms_min",
    "vac_rms_max",
    "f_line_hz",
    "vdc_target_v",
    "pout_w",
    "fsw_hz",
    "dc_bus_ripple_percent",
    "inductor_current_ripple_ratio",
    "power_factor_target",
    "sizing_efficiency_assumption",
    "input_inductance_h",
)


def build_baseline() -> dict[str, object]:
    """Run the current full pipeline and return a stable comparison payload."""

    registry = build_default_registry()
    plugin = registry.get_plugin(TOPOLOGY_ID)
    topology_module = import_module(plugin.__module__)
    default_inputs = topology_module.build_default_inputs()
    cases: list[dict[str, object]] = []
    options = PipelineOptions(
        enable_magnetic_design=True,
        enable_capacitor_design=True,
        enable_bridge_rectifier_selection=True,
    )

    with tempfile.TemporaryDirectory(prefix="step0_boost_pfc_") as output_root:
        for case_id, vac_rms in CASE_INPUTS.items():
            raw_input = dict(default_inputs)
            raw_input["vac_rms"] = vac_rms
            report = run_full_pipeline(
                plugin=plugin,
                raw_input=raw_input,
                include_waveforms=True,
                pipeline_options=options,
                output_root=output_root,
            )
            sweep = run_efficiency_sweep(
                report,
                plugin=plugin,
                load_points=(0.5, 1.0),
                output_dir=Path(output_root) / case_id / "efficiency_sweep",
            )
            cases.append(_snapshot_case(case_id, raw_input, report, sweep))

    return {
        "schema_version": "single_phase_boost_pfc_step0_baseline_v1",
        "topology_id": TOPOLOGY_ID,
        "scope": {
            "design_point": "full pipeline with magnetic, capacitor, bridge, semiconductor, loss, thermal, and geometry stages",
            "operating_points": ["nominal", "low_line", "high_line"],
            "efficiency_load_grid": [0.5, 1.0],
            "hardware_policy": "efficiency sweep reuses selected design-point hardware",
            "dynamic_fields_excluded": ["run_id", "timestamps", "runtime_seconds", "temporary_paths", "signatures"],
        },
        "cases": cases,
    }


def _snapshot_case(case_id: str, raw_input: dict[str, str], report: Any, sweep: Any) -> dict[str, object]:
    candidate = report.candidate
    waveform = report.waveform
    stress = report.stress
    if candidate is None or waveform is None or stress is None:
        raise AssertionError(f"Incomplete Boost PFC baseline case: {case_id}")

    recommended_capacitor = getattr(getattr(report.capacitor, "output_selection", None), "recommended", None)
    bridge_candidate = getattr(report.bridge_rectifier, "selected_candidate", None)
    magnetic = report.magnetic
    thermal = report.thermal
    geometry = report.geometry
    loss = report.loss

    return {
        "case_id": case_id,
        "raw_input": {key: raw_input.get(key) for key in RAW_INPUT_KEYS},
        "presence": {
            key: getattr(report, key) is not None
            for key in (
                "candidate",
                "waveform",
                "stress",
                "device",
                "bridge_rectifier",
                "magnetic",
                "capacitor",
                "loss",
                "thermal",
                "geometry",
                "topology_result",
            )
        },
        "candidate": {
            key: _stable(getattr(candidate, key))
            for key in (
                "topology_id",
                "vin_min",
                "vin_max",
                "vin_nom",
                "vout_target",
                "pout_target",
                "duty_nom",
                "iout",
                "fs_hz",
                "inductance_h",
                "capacitance_f",
                "delta_il",
                "delta_vo",
                "il_peak",
                "il_valley",
                "ccm_valid",
                "feasible",
                "failure_reason",
            )
        },
        "candidate_metadata": {
            key: _stable(candidate.metadata.get(key))
            for key in (
                "vac_rms_v",
                "vac_rms_min_v",
                "vac_rms_max_v",
                "vdc_target_v",
                "fsw_hz",
                "sizing_input_power_w",
                "sizing_input_current_rms_a",
                "boost_inductor_required_h",
                "total_series_inductance_required_h",
                "dc_link_capacitance_required_f",
                "bridge_reverse_stress_v",
                "recommended_diode_vrrm_v",
                "vdc_feasibility_passed",
            )
        },
        "waveform": {
            key: _stable(getattr(waveform, key))
            for key in (
                "operating_vin_v",
                "operating_vout_v",
                "duty",
                "load_ratio",
                "mode",
                "inductor_current_min_a",
                "inductor_current_max_a",
            )
        },
        "stress": {
            "switch": _stress_snapshot(stress.switch),
            "rectifier": _stress_snapshot(stress.rectifier),
        },
        "hardware": {
            "selected_devices": dict(report.device.selected_devices) if report.device is not None else None,
            "bridge_candidate_id": getattr(bridge_candidate, "candidate_id", None),
            "bridge_part_number": getattr(bridge_candidate, "part_number", None),
            "magnetic_selected_design_id": getattr(magnetic, "selected_design_id", None),
            "capacitor_part_number": getattr(getattr(recommended_capacitor, "candidate", None), "part_number", None),
            "capacitor_bank_capacitance_f": _stable(getattr(recommended_capacitor, "equivalent_capacitance_f", None)),
        },
        "loss": {
            "total_loss_w": _stable(getattr(loss, "total_loss_w", None)),
            "breakdown_w": _stable(getattr(loss, "breakdown_w", {})),
        },
        "thermal": {
            "summary": getattr(thermal, "summary", None),
            "recommended_design_id": getattr(thermal, "recommended_design_id", None),
        },
        "geometry": {
            "component_type": getattr(geometry, "component_type", None),
            "footprint_mm2": _stable(getattr(geometry, "footprint_mm2", None)),
            "loss_w": _stable(getattr(geometry, "loss_w", None)),
        },
        "efficiency_sweep": {
            "status": sweep.status,
            "load_grid": [_stable(value) for value in sweep.load_grid],
            "points": [
                {
                    "load_pu": _stable(point.load_pu),
                    "output_power_w": _stable(point.output_power_w),
                    "total_loss_w": _stable(point.total_loss_w),
                    "efficiency": _stable(point.efficiency),
                    "semiconductor_loss_w": _stable(point.semiconductor_loss_w),
                    "magnetic_loss_w": _stable(point.magnetic_loss_w),
                    "capacitor_loss_w": _stable(point.capacitor_loss_w),
                    "bridge_rectifier_loss_w": _stable(point.bridge_rectifier_loss_w),
                    "other_loss_w": _stable(point.other_loss_w),
                    "warnings": list(point.warnings),
                }
                for point in sweep.points
            ],
            "warnings": list(sweep.warnings),
            "artifact_names": sorted(sweep.artifact_paths),
        },
        "notes": list(report.notes),
    }


def _stress_snapshot(metric: Any) -> dict[str, object]:
    return {
        "voltage_max_v": _stable(metric.voltage_max_v),
        "current_peak_a": _stable(metric.current_peak_a),
        "current_rms_a": _stable(metric.current_rms_a),
        "current_avg_a": _stable(metric.current_avg_a),
    }


def _stable(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 12)
    if isinstance(value, dict):
        return {str(key): _stable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_stable(item) for item in value]
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Path for the JSON baseline fixture.")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build_baseline(), indent=2, sort_keys=True) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
