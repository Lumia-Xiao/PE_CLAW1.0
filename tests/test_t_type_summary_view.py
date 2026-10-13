"""T-type overview readback stays compact without changing detailed evidence."""
from __future__ import annotations

import copy
from dataclasses import asdict, replace
import tkinter as tk

import pytest

from pe_claw_gui.app.result_views.summary_view import SummaryView
from pe_claw_gui.app.result_views.stress_view import build_stress_summary_lines
from pe_claw_gui.models.device_result import DeviceSelectionResult
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import PLUGIN
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.stress import PAYLOAD_KEY


@pytest.fixture(scope="module")
def view():
    root = tk.Tk()
    root.withdraw()
    widget = SummaryView(root)
    yield widget
    root.destroy()


@pytest.fixture(scope="module")
def design():
    spec = PLUGIN.build_spec({})
    candidate = PLUGIN.synthesize(spec)
    return PLUGIN.build_report(spec, candidate)


@pytest.fixture(scope="module")
def current(design):
    op = OperatingPoint(vin_v=700, load_ratio=.5, power_factor=.8)
    waveform = PLUGIN.generate_waveforms(design.candidate, op)
    return PLUGIN.build_report(design.spec, design.candidate, op, waveform)


def read(view, report):
    view.render(report)
    return view.text.get("1.0", "end")


def test_design_parameters_and_missing_actual_currents(view, design):
    text = read(view, design)
    assert "Vdc_nom = 700.000000 V" in text
    assert "Vac line-line rms = 400.000000 V" in text
    assert "Pout = 10000.000000 W" in text
    assert "f_line / fsw = 50 / 20000.00 Hz" in text
    assert "Cdc per-bank proxy = 81.632653 uF" in text
    assert "L_phase initial = 1071.651762 uH" in text
    assert "design_estimate" in text
    assert "RMS=N/A, average=N/A" in text
    assert "Operating I_phase" not in text
    assert "Loss and system efficiency are unavailable." in text


def test_current_role_envelopes_and_detailed_positions_keep_original_source(view, current):
    frozen = copy.deepcopy(asdict(current))
    data = current.waveform.metadata[PAYLOAD_KEY]
    text = read(view, current)
    assert "Operating active power = 5000.000000 W" in text
    assert "Operating PF = 0.800000 lagging" in text
    assert f"Operating I_phase rms (A phase, including PWM ripple) = {data['diagnostics']['phase_statistics']['a']['rms_a']:.6f} A" in text
    detail = "\n".join(build_stress_summary_lines(current))
    assert "12 position metrics" not in text
    assert "12 position metrics" in detail
    for role in ("main", "midpoint"):
        metrics = data["stress"][role]
        assert f"Static blocking maximum = {metrics['voltage_max_v']:.6f} V" in text
        for path in ("signed", "channel", "diode"):
            assert f"{path}: peak={metrics[path+'_peak_a']:.6f} A, RMS={metrics[path+'_rms_a']:.6f} A, average={metrics[path+'_avg_a']:.6f} A" in text
    for position in data["stress"]["positions"]:
        assert position not in text
        assert position in detail
    assert "Topology evaluation" not in text
    assert len(text.splitlines()) < 75
    assert asdict(current) == frozen


def test_unknown_report_and_stress_warnings_remain_visible(view, current):
    report = replace(current, notes=[*current.notes, "Controlled failure: missing required component."],
                     stress=replace(current.stress, notes=[*current.stress.notes, "Controlled stress warning: source invalid."]))
    text = read(view, report)
    assert "Controlled failure: missing required component." in text
    assert "Controlled stress warning: source invalid." in text
    assert "Stages not run:" in text
    assert "stage not run; outside first-pass" not in text


@pytest.mark.parametrize("selected, scheme, available", [
    ({"t_type_main_switch": "main"}, "single", False),
    ({"t_type_main_switch": "main", "t_type_midpoint_switch": "midpoint"}, None, False),
    ({"t_type_main_switch": "main", "t_type_midpoint_switch": "midpoint"}, "single", True),
])
def test_selection_status_requires_both_published_roles(view, design, selected, scheme, available):
    report = replace(design, device=DeviceSelectionResult(selected_devices=selected, active_scheme_id=scheme),
                     notes=[n for n in design.notes if not n.startswith("device: stage not run")])
    text = read(view, report)
    assert ("Semiconductor selection = available (conduction only; see Devices)." in text) is available
    assert ("required two-role hardware incomplete" in text) is not available
    assert "Loss and system efficiency are unavailable." in text


def test_failed_operating_refresh_cannot_show_stale_actual_stress(view, current):
    report = replace(current, waveform=None, stress=None, topology_result=None,
                     notes=[*current.notes, "Controlled failure: modulation command exceeds limit."])
    text = read(view, report)
    assert "Stress results are not available for this report." in text
    assert "Operating I_phase" not in text
    assert "waveform_actual" not in text
    assert "Controlled failure: modulation command exceeds limit." in text
