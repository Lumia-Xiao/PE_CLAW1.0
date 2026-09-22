"""Exercise real LLC Run Design/Generate Waveforms buttons and Tk result views.

Requires a graphical Tk session. Physics and device selection are real; only
output location and modal error display are intercepted. No mouse-click or
user-project acceptance is implied by this programmatic widget check.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from math import isclose
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from scripts.build_llc_waveform_operating_point_baseline import arrays, digest
from pe_claw_gui.app.controllers import run_design_controller
from pe_claw_gui.app.result_views.loss_view import build_system_loss_summary
from pe_claw_gui.app.result_views.stress_view import build_stress_summary_lines
from pe_claw_gui.app.shell.main_window import PEClawMainWindow
from pe_claw_gui.reports.structured_output import build_structured_report


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def edit_operating(form, key, value):
    entry = next(w for w in descendants(form)
                 if w.winfo_class() == "TEntry"
                 and str(w.cget("textvariable")) == str(form.operating_vars[key]))
    entry.delete(0, "end")
    entry.insert(0, str(value))


def contained(widget, parent):
    x = widget.winfo_rootx() - parent.winfo_rootx()
    y = widget.winfo_rooty() - parent.winfo_rooty()
    return (0 <= x and 0 <= y
            and x + widget.winfo_width() <= parent.winfo_width()
            and y + widget.winfo_height() <= parent.winfo_height())


def verify(output_root, baseline_path):
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    result = {
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "method": "Real MainWindow, ttk.Entry edits, ttk.Button.invoke, FigureCanvasTkAgg; real design/device/refresh pipelines",
        "limits": "Default reconstructed designs; no manual mouse acceptance or supplied user project. Magnetic/capacitor design stages not run here; their existing LLC tests run separately.",
        "variants": [],
    }
    app = PEClawMainWindow()
    callback_errors = []
    app.report_callback_exception = lambda *args: callback_errors.append(str(args[1]))
    errors = []
    pipeline = run_design_controller.run_full_pipeline

    def isolated_pipeline(**kwargs):
        return pipeline(**kwargs, output_root=output_root)

    try:
        with patch.object(run_design_controller, "run_full_pipeline", side_effect=isolated_pipeline) as design_calls, \
             patch("pe_claw_gui.app.shell.main_window.messagebox.showerror", side_effect=lambda *a: errors.append(a)), \
             patch("pe_claw_gui.app.shell.main_window.messagebox.showwarning", side_effect=lambda *a: errors.append(a)):
            for index, variant in enumerate(baseline["variants"]):
                app._on_topology_selected(variant["topology"])
                form = app.workspace.active_form
                for key, value in variant["raw_design_input"].items():
                    if key in form.design_vars:
                        form.design_vars[key].set(value)
                app.update()
                assert set(form.operating_vars) == {"vin_v", "vout_v", "load_ratio"}
                assert all(w.winfo_class() != "TEntry" for w in descendants(form)
                           if "textvariable" in w.keys()
                           and str(w.cget("textvariable")) in map(str, form.waveform_readback_vars.values()))
                layout = []
                for size in ("1400x860", "1240x760"):
                    app.geometry(size)
                    app.update()
                    canvas = app.workspace.form_canvas
                    canvas.yview_moveto(1)
                    app.update()
                    assert contained(form.generate_waveforms_button, canvas), size
                    assert contained(canvas, app), size
                    layout.append({"window": size, "scroll_fraction": list(canvas.yview()), "generate_button_reachable": True})
                app.geometry("1400x860")
                app.workspace.form_canvas.yview_moveto(0)
                app.update()
                assert contained(form.run_design_button, app.workspace.form_canvas)
                form.run_design_button.invoke()
                app.update()
                assert not errors, errors
                initial = app.state_store.design_report
                assert initial.device.selected_devices
                selected = dict(initial.device.selected_devices)
                candidate_digest = digest(asdict(initial.candidate))
                app.workspace.form_canvas.yview_moveto(1)
                app.update()
                rows = []
                points = [("nominal", 400, 48, 1), ("repeat", 400, 48, 1), ("vin_min", 360, 48, 1),
                          ("vin_max", 420, 48, 1), ("load_50pct", 400, 48, .5), ("load_10pct", 400, 48, .1),
                          ("vout_low", 400, 46, 1), ("vout_high", 400, 50, 1),
                          ("load_overload", 400, 48, 1.5), ("return_nominal", 400, 48, 1)]
                for name, vin, target, load in points:
                    edit_operating(form, "vin_v", vin)
                    edit_operating(form, "vout_v", target)
                    edit_operating(form, "load_ratio", load)
                    assert all(v.get() == "-" for v in form.waveform_readback_vars.values())
                    form.generate_waveforms_button.invoke()
                    app.update()
                    assert not errors and not callback_errors, (errors, callback_errors)
                    report = app.state_store.design_report
                    waveform = report.waveform
                    assert report.candidate is initial.candidate
                    assert digest(asdict(report.candidate)) == candidate_digest
                    assert report.device.selected_devices == selected
                    assert report.device.design_point_losses == initial.device.design_point_losses
                    assert report.magnetic is initial.magnetic and report.capacitor is initial.capacitor
                    assert design_calls.call_count == index + 1
                    assert report.operating_point == form.get_operating_point()
                    array_digest = digest(arrays(asdict(waveform)))
                    reference = app.state_store.active_plugin.generate_waveforms(initial.candidate, report.operating_point)
                    assert arrays(asdict(waveform)) == arrays(asdict(reference)), name
                    assert isclose(waveform.operating_vout_v, target, rel_tol=1e-8)
                    assert isclose(float(form.waveform_readback_vars["vout_v"].get()), waveform.operating_vout_v, rel_tol=1e-3)
                    assert isclose(float(form.waveform_readback_vars["switching_frequency_hz"].get()), 1e-3 / waveform.switching_period_s, rel_tol=1e-5)
                    figure = app.workspace.waveform_view.figure
                    assert app.workspace.results_notebook.select() == str(app.workspace.waveform_view)
                    series = (waveform.switch_node_voltage_v, waveform.inductor_current_a,
                              waveform.capacitor_current_a, waveform.output_voltage_v)
                    assert len(figure.axes) == 4
                    for axis, values in zip(figure.axes, series, strict=True):
                        assert len(axis.lines) == 1
                        assert list(axis.lines[0].get_ydata()) == values
                        assert list(axis.lines[0].get_xdata()) == [t * 1e6 for t in waveform.time_s]
                        assert axis.get_ylim()[0] <= min(values) <= max(values) <= axis.get_ylim()[1]
                        assert axis.get_xlim() == (waveform.time_s[0] * 1e6, waveform.time_s[-1] * 1e6)
                    title = figure._suptitle.get_text()
                    assert f"Vin={vin:.3f}" in title and f"Load={waveform.load_ratio:.3f}" in title
                    assert f"Vout(actual)={waveform.operating_vout_v:.3f}" in title
                    assert f"Vout(target)={target:.3f}" in title and f"f_sw={1e-3 / waveform.switching_period_s:.3f} kHz" in title
                    assert report.stress == app.state_store.active_plugin.extract_stress(report.candidate, waveform)
                    stress_text = app.workspace.stress_view.text.get("1.0", "end-1c")
                    loss_text = app.workspace.loss_view.text.get("1.0", "end-1c")
                    assert stress_text == "\n".join(build_stress_summary_lines(report))
                    assert loss_text == "\n".join(build_system_loss_summary(report))
                    assert report.device.current_operating_summary in loss_text
                    payload = build_structured_report(report)
                    assert payload["waveform"]["operating"]["output_voltage"]["value"] == waveform.operating_vout_v
                    assert payload["stress"]["switch"]["current_rms"]["value"] == report.stress.switch.current_rms_a
                    losses = {v.role: v.p_cond_W for v in report.device.current_operating_losses.values()}
                    assert set(losses) == set(selected)
                    rows.append({"case": name, "vin_v": vin, "target_vout_v": target, "load_ratio_input": load,
                                 "actual_vout_v": waveform.operating_vout_v, "actual_frequency_hz": 1 / waveform.switching_period_s,
                                 "all_arrays_sha256": array_digest, "switch_rms_a": report.stress.switch.current_rms_a,
                                 "conduction_losses_w": losses, "title": title,
                                 "ylim": [list(a.get_ylim()) for a in figure.axes],
                                 "yticks": [list(a.get_yticks()) for a in figure.axes],
                                 "current_report_and_plot_match": True})
                    if index == 0 and name in ("nominal", "load_50pct"):
                        figure.savefig(output_root / f"gui-{name}.png")
                assert rows[0]["all_arrays_sha256"] == rows[1]["all_arrays_sha256"] == rows[-1]["all_arrays_sha256"]
                assert all(row['actual_frequency_hz'] != rows[0]['actual_frequency_hz'] for row in rows[2:-1])
                assert rows[0]["ylim"][1] != rows[4]["ylim"][1]
                for role in selected:
                    assert rows[4]["conduction_losses_w"][role] < rows[0]["conduction_losses_w"][role]
                rejected = []
                for field, invalid in (("vin_v", "not-a-number"), ("vin_v", "0"), ("vout_v", "1000"),
                                       ("vout_v", "0"), ("load_ratio", "0"), ("load_ratio", "-0.1"), ("vout_v", "nan")):
                    prior = app.state_store.design_report
                    edit_operating(form, field, invalid)
                    form.generate_waveforms_button.invoke()
                    app.update()
                    assert len(errors) == 1 and errors[0][0] == "Waveform Error", errors
                    assert app.state_store.design_report is prior
                    assert all(v.get() == "-" for v in form.waveform_readback_vars.values())
                    assert not any(axis.lines for axis in app.workspace.waveform_view.figure.axes)
                    rejected.append({"field": field, "input": invalid, "dialog": list(errors.pop()), "old_plot_cleared": True})
                    edit_operating(form, "vin_v", 400)
                    edit_operating(form, "vout_v", 48)
                    edit_operating(form, "load_ratio", 1)
                    form.generate_waveforms_button.invoke()
                    app.update()
                    assert not errors
                    assert digest(arrays(asdict(app.state_store.design_report.waveform))) == rows[0]["all_arrays_sha256"]
                assert not callback_errors, callback_errors
                assert design_calls.call_count == index + 1
                result["variants"].append({"topology": variant["topology"], "primary": variant["primary"],
                    "secondary": variant["secondary"], "layout": layout, "selected_devices": selected,
                    "candidate_preserved": True, "design_calls": 1, "waveform_button_invocations": len(points) + 2 * len(rejected),
                    "cases": rows, "rejected_inputs_and_recovery": rejected})
                print(f"PASS {variant['topology']}/{variant['primary']}/{variant['secondary']}: {len(points) + 2 * len(rejected)} button invocations, 2 window sizes", flush=True)
    finally:
        app.destroy()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, default=ROOT / "Plan/completed/llc_waveform_operating_point_evidence/step1_baseline.json")
    parser.add_argument("--runtime-output", type=Path, default=ROOT / "pytest_temp/llc-auto-frequency-gui")
    args = parser.parse_args()
    args.runtime_output.mkdir(parents=True, exist_ok=True)
    evidence = verify(args.runtime_output.resolve(), args.baseline)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
