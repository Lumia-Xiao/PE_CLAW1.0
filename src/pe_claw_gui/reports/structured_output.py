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
from ..pipeline.llc_pf_artifacts import llc_pf_artifact_payload
from ..pipeline.llc_representatives import build_llc_representative_payload


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
    payload = {
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
    npc_validation = _npc_waveform_validation_payload(report)
    if npc_validation:
        payload["npc_current_validation"] = npc_validation
    return payload


def _npc_waveform_validation_payload(report: DesignReport) -> dict[str, Any]:
    """Expose compact NPC current and event validation evidence in reports."""

    if report.spec.topology_id != "three_phase_three_level_npc_inverter" or report.waveform is None:
        return {}
    metadata = report.waveform.metadata if isinstance(report.waveform.metadata, Mapping) else {}
    details = metadata.get("three_phase_npc_pd_spwm_waveforms")
    if not isinstance(details, Mapping):
        return {}
    phases = ("a", "b", "c")

    def series(key: str, unit: str = "A") -> dict[str, Any]:
        values = details.get(key, [])
        return _series_summary(values if isinstance(values, Sequence) else [], unit, f"npc.waveform.{key}")

    actual_currents = [details.get(f"i{phase}_a", []) for phase in phases]
    current_sum = [
        sum(float(actual_currents[phase_index][index]) for phase_index in range(3))
        for index in range(min((len(values) for values in actual_currents), default=0))
    ]
    periodic_initial = metadata.get("phase_current_periodic_steady_state_initial_current_a", [])
    periodic_end = metadata.get("phase_current_periodic_steady_state_period_end_current_a", [])
    periodic_residual = metadata.get("phase_current_periodic_steady_state_residual_a", [])
    average_errors = metadata.get("phase_current_average_error_a", {})

    return {
        "status": "available",
        "phase_current_source": "three_phase_npc_pd_spwm_waveforms.ia_a_ib_a_ic_a",
        "phases": {
            phase: {
                "reference_average": series(f"i{phase}_reference_average_a"),
                "actual_average": series(f"i{phase}_actual_average_a"),
                "average_error": _series_summary(
                    average_errors.get(phase, []) if isinstance(average_errors, Mapping) else [],
                    "A",
                    f"npc.metadata.phase_current_average_error_a.{phase}",
                ),
                "switching_ripple": series(f"i{phase}_switching_ripple_a"),
            }
            for phase in phases
        },
        "three_phase_current_sum": _series_summary(current_sum, "A", "npc.waveform.ia_plus_ib_plus_ic"),
        "periodic_steady_state": {
            "solver_method": metadata.get("phase_current_periodic_steady_state_solver_method"),
            "status": metadata.get("phase_current_periodic_steady_state_solver_status"),
            "converged": metadata.get("phase_current_periodic_steady_state_converged"),
            "initial_current": _field(periodic_initial, "A", "npc.periodic_steady_state.initial"),
            "period_end_current": _field(periodic_end, "A", "npc.periodic_steady_state.period_end"),
            "residual": _field(periodic_residual, "A", "npc.periodic_steady_state.residual"),
            "residual_max": _metric(
                max((abs(float(value)) for value in periodic_residual), default=0.0),
                "A",
                "npc.periodic_steady_state.residual",
            ),
            "tolerance": _metric(
                metadata.get("phase_current_periodic_steady_state_tolerance_a"),
                "A",
                "npc.periodic_steady_state.tolerance",
            ),
            "modulation_saturated": metadata.get("phase_current_periodic_steady_state_modulation_saturated"),
        },
        "average_error_max": _metric(
            metadata.get("phase_current_average_error_max_a"),
            "A",
            "npc.current_tracking.average_error",
        ),
        "event_count": _metric(
            metadata.get("three_phase_npc_switching_event_count"),
            "count",
            "npc.waveform.events",
        ),
        "event_source": metadata.get("npc_switching_event_source"),
        "event_current_source": metadata.get("npc_switching_event_current_source"),
        "event_blocking_voltage_source": metadata.get("npc_switching_event_blocking_voltage_source"),
        "endpoint_correction_applied": metadata.get("phase_current_periodic_correction_applied"),
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
    if getattr(magnetic, "result_type", "") == "separated_llc_transformer":
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
                    "chosen_candidates": _metric(getattr(stage, "chosen_candidate_count", None), "count", f"{source}.chosen"),
                },
                "recommended_design_id": getattr(stage, "recommended_design_id", None),
                "prefilter_rejection_counts": dict(getattr(stage, "prefilter_rejection_counts", {}) or {}),
                "failure_code": getattr(stage, "failure_code", None),
                "failure_reason": getattr(stage, "failure_reason", None),
                "artifact_paths": list(getattr(stage, "artifact_paths", []) or []),
            }

        payload["llc"] = {
            "transformer": stage_payload(
                getattr(llc_summary, "transformer", None), "magnetic.llc.transformer"
            ),
            "external_lr": stage_payload(
                getattr(llc_summary, "external_lr", None), "magnetic.llc.external_lr"
            ),
            "recommendations": {
                "transformer_design_id": getattr(contract, "transformer_design_id", getattr(llc_summary, "recommended_transformer_design_id", None)),
                "external_lr_design_id": getattr(contract, "external_lr_design_id", getattr(llc_summary, "recommended_external_lr_design_id", None)),
                "combined_magnetic_design_id": getattr(contract, "combined_magnetic_design_id", getattr(llc_summary, "recommended_combined_magnetic_design_id", None)),
            },
        }
        pf_artifacts = llc_pf_artifact_payload(
            getattr(magnetic, "llc_pf_artifact_contracts", {}) or {}
        )
        payload["llc"]["pf_artifacts"] = pf_artifacts
        payload["llc"]["representatives"] = build_llc_representative_payload(magnetic)
        if contract is not None:
            payload["llc"]["magnetic_contract"] = contract.to_dict()
    return payload


