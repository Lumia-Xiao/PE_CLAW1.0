"""Capture the current LLC contract, including complete-array comparisons.

This is diagnostic evidence, not an assertion that ignored Vout or permissive
boundary handling is desired. No full design pipeline is started.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import hashlib
import json
from math import sqrt
from pathlib import Path
import subprocess
import sys
import tkinter as tk
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from pe_claw_gui.app.controllers.run_design_controller import RunDesignController
from pe_claw_gui.app.controllers.waveform_controller import WaveformController
from pe_claw_gui.app.result_views.waveform_view import WaveformView
from pe_claw_gui.app.shell.state_store import AppStateStore
from pe_claw_gui.models.design_report import DesignReport
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.input_schema import build_default_inputs as diode_inputs
from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_synchronous_rectifier.input_schema import build_default_inputs as sr_inputs


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def arrays(value, prefix=""):
    """Include every numeric array, including nested branch/gate metadata."""
    result = {}
    if isinstance(value, dict):
        for key, item in value.items():
            result.update(arrays(item, f"{prefix}.{key}" if prefix else key))
    elif isinstance(value, list) and all(isinstance(x, (int, float)) for x in value):
        result[prefix] = value
    return result


def sample(plugin, candidate, point, reference):
    try:
        waveform = plugin.generate_waveforms(candidate, point)
    except ValueError as exc:
        return {"input": asdict(point) if point else None, "error": str(exc)}, None
    data = arrays(asdict(waveform))
    ref = arrays(asdict(reference)) if reference else data
    assert data.keys() == ref.keys()
    changed = [key for key in data if data[key] != ref[key]]
    details = waveform.metadata["llc_fha_waveforms"]
    current = waveform.inductor_current_a
    return {
        "input": asdict(point) if point else None,
        "actual_vout_v": waveform.operating_vout_v,
        "actual_frequency_hz": 1 / waveform.switching_period_s,
        "actual_load_ratio": waveform.load_ratio,
        "load_resistance_ohm": details["operating_load_resistance_ohm"],
        "actual_power_w": details["pout_op_w"],
        "current_peak_a": max(abs(x) for x in current),
        "current_sample_rms_a": sqrt(sum(x*x for x in current) / len(current)),
        "frequency_feasible": details["operating_point_feasible"],
        "array_count": len(data),
        "total_sample_count": sum(map(len, data.values())),
        "all_arrays_sha256": digest(data),
        "all_arrays_equal_nominal": not changed,
        "changed_arrays": changed,
        "max_abs_delta": {key: max((abs(a-b) for a, b in zip(data[key], ref[key], strict=True)), default=0) for key in changed},
        "notes": waveform.notes,
    }, waveform


def build():
    registry = build_default_registry()
    result = {"source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "scope": "Current characterization; generated default inputs, not user's unsupplied exact case; no selected hardware/loss acceptance", "variants": []}
    root = tk.Tk()
    root.withdraw()
    try:
        for kind, defaults in (("diode", diode_inputs), ("synchronous", sr_inputs)):
            topology = f"llc_resonant_converter_{kind}_rectifier"
            plugin = registry.get_plugin(topology)
            secondaries = ("full_bridge_rectifier", "full_wave_center_tapped_rectifier") if kind == "diode" else ("full_bridge_synchronous_rectifier",)
            for primary in ("full_bridge", "half_bridge"):
                for secondary in secondaries:
                    raw = defaults()
                    raw.update(primary_bridge_type=primary, secondary_rectifier_type=secondary)
                    spec = plugin.build_spec(raw)
                    candidate = plugin.synthesize(spec)
                    snapshot = digest(asdict(candidate))
                    point = OperatingPoint(candidate.vin_nom, 1.0, candidate.vout_target)
                    fha = candidate.metadata["llc_fha"]
                    cases = {"nominal": point, "repeat": point, "legacy_none": None,
                             "vout_low": replace(point, vout_v=36), "vout_high": replace(point, vout_v=60),
                             "vout_none": replace(point, vout_v=None),
                             "vin_min": replace(point, vin_v=candidate.vin_min), "vin_max": replace(point, vin_v=candidate.vin_max),
                             "load_10pct": replace(point, load_ratio=.1), "load_50pct": replace(point, load_ratio=.5),
                             "load_zero": replace(point, load_ratio=0), "load_negative": replace(point, load_ratio=-.1),
                             "load_overload": replace(point, load_ratio=1.5), "vin_zero": replace(point, vin_v=0),
                             "frequency_min": replace(point, switching_frequency_hz=fha["fs_min_hz"]),
                             "frequency_max": replace(point, switching_frequency_hz=fha["fs_max_hz"]),
                             "frequency_below": replace(point, switching_frequency_hz=fha["fs_min_hz"]*.9),
                             "frequency_above": replace(point, switching_frequency_hz=fha["fs_max_hz"]*1.1),
                             "frequency_zero": replace(point, switching_frequency_hz=0)}
                    rows = {}
                    reference = None
                    for name, op in cases.items():
                        rows[name], waveform = sample(plugin, candidate, op, reference)
                        if name == "nominal":
                            reference = waveform
                    assert rows["repeat"]["all_arrays_equal_nominal"]
                    for name in ("vin_min", "vin_max", "load_10pct", "load_50pct", "frequency_min", "frequency_max"):
                        assert not rows[name]["all_arrays_equal_nominal"], name
                    assert snapshot == digest(asdict(candidate))

                    form = registry.get_form_class(topology)(root)
                    for key, value in raw.items():
                        if key in form.design_vars:
                            form.design_vars[key].set(value)
                    gui_raw = form.get_raw_input()
                    state = AppStateStore(registry=registry, selected_topology_id=topology, active_plugin=plugin,
                                          last_raw_input=gui_raw, design_report=DesignReport(spec=spec, candidate=candidate))
                    controller = WaveformController(state)
                    figure = Figure(figsize=(9, 7))
                    view = SimpleNamespace(figure=figure, canvas=FigureCanvasAgg(figure))
                    gui_rows = []
                    for vin, vout, load in ((400, 36, 1), (400, 60, 1), (360, 48, .5), (420, 48, .1)):
                        for key, value in (("vin_v", vin), ("vout_v", vout), ("load_ratio", load)):
                            if key in form.operating_vars:
                                form.operating_vars[key].set(str(value))
                        assert form.get_raw_input() == gui_raw
                        assert RunDesignController(state).ensure_active_topology_current(gui_raw) is state.design_report
                        op = form.get_operating_point()
                        previous_device = state.design_report.device
                        report = controller.generate_waveforms(op)
                        changed_fields = [key for key, value in asdict(report.candidate).items()
                                          if asdict(candidate)[key] != value]
                        # SR selection can enrich audit metadata without redesigning
                        # the resonant tank; capture that separately from hardware.
                        assert set(changed_fields) <= {"metadata", "notes"}
                        assert report.candidate.metadata["llc_fha"] == candidate.metadata["llc_fha"]
                        selected = dict(report.device.selected_devices) if report.device else {}
                        if previous_device is not None:
                            assert selected == previous_device.selected_devices
                        assert report.operating_point == op
                        assert report.waveform == plugin.generate_waveforms(candidate, op)
                        WaveformView.render(view, report)
                        expected = (report.waveform.switch_node_voltage_v, report.waveform.inductor_current_a,
                                    report.waveform.capacitor_current_a, report.waveform.output_voltage_v)
                        assert len(figure.axes) == 4
                        for axis, series in zip(figure.axes, expected, strict=True):
                            assert len(axis.lines) == 1
                            assert list(axis.lines[0].get_ydata()) == series
                        gui_rows.append({"input": asdict(op), "all_arrays_sha256": digest(arrays(asdict(report.waveform))),
                                         "plot_matches_current_waveform": True, "electrical_candidate_preserved": True,
                                         "changed_candidate_fields": changed_fields,
                                         "device_populated_from_empty_report": previous_device is None and report.device is not None,
                                         "selected_devices": selected,
                                         "title": figure._suptitle.get_text()})
                    form.destroy()
                    assert snapshot == digest(asdict(candidate))
                    result["variants"].append({"topology": topology, "primary": primary, "secondary": secondary,
                        "raw_design_input": raw, "candidate_sha256": snapshot, "form_class": registry.get_form_class(topology).__name__,
                        "nominal_load_resistance_ohm": fha["rout_nom_ohm"], "frequency_range_hz": [fha["fs_min_hz"], fha["fs_max_hz"]],
                        "cases": rows, "gui_chain": gui_rows})
                    print(f"PASS {kind}/{primary}/{secondary}: {len(rows)} cases, {len(gui_rows)} GUI-chain checks", flush=True)
    finally:
        root.destroy()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    evidence = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Evidence: {args.output}")
