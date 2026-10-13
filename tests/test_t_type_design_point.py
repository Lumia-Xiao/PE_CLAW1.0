"""Nominal selection basis and safe, waveform-scoped stress integral reuse."""
from __future__ import annotations

import copy
from dataclasses import asdict, replace
from importlib import import_module
import json

import pytest

from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.models.waveform import WaveformSet
from pe_claw_gui.pipeline.run_topology_pipeline import run_topology_pipeline
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.reports.structured_output import build_structured_report
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import PLUGIN
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.engineering_adapter import (
    build_design_basis, build_device_selection_requests,
)
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.stress import PAYLOAD_KEY, stress_readback
from scripts.report_schema_validation import validate_report

MODULE = "pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter"


@pytest.fixture(scope="module")
def actual():
    candidate = PLUGIN.synthesize(PLUGIN.build_spec({}))
    return candidate, PLUGIN.generate_waveforms(candidate)


@pytest.fixture(scope="module")
def selected(tmp_path_factory):
    return run_full_pipeline(PLUGIN, {}, output_root=tmp_path_factory.mktemp("nominal-selected"))


@pytest.mark.parametrize("bus,pf,phase", [(700, 1, "lagging"), (800, .8, "lagging"), (700, .9, "leading")])
def test_selection_basis_is_rated_point_independent_of_current_waveform(tmp_path, bus, pf, phase):
    report = run_topology_pipeline(PLUGIN, {"vdc_nom": str(bus), "power_factor": str(pf), "power_factor_phase": phase}, output_root=tmp_path).report
    basis = build_design_basis(report)
    assert basis.cases == ((bus, 1.0, pf),)
    assert basis.selection_policy == "nominal_design_point"
    changed = replace(report, operating_point=OperatingPoint(vin_v=900, load_ratio=.1, power_factor=.5))
    assert build_design_basis(changed) == basis
    assert basis.phase == phase
    assert (basis.voltage_margin_ratio, basis.current_margin_ratio) == (.2, .1)


@pytest.mark.parametrize("key", ["engineering_vdc_min_v", "engineering_vdc_max_v", "engineering_pf_min", "engineering_pf_max", "engineering_load_min", "engineering_load_max"])
def test_retired_envelope_inputs_are_not_silently_ignored(key):
    with pytest.raises(ValueError, match=f"{key}.*retired"):
        PLUGIN.build_spec({key: "1"})


def test_default_spec_no_longer_carries_hidden_envelope():
    spec = PLUGIN.build_spec({})
    assert not any(key.startswith(("engineering_vdc_", "engineering_pf_", "engineering_load_")) for key in spec.metadata)


@pytest.mark.parametrize("field,value", [("cases", ((800., .5, .8),)), ("phase", "leading"), ("ambient_temp_c", 30), ("run_id", "stale"), ("selection_policy", "legacy_envelope")])
def test_modified_selection_basis_is_rejected_before_any_waveform(selected, monkeypatch, field, value):
    basis = replace(selected.t_type_engineering.design_basis, **{field: value})
    monkeypatch.setattr(type(PLUGIN), "generate_waveforms", lambda *a, **kw: pytest.fail("stale source reached solver"))
    with pytest.raises(ValueError, match="source mismatch"):
        build_device_selection_requests(selected, basis, PLUGIN)


def test_changed_candidate_scalar_cannot_become_valid_design_source(selected):
    changed = replace(selected, candidate=replace(selected.candidate, vin_nom=800))
    with pytest.raises(ValueError, match="metadata mismatch"):
        build_design_basis(changed)


def test_stress_is_integrated_once_per_generated_waveform(monkeypatch, tmp_path):
    stress_module = import_module(MODULE + ".stress")
    waveform_module = import_module(MODULE + ".waveform")
    calculate = stress_module.calculate_position_stress
    calls = []
    def counted(*args, **kwargs):
        calls.append(args[1]["load_ratio"])
        return calculate(*args, **kwargs)
    monkeypatch.setattr(stress_module, "calculate_position_stress", counted)
    monkeypatch.setattr(waveform_module, "calculate_position_stress", counted)
    source = run_topology_pipeline(PLUGIN, {}, include_waveforms=True, output_root=tmp_path).report
    basis = build_design_basis(source)
    # Consumers validate but do not re-integrate the same immutable numerical source.
    stress_readback(source.candidate, source.waveform)
    assert calls == [1.0]
    stress, requests = build_device_selection_requests(source, basis, PLUGIN)
    assert calls == [1.0, 1.0]  # A separate selection waveform owns a separate receipt.
    assert len(requests) == 12 and all(r.case == (700., 1., 1.) for r in requests)
    assert all(len(cases) == 1 for cases in stress.values())