def _capacitor_payload(report: DesignReport) -> dict[str, Any]:
    capacitor = report.capacitor
    if capacitor is None:
        return {"available": False, "input": {}, "output": {}, "llc_resonant": {}, "metadata": {}}

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

    llc_search = getattr(capacitor, "llc_resonant_capacitor_search_result", None)
    llc_request = getattr(llc_search, "request", None) if llc_search is not None else None
    llc_recommended = getattr(llc_search, "recommended_candidate", None) if llc_search is not None else None
    coverage = getattr(llc_search, "coverage_summary", {}) or {}

    def near_miss_payload(candidate: Any) -> dict[str, Any] | None:
        if candidate is None:
            return None
        return {
            "design_id": getattr(candidate, "design_id", None),
            "bank_capacitance": _metric(getattr(candidate, "bank_capacitance_f", None), "F", "capacitor.llc_resonant.near_miss"),
            "capacitance_error": _metric(getattr(candidate, "capacitance_error_percent", None), "%", "capacitor.llc_resonant.near_miss"),
            "rejection_reason": getattr(candidate, "rejection_reason", ""),
        }

    llc_status = "not_evaluated"
    if llc_search is not None and llc_request is not None:
        llc_status = "pass" if llc_recommended is not None else "fail"
    llc_payload = {
        "available": llc_search is not None,
        "status": llc_status,
        "target": _metric(getattr(llc_request, "cr_target_f", None), "F", "capacitor.llc_resonant.request"),
        "constraint": {
            "capacitance_error_limit": _metric(coverage.get("capacitance_error_limit_percent"), "%", "capacitor.llc_resonant.constraint"),
            "capacitance_warning_threshold": _metric(coverage.get("capacitance_warning_percent"), "%", "capacitor.llc_resonant.constraint"),
            "source": coverage.get("capacitance_constraint_source"),
        },
        "counts": {
            "evaluated": _metric(len(getattr(llc_search, "candidates", []) or []) if llc_search is not None else None, "count", "capacitor.llc_resonant.search"),
            "feasible": _metric(len(getattr(llc_search, "feasible_candidates", []) or []) if llc_search is not None else None, "count", "capacitor.llc_resonant.search"),
            "pareto": _metric(len(getattr(llc_search, "pareto_candidates", []) or []) if llc_search is not None else None, "count", "capacitor.llc_resonant.search"),
            "chosen": _metric(len(getattr(llc_search, "chosen_candidates", []) or []) if llc_search is not None else None, "count", "capacitor.llc_resonant.search"),
        },
        "recommended": {
            "design_id": getattr(llc_recommended, "design_id", None),
            "part_number": getattr(llc_recommended, "part_number", None),
            "bank_capacitance": _metric(getattr(llc_recommended, "bank_capacitance_f", None), "F", "capacitor.llc_resonant.recommended"),
            "capacitance_error": _metric(getattr(llc_recommended, "capacitance_error_percent", None), "%", "capacitor.llc_resonant.recommended"),
        },
        "rejection_counts": dict(getattr(llc_search, "rejection_counts", {}) or {}),
        "near_miss": {
            "closest_absolute_error": near_miss_payload(getattr(llc_search, "closest_absolute_error_bank", None)),
            "lowest_loss": near_miss_payload(getattr(llc_search, "lowest_loss_near_miss", None)),
            "lowest_volume": near_miss_payload(getattr(llc_search, "lowest_volume_near_miss", None)),
        },
        "artifact_paths": {
            key: value
            for key, value in {
                "feasible_csv": getattr(llc_search, "feasible_csv_path", ""),
                "near_miss_csv": getattr(llc_search, "near_miss_csv_path", ""),
                "pareto_csv": getattr(llc_search, "pareto_csv_path", ""),
                "chosen_csv": getattr(llc_search, "chosen_csv_path", ""),
                "pareto_png": getattr(llc_search, "pareto_png_path", ""),
            }.items()
            if value
        },
        "warnings": list(getattr(llc_search, "warnings", []) or []),
    }

    return {
        "available": True,
        "input": side_payload(getattr(capacitor, "input_selection", None), "capacitor.input_selection"),
        "output": side_payload(getattr(capacitor, "output_selection", None), "capacitor.output_selection"),
        "llc_resonant": llc_payload,
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
        component_entries = getattr(thermal, "llc_component_estimates", {}) or {}
        payload["llc_components"] = {
            str(role): {
                "status": str(values.get("status", "not_evaluated")),
                "design_id": values.get("design_id"),
                "assembly_type": values.get("assembly_type", role),
                "ambient_temperature": _metric(values.get("ambient_c"), "degC", f"thermal.llc.{role}"),
                "core_loss": _metric(values.get("core_loss_w"), "W", f"thermal.llc.{role}"),
                "copper_loss": _metric(values.get("copper_loss_w"), "W", f"thermal.llc.{role}"),
                "total_loss": _metric(values.get("total_loss_w"), "W", f"thermal.llc.{role}"),
                "hotspot_temperature": _metric(values.get("hotspot_c"), "degC", f"thermal.llc.{role}"),
                "loss_basis": values.get("loss_basis", ""),
                "source": values.get("source", ""),
                "estimate_available": component_entries.get(role) is not None,
            }
            for role, values in components.items()
            if isinstance(values, Mapping)
        }
    return payload


def _loss_payload(report: DesignReport) -> dict[str, Any]:
    loss = report.loss
    if loss is None:
        payload = {"available": False, "recommended_design_id": None, "metrics": {}, "metadata": {}}
        npc_audit = _npc_switching_audit_payload(report)
        if npc_audit:
            payload["npc_switching"] = npc_audit
        return payload
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
    npc_audit = _npc_switching_audit_payload(report)
    if npc_audit:
        payload["npc_switching"] = npc_audit
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


def _npc_switching_audit_payload(report: DesignReport) -> dict[str, Any]:
    """Expose the event-level NPC loss basis without duplicating raw events."""

    if report.spec.topology_id != "three_phase_three_level_npc_inverter" or report.waveform is None:
        return {}
    metadata = report.waveform.metadata if isinstance(report.waveform.metadata, Mapping) else {}
    raw_events = metadata.get("three_phase_npc_switching_events")
    events = [event for event in raw_events if isinstance(event, Mapping)] if isinstance(raw_events, list) else []
    if not events:
        return {"status": "not_available", "event_count": _metric(0, "count", "npc.waveform.events")}

    def numeric_values(key: str) -> list[float]:
        values = []
        for event in events:
            try:
                values.append(float(event[key]))
            except (KeyError, TypeError, ValueError):
                continue
        return values

    currents = numeric_values("signed_current_A")
    voltages = [abs(value) for value in numeric_values("blocking_voltage_V")]
    turn_on = [event for event in events if event.get("event_type") == "turn_on"]
    turn_off = [event for event in events if event.get("event_type") == "turn_off"]
    line_frequency = _npc_report_frequency(metadata, report)
    device = report.device
    losses = {}
    if device is not None:
        losses = device.current_operating_losses or device.design_point_losses or device.evaluated_losses

    def role_payload(role: str) -> dict[str, Any]:
        role_events = [event for event in events if event.get("role") == role]
        loss_result = next(
            (item for item in losses.values() if getattr(item, "role", "") == f"npc_{role}"),
            None,
        )
        return {
            "event_count": _metric(len(role_events), "count", "npc.waveform.events"),
            "turn_on_count": _metric(sum(event.get("event_type") == "turn_on" for event in role_events), "count", "npc.waveform.events"),
            "turn_off_count": _metric(sum(event.get("event_type") == "turn_off" for event in role_events), "count", "npc.waveform.events"),
            "switching_loss_on": _metric(getattr(loss_result, "p_sw_on_W", None), "W", "npc.loss.event_average"),
            "switching_loss_off": _metric(getattr(loss_result, "p_sw_off_W", None), "W", "npc.loss.event_average"),
        }

    payload = {
        "status": "available",
        "event_count": _metric(len(events), "count", "npc.waveform.events"),
        "turn_on_count": _metric(len(turn_on), "count", "npc.waveform.events"),
        "turn_off_count": _metric(len(turn_off), "count", "npc.waveform.events"),
        "soft_turn_on_count": _metric(sum(float(event.get("signed_current_A", 0.0)) < 0.0 for event in turn_on), "count", "npc.loss.event_model"),
        "hard_turn_on_count": _metric(sum(float(event.get("signed_current_A", 0.0)) >= 0.0 for event in turn_on), "count", "npc.loss.event_model"),
        "signed_current_min": _metric(min(currents) if currents else None, "A", "npc.waveform.events"),
        "signed_current_max": _metric(max(currents) if currents else None, "A", "npc.waveform.events"),
        "blocking_voltage_min": _metric(min(voltages) if voltages else None, "V", "npc.waveform.events"),
        "blocking_voltage_max": _metric(max(voltages) if voltages else None, "V", "npc.waveform.events"),
        "line_frequency": _metric(line_frequency, "Hz", "npc.waveform.metadata"),
        "line_period": _metric(1.0 / line_frequency if line_frequency > 0.0 else None, "s", "npc.loss.event_average"),
        "switching_frequency": _metric(metadata.get("fsw_hz"), "Hz", "npc.waveform.metadata"),
        "reverse_recovery_loss": _metric(0.0, "W", "npc.loss.event_model"),
        "formula": "Psw = sum(Eon + Eoff) / Tline; Eon/Eoff use each event's signed current and blocking voltage",
        "roles": {role: role_payload(role) for role in ("outer_switch", "inner_switch", "clamp_diode")},
    }
    return payload


def _npc_report_frequency(metadata: Mapping[str, Any], report: DesignReport) -> float:
    for source in (metadata, report.spec.metadata, report.candidate.metadata if report.candidate is not None else {}):
        try:
            value = float(source.get("f_line_hz", 0.0))
        except (TypeError, ValueError):
            continue
        if value > 0.0:
            return value
    return 0.0


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
                "component_role": getattr(target, "component_role", getattr(geometry, "component_type", "fixed_inductor")),
                "representative_role": getattr(target, "representative_role", None),
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
            "component_roles": sorted({
                getattr(target, "component_role", getattr(geometry, "component_type", "fixed_inductor"))
                for target in geometry.targets
            }),
            "artifact_paths": [str(path) for path in geometry.artifact_paths],
            "summary": geometry.summary,
        },
    }


