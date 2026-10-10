"""Positive and fault-injection checks for the test-only engineering contracts."""

from copy import deepcopy
from dataclasses import replace
import csv
import json

import pytest

from engineering_support.assertions import (
    assert_loss_balance, assert_operating_basis, assert_fixed_hardware, assert_physical_instances,
)
from engineering_support.interleaved_boost_pfc import (
    COMPONENTS, TOPOLOGY_ID, PHASE_ROLES, design_loss_snapshot, point_loss_snapshot,
    full_load_point, assert_point_loss, independent_waveform_reference, assert_waveform_reference,
    DEVICE_ROLES, assert_sweep_contract, assert_export_matches, assert_display_matches,
)
from pe_claw_gui.models.design_report import DesignReport
from pe_claw_gui.models.efficiency_sweep import EfficiencySweepPoint, EfficiencySweepResult
from pe_claw_gui.models.loss_result import LossResult
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.topologies.ac_dc.single_phase_interleaved_boost_pfc_diode_bridge import PLUGIN, build_default_inputs
from pe_claw_gui.topologies.ac_dc.single_phase_interleaved_boost_pfc_diode_bridge.loss_readback import (
    resolve_interleaved_boost_pfc_loss_snapshot,
)


LOSS_TOLERANCES = dict(loss_abs_tol=1e-9, loss_rel_tol=1e-9,
                       efficiency_abs_tol=1e-12, efficiency_rel_tol=1e-9)


@pytest.fixture
def point():
    return EfficiencySweepPoint(
        load_pu=1.0, output_power_w=1000.0, total_loss_w=25.0, efficiency=1000 / 1025,
        bridge_rectifier_loss_w=5.0, semiconductor_loss_w=15.0, magnetic_loss_w=2.0,
        capacitor_loss_w=3.0, other_loss_w=0.0,
        loss_breakdown_w={"bridge_rectifier": 5.0, "semiconductor": 15.0, "magnetic": 2.0,
                          "capacitor": 3.0, "other": 0.0, "phase_1_inductor": 0.8, "phase_2_inductor": 1.2},
    )


def test_loss_contract_accepts_explicit_components_and_ignores_diagnostic_children(point):
    assert_point_loss(point, **LOSS_TOLERANCES)
    snapshot = point_loss_snapshot(point)
    assert set(snapshot["components"]) == set(COMPONENTS)
    assert snapshot["components"]["other"] == 0.0
    assert snapshot["total_loss_w"] == point.total_loss_w


@pytest.mark.parametrize("fault,rule", [
    ("missing", "LOSS_COMPONENT_MISSING"), ("none", "LOSS_COMPONENT_VALUE"),
    ("nan", "LOSS_COMPONENT_VALUE"), ("inf", "LOSS_COMPONENT_VALUE"),
    ("negative", "LOSS_COMPONENT_VALUE"), ("bool", "LOSS_COMPONENT_VALUE"),
    ("total", "LOSS_TOTAL"), ("magnetic_as_system", "LOSS_TOTAL"),
    ("efficiency", "LOSS_EFFICIENCY"), ("percent", "LOSS_EFFICIENCY_VALUE"),
    ("nan_total", "LOSS_TOTAL_VALUE"), ("inf_eta", "LOSS_EFFICIENCY_VALUE"),
    ("zero_power", "LOSS_POWER"), ("missing_power", "LOSS_POWER"),
])
def test_loss_contract_rejects_known_faults_with_field_diagnostics(point, fault, rule):
    snapshot = point_loss_snapshot(point)
    if fault == "missing":
        del snapshot["components"]["capacitor"]
    elif fault in ("none", "nan", "inf", "negative", "bool"):
        snapshot["components"]["capacitor"] = {"none": None, "nan": float("nan"), "inf": float("inf"), "negative": -3.0, "bool": True}[fault]
    else:
        field, value = {"total": ("total_loss_w", 26.0), "magnetic_as_system": ("total_loss_w", 2.0),
                        "efficiency": ("efficiency", 0.99), "percent": ("efficiency", 97.56),
                        "nan_total": ("total_loss_w", float("nan")), "inf_eta": ("efficiency", float("inf")),
                        "zero_power": ("output_power_w", 0.0), "missing_power": ("output_power_w", None)}[fault]
        snapshot[field] = value
    with pytest.raises(AssertionError, match=rule) as error:
        assert_loss_balance(**snapshot, required_components=COMPONENTS, **LOSS_TOLERANCES)
    assert "expected" in str(error.value) and "actual" in str(error.value)


