"""Probe existing interfaces before the second-round adapter is implemented.

Selector callback tests prove routing/filter contracts, not actual T-type
selection or thermal acceptance. The operating grid exercises real first-pass
waveforms; the library probes use existing conduction tables only.
"""
from __future__ import annotations

from dataclasses import replace
import itertools
import json
import math
from pathlib import Path
import sys

import pytest

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "src"),
               str(Path(__file__).resolve().parents[1] / "scripts")]
from validate_t_type_engineering_step0 import encode, normalize
from pe_claw_gui.engines.devices import selector
from pe_claw_gui.libraries.semiconductors.registry import build_default_semiconductor_registry
from pe_claw_gui.libraries.semiconductors.igbt_discrete_models import RohmRGIGBTDevice
from pe_claw_gui.libraries.semiconductors.mitsubishi.igbt_modules import MitsubishiIGBTModule
from pe_claw_gui.libraries.semiconductors.topology_roles import get_semiconductor_roles_for_topology
from pe_claw_gui.models.device_loss import DeviceLossResult, SwitchStress
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import PLUGIN
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.paths_events import conduction_currents
from pe_claw_gui.topology_capabilities import is_first_pass_topology_only, has_semiconductor_selection_path, has_split_dc_link_capacitor_bank


@pytest.fixture(scope="module")
def devices():
    return build_default_semiconductor_registry().list_devices("IGBT")


def test_staged_integration_keeps_unimplemented_engineering_routes_protected():
    from pe_claw_gui.topology_capabilities import supports_engineering_stage
    assert not is_first_pass_topology_only(PLUGIN.topology_id)
    assert has_semiconductor_selection_path(PLUGIN.topology_id)
    assert has_split_dc_link_capacitor_bank(PLUGIN.topology_id)
    assert get_semiconductor_roles_for_topology(PLUGIN.topology_id) == ["t_type_main_switch","t_type_midpoint_switch"]
    assert not supports_engineering_stage(PLUGIN.topology_id,"system")


@pytest.mark.parametrize("state,current,expected", [
    (1, 7., (7., 0., 0., 0.)), (1, -7., (-7., 0., 0., 0.)),
    (0, 7., (0., 0., -7., 7.)), (0, -7., (0., 0., 7., -7.)),
    (-1, 7., (0., -7., 0., 0.)), (-1, -7., (0., 7., 0., 0.)),
])
def test_terminal_direction_and_diode_decomposition(state, current, expected):
    actual = conduction_currents(state, current)
    assert tuple(actual[p].signed_a for p in ("QP", "QN", "QA", "QO")) == expected
    for p in actual.values():
        assert p.signed_a == p.channel_a - p.diode_a
        assert p.channel_a * p.diode_a == 0


def test_library_conduction_interfaces_can_be_called_without_energy(devices, monkeypatch):
    def forbidden(*a, **kw):
        raise AssertionError("Energy/whole-loss evaluator must not be used for conduction-table probe")
    for cls in (RohmRGIGBTDevice, MitsubishiIGBTModule):
        for name in ("eon_mJ", "eoff_mJ", "err_mJ", "igbt_switching_loss_W"):
            monkeypatch.setattr(cls, name, forbidden)
    supported = unsupported = 0
    for device in devices:
        payload = device.payload
        if isinstance(payload, RohmRGIGBTDevice):
            if not payload.has_frd:
                unsupported += 1
                continue  # Existing frd_vf_V returns zero without a model: never treat that as physical zero.
            diode_drop = payload.frd_vf_V
        elif isinstance(payload, MitsubishiIGBTModule):
            assert payload.diode_loss_model is not None
            diode_drop = payload.vec_V
        else:
            pytest.fail(f"Unknown IGBT payload {type(payload).__name__}")
        for current, temperature in itertools.product((1., 5.), (25., 75.)):
            assert math.isfinite(payload.vce_sat_V(current, temperature))
            assert payload.vce_sat_V(current, temperature) > 0
            assert math.isfinite(diode_drop(current, temperature))
            assert diode_drop(current, temperature) > 0
        supported += 1
    assert supported > 0 and unsupported > 0


