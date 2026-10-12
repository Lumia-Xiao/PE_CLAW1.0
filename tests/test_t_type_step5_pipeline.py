from __future__ import annotations

import copy
import dataclasses
import json
import math
from pathlib import Path

import pytest
from scipy.integrate import simpson
import numpy as np

from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.run_topology_pipeline import run_topology_pipeline
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import PLUGIN
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.evaluator import NOT_RUN
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.stress import PAYLOAD_KEY, calculate_position_stress, stress_readback


@pytest.fixture(scope="module")
def actual(tmp_path_factory):
    root = tmp_path_factory.mktemp("t-type-pipeline")
    return run_topology_pipeline(PLUGIN, {}, include_waveforms=True, output_root=root)


def test_real_pipeline_report_and_run_identity(actual):
    report = actual.report
    assert report.spec.topology_id == PLUGIN.topology_id
    assert report.waveform is actual.waveform
    assert report.candidate is actual.candidate
    assert report.topology_result == actual.topology_result
    context = report.run_context
    assert context.topology_id == PLUGIN.topology_id
    assert context.stage_status["design"] == "succeeded"
    assert all(v == "not_started" for k,v in context.stage_status.items() if k != "design")
    manifest = json.loads(Path(context.manifest_path).read_text())
    assert manifest["run"]["run_id"] == context.run_id
    for stage in NOT_RUN:
        assert getattr(report,stage) is None
        assert any(stage+": stage not run" in note for note in report.notes)
    assert report.stress.role_voltage_checks == {}
    assert report.stress.switch.voltage_max_v == 700
    assert report.stress.rectifier.voltage_max_v == 700
    assert report.stress.switch.current_rms_a == pytest.approx(9.092248363573049, rel=1e-9)
    payload = report.waveform.metadata[PAYLOAD_KEY]
    assert payload["stress"]["basis"] == "waveform_actual"
    assert len(payload["stress"]["positions"]) == 12
    assert payload["stress"]["midpoint"]["voltage_max_v"] == 350
    assert report.waveform.metadata["t_type_phase_current_rms_a"][0] > report.candidate.iout


def test_without_waveform_only_peak_estimates_and_no_hardware(tmp_path):
    bundle = run_topology_pipeline(PLUGIN, {}, include_waveforms=False, output_root=tmp_path)
    assert bundle.waveform is None
    assert bundle.report.stress.switch.current_peak_a == bundle.candidate.il_peak
    assert bundle.report.stress.switch.current_rms_a is None
    assert bundle.report.stress.rectifier.current_avg_a is None
    assert stress_readback(bundle.candidate)["basis"] == "design_estimate"
    assert "design_estimate" in bundle.topology_result.summary_lines[0]


def test_position_integrals_against_independent_dense_reference_and_refinement(actual):
    payload = actual.waveform.metadata[PAYLOAD_KEY]
    basis = payload["basis"]
    expected = payload["stress"]["positions"]
    refined = calculate_position_stress(payload["segments"],basis,subdivisions=2)["positions"]
    for key in expected:
        assert refined[key] == pytest.approx(expected[key],rel=1e-4,abs=1e-6)
    # Independent circuit table and trapezoid-free dense Simpson integration.
    table = {1:(1,0,0,0), 0:(0,0,-1,1), -1:(0,-1,0,0)}
    for index,phase in enumerate(("a","b","c")):
        totals = {role: {path:[0.,0.,0.] for path in ("signed","channel","diode")} for role in ("QP","QN","QA","QO")}
        angle = (0,-2*math.pi/3,2*math.pi/3)[index]
        omega = 2*math.pi*basis["f_line_hz"]
        peak = math.sqrt(2/3)*basis["vac_ll_rms_v"]
        for segment in payload["segments"]:
            left,right = segment["start_time_s"],segment["end_time_s"]
            times = np.linspace(left,right,129)
            current = segment["start_currents_a"][index] + (segment["phase_neutral_voltages_v"][index]*(times-left)+peak/omega*(np.cos(omega*times+angle)-math.cos(omega*left+angle)))/basis["inductance_h"]
            for role,sign in zip(totals,table[segment["states"][index]]):
                signed = sign*current
                for path,values in (("signed",signed),("channel",np.maximum(signed,0)),("diode",np.maximum(-signed,0))):
                    total=totals[role][path]
                    total[0]+=simpson(values,x=times)
                    total[1]+=simpson(values**2,x=times)
                    total[2]=max(total[2],float(max(abs(values))))
        for role,paths in totals.items():
            record=expected[f"{phase}_{role}"]
            for path,(area,square,peak_a) in paths.items():
                assert record[f"{path}_avg_a"] == pytest.approx(area/.02,rel=1e-4,abs=1e-6)
                assert record[f"{path}_rms_a"] == pytest.approx(math.sqrt(square/.02),rel=1e-4,abs=1e-6)
                assert record[f"{path}_peak_a"] == pytest.approx(peak_a,rel=1e-4,abs=1e-6)
            assert record["signed_avg_a"] == pytest.approx(record["channel_avg_a"]-record["diode_avg_a"],abs=1e-8)
            assert record["signed_rms_a"]**2 == pytest.approx(record["channel_rms_a"]**2+record["diode_rms_a"]**2,abs=1e-8)


