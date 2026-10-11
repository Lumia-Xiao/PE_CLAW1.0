"""Independent reference checks and controlled faults; no library search here."""
from copy import deepcopy
import json
import sys

import pytest

from scripts import record_two_phase_interleaved_boost_pfc_current_reference as reference


@pytest.fixture
def baseline():
    return json.loads(reference.CURRENT.read_text(encoding="utf-8"))


@pytest.mark.parametrize("index", (0, 1, 2), ids=("nominal", "low_line", "high_line"))
def test_frozen_current_reference_satisfies_independent_equations(baseline, index):
    assert baseline["schema_version"] == reference.SCHEMA
    reference.validate_case(baseline["cases"][index])


@pytest.mark.parametrize("fault,diagnostic", (
    ("duty", "waveform.public.duty"), ("rms", "phase_1.i_rms_a"),
    ("copper", "phase_1.copper_loss_w"), ("core", "phase_1.core_loss_w"),
    ("total", "system.total_loss_w"), ("instance", "REFERENCE_INSTANCES"),
    ("vin", "phase_1.operating_vin"), ("resistance", "phase_1.copper_loss_w"),
    ("missing", "REFERENCE_FINITE"), ("basis", "REFERENCE_BASIS"),
    ("display", "REFERENCE_DISPLAY"), ("thermal_loss", "thermal.copper_loss_w"),
    ("thermal_rise", "thermal.estimated_winding_temp_rise_c"),
))
def test_current_reference_rejects_physical_and_contract_faults(baseline, fault, diagnostic):
    case = deepcopy(baseline["cases"][0])
    engineering = case["engineering_reference"]
    evaluation = engineering["operating_evaluations"][0]
    if fault == "duty": case["waveform"]["public"]["duty"] = case["candidate"]["duty_nom"]
    elif fault == "rms": evaluation["i_rms_a"] *= 1.1
    elif fault == "copper": evaluation["copper_loss_w"] *= 1.1
    elif fault == "core": evaluation["core_loss_w"] *= 2
    elif fault == "total": case["loss"]["total_loss_w"] += 1
    elif fault == "instance": engineering["hardware_inputs"][1]["metadata"]["physical_instance_id"] = "phase_1"
    elif fault == "vin": evaluation["operating_vin_v"] = 180
    elif fault == "resistance": engineering["hardware_inputs"][0]["rdc_25c_ohm"] *= 2
    elif fault == "missing": evaluation["core_loss_w"] = None
    elif fault == "display": case["gui"]["loss_summary_lines"][3] = "  Total estimated loss: 0.478755 W"
    elif fault == "thermal_loss": engineering["thermal_rows"][0]["copper_loss_w"] = "0.312975212399"
    elif fault == "thermal_rise": engineering["thermal_rows"][0]["estimated_winding_temp_rise_c"] = "9"
    else: engineering["basis"] = "sweep"
    with pytest.raises(AssertionError, match=diagnostic):
        reference.validate_case(case)


@pytest.mark.parametrize("fault", ("hardware", "new_field", "array"))
def test_history_transition_rejects_unexplained_changes(baseline, fault):
    historical = json.loads(reference.HISTORICAL.read_text(encoding="ascii"))["cases"][0]
    current = {k:v for k,v in baseline["cases"][0].items() if k != "engineering_reference"}
    if fault == "hardware": current["hardware"]["bridge_part_number"] = "different"
    elif fault == "new_field": current["loss"]["unexplained"] = 1
    else: current["waveform"]["phase_current_arrays"]["phase_1"].append(0)
    with pytest.raises(AssertionError, match="REFERENCE_HISTORY"):
        reference.historical_differences(historical, current)


def test_reference_generator_refuses_existing_output_before_search(tmp_path, monkeypatch):
    existing = tmp_path / "frozen.json"
    existing.write_text("preserve", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["reference", str(existing), "--output-root", str(tmp_path/"new")])
    monkeypatch.setattr(reference, "build_current_reference", lambda *args: pytest.fail("must not search"))
    with pytest.raises(SystemExit) as error:
        reference.main()
    assert error.value.code == 2
    assert existing.read_text(encoding="utf-8") == "preserve"
    assert not (tmp_path/"new").exists()
