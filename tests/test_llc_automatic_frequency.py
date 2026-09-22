"""Voltage matching, gain-curve roots and current-result propagation."""
from dataclasses import asdict, replace
from math import pi, sqrt

import numpy as np
import pytest

from scripts.build_llc_waveform_operating_point_baseline import arrays
from scripts.report_schema_validation import validate_report
from tests.test_llc_waveform_operating_point import design
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.engines.devices.stress_adapter import build_current_operating_switch_stress_case
from pe_claw_gui.pipeline.run_capacitor_pipeline import _operating_switching_frequency_hz
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import _sweep_operating_point
from pe_claw_gui.pipeline.run_operating_point_refresh import run_operating_point_refresh
from pe_claw_gui.reports.structured_output import build_structured_report
from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.fha_design import matching_fha_frequencies


def test_llc_vin_vout_and_load_each_change_frequency_with_fixed_hardware(design):
    _, plugin, initial, _ = design
    original = asdict(initial.candidate)
    points = [(400, 48, 1), (360, 48, 1), (420, 48, 1), (400, 46, 1),
              (400, 50, 1), (400, 48, .5), (400, 48, .1), (400, 48, 1.5)]
    reports = []
    for vin, target, load in points:
        report = run_operating_point_refresh(initial, plugin, OperatingPoint(vin, load, target))
        w = report.waveform
        f = 1 / w.switching_period_s
        tank = initial.candidate.metadata['llc_fha']
        assert tank['fs_min_hz'] <= f <= tank['fs_max_hz']
        assert w.operating_vout_v == pytest.approx(target, rel=1e-8)
        assert w.load_ratio == load
        assert report.candidate is initial.candidate
        assert asdict(report.candidate) == original
        # Independent complex impedance calculation checks the achieved gain,
        # rather than merely checking solver metadata against itself.
        rload = tank['rout_nom_ohm'] / load
        rac = 8 / pi**2 * tank['turns_ratio']**2 * rload
        omega = 2 * pi * f
        zm = 1j * omega * tank['lm_h']
        parallel = zm * rac / (zm + rac)
        transfer = parallel / (1j * omega * tank['lr_h'] + 1/(1j * omega * tank['cr_f']) + parallel)
        actual = abs(transfer) * tank['primary_bridge_gain_factor'] * vin / tank['turns_ratio']
        assert actual == pytest.approx(target, rel=1e-8)
        assert w.metadata['llc_fha_waveforms']['pout_op_w'] == pytest.approx(target**2 / rload)
        assert _operating_switching_frequency_hz(report) == f
        stress = build_current_operating_switch_stress_case(report, plugin)
        assert all(s.fsw_Hz == f for s in stress.stresses)
        payload = build_structured_report(report)
        assert not validate_report(payload)
        assert payload['operating_point']['output_voltage']['value'] == target
        assert payload['waveform']['operating']['switching_frequency']['value'] == f
        assert _sweep_operating_point(report, .25) == replace(report.operating_point, load_ratio=.25)
        reports.append(report)
    assert all(r.waveform.switching_period_s != reports[0].waveform.switching_period_s for r in reports[1:])
    assert all(arrays(asdict(r.waveform)) != arrays(asdict(reports[0].waveform)) for r in reports[1:])
    repeated = plugin.generate_waveforms(initial.candidate, OperatingPoint(400, 1, 48))
    assert repeated == reports[0].waveform


def test_llc_unreachable_invalid_and_nonfinite_targets_are_rejected(design):
    _, plugin, initial, _ = design
    for point in (OperatingPoint(400, 1, 1), OperatingPoint(400, 1, 1000)):
        with pytest.raises(ValueError, match='No LLC switching frequency matches'):
            plugin.generate_waveforms(initial.candidate, point)
    for point in (OperatingPoint(0, 1, 48), OperatingPoint(400, 0, 48),
                  OperatingPoint(400, -.1, 48), OperatingPoint(400, 1, 0),
                  OperatingPoint(400, 1, -1), OperatingPoint(float('inf'), 1, 48),
                  OperatingPoint(400, float('nan'), 48), OperatingPoint(400, 1, float('nan')),
                  OperatingPoint(400, 1, float('inf'))):
        with pytest.raises(ValueError):
            plugin.generate_waveforms(initial.candidate, point)


def test_llc_explicit_frequency_override_and_legacy_no_target(design):
    _, plugin, initial, _ = design
    for target in (36, 48, 60):
        wave = plugin.generate_waveforms(initial.candidate, OperatingPoint(400, 1, target, switching_frequency_hz=120000))
        assert wave == plugin.generate_waveforms(initial.candidate, OperatingPoint(400))
        assert wave.operating_vout_v == 50


def test_llc_gain_roots_include_two_branches_endpoints_and_tangent():
    # Solve the gain equation as a cubic in fn^2 as an independent oracle.
    ln, q, gain = 5., .55, 1.1
    a, b = 1 + 1/ln, 1/ln
    x_roots = np.roots([q*q, a*a - 2*q*q - 1/gain**2, q*q - 2*a*b, b*b])
    expected = sorted(sqrt(x.real) * 120000 for x in x_roots if abs(x.imag) < 1e-10 and x.real > 0)
    args = dict(fr_hz=120000., ln=ln, q=q, required_gain=gain, fs_min_hz=12000., fs_max_hz=240000.)
    roots = matching_fha_frequencies(**args)
    assert len(roots) == 2
    assert roots == pytest.approx(expected, rel=1e-9)
    assert matching_fha_frequencies(**{**args, 'fs_min_hz': roots[0], 'fs_max_hz': roots[1]}) == pytest.approx(roots)
    assert matching_fha_frequencies(**{**args, 'fs_min_hz': roots[1], 'fs_max_hz': roots[1]}) == pytest.approx((roots[1],))
    peak_x = next(x.real for x in np.roots([q*q, 0, 2*a*b-q*q, -2*b*b]) if abs(x.imag) < 1e-10 and x.real > 0)
    peak_fn = sqrt(peak_x)
    peak_gain = 1/sqrt((a-b/peak_x)**2 + q*q*(peak_fn-1/peak_fn)**2)
    assert matching_fha_frequencies(**{**args, 'required_gain': peak_gain}) == pytest.approx((peak_fn*120000,), rel=1e-9)
    assert matching_fha_frequencies(**{**args, 'required_gain': peak_gain * 1.001}) == ()


def test_llc_multiple_solutions_choose_highest_frequency(design):
    _, plugin, initial, _ = design
    tank = {**initial.candidate.metadata['llc_fha'], 'fs_min_hz': 12000., 'fs_max_hz': 240000.}
    candidate = replace(initial.candidate, metadata={**initial.candidate.metadata, 'llc_fha': tank})
    w = plugin.generate_waveforms(candidate, OperatingPoint(400, 1, 55))
    data = w.metadata['llc_fha_waveforms']
    assert len(data['matching_frequencies_hz']) == 2
    assert 1/w.switching_period_s == pytest.approx(max(data['matching_frequencies_hz']))
    assert data['target_voltage_relative_error'] < 1e-8