@pytest.mark.parametrize("thermal_feasible", [True, False])
def test_existing_selector_callback_bypasses_whole_energy_evaluation(devices, monkeypatch, thermal_feasible):
    candidate = next(d for d in devices if isinstance(d.payload, RohmRGIGBTDevice)
                     and d.payload.has_frd and d.static.vdss_max_V >= 1200)
    stress = SwitchStress("t_type_main_switch", "callback_contract_probe", 800., 2., 1.,
                          5., 5., 20000., .5, .5 / 20000., ambient_temp_C=25.)
    called = []
    def forbidden(*a, **kw):
        raise AssertionError("Default full-loss evaluator invoked")
    monkeypatch.setattr(selector, "evaluate_switch_loss", forbidden)
    def callback(device, supplied):
        called.append((device.part_number, supplied))
        # Controlled routing fixture; not a component loss or thermal acceptance model.
        return DeviceLossResult(device.part_number, supplied.role, supplied.mode,
                                1., 0., 0., 0., 0., 0., 1., 26.,
                                thermal_feasible=thermal_feasible, method="contract_fixture")
    selected, ranked, _, audit = selector.select_switch_device_with_audit([candidate], stress, loss_evaluator=callback)
    assert called == [(candidate.part_number, stress)]
    assert audit.considered_count == 1
    assert audit.traces[0].required_voltage_rating_V == 960
    assert (selected is not None) == thermal_feasible
    assert len(ranked) == int(thermal_feasible)
    if not thermal_feasible:
        assert any("thermal filter failed" in r for r in audit.traces[0].rejection_reasons)
    called.clear()
    _, _, _, rejected = selector.select_switch_device_with_audit(
        [candidate], replace(stress, v_block_V=1e6), loss_evaluator=callback)
    assert not called and rejected.passed_count == 0
    assert any("voltage filter failed" in r for r in rejected.traces[0].rejection_reasons)


def test_baseline_normalization_preserves_engineering_values_and_missing_data():
    payload = {"run_id": "r1", "created_at": "today", "hardware_id": "hw1",
               "source": "/a/run/curve.xml", "scope": "npc_full", "warning": "kept",
               "missing_loss": None, "loss_W": 7., "nonfinite": float("nan")}
    actual = normalize(encode(payload), (("/a/run", "$RUN_ROOT"),))
    assert actual == {"hardware_id": "hw1", "source": "$RUN_ROOT/curve.xml",
                      "scope": "npc_full", "warning": "kept", "missing_loss": None,
                      "loss_W": 7., "nonfinite": {"$nonfinite": "nan"}}
    json.dumps(actual, allow_nan=False)


@pytest.mark.parametrize("phase", ["lagging", "leading"])
def test_real_waveform_design_envelope_is_feasible_and_fixed(phase, tmp_path):
    candidate = PLUGIN.synthesize(PLUGIN.build_spec({"power_factor_phase": phase}))
    original = encode(candidate)
    cases = []
    for bus, load, pf in itertools.product((700., 800.), (.1, .5, 1.), (.8, 1.)):
        wave = PLUGIN.generate_waveforms(candidate, OperatingPoint(vin_v=bus, load_ratio=load, power_factor=pf))
        stress = PLUGIN.extract_stress(candidate, wave)
        payload = wave.metadata["three_phase_t_type_pd_spwm_waveforms"]
        positions = payload["stress"]["positions"]
        assert len(positions) == 12
        assert payload["basis"]["inductance_h"] == candidate.inductance_h
        assert payload["basis"]["power_factor_phase"] == phase
        assert payload["diagnostics"]["modulation_valid"]
        assert not payload["diagnostics"]["actual_command_saturated"]
        assert stress.switch.voltage_max_v == bus
        for key, position in positions.items():
            assert position["voltage_max_v"] == bus * (1 if key.endswith(("QP", "QN")) else .5)
        main = [k for k in positions if k.endswith(("QP", "QN"))]
        midpoint = [k for k in positions if k.endswith(("QA", "QO"))]
        assert len(main) == len(midpoint) == 6
        assert encode(candidate) == original
        cases.append({"bus_V": bus, "load": load, "pf_magnitude": pf, "phase": phase,
                      "L_H": candidate.inductance_h, "positions": positions,
                      "modulation": payload["diagnostics"]["modulation_index_command"]})
    (tmp_path / "envelope.json").write_text(json.dumps(cases, indent=2, allow_nan=False), encoding="utf-8")