@pytest.mark.parametrize("required", [(), ("magnetic", "magnetic")])
def test_loss_contract_rejects_empty_or_duplicate_requirements(point, required):
    with pytest.raises(AssertionError, match="LOSS_COMPONENTS"):
        assert_loss_balance(**point_loss_snapshot(point), required_components=required, **LOSS_TOLERANCES)


@pytest.mark.parametrize("field", ["total_loss_w", "efficiency"])
def test_checker_rejects_corrupt_published_value_even_when_resolver_recalculates(point, field):
    spec = PLUGIN.build_spec(build_default_inputs())
    corrupt = replace(point, **{field: 1.0})
    report = DesignReport(spec=spec, efficiency_sweep=EfficiencySweepResult(points=(corrupt,), load_grid=(1.0,)))
    # The existing display resolver's arithmetic can look correct; validate the original too.
    snapshot = resolve_interleaved_boost_pfc_loss_snapshot(report)
    assert snapshot.total_loss_w == 25.0
    with pytest.raises(AssertionError, match="LOSS_TOTAL|LOSS_EFFICIENCY"):
        assert_point_loss(corrupt, **LOSS_TOLERANCES)


def test_design_adapter_keeps_missing_components_and_original_magnetic_stage_total():
    spec = PLUGIN.build_spec(build_default_inputs())
    report = DesignReport(spec=spec, loss=LossResult(total_loss_w=2.0, breakdown_w={"inductor_total_loss_w": 2.0}))
    snapshot = design_loss_snapshot(report)
    assert snapshot["components"]["bridge_rectifier"] is None
    assert snapshot["total_loss_w"] == 2.0
    with pytest.raises(AssertionError, match="LOSS_COMPONENT_VALUE"):
        assert_loss_balance(components=snapshot["components"], required_components=COMPONENTS,
                            total_loss_w=snapshot["total_loss_w"], output_power_w=snapshot["output_power_w"],
                            efficiency=0.999, **LOSS_TOLERANCES)
    with pytest.raises(AssertionError, match="TOPOLOGY"):
        design_loss_snapshot(replace(report, spec=replace(spec, topology_id="wrong")))


@pytest.mark.parametrize("fault", ["absent", "nearby", "duplicate", "blocked", "empty"])
def test_full_load_lookup_rejects_inexact_missing_or_ambiguous_points(point, fault):
    points = {"absent": (replace(point, load_pu=0.5),), "nearby": (replace(point, load_pu=0.999),),
              "duplicate": (point, point), "blocked": (point,), "empty": ()}[fault]
    result = EfficiencySweepResult(points=points, status="blocked" if fault == "blocked" else "available")
    with pytest.raises(AssertionError, match="SWEEP_STATUS|SWEEP_FULL_LOAD"):
        full_load_point(result)


@pytest.mark.parametrize("fault", ["phase", "breakdown", "phase_nan"])
def test_point_contract_requires_phase_children_and_agrees_with_breakdown(point, fault):
    data = dict(point.loss_breakdown_w)
    if fault == "phase": del data["phase_2_inductor"]
    elif fault == "phase_nan": data["phase_2_inductor"] = float("nan")
    else: data["semiconductor"] = 16.0
    with pytest.raises(AssertionError, match="LOSS_COMPONENT_VALUE|LOSS_BREAKDOWN"):
        assert_point_loss(replace(point, loss_breakdown_w=data), **LOSS_TOLERANCES)


@pytest.mark.parametrize("fault", ["stale_vin", "stale_load", "missing", "nan", "source", "tolerance"])
def test_operating_basis_rejects_stale_or_incomplete_source(fault):
    expected = {"vin_rms_v": 180.0, "load_ratio": 0.5, "source": "recomputed_from_operating_point"}
    actual = dict(expected)
    tolerances = {"vin_rms_v": (1e-9, 1e-9), "load_ratio": (1e-12, 1e-9)}
    if fault == "stale_vin": actual["vin_rms_v"] = 230.0
    elif fault == "stale_load": actual["load_ratio"] = 1.0
    elif fault == "missing": del actual["vin_rms_v"]
    elif fault == "nan": actual["vin_rms_v"] = float("nan")
    elif fault == "source": actual["source"] = "design_point"
    else: del tolerances["vin_rms_v"]
    with pytest.raises(AssertionError, match="BASIS_"):
        assert_operating_basis(expected=expected, actual=actual, required_keys=tuple(expected), tolerances=tolerances)


@pytest.mark.parametrize("fault", ["missing", "changed", "selection"])
def test_fixed_hardware_rejects_missing_roles_reselection_or_changed_identity(fault):
    before = {"phase_1": "core::phase_1", "phase_2": "core::phase_2"}
    after = dict(before)
    calls = []
    if fault == "missing": del after["phase_2"]
    elif fault == "changed": after["phase_2"] = "new-core::phase_2"
    else: calls.append("select_inductor")
    with pytest.raises(AssertionError, match="HARDWARE_"):
        assert_fixed_hardware(before=before, after=after, required_roles=PHASE_ROLES, selection_calls=calls)


