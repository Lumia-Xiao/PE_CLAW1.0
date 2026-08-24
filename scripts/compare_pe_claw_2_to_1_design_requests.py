"""Replay PE-Claw 2.0 design-request cases through the PE-Claw 1.0 runtime.

The comparison deliberately separates input parity, topology-level electrical
parity, and downstream library-selected hardware.  The latter is reported but
is not used as a migration verdict because the two projects may carry
different component-library snapshots and ranking policies.
"""

from __future__ import annotations

import argparse
import csv
import importlib
import json
import math
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


TOPOLOGY_DIR_RE = re.compile(r"^(0[1-9]|1[0-7])_")
TABLE_ROW_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$")
NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?")


@dataclass(frozen=True)
class CaseRecord:
    matrix_id: str
    case_id: str
    topology_id: str
    source_request: str
    source_result: str
    target_input: dict[str, str]
    status: str
    reason: str = ""
    compared_fields: int = 0
    matched_fields: int = 0
    core_compared_fields: int = 0
    core_matched_fields: int = 0
    max_relative_error: float | None = None
    verdict: str = ""
    fields: tuple[dict[str, Any], ...] = ()


def _scalar(value: str) -> Any:
    value = value.strip()
    if not value or value.lower() in {"null", "none", "-"}:
        return None
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    value = re.sub(r"\s+(?:V|A|W|Hz|kHz|H|F|T|deg|p\.u\.|%)\s*(?:pp)?\s*$", "", value)
    match = NUMBER_RE.search(value.replace(",", ""))
    if match and match.group(0) == value.strip():
        try:
            return float(value)
        except ValueError:
            pass
    return value


def _parse_front_matter(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"Missing request front matter: {path}")
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(0, root)]
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, separator, raw_value = line.strip().partition(":")
        if not separator:
            continue
        while stack[-1][0] >= indent and len(stack) > 1:
            stack.pop()
        parent = stack[-1][1]
        if not raw_value.strip():
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _scalar(raw_value)
    return root


def _table_values(path: Path) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = TABLE_ROW_RE.match(line.strip())
        if match:
            key, raw_value = match.groups()
            if key.lower() not in {"field", "artifact", "term", "component", "role", "load_pu"}:
                values[key.strip()] = _scalar(raw_value)
    return values


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = NUMBER_RE.search(str(value).replace(",", ""))
    return float(match.group(0)) if match else None