@pytest.mark.parametrize("kind, message",[("missing_position","positions"),("nonfinite","nonfinite"),("periodic","solver"),("basis","basis"),("segment","formula"),("stress","stress"),("gates","gates"),("statistics","statistics")])
def test_invalid_actual_waveform_never_falls_back(actual,kind,message):
    waveform=copy.deepcopy(actual.waveform)
    payload=waveform.metadata[PAYLOAD_KEY]
    if kind=="missing_position": del payload["positions"]["c_QO"]
    elif kind=="nonfinite": payload["segments"][0]["end_currents_a"]= [float("nan"),0.,0.]
    elif kind=="periodic": payload["diagnostics"]["periodic_solver"]["converged"]=False
    elif kind=="basis": payload["basis"]["inductance_h"]*=2
    elif kind=="segment": payload["segments"][0]["end_currents_a"]= [1.,-1.,0.]
    elif kind=="gates": payload["phases"]["a"]["gates"]["QP"][0]=1
    elif kind=="statistics": payload["diagnostics"]["phase_statistics"]["a"]["rms_a"]=0.
    else: del payload["stress"]
    with pytest.raises(ValueError,match=message): PLUGIN.extract_stress(actual.candidate,waveform)


def test_operating_refresh_keeps_candidate_and_old_waveform_and_report_checks_request(actual):
    candidate=actual.candidate
    saved=copy.deepcopy(dataclasses.asdict(candidate))
    old=copy.deepcopy(dataclasses.asdict(actual.waveform))
    op=OperatingPoint(vin_v=800,load_ratio=.5,power_factor=.8)
    waveform=PLUGIN.generate_waveforms(candidate,op)
    stress=PLUGIN.extract_stress(candidate,waveform)
    assert stress.switch.voltage_max_v==800
    assert stress_readback(candidate,waveform)["midpoint"]["voltage_max_v"]==400
    report=PLUGIN.build_report(actual.spec,candidate,op,waveform,stress)
    assert report.operating_point==op
    assert report.waveform.metadata[PAYLOAD_KEY]["basis"]["pout_w"]==5000
    assert dataclasses.asdict(candidate)==saved
    assert dataclasses.asdict(actual.waveform)==old
    with pytest.raises(ValueError,match="requested operating"):
        PLUGIN.build_report(actual.spec,candidate,OperatingPoint(vin_v=700),waveform,stress)
    with pytest.raises(ValueError,match="stale"):
        PLUGIN.build_report(actual.spec,candidate,op,waveform,actual.report.stress)


def test_controlled_failure_pipeline_keeps_reason_and_run_ownership(tmp_path):
    with pytest.raises(ValueError,match="modulation command"):
        run_topology_pipeline(PLUGIN,{"vdc_nom":"500"},include_waveforms=True,output_root=tmp_path)
    manifest=json.loads((tmp_path/"manifest.json").read_text())
    assert manifest["run"]["topology_id"]==PLUGIN.topology_id
    assert manifest["stage_status"]["design"]=="failed"
    assert "modulation command" in manifest["failure"]["reason"]
    assert manifest["run"]["run_id"]


def test_npc_t_type_order_repeat_isolation(actual, tmp_path):
    from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter import PLUGIN as npc
    reference = copy.deepcopy(dataclasses.asdict(actual.waveform))
    candidate_snapshot = copy.deepcopy(dataclasses.asdict(actual.candidate))
    npc_spec = npc.build_spec({})
    npc_candidate = npc.synthesize(npc_spec)
    first = npc.generate_waveforms(npc_candidate)
    first_snapshot = copy.deepcopy(dataclasses.asdict(first))
    # NPC -> T-type -> NPC -> T-type, each run owns fresh arrays and directories.
    a = run_topology_pipeline(PLUGIN, {}, include_waveforms=True, output_root=tmp_path/"a")
    second = npc.generate_waveforms(npc_candidate)
    b = run_topology_pipeline(PLUGIN, {}, include_waveforms=True, output_root=tmp_path/"b")
    assert dataclasses.asdict(first) == first_snapshot == dataclasses.asdict(second)
    assert dataclasses.asdict(a.waveform) == reference == dataclasses.asdict(b.waveform)
    assert dataclasses.asdict(actual.candidate) == candidate_snapshot
    assert a.report.run_context.run_id != b.report.run_context.run_id
    assert a.report.run_context.output_root != b.report.run_context.output_root
    a.waveform.metadata[PAYLOAD_KEY]["stress"]["positions"]["a_QP"]["channel_peak_a"] = -1
    assert dataclasses.asdict(b.waveform) == reference


@pytest.mark.parametrize("phase,load,bus", [("lagging",0,700),("lagging",.1,700),("lagging",1,700),("leading",1,700),("lagging",.5,800)])
def test_all_supported_operating_cases_have_complete_stress(phase,load,bus):
    candidate = PLUGIN.synthesize(PLUGIN.build_spec({"power_factor":"0.8","power_factor_phase":phase}))
    wave = PLUGIN.generate_waveforms(candidate,OperatingPoint(vin_v=bus,load_ratio=load))
    stress = PLUGIN.extract_stress(candidate,wave)
    assert stress.switch.voltage_max_v == bus
    assert math.isfinite(stress.switch.current_rms_a)
    assert math.isfinite(stress.rectifier.current_avg_a)
    assert len(wave.metadata[PAYLOAD_KEY]["stress"]["positions"]) == 12


def test_npc_empty_solver_retains_four_empty_gates():
    from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter.waveform import _simulate_npc_event_segmented_currents
    result = _simulate_npc_event_segmented_currents(time_s=[],phase_grid_voltage_v=([],[],[]),phase_current_reference_a=([],[],[]),phase_current_reference_average_a={"a":[],"b":[],"c":[]},inductance_h=.001,grid_voltage_peak_v=326,line_frequency_hz=50,half_bus_voltage_v=350,samples_per_switching_period=8)
    assert result["gates"] == {phase:([],[],[],[]) for phase in "abc"}