@pytest.mark.parametrize("fault", ["count", "role", "design_id", "physical_id", "absent_id"])
def test_physical_instances_reject_missing_or_duplicated_phase(fault):
    instances = [{"role": p, "design_id": f"core::{p}", "physical_id": p, "library_id": "same-core"} for p in PHASE_ROLES]
    if fault == "count": instances.pop()
    elif fault == "absent_id": instances[1].pop("physical_id")
    else: instances[1][fault] = instances[0][fault]
    with pytest.raises(AssertionError, match="INSTANCE_"):
        assert_physical_instances(instances=instances, expected_roles=PHASE_ROLES, expected_count=2)


def test_identity_contract_accepts_equal_models_and_basis_at_explicit_tolerance():
    ids = {"phase_1": "core::phase_1", "phase_2": "core::phase_2"}
    assert_fixed_hardware(before=ids, after=deepcopy(ids), required_roles=PHASE_ROLES, selection_calls=[])
    assert_physical_instances(instances=[{"role": p, "design_id": ids[p], "physical_id": p, "library_id": "same"} for p in PHASE_ROLES],
                             expected_roles=PHASE_ROLES, expected_count=2)
    assert_operating_basis(expected={"vin": 180.0, "source": "current"}, actual={"vin": 180.0 + 1e-10, "source": "current"},
                           required_keys=("vin", "source"), tolerances={"vin": (1e-9, 1e-9)})


@pytest.mark.parametrize("vin", (180.0, 230.0, 265.0))
@pytest.mark.parametrize("load", (0.1, 0.5, 1.0))
def test_independent_line_load_reference_checks_actual_phase_metrics(vin, load):
    spec = PLUGIN.build_spec(build_default_inputs())
    candidate = PLUGIN.synthesize(spec)
    point = OperatingPoint(vin_v=vin, load_ratio=load)
    waveform = PLUGIN.generate_waveforms(candidate, point)
    reference = independent_waveform_reference(candidate, vin, load)
    assert_waveform_reference(waveform, reference, abs_tol=1e-9, rel_tol=1e-9)


@pytest.fixture
def sweep(point):
    hardware = {"bridge_rectifier": "bridge", "devices": {role: role for role in DEVICE_ROLES},
                "phase_inductors": {role: f"core::{role}" for role in PHASE_ROLES},
                "dc_link_capacitor": {"part_number": "cap", "series_count": 1, "parallel_count": 2}}
    return EfficiencySweepResult(
        topology_id=TOPOLOGY_ID, run_id="test-run", input_sha256="test-input-hash",
        points=(replace(point, switching_loss_audit={"fixed_hardware_ids": deepcopy(hardware)}),),
        load_grid=(1.0,), full_load_efficiency=point.efficiency,
        sweep_basis={"fixed_hardware_ids": hardware},
    )


@pytest.mark.parametrize("fault,rule", [(None, None), ("grid", "SWEEP_GRID"), ("points", "SWEEP_GRID"),
    ("topology", "SWEEP_SOURCE"), ("sweep_hardware", "HARDWARE_CHANGED"),
    ("point_hardware", "HARDWARE_MISSING"), ("eta", "SWEEP_FULL_LOAD_EFFICIENCY"),
    ("phase_total", "LOSS_PHASE_TOTAL")])
def test_sweep_adapter_requires_current_grid_original_values_and_all_hardware(sweep, fault, rule):
    expected_hardware = deepcopy(sweep.sweep_basis["fixed_hardware_ids"])
    if fault == "grid": sweep = replace(sweep, load_grid=(0.5,))
    elif fault == "points": sweep = replace(sweep, points=(replace(sweep.points[0], load_pu=0.5),))
    elif fault == "topology": sweep = replace(sweep, topology_id="old-topology")
    elif fault == "sweep_hardware": sweep.sweep_basis["fixed_hardware_ids"]["devices"][DEVICE_ROLES[0]] = "new-device"
    elif fault == "point_hardware": sweep.points[0].switching_loss_audit["fixed_hardware_ids"]["phase_inductors"].pop("phase_2")
    elif fault == "eta": sweep = replace(sweep, full_load_efficiency=0.99)
    elif fault == "phase_total": sweep.points[0].loss_breakdown_w["phase_2_inductor"] = 2.0
    kwargs = dict(expected_grid=(1.0,), expected_hardware=expected_hardware, selection_calls=[], **LOSS_TOLERANCES)
    if rule is None:
        assert_sweep_contract(sweep, **kwargs)
    else:
        with pytest.raises(AssertionError, match=rule):
            assert_sweep_contract(sweep, **kwargs)