@pytest.mark.parametrize("kind,message", [("stress", "stress"), ("both_metrics", "stress"), ("position", "metrics"), ("segment", "formula"), ("statistics", "statistics"), ("gate", "gates"), ("basis", "basis"), ("missing_stress", "stress"), ("nonfinite", "stress")])
def test_runtime_receipt_does_not_hide_corrupted_waveform(actual, kind, message):
    candidate, waveform = actual
    wave = copy.deepcopy(waveform)
    payload = wave.metadata[PAYLOAD_KEY]
    stress_readback(candidate, wave)
    if kind in ("stress", "both_metrics"):
        payload["stress"]["positions"]["a_QP"]["channel_peak_a"] += 1
        if kind == "both_metrics":
            payload["positions"]["a_QP"]["metrics"]["channel_peak_a"] += 1
    elif kind == "position": payload["positions"]["a_QP"]["metrics"]["channel_peak_a"] += 1
    elif kind == "segment":
        values = list(payload["segments"][0]["end_currents_a"])
        values[0] += 1
        values[1] -= 1  # Keep KCL valid so the exact-current formula check owns the failure.
        payload["segments"][0]["end_currents_a"] = values
    elif kind == "statistics": payload["diagnostics"]["phase_statistics"]["a"]["rms_a"] += 1
    elif kind == "gate": payload["phases"]["a"]["gates"]["QP"][0] = 1 - payload["phases"]["a"]["gates"]["QP"][0]
    elif kind == "basis": payload["basis"]["inductance_h"] *= 2
    elif kind == "missing_stress": del payload["stress"]
    else: payload["stress"]["positions"]["a_QP"]["channel_peak_a"] = float("nan")
    with pytest.raises(ValueError, match=message):
        stress_readback(candidate, wave)


def test_plain_or_replaced_waveform_without_receipt_is_verified_by_integration(actual, monkeypatch):
    candidate, waveform = actual
    module = import_module(MODULE + ".stress")
    calculate = module.calculate_position_stress
    count = []
    monkeypatch.setattr(module, "calculate_position_stress", lambda *a, **kw: (count.append(1), calculate(*a, **kw))[1])
    plain = WaveformSet(**copy.deepcopy(asdict(waveform)))
    assert stress_readback(candidate, plain) == waveform.metadata[PAYLOAD_KEY]["stress"]
    assert len(count) == 1
    replaced = replace(waveform)
    stress_readback(candidate, replaced)
    stress_readback(candidate, replaced)
    assert len(count) == 2


def test_receipt_is_not_serialized_and_readback_is_an_independent_copy(actual):
    candidate, waveform = actual
    encoded = json.dumps(asdict(waveform), allow_nan=False)
    assert "_position_stress_key" not in encoded
    result = stress_readback(candidate, waveform)
    original = waveform.metadata[PAYLOAD_KEY]["stress"]["main"]["channel_peak_a"]
    result["main"]["channel_peak_a"] = -1
    assert stress_readback(candidate, waveform)["main"]["channel_peak_a"] == original


def test_nominal_policy_is_explicit_in_export_and_legacy_remains_distinct(selected):
    payload = build_structured_report(selected)
    assert not validate_report(payload)
    assert payload["engineering_result"]["design_basis"]["selection_policy"] == "nominal_design_point"
    legacy = copy.deepcopy(payload)
    del legacy["engineering_result"]["design_basis"]["selection_policy"]
    legacy["engineering_result"]["design_basis"]["cases"] = ((700., 1., 1.), (800., .5, .8))
    assert not validate_report(legacy)


@pytest.mark.parametrize("kind", ["cases", "load", "pf", "reference", "policy"])
def test_export_rejects_mislabeled_nominal_selection(selected, kind):
    payload = copy.deepcopy(build_structured_report(selected))
    engineering = payload["engineering_result"]
    basis = engineering["design_basis"]
    if kind == "cases": basis["cases"] = ((700., 1., 1.), (800., 1., 1.))
    elif kind == "load": basis["cases"] = ((700., .5, 1.),)
    elif kind == "pf": basis["cases"] = ((700., 1., .8),)
    elif kind == "reference": next(iter(engineering["role_selection_reference"].values()))["case"] = (800., .5, .8)
    else: basis["selection_policy"] = "unrecognized"
    assert any("design_point" in error or "reference_case" in error or "selection_policy" in error for error in validate_report(payload))
