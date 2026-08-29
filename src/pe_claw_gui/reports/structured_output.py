"""Stable cross-version design-report output contract.

The GUI models remain the runtime handoff objects.  This module is the single
boundary used by JSON, CSV, and Markdown exporters so presentation text cannot
silently become the source of engineering field semantics.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

from ..models.design_report import DesignReport


REPORT_SCHEMA_VERSION = "pe_claw_structured_design_report_v1"
STATUS_VALUES = ("pass", "fail", "not_evaluated", "boundary", "unknown")


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(float(value)) else None
    return None


def _field(value: Any, unit: str, source: str) -> dict[str, Any]:
    return {"value": value, "unit": unit, "source": source}


def _metric(value: Any, unit: str, source: str) -> dict[str, Any]:
    return _field(_number(value), unit, source)


def _series_summary(values: Sequence[Any], unit: str, source: str) -> dict[str, Any]:
    numbers = [float(value) for value in values if _number(value) is not None]
    if not numbers:
        return {
            key: _metric(None, unit, source)
            for key in ("average", "rms", "peak", "valley", "peak_to_peak")
        }
    average = sum(numbers) / len(numbers)
    return {
        "average": _metric(average, unit, source),
        "rms": _metric(math.sqrt(sum(value * value for value in numbers) / len(numbers)), unit, source),
        "peak": _metric(max(numbers), unit, source),
        "valley": _metric(min(numbers), unit, source),
        "peak_to_peak": _metric(max(numbers) - min(numbers), unit, source),
    }


def _lookup(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            return value
    return None


def _find_bool(value: Any, keys: set[str]) -> bool | None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in keys and isinstance(item, bool):
                return item
            found = _find_bool(item, keys)
            if found is not None:
                return found
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            found = _find_bool(item, keys)
            if found is not None:
                return found
    return None


def _status(value: bool | None) -> str:
    if value is None:
        return "not_evaluated"
    return "pass" if value else "fail"


def _waveform_payload(report: DesignReport) -> dict[str, Any]:
    waveform = report.waveform
    if waveform is None:
        return {"available": False, "operating": {}, "series": {}, "metadata": {}}
    source = "topology.waveform_post_processing"
    series = {
        "switch_node_voltage": _series_summary(waveform.switch_node_voltage_v, "V", source),
        "inductor_current": _series_summary(waveform.inductor_current_a, "A", source),
        "capacitor_current": _series_summary(waveform.capacitor_current_a, "A", source),
        "output_voltage": _series_summary(waveform.output_voltage_v, "V", source),
        "switch_current": _series_summary(waveform.switch_current_a, "A", source),
        "diode_current": _series_summary(waveform.diode_current_a, "A", source),
        "input_source_current": _series_summary(waveform.input_source_current_a, "A", source),
        "inductor_voltage": _series_summary(waveform.inductor_voltage_v, "V", source),
        "output_ripple": _series_summary(waveform.output_ripple_v, "V", source),
    }
    metadata = waveform.metadata if isinstance(waveform.metadata, Mapping) else {}
    metadata_keys = {
        "solver", "step_size_s", "samples_per_period", "samples_per_line_cycle",
        "cycles_simulated", "settling_cycles_discarded", "converged", "convergence_status",
        "power_factor", "zvs_status", "fha_status",
    }
    return {
        "available": True,
        "operating": {
            "input_voltage": _metric(waveform.operating_vin_v, "V", "topology.waveform"),
            "output_voltage": _metric(waveform.operating_vout_v, "V", "topology.waveform"),
            "load_ratio": _metric(waveform.load_ratio, "p.u.", "topology.waveform"),
            "duty": _metric(waveform.duty, "ratio", "topology.waveform"),
            "switching_frequency": _metric(
                1.0 / waveform.switching_period_s if waveform.switching_period_s else None,
                "Hz",
                "topology.waveform",
            ),
            "switching_period": _metric(waveform.switching_period_s, "s", "topology.waveform"),
            "time_span": _metric(waveform.time_span_s, "s", "topology.waveform"),
        },
        "mode": waveform.mode,
        "series": series,
        "metadata": {key: metadata[key] for key in sorted(metadata_keys) if key in metadata},
    }


def _hardware_payload(report: DesignReport) -> dict[str, Any]:
    device = report.device
    magnetic = report.magnetic
    capacitor = report.capacitor

    def part(side: str) -> str | None:
        selection = getattr(capacitor, side, None) if capacitor is not None else None
        recommended = getattr(selection, "recommended", None)
        candidate = getattr(recommended, "candidate", None)
        return getattr(candidate, "part_number", None)

    is_llc = bool(magnetic and getattr(magnetic, "result_type", "") == "separated_llc_transformer")
    llc_summary = getattr(magnetic, "llc_result_summary", None) if is_llc else None
    llc_contract = getattr(magnetic, "llc_magnetic_contract", None) if is_llc else None
    llc_transformer_id = (
        getattr(llc_contract, "transformer_design_id", None)
        or getattr(magnetic, "recommended_transformer_design_id", None)
        if is_llc
        else None
    )
    llc_external_id = (
        getattr(llc_contract, "external_lr_design_id", None)
        if is_llc and llc_contract is not None
        else getattr(magnetic, "recommended_external_lr_design_id", None) if is_llc else None
    )
    llc_combined_id = (
        getattr(llc_contract, "combined_magnetic_design_id", None)
        if is_llc and llc_contract is not None
        else getattr(magnetic, "recommended_combined_magnetic_design_id", None) if is_llc else None
    )
    llc_external_status = getattr(getattr(llc_summary, "external_lr", None), "status", "not_evaluated")
    llc_selection_id = llc_combined_id or (llc_transformer_id if llc_external_status == "not_required" else None)
    llc_selection_ids = [item for item in (llc_transformer_id, llc_external_id) if item]
    payload = {
        "semiconductor": {
            "selected_devices": dict(getattr(device, "selected_devices", {}) or {}) if device else {},
            "selection_status": "pass" if device and device.selected_devices else "not_evaluated",
        },
        "magnetic": {
            "selected_design_id": llc_selection_id if is_llc else (getattr(magnetic, "selected_design_id", None) if magnetic else None),
            "chosen_design_ids": llc_selection_ids if is_llc else [getattr(item, "design_id", None) for item in (getattr(magnetic, "chosen_designs", []) or [])] if magnetic else [],
            "selection_status": (
                "pass" if llc_selection_id else (llc_external_status if is_llc else "not_evaluated")
            ),
        },
        "capacitor": {
            "input_part_number": part("input_selection"),
            "output_part_number": part("output_selection"),
            "selection_status": "pass" if capacitor else "not_evaluated",
        },
    }
    if llc_contract is not None:
        payload["magnetic"]["llc_magnetic_contract"] = llc_contract.to_dict()
    return payload


def _magnetic_payload(report: DesignReport) -> dict[str, Any]:
    magnetic = report.magnetic
    if magnetic is None:
        return {"available": False, "selected_design_id": None, "chosen_design_ids": [], "metrics": {}, "metadata": {}}
    chosen = getattr(magnetic, "chosen_designs", []) or []
    selected = getattr(magnetic, "selected_design_id", None)
    payload = {
        "available": True,
        "selected_design_id": selected,
        "chosen_design_ids": [getattr(item, "design_id", None) for item in chosen],
        "metrics": {
            "feasible_count": _metric(getattr(magnetic, "feasible_count", None), "count", "magnetic.selection"),
            "pareto_count": _metric(getattr(magnetic, "pareto_count", None), "count", "magnetic.selection"),
        },
        "metadata": {
            "result_type": getattr(magnetic, "result_type", ""),
            "design_type": getattr(magnetic, "design_type", ""),
            "performance_timing": getattr(magnetic, "performance_timing", {}),
        },
    }
    llc_summary = getattr(magnetic, "llc_result_summary", None)
    if getattr(magnetic, "result_type", "") == "separated_llc_transformer" and llc_summary is not None:
        contract = getattr(magnetic, "llc_magnetic_contract", None)
        def stage_payload(stage: Any, source: str) -> dict[str, Any]:
            return {
                "status": getattr(stage, "status", "not_evaluated"),
                "metrics": {
                    "generated_candidates": _metric(getattr(stage, "generated_candidate_count", None), "count", f"{source}.generated"),
                    "prefilter_rejected_candidates": _metric(getattr(stage, "prefilter_rejected_candidate_count", None), "count", f"{source}.prefilter_rejected"),
                    "prefilter_pass_candidates": _metric(getattr(stage, "prefilter_pass_count", None), "count", f"{source}.prefilter_pass"),
                    "precise_evaluated_candidates": _metric(getattr(stage, "precise_evaluated_candidate_count", None), "count", f"{source}.precise"),
                    "feasible_candidates": _metric(getattr(stage, "feasible_candidate_count", None), "count", f"{source}.feasible"),
                    "pareto_candidates": _metric(getattr(stage, "pareto_candidate_count", None), "count", f"{source}.pareto"),
                },
                "recommended_design_id": getattr(stage, "recommended_design_id", None),
                "prefilter_rejection_counts": dict(getattr(stage, "prefilter_rejection_counts", {}) or {}),
                "failure_code": getattr(stage, "failure_code", None),
                "failure_reason": getattr(stage, "failure_reason", None),
                "artifact_paths": list(getattr(stage, "artifact_paths", []) or []),
            }

        payload["llc"] = {
            "transformer": stage_payload(llc_summary.transformer, "magnetic.llc.transformer"),
            "external_lr": stage_payload(llc_summary.external_lr, "magnetic.llc.external_lr"),
            "recommendations": {
                "transformer_design_id": getattr(contract, "transformer_design_id", getattr(llc_summary, "recommended_transformer_design_id", None)),
                "external_lr_design_id": getattr(contract, "external_lr_design_id", getattr(llc_summary, "recommended_external_lr_design_id", None)),
                "combined_magnetic_design_id": getattr(contract, "combined_magnetic_design_id", getattr(llc_summary, "recommended_combined_magnetic_design_id", None)),
            },
        }
        if contract is not None:
            payload["llc"]["magnetic_contract"] = contract.to_dict()
    return payload


def _capacitor_payload(report: DesignReport) -> dict[str, Any]:
    capacitor = report.capacitor
    if capacitor is None:
        return {"available": False, "input": {}, "output": {}, "metadata": {}}

    def side_payload(side: Any, source: str) -> dict[str, Any]:
        entry = getattr(side, "recommended", None) if side is not None else None
        candidate = getattr(entry, "candidate", None)
        return {
            "part_number": getattr(candidate, "part_number", None),
            "metrics": {
                "capacitance": _metric(getattr(entry, "equivalent_capacitance_f", None), "F", source),
                "ripple_total": _metric(getattr(entry, "ripple_total_pp_v", None), "V", source),
                "current_rms": _metric(getattr(entry, "capacitor_current_rms_total_a", None), "A", source),
                "hotspot_temperature": _metric(getattr(entry, "hotspot_temp_c", None), "degC", source),
            },
            "selection_status": "pass" if entry is not None else "not_evaluated",
        }

    return {
        "available": True,
        "input": side_payload(getattr(capacitor, "input_selection", None), "capacitor.input_selection"),
        "output": side_payload(getattr(capacitor, "output_selection", None), "capacitor.output_selection"),
        "metadata": {},
    }


def _thermal_payload(report: DesignReport) -> dict[str, Any]:
    thermal = report.thermal
    estimate = getattr(thermal, "recommended_estimate", None) if thermal is not None else None
    if thermal is None:
        return {"available": False, "status": "not_evaluated", "metrics": {}, "metadata": {}}
    source = "thermal.evaluation"
    payload = {
        "available": True,
        "status": getattr(thermal, "status", "not_evaluated"),
        "metrics": {
            "ambient_temperature": _metric(getattr(thermal, "ambient_temp_c", None), "degC", source),
            "hotspot_temperature": _metric(getattr(estimate, "hotspot_proxy_temp_c", None), "degC", source),
            "total_loss": _metric(getattr(estimate, "total_loss_w", None), "W", source),
        },
        "metadata": {"summary": getattr(thermal, "summary", "")},
    }
    components = getattr(thermal, "llc_component_thermal", {}) or {}
    if components:
        payload["llc_components"] = {
            str(role): {
                "status": str(values.get("status", "not_evaluated")),
                "design_id": values.get("design_id"),
                "hotspot_temperature": _metric(values.get("hotspot_c"), "degC", f"thermal.llc.{role}"),
                "source": values.get("source", ""),
            }
            for role, values in components.items()
            if isinstance(values, Mapping)
        }
    return payload


def _loss_payload(report: DesignReport) -> dict[str, Any]:
    loss = report.loss
    if loss is None:
        return {"available": False, "recommended_design_id": None, "metrics": {}, "metadata": {}}
    payload: dict[str, Any] = {
        "available": True,
        "recommended_design_id": loss.recommended_design_id,
        "metrics": {
            "total_loss": _metric(loss.total_loss_w, "W", "loss.total"),
            "recommended_volume": _metric(
                loss.recommended_design_total_volume_m3,
                "m3",
                "loss.recommended_volume",
            ),
        },
        "metadata": {"core_loss_status": getattr(loss, "core_loss_status", "not_evaluated")},
    }
    if report.magnetic is not None and report.magnetic.result_type == "separated_llc_transformer":
        breakdown = loss.breakdown_w
        volumes = getattr(loss, "component_volumes_m3", {}) or {}
        contract = getattr(report.magnetic, "llc_magnetic_contract", None)
        payload["llc"] = {
            "transformer": {
                "design_id": getattr(contract, "transformer_design_id", report.magnetic.recommended_transformer_design_id),
                "core_loss": _metric(breakdown.get("llc_transformer_core_loss_w"), "W", "loss.llc.transformer.core"),
                "copper_loss": _metric(breakdown.get("llc_transformer_copper_loss_w"), "W", "loss.llc.transformer.copper"),
                "total_loss": _metric(breakdown.get("llc_transformer_total_loss_w"), "W", "loss.llc.transformer.total"),
                "volume": _metric(volumes.get("transformer_volume_m3"), "m3", "loss.llc.transformer.volume"),
            },
            "external_lr": {
                "design_id": getattr(contract, "external_lr_design_id", report.magnetic.recommended_external_lr_design_id),
                "core_loss": _metric(breakdown.get("llc_external_resonant_inductor_core_loss_w"), "W", "loss.llc.external_lr.core"),
                "copper_loss": _metric(breakdown.get("llc_external_resonant_inductor_copper_loss_w"), "W", "loss.llc.external_lr.copper"),
                "total_loss": _metric(breakdown.get("llc_external_resonant_inductor_total_loss_w"), "W", "loss.llc.external_lr.total"),
                "volume": _metric(volumes.get("external_lr_volume_m3"), "m3", "loss.llc.external_lr.volume"),
            },
            "combined": {
                "design_id": getattr(contract, "combined_magnetic_design_id", report.magnetic.recommended_combined_magnetic_design_id),
                "core_loss": _metric(breakdown.get("llc_magnetic_core_loss_w"), "W", "loss.llc.combined.core"),
                "copper_loss": _metric(breakdown.get("llc_magnetic_copper_loss_w"), "W", "loss.llc.combined.copper"),
                "total_loss": _metric(breakdown.get("llc_magnetic_total_loss_w"), "W", "loss.llc.combined.total"),
                "volume": _metric(volumes.get("combined_magnetic_volume_m3"), "m3", "loss.llc.combined.volume"),
            },
        }
        if contract is not None:
            payload["llc"]["magnetic_contract"] = contract.to_dict()
    return payload


def _geometry_payload(report: DesignReport) -> dict[str, Any]:
    geometry = report.geometry
    if geometry is None:
        return {"available": False, "selected_design_id": None, "targets": [], "metadata": {}}
    return {
        "available": True,
        "selected_design_id": geometry.selected_design_id,
        "targets": [
            {
                "role": target.role,
                "label": target.label,
                "design_id": target.design_id,
                "volume": _metric(target.volume_m3, "m3", f"geometry.{target.role}.volume"),
                "loss": _metric(target.loss_w, "W", f"geometry.{target.role}.loss"),
                "artifact_paths": [str(path) for path in target.artifact_paths],
                "duplicate_of": target.duplicate_of,
                "error": target.error_message,
            }
            for target in geometry.targets
        ],
        "metadata": {
            "component_type": getattr(geometry, "component_type", "fixed_inductor"),
            "artifact_paths": [str(path) for path in geometry.artifact_paths],
            "summary": geometry.summary,
        },
    }


def build_structured_report(report: DesignReport) -> dict[str, Any]:
    """Convert a runtime report to the stable, unit-explicit contract."""

    candidate = report.candidate
    spec = report.spec
    metadata = candidate.metadata if candidate is not None and isinstance(candidate.metadata, Mapping) else {}
    zvs_value = _find_bool(metadata, {"zvs_pass", "full_load_zvs_pass", "min_load_zvs_pass"})
    pf_value = _lookup(metadata, "power_factor", "pf")
    thermal_status = getattr(report.thermal, "status", "not_evaluated") if report.thermal else "not_evaluated"
    if thermal_status not in STATUS_VALUES:
        thermal_status = "unknown"
    output_ripple_target = float(spec.ripple_voltage_ratio_percent) / 100.0 * float(spec.vout) if spec.vout else None
    estimated_ripple = candidate.delta_vo if candidate is not None else None
    simulated_ripple = None
    if report.waveform is not None and report.waveform.output_voltage_v:
        simulated_ripple = max(report.waveform.output_voltage_v) - min(report.waveform.output_voltage_v)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_kind": "design_report",
        "topology": {"id": spec.topology_id, "display_name": spec.display_name},
        "request": {
            "raw_input": dict(spec.raw_input),
            "input_voltage_min": _metric(spec.vin_min, "V", "request.normalized"),
            "input_voltage_max": _metric(spec.vin_max, "V", "request.normalized"),
            "output_voltage": _metric(spec.vout, "V", "request.normalized"),
            "output_power": _metric(spec.pout, "W", "request.normalized"),
            "switching_frequency": _metric(spec.fs_khz * 1000.0, "Hz", "request.normalized"),
            "ripple_current_ratio": _metric(spec.ripple_current_ratio, "ratio", "request.normalized"),
            "ripple_voltage_ratio": _metric(spec.ripple_voltage_ratio_percent / 100.0, "ratio", "request.normalized"),
        },
        "candidate": {
            "available": candidate is not None,
            "inductance": _metric(getattr(candidate, "inductance_h", None), "H", "candidate.synthesis"),
            "capacitance": _metric(getattr(candidate, "capacitance_f", None), "F", "candidate.synthesis"),
            "duty": _metric(getattr(candidate, "duty_nom", None), "ratio", "candidate.synthesis"),
            "output_current": _metric(getattr(candidate, "iout", None), "A", "candidate.synthesis"),
            "switching_frequency": _metric(getattr(candidate, "fs_hz", None), "Hz", "candidate.synthesis"),
            "inductor_ripple": _metric(getattr(candidate, "delta_il", None), "A", "candidate.synthesis"),
            "output_ripple_estimated": _metric(estimated_ripple, "V", "candidate.synthesis"),
            "feasible": getattr(candidate, "feasible", None),
            "ccm_valid": getattr(candidate, "ccm_valid", None),
            "mode": getattr(candidate, "mode_capable", None),
        },
        "operating_point": {
            "available": report.operating_point is not None,
            "input_voltage": _metric(getattr(report.operating_point, "vin_v", None), "V", "operating_point.input"),
            "load_ratio": _metric(getattr(report.operating_point, "load_ratio", None), "p.u.", "operating_point.input"),
            "output_voltage": _metric(getattr(report.operating_point, "vout_v", None), "V", "operating_point.input"),
            "power_factor": _metric(getattr(report.operating_point, "power_factor", None), "ratio", "operating_point.input"),
            "switching_frequency": _metric(getattr(report.operating_point, "switching_frequency_hz", None), "Hz", "operating_point.input"),
        },
        "waveform": _waveform_payload(report),
        "stress": {
            "available": report.stress is not None,
            "switch": _stress_metric(getattr(report.stress, "switch", None)),
            "rectifier": _stress_metric(getattr(report.stress, "rectifier", None)),
        },
        "magnetic": _magnetic_payload(report),
        "loss": _loss_payload(report),
        "geometry": _geometry_payload(report),
        "capacitor": _capacitor_payload(report),
        "thermal": _thermal_payload(report),
        "hardware": _hardware_payload(report),
        "ripple": {
            "output_ripple_target": _metric(output_ripple_target, "V", "request.normalized"),
            "output_ripple_estimated": _metric(estimated_ripple, "V", "candidate.synthesis"),
            "output_ripple_predicted": _metric(_capacitor_ripple(report), "V", "capacitor.selection"),
            "output_ripple_simulated": _metric(simulated_ripple, "V", "waveform.post_processing"),
            "dc_link_ripple_limit": _metric(None, "V", "request.normalized"),
            "dc_link_ripple_predicted": _metric(None, "V", "capacitor.selection"),
        },
        "status": {
            "feasible": getattr(candidate, "feasible", None),
            "ccm_valid": getattr(candidate, "ccm_valid", None),
            "zvs_status": _status(zvs_value),
            "pf_status": "pass" if isinstance(pf_value, (int, float)) and float(pf_value) >= 0.99 else "not_evaluated",
            "thermal_status": thermal_status,
        },
        "audit": {
            "notes": [*report.notes, *(report.stress.notes if report.stress else [])],
            "source_stages": ["request", "candidate", "waveform", "stress", "magnetic", "capacitor", "thermal", "status"],
        },
    }


def _stress_metric(metric: Any) -> dict[str, Any]:
    return {
        "voltage_max": _metric(getattr(metric, "voltage_max_v", None), "V", "stress.extraction"),
        "current_peak": _metric(getattr(metric, "current_peak_a", None), "A", "stress.extraction"),
        "current_rms": _metric(getattr(metric, "current_rms_a", None), "A", "stress.extraction"),
        "current_average": _metric(getattr(metric, "current_avg_a", None), "A", "stress.extraction"),
    }


def _capacitor_ripple(report: DesignReport) -> float | None:
    capacitor = report.capacitor
    selection = getattr(capacitor, "output_selection", None) if capacitor else None
    entry = getattr(selection, "recommended", None)
    return getattr(entry, "ripple_total_pp_v", None)


def canonical_json(payload: Mapping[str, Any]) -> str:
    """Return deterministic JSON used for checksums and snapshots."""

    return json.dumps(payload, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":"))


def render_markdown_report(payload: Mapping[str, Any]) -> str:
    """Render the contract without reinterpreting engineering values."""

    topology = payload["topology"]
    lines = [
        "# PE-Claw Design Report",
        "",
        f"Schema Version: `{payload['schema_version']}`",
        "",
        "## Topology",
        "",
        f"- ID: `{topology['id']}`",
        f"- Display Name: {topology['display_name']}",
        "",
        "## Status",
        "",
        "| Field | Value |",
        "| --- | --- |",
    ]
    for key, value in payload["status"].items():
        lines.append(f"| {key} | {value} |")
    for section_name in ("request", "candidate", "operating_point", "waveform", "stress", "magnetic", "capacitor", "thermal", "ripple"):
        section = payload.get(section_name, {})
        rows = list(_quantity_rows(section))
        if not rows:
            continue
        lines.extend(["", f"## {section_name.replace('_', ' ').title()}", "", "| Field | Value | Unit | Source |", "| --- | ---: | --- | --- |"])
        lines.extend(f"| {path} | {value} | {unit} | {source} |" for path, value, unit, source in rows)
    return "\n".join(lines) + "\n"


def _quantity_rows(value: Any, prefix: str = "") -> list[tuple[str, Any, str, str]]:
    """Flatten only quantity objects; display values come from the contract."""
    if isinstance(value, Mapping):
        if {"value", "unit", "source"}.issubset(value):
            return [(prefix, value["value"], value["unit"], value["source"])]
        rows: list[tuple[str, Any, str, str]] = []
        for key in sorted(value):
            path = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(_quantity_rows(value[key], path))
        return rows
    return []


def flatten_quantity_rows(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return CSV-ready rows without parsing Markdown or display strings."""
    rows = []
    for path, value, unit, source in _quantity_rows(payload):
        rows.append({"path": path, "value": value, "unit": unit, "source": source})
    return rows


__all__ = ["REPORT_SCHEMA_VERSION", "build_structured_report", "canonical_json", "flatten_quantity_rows", "render_markdown_report"]
