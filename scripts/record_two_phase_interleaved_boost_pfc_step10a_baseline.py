"""Freeze the Step 10A design-boundary baseline for two-phase interleaved Boost PFC."""

from __future__ import annotations

import argparse
import json
from importlib import import_module
from pathlib import Path
import tempfile
from typing import Any

from pe_claw_gui.app.result_views.loss_view import _build_interleaved_boost_pfc_loss_summary
from pe_claw_gui.app.result_views.summary_view import _build_electrical_parameter_lines
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry


TOPOLOGY_ID = "single_phase_interleaved_boost_pfc_diode_bridge"
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
    "input_inductance_h",
)
BOUNDARY_METADATA_KEYS = (
    "vac_rms_v",
    "vac_rms_min_v",
    "vac_rms_max_v",
    "vdc_target_v",
    "fsw_hz",
    "power_factor_target",
    "electrical_current_basis",
    "electrical_input_current_rms_a",
    "electrical_input_current_peak_a",
    "phase_current_rms_a",
    "phase_current_peak_a",
    "phase_current_fraction",
    "current_sharing_assumption",
    "input_inductance_h",
    "input_inductance_role",
    "inductor_design_line",
    "boost_inductor_required_h",
    "phase_boost_inductance_h",
    "total_series_inductance_required_h",
    "phase_total_series_inductance_h",
    "boost_inductor_requirement_basis",
    "boost_inductor_worst_theta_deg",
    "boost_inductor_worst_vrectified_v",
    "boost_inductor_worst_duty",
    "boost_inductor_worst_delta_i_allowed_a",
    "delta_il_pp_target_a",
    "delta_il_pp_nom_a",
    "inductor_ripple_worst_case_a",
    "inductor_ripple_worst_theta_deg",
    "inductor_ripple_reference",
    "inductor_ripple_equation",
    "bridge_current_basis",
    "bridge_reverse_stress_v",
    "recommended_diode_vrrm_v",
    "required_min_vdc_v",
    "vdc_feasibility_passed",
)
LINE_CYCLE_KEYS = (
    "theta_deg",
    "v_rectified_v",
    "total_input_current_a",
    "phase_current_a",
    "duty",
    "delta_i_allowed_a",
)


def build_baseline() -> dict[str, object]:
    """Run the current two-phase design chain and return stable evidence."""

    registry = build_default_registry()
    plugin = registry.get_plugin(TOPOLOGY_ID)
    topology_module = import_module(plugin.__module__)
    default_inputs = topology_module.build_default_inputs()
    options = PipelineOptions(
        enable_magnetic_design=True,
        enable_capacitor_design=True,
        enable_bridge_rectifier_selection=True,
    )
    cases: list[dict[str, object]] = []

    with tempfile.TemporaryDirectory(prefix="s10a_pfc_") as output_root:
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
            cases.append(_snapshot_case(case_id, raw_input, report))

    return {
        "schema_version": "two_phase_interleaved_boost_pfc_step10a_baseline_v1",
        "topology_id": TOPOLOGY_ID,
        "scope": {
            "design_point": "full two-phase pipeline with bridge, semiconductor, magnetic, capacitor, loss, thermal, and geometry stages",
            "operating_points": ["nominal", "low_line", "high_line"],
            "frozen_semantics": {
                "candidate_inductance_h": "per-phase total series inductance",
                "phase_boost_inductance_h": "per-phase Boost inductor target used by magnetic selection",
                "input_inductance_h": "per-phase series input inductance contribution",
                "phase_current_average": "line-cycle average of one ideal-equal-sharing phase current",
                "phase_current_rms": "RMS of one phase current envelope plus switching-ripple contribution where applicable",
                "phase_current_peak": "design-boundary phase current peak before or with switching ripple as explicitly reported",
            },
            "design_boundaries": {
                "inductance_and_current": "low-line current envelope",
                "device_and_bridge_voltage": "high-line rectified peak / DC-bus blocking boundary",
                "nominal_waveform": "nominal line used for GUI operating-point readback",
            },
            "dynamic_fields_excluded": ["run_id", "timestamps", "runtime_seconds", "temporary_paths", "artifact_paths"],
        },
        "cases": cases,
    }