def _value(values: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in values:
            return values[key]
    return None


def _target_module(registry: Any, topology_id: str) -> tuple[Any, Any]:
    plugin = registry.get_plugin(topology_id)
    return plugin, importlib.import_module(plugin.__module__)


def _base_dc_dc(request: dict[str, Any]) -> dict[str, str]:
    inp = request["input"]
    out = request["output"]
    power = request["power"]
    switching = request["switching"]
    rectifier = request.get("rectifier", {})
    modulation = request.get("modulation", {})
    return {
        "vin_min": str(inp.get("voltage_min_v")),
        "vin_max": str(inp.get("voltage_max_v")),
        "vout": str(out.get("voltage_v")),
        "pout": str(power.get("output_power_w")),
        "fs_khz": str(float(switching.get("frequency_hz")) / 1000.0),
        "ripple_current_ratio": str(rectifier.get("inductor_current_ripple_ratio") or 0.3),
        "ripple_voltage_ratio_percent": str(request.get("dc_bus", {}).get("ripple_voltage_ratio_percent") or 1.0),
    }


def _map_dc_dc(topology_id: str, request: dict[str, Any]) -> dict[str, str]:
    raw = _base_dc_dc(request)
    modulation = request.get("modulation", {})
    rectifier = request.get("rectifier", {})
    constraints = request.get("constraints", {})
    if topology_id == "flyback_diode_rectified_isolated":
        raw.update({
            "target_duty": str(constraints.get("target_duty", 0.42)),
            "turns_ratio_ns_np": str(constraints.get("turns_ratio_ns_np", "auto")),
            "rectifier_diode_drop_v": str(constraints.get("rectifier_diode_drop_v", rectifier.get("diode_forward_drop_v", 1.5))),
            "clamp_spike_margin_v": str(constraints.get("clamp_spike_margin_v", 50)),
            "efficiency_estimate": str(constraints.get("efficiency_estimate", 0.90)),
            "flyback_mode": str(constraints.get("flyback_mode", modulation.get("conduction_mode", "ccm"))),
        })
    elif topology_id == "phase_shifted_full_bridge_diode_rectifier_isolated":
        psfb = request.get("psfb", {})
        raw.update({
            "vin_nom": str(request["input"].get("voltage_nominal_v")),
            "max_effective_duty": str(psfb.get("max_effective_duty", 0.78)),
            "max_command_duty": str(psfb.get("max_command_duty", 0.90)),
            "deadtime_ns": str(psfb.get("deadtime_ns", 150)),
            "zvs_load_ratio_min": str(psfb.get("zvs_load_ratio_min", 0.50)),
            "target_bmax_t": str(psfb.get("target_bmax_t", 0.18)),
            "turns_ratio_np_ns": str(psfb.get("turns_ratio_np_ns", "auto")),
            "leakage_inductance_target_uh": str(float(psfb.get("leakage_inductance_target_h", 10e-6)) * 1e6),
            "magnetizing_inductance_uh": str(float(psfb.get("magnetizing_inductance_h", 600e-6)) * 1e6),
            "rectifier_diode_drop_v": str(psfb.get("rectifier_diode_drop_v", 1.2)),
            "primary_switch_eoss_uj": str(psfb.get("primary_switch_eoss_uj", 30)),
            "primary_switch_qoss_nc": str(psfb.get("primary_switch_qoss_nc", 100)),
            "secondary_rectifier_type": str(psfb.get("secondary_rectifier_type", "full_bridge_diode")),
        })
    elif topology_id == "llc_resonant_converter_diode_rectifier":
        # LLC c02-c06 are operating-point replays.  PE-Claw 2.0 stores the
        # frozen c01 hardware snapshot in constraints, while the 1.0 schema
        # requires every member of that snapshot to be present in raw_input.
        fixed_hardware_keys = (
            "resonant_inductance_h",
            "magnetizing_inductance_h",
            "resonant_capacitance_f",
            "output_capacitance_f",
            "output_capacitor_esr_ohm",
            "transformer_primary_turns",
            "transformer_secondary_turns",
            "load_resistance_ohm",
        )
        raw = {
            "vin_min": str(request["input"].get("voltage_min_v")),
            "vin_nom": str(request["input"].get("voltage_nominal_v")),
            "vin_max": str(request["input"].get("voltage_max_v")),
            "vout_min": str(request["output"].get("voltage_min_v")),
            "vout_nom": str(request["output"].get("voltage_v")),
            "vout_max": str(request["output"].get("voltage_max_v")),
            "pout_max": str(request["power"].get("output_power_w")),
            "min_load_ratio": str(constraints.get("min_load_ratio") or 0.1),
            "fs_min_hz": str(request["switching"].get("frequency_min_hz")),
            "fs_max_hz": str(request["switching"].get("frequency_max_hz")),
            "commanded_switching_frequency_hz": str(request["switching"].get("frequency_hz")),
            "ripple_voltage_ratio_percent": str(request.get("dc_bus", {}).get("ripple_voltage_ratio_percent") or 1.0),
            "primary_bridge_type": str(constraints.get("primary_bridge_type", "full_bridge")),
            "secondary_rectifier_type": str(constraints.get("secondary_rectifier_type", "full_bridge_rectifier")),
            "hardware_reuse_mode": str(constraints.get("hardware_reuse_mode", "new_design")),
            "hardware_design_case_id": str(constraints.get("hardware_design_case_id") or ""),
            "load_ratio": str(constraints.get("load_ratio") or 1.0),
            "load_ratio_source": str(constraints.get("load_ratio_source") or "source_request"),
        }
        for key in fixed_hardware_keys:
            if constraints.get(key) not in (None, ""):
                raw[key] = str(constraints[key])
    return raw


def _map_ac_dc(topology_id: str, request: dict[str, Any]) -> dict[str, str]:
    inp = request["input"]
    out = request["output"]
    power = request["power"]
    switching = request["switching"]
    rectifier = request.get("rectifier", {})
    dc_bus = request.get("dc_bus", {})
    output_voltage = out.get("voltage_v") or dc_bus.get("voltage_nominal_v")
    source_ripple_percent = dc_bus.get("ripple_voltage_ratio_percent")
    # The PE-Claw 2.0 request contract names this value in percent.  The
    # passive AC-DC 1.0 schemas consume a unit ratio (0.05 for 5 percent).
    ripple_ratio = float(source_ripple_percent or 5.0) / 100.0
    raw: dict[str, str]
    if topology_id == "single_phase_diode_bridge_rectifier_capacitor_filter":
        raw = {
            "vac_rms": str(inp.get("voltage_rms_v")), "f_line_hz": str(inp.get("frequency_hz")),
            "vout_v": str(output_voltage), "pout_w": str(power.get("output_power_w")),
            "ripple_ratio": str(ripple_ratio),
            "diode_forward_drop_v": str(rectifier.get("diode_forward_drop_v", 1.0)),
            "diode_voltage_margin": str(rectifier.get("diode_voltage_margin_v", 2.0)),
            "source_resistance_ohm": str(rectifier.get("source_resistance_ohm", 0.1)),
        }
    elif topology_id == "single_phase_diode_bridge_rectifier_dc_inductor_filter":
        raw = {
            "vac_rms": str(inp.get("voltage_rms_v")), "f_line_hz": str(inp.get("frequency_hz")),
            "vout_v": str(output_voltage), "pout_w": str(power.get("output_power_w")),
            "ripple_ratio": str(ripple_ratio),
            "dc_reactor_inductance_mh": str(rectifier.get("dc_reactor_inductance_mh") or 2.0),
            "dc_reactor_max_inductance_mh": str(rectifier.get("dc_reactor_max_inductance_mh") or 5.0),
            # This legacy 1.0 field is entered as percent by the 1.0 parser.
            "inductor_current_ripple_ratio": str(float(rectifier.get("inductor_current_ripple_ratio") or 100.0) * 100.0),
            "ccm_margin": str(rectifier.get("ccm_margin") or 1.5),
            "diode_forward_drop_v": str(rectifier.get("diode_forward_drop_v", 1.0)),
            "diode_voltage_margin": str(rectifier.get("diode_voltage_margin_v", 2.0)),
            "source_resistance_ohm": str(rectifier.get("source_resistance_ohm", 0.1)),
        }
    elif topology_id == "three_phase_diode_bridge_rectifier_capacitor_filter":
        raw = {
            "vll_rms": str(inp.get("voltage_line_line_rms_v")), "f_line_hz": str(inp.get("frequency_hz")),
            "vout_v": str(output_voltage), "pout_w": str(power.get("output_power_w")),
            "dc_link_ripple_ratio": str(ripple_ratio),
            "diode_forward_drop_v": str(rectifier.get("diode_forward_drop_v", 1.0)),
            "diode_voltage_margin": str(rectifier.get("diode_voltage_margin_v", 2.0)),
            "source_resistance_ohm": str(rectifier.get("source_resistance_ohm", 0.05)),
        }
    else:
        pfc = request.get("pfc", {})
        raw = {
            "vac_rms": str(inp.get("voltage_rms_v")), "vac_rms_min": str(inp.get("voltage_min_v")),
            "vac_rms_max": str(inp.get("voltage_max_v")), "f_line_hz": str(inp.get("frequency_hz")),
            "vdc_target_v": str(out.get("voltage_v")), "pout_w": str(power.get("output_power_w")),
            "fsw_hz": str(switching.get("frequency_hz")),
            "dc_bus_ripple_percent": str(request.get("dc_bus", {}).get("ripple_voltage_ratio_percent") or 5.0),
            "inductor_current_ripple_ratio": str(pfc.get("inductor_current_ripple_ratio") or rectifier.get("inductor_current_ripple_ratio") or 0.3),
            "power_factor_target": str(pfc.get("power_factor_target") or request.get("ac_source", {}).get("power_factor") or 0.99),
            "sizing_efficiency_assumption": "0.98" if topology_id == "single_phase_totem_pole_bridgeless_pfc" else "0.95",
        }
        if topology_id == "single_phase_boost_pfc_diode_bridge":
            raw["input_inductance_h"] = str(pfc.get("input_inductance_h") or 0.0001)
    return raw


def _map_dc_ac(topology_id: str, request: dict[str, Any]) -> dict[str, str]:
    inp = request["input"]
    out = request["output"]
    power = request["power"]
    switching = request["switching"]
    modulation = request.get("modulation", {})
    return {
        "vdc_nom": str(inp.get("voltage_nominal_v")),
        "vac_rms": str(out.get("voltage_rms_v")),
        "vac_ll_rms": str(out.get("voltage_line_line_rms_v")),
        "f_line_hz": str(out.get("frequency_hz")),
        "fsw_hz": str(switching.get("frequency_hz")),
        "pout_w": str(power.get("output_power_w")),
        "power_factor": str(request.get("ac_source", {}).get("power_factor") or 1.0),
        "inductor_current_ripple_ratio": str(request.get("rectifier", {}).get("inductor_current_ripple_ratio") or 0.2),
        "dc_link_voltage_ripple_ratio": str(float(request.get("dc_bus", {}).get("ripple_voltage_ratio_percent") or 5.0) / 100.0),
        "conduction_mode": str(modulation.get("conduction_mode") or "ccm"),
    }


def map_request(topology_id: str, request: dict[str, Any]) -> dict[str, str]:
    if topology_id in {
        "buck_diode_rectified_unidirectional", "buck_synchronous_rectified_unidirectional",
        "boost_diode_rectified_unidirectional", "boost_synchronous_rectified_unidirectional",
        "buck_boost_diode_rectified_unidirectional", "flyback_diode_rectified_isolated",
        "phase_shifted_full_bridge_diode_rectifier_isolated", "llc_resonant_converter_diode_rectifier",
    }:
        return _map_dc_dc(topology_id, request)
    if topology_id.startswith("single_phase_") and "inverter" in topology_id or topology_id.startswith("three_phase_") and "inverter" in topology_id:
        return _map_dc_ac(topology_id, request)
    return _map_ac_dc(topology_id, request)


def _target_values(report: Any) -> dict[str, Any]:
    candidate = report.candidate
    waveform = report.waveform
    stress = report.stress
    if candidate is None:
        return {}
    values: dict[str, Any] = {
        "Topology ID": candidate.topology_id,
        "Input Voltage Min": candidate.vin_min,
        "Input Voltage Max": candidate.vin_max,
        "Output Voltage": candidate.vout_target,
        "Output Power": candidate.pout_target,
        "Switching Frequency": candidate.fs_hz,
        "Duty": candidate.duty_nom,
        "Output Current": candidate.iout,
        "Inductance": candidate.inductance_h,
        "Output Capacitance": candidate.capacitance_f,
        "Inductor Ripple": candidate.delta_il,
        "Output Ripple": candidate.delta_vo,
        "Inductor Peak Current": candidate.il_peak,
        "Inductor Valley Current": candidate.il_valley,
        "CCM Valid": candidate.ccm_valid,
        "Feasible": candidate.feasible,
    }
    if waveform is not None:
        values.update({
            "Operating Input Voltage": waveform.operating_vin_v,
            "Operating Output Voltage": waveform.operating_vout_v,
            "Load Ratio": waveform.load_ratio,
            "Waveform Duty": waveform.duty,
        })
    if stress is not None:
        values.update({
            "Switch Voltage Max": stress.switch.voltage_max_v,
            "Switch Current Peak": stress.switch.current_peak_a,
            "Rectifier Voltage Max": stress.rectifier.voltage_max_v,
            "Rectifier Current Peak": stress.rectifier.current_peak_a,
        })
    for key, value in candidate.metadata.items():
        if isinstance(value, (str, int, float, bool)):
            values[f"metadata.{key}"] = value
    return values


def _source_values(path: Path) -> dict[str, Any]:
    values = _table_values(path)
    if "Switching Frequency" in values:
        frequency = _number(values["Switching Frequency"])
        if frequency is not None and "kHz" in str(values["Switching Frequency"]):
            values["Switching Frequency"] = frequency * 1000.0
    return values


def _compare_field(name: str, source: Any, target: Any, abs_tol: float, rel_tol: float, basis: str) -> dict[str, Any]:
    source_number = _number(source)
    target_number = _number(target)
    if isinstance(source, bool) or isinstance(target, bool) or isinstance(source, str) or isinstance(target, str):
        matched = str(source).strip().casefold() == str(target).strip().casefold()
        return {"field": name, "source": source, "target": target, "matched": matched, "relative_error": None, "basis": basis}
    if source_number is None or target_number is None:
        return {"field": name, "source": source, "target": target, "matched": source == target, "relative_error": None, "basis": basis}
    denominator = max(abs(source_number), abs_tol)
    relative_error = abs(target_number - source_number) / denominator
    matched = abs(target_number - source_number) <= max(abs_tol, rel_tol * abs(source_number))
    return {"field": name, "source": source_number, "target": target_number, "matched": matched, "relative_error": relative_error, "basis": basis}


def _field_pairs(topology_id: str, source: dict[str, Any], target: dict[str, Any]) -> list[tuple[str, Any, Any, float, float, str]]:
    # Keep the strict field set visible, but label quantities whose definition
    # changed between 2.0 and 1.0 as model-boundary evidence.  A library
    # selection or waveform-model delta must not be confused with topology
    # registration/input migration failure.
    fields = [
        "Duty", "Output Current", "Inductance", "Output Capacitance", "Inductor Ripple",
        "Output Ripple", "Inductor Peak Current", "Inductor Valley Current", "CCM Valid", "Feasible",
        "Switch Voltage Max", "Switch Current Peak", "Rectifier Voltage Max", "Rectifier Current Peak",
    ]
    boundary_fields: set[str] = set()
    if topology_id == "flyback_diode_rectified_isolated":
        boundary_fields.update({"Output Capacitance"})
    elif topology_id == "phase_shifted_full_bridge_diode_rectifier_isolated":
        boundary_fields.update({"Output Capacitance", "Inductor Ripple"})
    elif topology_id in {
        "single_phase_diode_bridge_rectifier_capacitor_filter",
        "single_phase_diode_bridge_rectifier_dc_inductor_filter",
        "three_phase_diode_bridge_rectifier_capacitor_filter",
    }:
        boundary_fields.update({"Output Current", "Output Capacitance", "Output Ripple", "Inductor Peak Current", "Inductor Valley Current"})
        if topology_id == "single_phase_diode_bridge_rectifier_dc_inductor_filter":
            boundary_fields.add("Inductor Ripple")
    elif topology_id in {
        "single_phase_boost_pfc_diode_bridge",
        "single_phase_totem_pole_bridgeless_pfc",
    }:
        boundary_fields.update({"Inductance", "Inductor Ripple", "Output Ripple", "Inductor Peak Current", "Inductor Valley Current"})
    pairs: list[tuple[str, Any, Any, float, float, str]] = []
    for name in fields:
        if name in source and name in target:
            pairs.append((name, source[name], target[name], 1e-9, 0.05, "model_boundary" if name in boundary_fields else "core"))
    return pairs


def run_case(registry: Any, source_root: Path, case_dir: Path, topology_id: str) -> CaseRecord:
    request_path = case_dir / "design_request.md"
    result_path = case_dir / "design_result.md"
    request = _parse_front_matter(request_path)
    target_input = map_request(topology_id, request)
    try:
        plugin, _module = _target_module(registry, topology_id)
        from pe_claw_gui.pipeline.options import PipelineOptions
        from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline

        report = run_full_pipeline(
            plugin=plugin,
            raw_input=target_input,
            include_waveforms=True,
            pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
        )
        source = _source_values(result_path)
        target = _target_values(report)
        fields = tuple(_compare_field(name, left, right, abs_tol, rel_tol, basis) for name, left, right, abs_tol, rel_tol, basis in _field_pairs(topology_id, source, target))
        max_error = max((field["relative_error"] for field in fields if field["relative_error"] is not None), default=None)
        matched = sum(1 for field in fields if field["matched"])
        compared = len(fields)
        core_fields = [field for field in fields if field["basis"] == "core"]
        core_matched = sum(1 for field in core_fields if field["matched"])
        if compared and matched == compared:
            verdict = "pass"
        elif core_fields and core_matched == len(core_fields):
            verdict = "pass_with_model_boundary"
        else:
            verdict = "mismatch"
        source_topology = str(source.get("Topology ID", ""))
        if source_topology and source_topology != topology_id:
            verdict = "input_or_topology_mismatch"
        return CaseRecord(
            matrix_id=case_dir.parent.name,
            case_id=case_dir.name,
            topology_id=topology_id,
            source_request=str(request_path), source_result=str(result_path), target_input=target_input,
            status="executed", compared_fields=compared, matched_fields=matched,
            core_compared_fields=len(core_fields), core_matched_fields=core_matched,
            max_relative_error=max_error, verdict=verdict, fields=fields,
        )
    except Exception as exc:  # noqa: BLE001 - preserve per-case failure evidence
        return CaseRecord(
            matrix_id=case_dir.parent.name, case_id=case_dir.name, topology_id=topology_id,
            source_request=str(request_path), source_result=str(result_path), target_input=target_input,
            status="failed", reason=f"{type(exc).__name__}: {exc}", verdict="execution_error",
        )


def _write_outputs(records: list[CaseRecord], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {"contract_version": "pe_claw_2_to_1_design_parity_v1", "records": [asdict(record) for record in records]}
    (output_dir / "comparison.json").write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    with (output_dir / "comparison.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["matrix_id", "case_id", "topology_id", "status", "verdict", "compared_fields", "matched_fields", "core_compared_fields", "core_matched_fields", "max_relative_error", "reason"])
        writer.writeheader()
        for record in records:
            writer.writerow({field: getattr(record, field) for field in writer.fieldnames})
    lines = [
        "# PE-Claw 2.0 to 1.0 Design Parity",
        "",
        "This report replays frozen PE-Claw 2.0 design requests through the PE-Claw 1.0 deterministic topology pipeline.",
        "",
        "| Matrix | Case | Topology | Status | Compared | Matched | Core | Max relative error | Verdict |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for record in records:
        error = "-" if record.max_relative_error is None else f"{record.max_relative_error:.4g}"
        lines.append(f"| {record.matrix_id} | {record.case_id} | `{record.topology_id}` | {record.status} | {record.compared_fields} | {record.matched_fields} | {record.core_matched_fields}/{record.core_compared_fields} | {error} | **{record.verdict}** |")
    lines.extend(["", "## Interpretation", "", "Numeric fields use a 5% relative tolerance. `pass` means every compared field matched. `pass_with_model_boundary` means all core topology/input fields matched, while only explicitly labeled model-boundary fields differ. Device part numbers, magnetic geometry IDs, and capacitor part numbers are not migration verdict fields because library snapshots and ranking policies are not guaranteed identical."])
    (output_dir / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary_lines = [
        "# PE-Claw 2.0 to 1.0 Topology Summary",
        "",
        "| Matrix | Cases | Executed | Pass | Model boundary | Mismatch | Core fields |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for matrix_id in sorted({record.matrix_id for record in records}):
        group = [record for record in records if record.matrix_id == matrix_id]
        summary_lines.append(
            f"| {matrix_id} | {len(group)} | {sum(record.status == 'executed' for record in group)} | "
            f"{sum(record.verdict == 'pass' for record in group)} | "
            f"{sum(record.verdict == 'pass_with_model_boundary' for record in group)} | "
            f"{sum(record.verdict == 'mismatch' for record in group)} | "
            f"{sum(record.core_matched_fields for record in group)}/{sum(record.core_compared_fields for record in group)} |"
        )
    (output_dir / "topology_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    target_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(target_root / "src"))
    from pe_claw_gui.topologies.base.registry import build_default_registry

    registry = build_default_registry()
    records: list[CaseRecord] = []
    request_root = args.source_root / "design_requests"
    for matrix_dir in sorted(path for path in request_root.iterdir() if path.is_dir() and TOPOLOGY_DIR_RE.match(path.name)):
        for case_dir in sorted(path for path in matrix_dir.iterdir() if path.is_dir()):
            request = _parse_front_matter(case_dir / "design_request.md")
            topology_id = str(request.get("topology_hint"))
            records.append(run_case(registry, args.source_root, case_dir, topology_id))
    _write_outputs(records, args.output_dir)
    summary: dict[str, int] = {}
    for record in records:
        summary[record.verdict] = summary.get(record.verdict, 0) + 1
    print(json.dumps({"cases": len(records), "verdicts": summary, "output_dir": str(args.output_dir)}, indent=2))
    return 0 if not any(record.status == "failed" for record in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