def _llc_requirements_payload(report: DesignReport) -> dict[str, Any] | None:
    """Expose LLC FHA targets and downstream actual values with explicit sources."""
    magnetic = report.magnetic
    if magnetic is None or getattr(magnetic, "result_type", "") != "separated_llc_transformer":
        return None
    requirements = getattr(magnetic, "design_requirements", {}) or {}
    if not isinstance(requirements, Mapping):
        return None

    def metric(key: str, unit: str, source: str) -> dict[str, Any]:
        return _metric(requirements.get(key), unit, source)

    return {
        "topology_id": requirements.get("topology_id"),
        "display_name": requirements.get("display_name"),
        "design_type": requirements.get("design_type"),
        "control_mode": requirements.get("control_mode"),
        "mode": requirements.get("mode"),
        "bridge_type": requirements.get("primary_bridge_type"),
        "rectifier_type": requirements.get("secondary_rectifier_type"),
        "field_status": dict(requirements.get("field_status") or {}),
        "ranges": {
            "vin": {
                "min": metric("vin_min_v", "V", "candidate.metadata.llc_fha"),
                "nom": metric("vin_nom_v", "V", "candidate.metadata.llc_fha"),
                "max": metric("vin_max_v", "V", "candidate.metadata.llc_fha"),
            },
            "vout": {
                "min": metric("vout_min_v", "V", "candidate.metadata.llc_fha"),
                "nom": metric("vout_nom_v", "V", "candidate.metadata.llc_fha"),
                "max": metric("vout_max_v", "V", "candidate.metadata.llc_fha"),
            },
            "pout": {
                "min": metric("pout_min_w", "W", "candidate.metadata.llc_fha"),
                "max": metric("pout_max_w", "W", "candidate.metadata.llc_fha"),
            },
            "fs": {
                "min": metric("fs_min_hz", "Hz", "candidate.metadata.llc_fha"),
                "nom": metric("fs_nom_hz", "Hz", "candidate.metadata.llc_fha"),
                "max": metric("fs_max_hz", "Hz", "candidate.metadata.llc_fha"),
                "basis": metric("fs_basis_hz", "Hz", "requirements.fs_basis_source"),
            },
        },
        "tank": {
            "lm_target": metric("lm_target_h", "H", "candidate.metadata.llc_fha"),
            "lm_actual": metric("lm_actual_h", "H", "magnetic.llc_magnetic_contract"),
            "lr_target": metric("lr_target_h", "H", "candidate.metadata.llc_fha"),
            "lr_actual": metric("total_lr_actual_h", "H", "magnetic.llc_magnetic_contract"),
            "external_lr_target": metric("external_lr_target_h", "H", "magnetic.llc_magnetic_contract"),
            "external_lr_actual": metric("external_lr_actual_h", "H", "magnetic.llc_magnetic_contract"),
            "cr_target": metric("cr_target_f", "F", "candidate.metadata.llc_fha"),
            "cr_actual": metric("cr_actual_f", "F", "capacitor.llc_resonant.recommended"),
            "cr_error": metric("cr_error_percent", "%", "capacitor.llc_resonant.recommended"),
            "cr_error_limit": metric("cr_error_limit_percent", "%", "capacitor.llc_resonant.constraint"),
        },
        "turns_ratio": {
            "base_np": requirements.get("base_np"),
            "base_ns": requirements.get("base_ns"),
            "recommended_np": requirements.get("recommended_np"),
            "recommended_ns": requirements.get("recommended_ns"),
        },
        "current": {
            "transformer_primary_rms": metric("primary_current_rms_a", "A", "magnetic.transformer.target"),
            "transformer_primary_peak": metric("primary_current_peak_a", "A", "magnetic.transformer.target"),
            "transformer_secondary_rms": metric("secondary_current_rms_a", "A", "magnetic.transformer.target"),
            "transformer_secondary_peak": metric("secondary_current_peak_a", "A", "magnetic.transformer.target"),
            "external_lr_rms": metric("external_lr_current_rms_a", "A", "magnetic.external_lr.target"),
            "external_lr_peak": metric("external_lr_current_peak_a", "A", "magnetic.external_lr.target"),
        },
        "constraints": {
            "b_limit": metric("b_limit_t", "T", "magnetic.transformer.target"),
            "turns_ratio_tolerance": metric("turns_ratio_tolerance_percent", "%", "candidate.metadata.llc_fha"),
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
    payload = {
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
        "efficiency_sweep": _efficiency_sweep_payload(report),
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
    llc_requirements = _llc_requirements_payload(report)
    if llc_requirements is not None:
        payload["llc_design_requirements"] = llc_requirements
    return payload


def _efficiency_sweep_payload(report: DesignReport) -> dict[str, Any]:
    sweep = report.efficiency_sweep
    if sweep is None:
        return {"available": False, "points": [], "pf_points": [], "metadata": {}}
    payload = {
        "available": True,
        "status": sweep.status,
        "metrics": {
            "peak_efficiency": _metric(sweep.peak_efficiency, "ratio", "efficiency_sweep.summary"),
            "full_load_efficiency": _metric(sweep.full_load_efficiency, "ratio", "efficiency_sweep.summary"),
            "light_load_efficiency": _metric(sweep.light_load_efficiency, "ratio", "efficiency_sweep.summary"),
        },
        "points": [
            {
                "load_ratio": _metric(point.load_pu, "p.u.", "efficiency_sweep.input"),
                "output_power": _metric(point.output_power_w, "W", "efficiency_sweep.result"),
                "total_loss": _metric(point.total_loss_w, "W", "efficiency_sweep.result"),
                "semiconductor_loss": _metric(point.semiconductor_loss_w, "W", "efficiency_sweep.result"),
                "efficiency": _metric(point.efficiency, "ratio", "efficiency_sweep.result"),
                "switching_loss_audit": dict(point.switching_loss_audit),
            }
            for point in sweep.points
        ],
        "pf_points": [
            {
                "power_factor": _metric(point.get("power_factor"), "ratio", "efficiency_sweep.pf_input"),
                "semiconductor_loss": _metric(point.get("semiconductor_loss_w"), "W", "efficiency_sweep.pf_result"),
                "efficiency": _metric(point.get("efficiency"), "ratio", "efficiency_sweep.pf_result"),
                "switching_loss_audit": dict(point.get("switching_loss_audit") or {}),
            }
            for point in sweep.pf_sweep_points
        ],
        "metadata": {
            "sweep_basis": dict(sweep.sweep_basis),
            "artifact_paths": {**sweep.artifact_paths, **sweep.pf_sweep_artifact_paths},
            "warnings": list(sweep.warnings),
        },
    }
    return payload


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