@pytest.mark.parametrize("fault,rule", [(None, None), ("csv_value", "EXPORT_CSV"),
    ("csv_nan", "EXPORT_CSV"), ("csv_audit", "EXPORT_CSV"), ("csv_rows", "EXPORT_CSV"),
    ("json_total", "EXPORT_JSON"), ("json_run", "EXPORT_JSON"),
    ("outside", "EXPORT_OWNER"), ("missing", "EXPORT_OWNER")])
def test_export_checker_rejects_stale_values_sources_and_foreign_paths(sweep, tmp_path, fault, rule):
    # Lightweight controlled artifacts test the checker; real plots/export are tested separately.
    from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import _write_sweep_csv
    root = tmp_path / "run"
    root.mkdir()
    paths = {key: str(root / name) for key, name in (
        ("result_json", "result.json"), ("efficiency_sweep_csv", "sweep.csv"),
        ("efficiency_curve", "curve.png"), ("loss_breakdown_stacked", "loss.png"))}
    for key in ("efficiency_curve", "loss_breakdown_stacked"):
        if fault == "outside" and key == "efficiency_curve": paths[key] = str(tmp_path / "foreign.png")
        if fault != "missing" or key != "efficiency_curve":
            from pathlib import Path
            Path(paths[key]).write_bytes(b"controlled checker fixture")
    sweep = replace(sweep, artifact_paths=paths)
    payload = sweep.to_dict()
    if fault == "json_total": payload["points"][0]["total_loss_w"] = 2.0
    if fault == "json_run": payload["run_id"] = "stale-run"
    (root / "result.json").write_text(json.dumps(payload), encoding="utf-8")
    _write_sweep_csv(sweep, root / "sweep.csv")
    if fault in ("csv_value", "csv_nan", "csv_audit", "csv_rows"):
        with (root / "sweep.csv").open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fields, rows = reader.fieldnames, list(reader)
        if fault == "csv_value": rows[0]["total_loss_w"] = "2.0"
        elif fault == "csv_nan": rows[0]["efficiency"] = "nan"
        elif fault == "csv_audit": rows[0]["switching_loss_audit"] = "{}"
        else: rows = []
        with (root / "sweep.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    if rule is None:
        assert_export_matches(sweep, output_root=root, **LOSS_TOLERANCES)
    else:
        with pytest.raises(AssertionError, match=rule):
            assert_export_matches(sweep, output_root=root, **LOSS_TOLERANCES)


@pytest.mark.parametrize("fault", (None, "loss_total", "loss_source", "inductor", "efficiency", "phase", "component"))
def test_display_checker_compares_numbers_phase_children_labels_and_source(point, fault):
    loss = """Total estimated loss: 25 W
Full-load efficiency sweep (1.0 p.u.) estimated efficiency: 97.561 %
Loss source: Full-load efficiency sweep (1.0 p.u.)
Input bridge: 5 W
Four phase-position semiconductor devices: 15 W
Both phase inductors: 2 W
Shared DC-link capacitor bank: 3 W
Other (not modeled): 0 W
Phase 1 inductor: 0.8 W
Phase 2 inductor: 1.2 W"""
    inductor = "system total loss (all components): 25 W\nsystem loss source: Full-load efficiency sweep (1.0 p.u.)"
    efficiency = "Full-load efficiency: 97.561%\ntotal: 25 W\nBridge: 5 W\nDevices: 15 W\nInductors: 2 W\nCapacitor: 3 W"
    if fault == "loss_total": loss = loss.replace("25 W", "2 W")
    elif fault == "loss_source": loss = loss.replace("Loss source: Full-load efficiency sweep (1.0 p.u.)", "Loss source: Design point")
    elif fault == "inductor": inductor = inductor.replace("25 W", "2 W")
    elif fault == "efficiency": efficiency = efficiency.replace("97.561%", "99.8%")
    elif fault == "phase": loss = loss.replace("Phase 2 inductor: 1.2 W", "Phase 2 inductor: 0.8 W")
    elif fault == "component": efficiency = efficiency.replace("Bridge: 5 W", "Bridge: 15 W")
    kwargs = dict(loss_text=loss, inductor_text=inductor, efficiency_text=efficiency,
                  efficiency_labels={"bridge_rectifier": "Bridge", "semiconductor": "Devices", "magnetic": "Inductors", "capacitor": "Capacitor"})
    if fault is None:
        assert_display_matches(point, **kwargs)
    else:
        with pytest.raises(AssertionError, match="DISPLAY_VALUE"):
            assert_display_matches(point, **kwargs)
