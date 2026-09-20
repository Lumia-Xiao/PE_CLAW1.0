"""Compare with the fixed remote DC-AC Completed revision, not moving HEAD."""

import ast
from dataclasses import asdict
import importlib
from pathlib import Path
import subprocess
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "646eb443dc7ad9cee927a7197a3e5a7967d0715b"


def baseline_source(path):
    return subprocess.check_output(
        ["git", "show", f"{BASELINE}:{path}"], cwd=ROOT, text=True, encoding="utf-8"
    )


def baseline_module(name):
    module = ModuleType(name)
    module.__package__ = name.rpartition(".")[0]
    path = "src/" + name.replace(".", "/") + ".py"
    exec(compile(baseline_source(path), path, "exec"), module.__dict__)
    return module


@pytest.mark.parametrize("path", [
    "src/pe_claw_gui/engines/devices/loss_evaluator.py",
    "src/pe_claw_gui/engines/devices/stress_adapter.py",
    "src/pe_claw_gui/topologies/dc_ac/three_phase_three_level_npc_inverter/waveform.py",
    "src/pe_claw_gui/topologies/dc_ac/three_phase_two_level_voltage_source_inverter/waveform.py",
])
def test_complete_event_modules_are_identical_to_remote(path):
    assert (ROOT / path).read_text(encoding="utf-8") == baseline_source(path)


@pytest.mark.parametrize(("path", "names"), [
    ("src/pe_claw_gui/pipeline/run_device_pipeline.py", [
        "_evaluate_switch_loss_for_context", "scale_switch_stress_for_parallel",
        "run_device_operating_point_refresh", "_apply_npc_event_switching_loss",
        "_apply_full_bridge_event_switching_loss", "_apply_vsi_event_switching_loss",
    ]),
    ("src/pe_claw_gui/engines/devices/stress_adapter.py", ["_build_three_phase_npc_inverter_stresses"]),
])
def test_event_call_chain_matches_remote(path, names):
    def functions(source):
        return {node.name: ast.dump(node) for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)}
    local = functions((ROOT / path).read_text(encoding="utf-8"))
    remote = functions(baseline_source(path))
    for name in names:
        assert local[name] == remote[name], name


def test_vendor_event_energy_and_base_temperature_match_remote():
    from pe_claw_gui.engines.devices import loss_evaluator as local
    from pe_claw_gui.libraries.semiconductors.registry import build_default_semiconductor_registry
    from pe_claw_gui.models.device_loss import SwitchStress

    remote = baseline_module(local.__name__)
    devices = build_default_semiconductor_registry().list_devices(device_type="MOSFET with Diode")
    by_vendor = {}
    for device in devices:
        by_vendor.setdefault(device.vendor, device)
    assert by_vendor
    for device in by_vendor.values():
        stress = SwitchStress(role="npc_outer_switch", mode="parity", v_block_V=350,
                              i_rms_A=8, i_avg_A=5, i_turn_on_A=10, i_turn_off_A=12,
                              fsw_Hz=20000, duty=0.5, conduction_time_s=25e-6)
        a, b = local.evaluate_switch_loss(device, stress), remote.evaluate_switch_loss(device, stress)
        assert asdict(a) == asdict(b)
        for current in (-10.0, 0.0, 5.0, 20.0):
            for edge in ("turn_on", "turn_off"):
                event = dict(event_type=edge, signed_current_A=current, blocking_voltage_V=350)
                for parallel in (1, 2):
                    kwargs = dict(junction_temp_c=a.tj_est_C, parallel_count=parallel)
                    assert local.evaluate_switching_event_energy(device, event, **kwargs) == remote.evaluate_switching_event_energy(device, event, **kwargs)


@pytest.mark.parametrize(("topology", "mode"), [
    ("three_phase_three_level_npc_inverter", "CCM"),
    ("three_phase_two_level_voltage_source_inverter", "CCM"),
    ("single_phase_full_bridge_inverter", "CCM"),
    ("single_phase_full_bridge_inverter", "TCM"),
])
@pytest.mark.parametrize("load", [0.1, 1.0])
def test_same_candidate_waveform_events_match_remote(topology, mode, load):
    from pe_claw_gui.models.operating_point import OperatingPoint
    from pe_claw_gui.topologies.base.registry import build_default_registry

    name = "pe_claw_gui.topologies.dc_ac." + topology
    topology_module = importlib.import_module(name)
    plugin = build_default_registry().get_plugin(topology)
    raw = topology_module.build_default_inputs()
    if mode == "TCM":
        raw.update(conduction_mode="TCM", fsw_min_hz="5000", fsw_max_hz="100000", tcm_valley_current_target_a="-1")
    candidate = plugin.synthesize(plugin.build_spec(raw))
    local = importlib.import_module(name + ".waveform")
    remote = baseline_module(local.__name__)
    point = OperatingPoint(vin_v=float(candidate.metadata["vdc_nom_v"]), load_ratio=load, power_factor=0.8)
    a, b = local.generate_waveforms(candidate, point), remote.generate_waveforms(candidate, point)
    assert a.time_s == b.time_s
    assert a.inductor_current_a == b.inductor_current_a
    if topology == "single_phase_full_bridge_inverter":
        key = "single_phase_inverter_tcm_envelope" if mode == "TCM" else "single_phase_inverter_refined_waveforms"
        assert a.metadata[key]["switching_events"] == b.metadata[key]["switching_events"]
    else:
        key = "three_phase_npc_switching_events" if "npc" in topology else "three_phase_vsi_switching_events"
        assert a.metadata[key] == b.metadata[key]