def _snapshot_case(case_id: str, raw_input: dict[str, str], report: Any) -> dict[str, object]:
    candidate = report.candidate
    waveform = report.waveform
    stress = report.stress
    if candidate is None or waveform is None or stress is None:
        raise AssertionError(f"Incomplete two-phase Step 10A baseline case: {case_id}")

    metadata = candidate.metadata if isinstance(candidate.metadata, dict) else {}
    waveform_metadata = waveform.metadata if isinstance(waveform.metadata, dict) else {}
    bridge = report.bridge_rectifier
    bridge_candidate = getattr(bridge, "selected_candidate", None)
    magnetic = report.magnetic
    selected_capacitor = getattr(getattr(report.capacitor, "output_selection", None), "recommended", None)

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
            key: _stable(metadata.get(key)) for key in BOUNDARY_METADATA_KEYS
        },
        "line_cycles": {
            name: _line_cycle_snapshot(metadata.get(name))
            for name in ("line_cycle", "low_line_line_cycle", "high_line_line_cycle")
        },
        "waveform": {
            "public": {
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
            "phase_device_metrics": _stable(waveform_metadata.get("phase_device_metrics")),
            "bridge_metrics": _stable(waveform_metadata.get("bridge_metrics")),
            "aggregate_metrics": {
                key: _stable(waveform_metadata.get(key))
                for key in (
                    "aggregate_inductor_current_avg_a",
                    "aggregate_inductor_current_rms_a",
                    "aggregate_switch_current_avg_a",
                    "aggregate_switch_current_rms_a",
                    "aggregate_diode_current_avg_a",
                    "aggregate_diode_current_rms_a",
                    "dc_link_capacitor_current_rms_a",
                )
            },
            "interleaved_ripple": _stable(waveform_metadata.get("interleaved_ripple_pp_a")),
            "phase_current_arrays": _stable(waveform_metadata.get("phase_currents_a")),
        },
        "stress": {
            "representative_phase": {
                "switch": _stress_snapshot(stress.switch),
                "rectifier": _stress_snapshot(stress.rectifier),
            },
            "phase_device_metrics": _stable(waveform_metadata.get("phase_device_metrics")),
            "notes": list(stress.notes),
        },
        "hardware": {
            "selected_devices": dict(report.device.selected_devices) if report.device is not None else None,
            "device_candidate_counts": _stable(getattr(report.device, "candidate_counts", {})),
            "device_passed_candidate_counts": _stable(getattr(report.device, "passed_candidate_counts", {})),
            "bridge_candidate_id": getattr(bridge_candidate, "candidate_id", None),
            "bridge_part_number": getattr(bridge_candidate, "part_number", None),
            "bridge_request": _bridge_request_snapshot(getattr(bridge, "request", None)),
            "magnetic_selected_design_id": getattr(magnetic, "selected_design_id", None),
            "magnetic_summary": getattr(magnetic, "summary", None),
            "magnetic_notes": list(getattr(magnetic, "notes", ())),
            "magnetic_designs": [_magnetic_design_snapshot(design) for design in getattr(magnetic, "chosen_designs", ())],
            "magnetic_requirements": _stable(getattr(magnetic, "design_requirements", {})),
            "capacitor_part_number": getattr(getattr(selected_capacitor, "candidate", None), "part_number", None),
            "capacitor_bank_capacitance_f": _stable(getattr(selected_capacitor, "equivalent_capacitance_f", None)),
        },
        "loss": {
            "total_loss_w": _stable(getattr(report.loss, "total_loss_w", None)),
            "breakdown_w": _stable(getattr(report.loss, "breakdown_w", {})),
            "notes": list(getattr(report.loss, "notes", ())),
        },
        "thermal": {
            "summary": getattr(report.thermal, "summary", None),
            "recommended_design_id": getattr(report.thermal, "recommended_design_id", None),
            "status": getattr(report.thermal, "status", None),
        },
        "geometry": {
            "component_type": getattr(report.geometry, "component_type", None),
            "footprint_mm2": _stable(getattr(report.geometry, "footprint_mm2", None)),
            "selected_design_id": getattr(report.geometry, "selected_design_id", None),
        },
        "gui": {
            "electrical_summary_lines": _build_electrical_parameter_lines(report),
            "loss_summary_lines": _build_interleaved_boost_pfc_loss_summary(report),
        },
        "notes": list(report.notes),
    }


def _line_cycle_snapshot(value: Any) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    return {key: _stable(value.get(key)) for key in LINE_CYCLE_KEYS}


def _stress_snapshot(metric: Any) -> dict[str, object]:
    return {
        "voltage_max_v": _stable(getattr(metric, "voltage_max_v", None)),
        "current_peak_a": _stable(getattr(metric, "current_peak_a", None)),
        "current_rms_a": _stable(getattr(metric, "current_rms_a", None)),
        "current_avg_a": _stable(getattr(metric, "current_avg_a", None)),
    }


def _bridge_request_snapshot(request: Any) -> dict[str, object] | None:
    if request is None:
        return None
    return {
        key: _stable(getattr(request, key, None))
        for key in (
            "topology_id",
            "ac_input_rms_v",
            "dc_bus_voltage_v",
            "output_power_w",
            "dc_output_current_a",
            "bridge_current_avg_a",
            "bridge_current_rms_a",
            "required_reverse_voltage_v",
            "recommended_reverse_voltage_v",
            "current_margin",
            "voltage_margin",
        )
    }


def _magnetic_design_snapshot(design: Any) -> dict[str, object]:
    metadata = getattr(design, "metadata", {})
    return {
        key: _stable(getattr(design, key, None))
        for key in (
            "candidate_id",
            "core_name",
            "material_name",
            "wire_name",
            "turns",
            "parallel_bundles",
            "inductance_h",
            "gap_m",
            "reference_copper_loss_w",
            "reference_core_loss_w",
            "reference_total_loss_w",
        )
    } | {
        "phase_role": _stable(metadata.get("phase_role")) if isinstance(metadata, dict) else None,
        "physical_instance_id": _stable(metadata.get("physical_instance_id")) if isinstance(metadata, dict) else None,
        "library_candidate_id": _stable(metadata.get("library_candidate_id")) if isinstance(metadata, dict) else None,
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
