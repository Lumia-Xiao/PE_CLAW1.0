"""Reviewed post-10I reference; explicit generation, no historical overwrite.

The independent equations below do not call the production waveform sampler,
magnetic request builder or loss evaluator. They validate the current first-pass
model, not measured hardware or the validity of that model outside CCM.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import hashlib
from importlib import import_module
import json
from math import fsum, isclose, isfinite, pi, sin, sqrt
from pathlib import Path

from scripts.record_two_phase_interleaved_boost_pfc_step10a_baseline import CASE_INPUTS, TOPOLOGY_ID, _snapshot_case
from scripts.record_two_phase_interleaved_boost_pfc_step10g_baseline import _audit_snapshot
from scripts.record_two_phase_interleaved_boost_pfc_step10h_baseline import _presentation_snapshot, _normalize_paths
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
HISTORICAL = FIXTURES / "two_phase_interleaved_boost_pfc_step10h_baseline.json"
CURRENT = FIXTURES / "two_phase_interleaved_boost_pfc_current_reference_v1.json"
SCHEMA = "two_phase_interleaved_boost_pfc_post_10i_reference_v1"
TOLERANCE = {"absolute": 1e-9, "relative": 1e-9}


def close(field, expected, actual):
    assert actual is not None and isfinite(float(actual)), f"REFERENCE_FINITE: {field}: {actual}"
    assert isclose(float(actual), expected, abs_tol=1e-9, rel_tol=1e-9), (
        f"REFERENCE_FORMULA: {field}: expected={expected}, actual={actual}")


def independent_phase(case, hardware):
    raw = case["raw_input"]
    vin, vout, power, fs, pf = (float(raw[key]) for key in
                              ("vac_rms", "vdc_target_v", "pout_w", "fsw_hz", "power_factor_target"))
    inductance = case["candidate"]["inductance_h"]
    voltage = [sqrt(2)*vin*abs(sin(pi*n/180)) for n in range(361)]
    current = [sqrt(2)*power/(2*vin*pf)*abs(sin(pi*n/180)) for n in range(361)]
    duty = [max(0, min(1, 1-v/vout)) for v in voltage]
    ripple = [v*d/(inductance*fs) for v,d in zip(voltage,duty)]
    rms = sqrt(fsum(i*i+r*r/12 for i,r in zip(current,ripple))/361)
    # Match the documented scalar first-pass operating core excitation: the
    # positive maximum of v_rect - duty*Vout, not a line-average core model.
    on_voltage = [v-d*vout for v,d in zip(voltage,duty)]
    index = max(range(361), key=on_voltage.__getitem__)
    meta = hardware["metadata"]
    assert hardware["stack_count"] == 1, "REFERENCE_SCOPE: single-core reference required"
    assert meta.get("core_loss_model", "steinmetz_raw") == "steinmetz_raw", "REFERENCE_SCOPE: core loss model"
    ranges = [r for r in meta["steinmetz_ranges"]
              if r["minimumFrequency"] <= fs <= r["maximumFrequency"]]
    assert len(ranges) == 1, "REFERENCE_SCOPE: one in-range Steinmetz record required"
    coeff = ranges[0]
    assert coeff.get("input_flux_definition", "ac_peak_t") == "ac_peak_t", "REFERENCE_SCOPE: flux convention"
    assert not any(k in coeff for k in ("ct0", "ct1", "ct2")), "REFERENCE_SCOPE: temperature correction"
    beta = meta.get("core_loss_beta_raw", coeff["beta"])
    ae, ve = meta["core_effective_area_m2"], meta["core_effective_volume_m3"]
    bac = max(on_voltage[index],0)*duty[index]/(2*fs*ae*hardware["turns"])
    core = coeff["k"]*fs**coeff["alpha"]*bac**beta*ve
    skin = sqrt(1.724e-8/(pi*fs*(4*pi*1e-7)))
    multiplier = 1+(meta["strand_diameter_m"]/skin)**4/192*sqrt(meta["total_strands"])
    copper = rms*rms*hardware["rdc_25c_ohm"]*multiplier
    return dict(duty_mean=fsum(duty)/361, rms_a=rms, peak_a=max(i+r/2 for i,r in zip(current,ripple)),
                average_a=fsum(current)/361, delta_i_pp_a=max(ripple), flux_ac_peak_t=bac,
                copper_loss_w=copper, core_loss_w=core, total_loss_w=copper+core)


def validate_case(case):
    reference = case["engineering_reference"]
    phases = reference["hardware_inputs"]
    evaluations = reference["operating_evaluations"]
    assert len(phases) == len(evaluations) == 2, "REFERENCE_INSTANCES: two phases required"
    assert {p["metadata"]["physical_instance_id"] for p in phases} == {"phase_1", "phase_2"}, "REFERENCE_INSTANCES"
    assert len({p["candidate_id"] for p in phases}) == 2, "REFERENCE_INSTANCES: distinct IDs"
    expected_losses = []
    for phase, (hardware, evaluation) in enumerate(zip(phases, evaluations), 1):
        assert hardware["candidate_id"] == evaluation["design_id"], "REFERENCE_IDENTITY"
        expected = independent_phase(case, hardware)
        close("waveform.public.duty", expected["duty_mean"], case["waveform"]["public"]["duty"])
        for key in ("i_rms_a", "i_peak_a", "delta_il_pp_a", "copper_loss_w", "core_loss_w", "total_loss_w"):
            source = {"i_rms_a":"rms_a", "i_peak_a":"peak_a", "delta_il_pp_a":"delta_i_pp_a"}.get(key,key)
            close(f"phase_{phase}.{key}", expected[source], evaluation[key])
        close(f"phase_{phase}.published_loss", expected["total_loss_w"],
              case["loss"]["breakdown_w"][f"phase_{phase}_inductor_total_loss_w"])
        close(f"phase_{phase}.operating_vin", float(case["raw_input"]["vac_rms"]), evaluation["operating_vin_v"])
        close(f"phase_{phase}.frequency", float(case["raw_input"]["fsw_hz"]), evaluation["fs_hz"])
        expected_losses.append(expected)
    breakdown = case["loss"]["breakdown_w"]
    for key in ("copper_loss_w", "core_loss_w", "total_loss_w"):
        close("inductor_"+key, fsum(p[key] for p in expected_losses), breakdown["inductor_"+key])
    fields = ("bridge_rectifier_loss_w", "semiconductor_loss_w", "inductor_total_loss_w", "dc_link_capacitor_loss_w", "other_loss_w")
    for field in fields:
        assert isfinite(breakdown[field]) and breakdown[field] >= 0, f"REFERENCE_COMPONENT: {field}"
    close("system.total_loss_w", fsum(breakdown[f] for f in fields), case["loss"]["total_loss_w"])
    assert reference["basis"] == "design_boundary_bridge_and_semiconductor_current_waveform_magnetics", "REFERENCE_BASIS"
    validate_readback(case, expected_losses)
    return expected_losses


def validate_readback(case, expected_losses):
    """Check changed numeric consumers, including actual thermal CSV inputs."""
    presentation = case["presentation"]
    breakdown = case["loss"]["breakdown_w"]
    total = case["loss"]["total_loss_w"]
    lines = case["gui"]["loss_summary_lines"]
    power = float(case["raw_input"]["pout_w"])
    expected_lines = [f"  Total estimated loss: {total:.6g} W",
                      f"  Design-point estimated efficiency: {100*power/(power+total):.6g} %"]
    for label, key in (("Input bridge", "bridge_rectifier_loss_w"),
                       ("Four phase-position semiconductor devices", "semiconductor_loss_w"),
                       ("Both phase inductors", "inductor_total_loss_w"),
                       ("Shared DC-link capacitor bank", "dc_link_capacitor_loss_w"),
                       ("Other (not modeled)", "other_loss_w")):
        expected_lines.append(f"  {label}: {breakdown[key]:.6g} W")
    close("presentation.inductor_group", fsum(p["total_loss_w"] for p in expected_losses),
          presentation["inductor_group"]["loss_w"])
    for index, expected in enumerate(expected_losses):
        phase = index+1
        loss = expected["total_loss_w"]
        expected_lines.append(f"  Phase {phase} inductor: {loss:.6g} W")
        for field in ("phase_geometry", "integrated_objects"):
            entry = presentation[field][index if field == "phase_geometry" else phase]
            close(f"presentation.{field}.phase_{phase}", loss, entry["loss_w"])
        close(f"presentation.child.phase_{phase}", loss, presentation["inductor_group"]["children"][index]["loss_w"])
    assert all(line in lines for line in expected_lines), "REFERENCE_DISPLAY: loss/efficiency readback"
    assert f"  magnetic inductor loss: {breakdown['inductor_total_loss_w']:.6g} W" in presentation["inductor_text"], "REFERENCE_DISPLAY: inductor"
    rows = case["engineering_reference"]["thermal_rows"]
    assert len(rows) == 2, "REFERENCE_THERMAL: two exported rows required"
    for index, (row, expected) in enumerate(zip(rows, expected_losses, strict=True)):
        assert row["design_id"] == case["engineering_reference"]["hardware_inputs"][index]["candidate_id"], "REFERENCE_THERMAL: identity"
        assert row["loss_basis"] == "operating_point", "REFERENCE_THERMAL: basis"
        for key in ("core_loss_w", "copper_loss_w", "total_loss_w"):
            close(f"thermal.{key}", expected[key], row[key])
        ambient, rc, rw = (float(row[k]) for k in ("ambient_temp_c", "rth_core_to_ambient_k_per_w", "rth_winding_to_ambient_k_per_w"))
        shared = 0.15*expected["total_loss_w"]*sqrt(rc*rw)
        core_rise = expected["core_loss_w"]*rc+shared
        winding_rise = expected["copper_loss_w"]*rw+shared
        area_cm2 = float(row["total_surface_area_proxy_m2"])*1e4
        hotspot = ambient+max(core_rise, winding_rise, (expected["total_loss_w"]/max(area_cm2,0.1))**0.833)
        for key, value in (("estimated_core_temp_rise_c",core_rise), ("estimated_winding_temp_rise_c",winding_rise),
                           ("estimated_core_temp_c",ambient+core_rise), ("estimated_winding_temp_c",ambient+winding_rise),
                           ("hotspot_proxy_temp_c",hotspot)):
            close("thermal."+key, value, row[key])
        if row["design_id"] == case["thermal"]["recommended_design_id"]:
            assert f"hotspot proxy of {hotspot:.2f} C." in case["thermal"]["summary"], "REFERENCE_THERMAL: summary"


ALLOWED_PATHS = {
    "waveform.public.duty", "thermal.summary", "presentation.inductor_text",
    *{f"gui.loss_summary_lines[{n}]" for n in (3,4,9,10,11)},
    "loss.total_loss_w",
    *{f"loss.breakdown_w.{key}" for key in ("inductor_copper_loss_w", "inductor_core_loss_w", "inductor_total_loss_w",
                                           "phase_1_inductor_total_loss_w", "phase_2_inductor_total_loss_w")},
    "presentation.inductor_group.loss_w",
    *{f"presentation.inductor_group.children[{n}].loss_w" for n in (0,1)},
    *{f"presentation.integrated_objects[{n}].loss_w" for n in (1,2)},
    *{f"presentation.phase_geometry[{n}].loss_w" for n in (0,1)},
}


def historical_differences(source, target, path=""):
    """Reject every unexplained field, including field presence or array changes."""
    if isinstance(source, dict) and isinstance(target, dict):
        assert source.keys() == target.keys(), f"REFERENCE_HISTORY_KEYS: {path}"
        return [d for key in source for d in historical_differences(source[key], target[key], f"{path}.{key}".lstrip("."))]
    if isinstance(source, list) and isinstance(target, list):
        assert len(source) == len(target), f"REFERENCE_HISTORY_LENGTH: {path}"
        return [d for n,(s,t) in enumerate(zip(source,target)) for d in historical_differences(s,t,f"{path}[{n}]")]
    if source == target:
        return []
    assert path in ALLOWED_PATHS, f"REFERENCE_HISTORY_UNEXPLAINED: {path}: {source!r} -> {target!r}"
    try:
        error = abs(float(target)-float(source))
        relative = error/abs(float(source)) if float(source) else None
    except (TypeError,ValueError):
        error = relative = None
    return [dict(path=path, source=source, target=target, absolute_error=error, relative_error=relative,
                 tolerance=0, owner=path.split(".")[0], category="post_10i_semantics",
                 basis="same design inputs; current operating waveform replaces 10H fallback",
                 evidence_path=f"cases.{path}")]


def build_current_reference(output_root):
    root = Path(output_root).resolve()
    root.mkdir(parents=True, exist_ok=False)
    historical = json.loads(HISTORICAL.read_text(encoding="ascii"))
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    topology = import_module(plugin.__module__)
    options = PipelineOptions(enable_magnetic_design=True,enable_capacitor_design=True,enable_bridge_rectifier_selection=True)
    cases, transitions = [], []
    for (case_id,vac), old in zip(CASE_INPUTS.items(),historical["cases"],strict=True):
        print(f"Current reference: {case_id}",flush=True)
        run_root = root/case_id
        inputs = {**topology.build_default_inputs(), "vac_rms":vac}
        report = run_full_pipeline(plugin,inputs,include_waveforms=True,pipeline_options=options,output_root=run_root)
        case = _snapshot_case(case_id,inputs,report)
        case["frontier_search_audit"] = _audit_snapshot(report.magnetic.frontier_search_audit)
        case["presentation"] = _audit_snapshot(_normalize_paths(_presentation_snapshot(report,run_root/"hardware_overview"),run_root))
        differences = historical_differences(old,case)
        transitions.append(dict(case_id=case_id,differences=differences))
        case["engineering_reference"] = dict(
            basis="design_boundary_bridge_and_semiconductor_current_waveform_magnetics",
            hardware_inputs=[asdict(d) for d in report.magnetic.chosen_designs],
            operating_evaluations=[asdict(e) for e in report.magnetic.evaluations])
        with (run_root/"inductor_design"/"thermal_summary.csv").open(encoding="utf-8",newline="") as handle:
            case["engineering_reference"]["thermal_rows"] = list(csv.DictReader(handle))
        # Retain only inputs needed by this independent check, not runtime paths
        # or arbitrary candidate metadata. Frozen IDs remain in the normal snapshot.
        for item in case["engineering_reference"]["hardware_inputs"]:
            item["metadata"] = {k:item["metadata"][k] for k in (
                "physical_instance_id","core_loss_model","core_loss_beta_raw","core_effective_area_m2",
                "core_effective_volume_m3","steinmetz_ranges","strand_diameter_m","total_strands")}
            item["notes"] = []
        validate_case(case)
        cases.append(case)
        (run_root/"validated_reference_case.json").write_text(json.dumps(case,indent=2,allow_nan=False),encoding="utf-8")
    return dict(schema_version=SCHEMA,topology_id=TOPOLOGY_ID,
                scope=dict(source_production_revision="351d6277c8e6583b3a188578b9fef7cbcde470f9",
                           historical_file=HISTORICAL.name,historical_sha256=hashlib.sha256(HISTORICAL.read_bytes()).hexdigest(),
                           tolerances=TOLERANCE,snapshot_comparison="exact after existing 12-decimal/path normalization",
                           model="first-pass ideal-equal-sharing CCM; scalar Steinmetz core excitation",
                           system_basis="design boundary bridge/semiconductor; actual nominal/low/high phase magnetics; not sweep"),
                cases=cases,historical_transitions=transitions)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    parser.add_argument("--output-root",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        parser.error("Reference output must be new; historical/current files are never overwritten.")
    result=build_current_reference(args.output_root)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf-8") as handle:
        handle.write(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")


if __name__ == "__main__":
    main()
