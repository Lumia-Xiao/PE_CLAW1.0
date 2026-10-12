from __future__ import annotations

import itertools
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pe_claw_gui.topologies.base.interface import TopologyPlugin
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import (  # noqa: E402
    PLUGIN,
    TOPOLOGY_ID,
    build_default_inputs,
    build_spec,
)
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.topology_contract import (  # noqa: E402
    CONVENTIONAL_T_TYPE_CONTRACT,
)


def test_t_type_default_spec_has_frozen_identity_and_si_metadata() -> None:
    raw = build_default_inputs()
    spec = build_spec(raw)

    assert spec.topology_id == TOPOLOGY_ID
    assert spec.display_name == "Three-Phase Three-Level T-type Inverter"
    assert spec.vin_min == spec.vin_max == 700.0
    assert spec.vout == 400.0
    assert spec.pout == 10000.0
    assert spec.fs_khz == 20.0
    assert spec.ripple_current_ratio == 0.2
    assert spec.ripple_voltage_ratio_percent == 5.0
    assert spec.metadata["power_factor_phase"] == "lagging"
    assert spec.metadata["t_type_model_scope"].endswith("balanced_split_bus")
    assert spec.metadata["t_type_contract"]["switch_position_count"] == 12


def test_t_type_input_normalization_is_defaulted_and_unknown_keys_are_not_electrical_inputs() -> None:
    raw = {"vdc_nom": "800", "power_factor_phase": "LEADING", "ui_only": "ignored"}
    spec = build_spec(raw)

    assert spec.metadata["vdc_nom_v"] == 800.0
    assert spec.metadata["power_factor_phase"] == "leading"
    assert "ui_only" not in spec.metadata
    assert "ui_only" not in spec.raw_input
    assert spec.raw_input["fsw_hz"] == "20000"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("vdc_nom", "0", "positive"),
        ("vac_ll_rms", "nan", "finite"),
        ("f_line_hz", "-1", "positive"),
        ("fsw_hz", "20001", "integer multiple"),
        ("pout_w", "0", "positive"),
        ("power_factor", "0", "range"),
        ("power_factor", "-0.8", "range"),
        ("power_factor_phase", "quadrature", "lagging.*leading"),
        ("inductor_current_ripple_ratio", "2", "range"),
        ("dc_link_voltage_ripple_ratio", "1", "range"),
    ],
)
def test_t_type_invalid_input_is_rejected_with_field_diagnostic(field: str, value: str, message: str) -> None:
    raw = build_default_inputs()
    raw[field] = value

    with pytest.raises(ValueError, match=message) as error:
        build_spec(raw)
    assert field in str(error.value)


@pytest.mark.parametrize("field", tuple(key for key in build_default_inputs() if key != "power_factor_phase"))
@pytest.mark.parametrize("value", ["nan", "inf", "-inf", "invalid", ""])
def test_every_t_type_numeric_input_requires_a_finite_number(field: str, value: str) -> None:
    with pytest.raises(ValueError, match=field):
        build_spec({field: value})


@pytest.mark.parametrize(
    "override",
    [
        {"dead_time_ns": "200"},
        {"dead_time_ns": "nan"},
        {"modulation_method": "svpwm"},
        {"model_scope": "unbalanced_dynamic_bus"},
        {"fsw_hz": "1e308", "f_line_hz": "1e-308"},
        {"fsw_hz": "1e-308", "f_line_hz": "1e308"},
    ],
)
def test_t_type_rejects_unsupported_model_requests_and_invalid_frequency_ratio(override: dict[str, str]) -> None:
    with pytest.raises(ValueError, match="dead_time_ns|modulation_method|model_scope|fsw_hz"):
        build_spec(override)


def test_t_type_defaults_and_metadata_are_independent_between_calls() -> None:
    defaults = build_default_inputs()
    defaults["vdc_nom"] = "1"
    first = build_spec({})
    first.metadata["t_type_contract"]["gate_states"]["P"][0] = 0
    second = build_spec({})
    assert second.vin_min == 700
    assert second.metadata["t_type_contract"]["gate_states"]["P"] == [1, 0, 0, 1]
    assert CONVENTIONAL_T_TYPE_CONTRACT.gate_states["P"] == (1, 0, 0, 1)


def test_t_type_contract_has_three_states_twelve_positions_and_legal_gates() -> None:
    contract = CONVENTIONAL_T_TYPE_CONTRACT

    assert contract.phase_count == 3
    assert contract.level_count == 3
    assert contract.states == ("P", "O", "N")
    assert len(contract.switch_positions) == 12
    assert len({position.name for position in contract.switch_positions}) == 12
    assert contract.validate_gate_vector(contract.gate_states["P"])
    assert contract.validate_gate_vector(contract.gate_states["O"])
    assert contract.validate_gate_vector(contract.gate_states["N"])
    assert not contract.validate_gate_vector((1, 1, 1, 1))
    assert ("P", "N") in contract.forbidden_direct_transitions
    assert ("N", "P") in contract.forbidden_direct_transitions

    for gates in contract.gate_states.values():
        gp, gn, ga, go = gates
        assert gp * gn == gp * ga == gn * go == 0
    legal = {(1, 0, 0, 1), (0, 0, 1, 1), (0, 1, 1, 0)}
    for gates in itertools.product((0, 1), repeat=4):
        assert contract.validate_gate_vector(gates) == (gates in legal)


def test_t_type_physical_connections_and_groups_follow_common_emitter_circuit() -> None:
    contract = CONVENTIONAL_T_TYPE_CONTRACT
    positions = {position.name: position for position in contract.switch_positions}
    for phase in ("a", "b", "c"):
        expected = {"QP": ("P", phase), "QN": (phase, "N"), "QA": (phase, f"X{phase}"), "QO": ("O", f"X{phase}")}
        for role, terminals in expected.items():
            position = positions[f"{phase}_{role}"]
            assert position.terminals == terminals
            assert position.forward_current == "_to_".join(terminals)
            assert position.antiparallel_current == "_to_".join(reversed(terminals))
        assert positions[f"{phase}_QA"].terminals[1] == positions[f"{phase}_QO"].terminals[1]
    main = set(contract.role_position_labels["t_type_main_switch"])
    midpoint = set(contract.role_position_labels["t_type_midpoint_switch"])
    assert len(main) == len(midpoint) == 6
    assert main.isdisjoint(midpoint) and main | midpoint == set(positions)
    assert contract.to_dict()["independent_clamp_diode_count"] == 0


def test_t_type_plugin_is_isolated_from_registry_and_unimplemented_later_hooks_fail_closed() -> None:
    registry = build_default_registry()
    assert TOPOLOGY_ID not in {definition.topology_id for definition in registry.list_definitions()}
    assert PLUGIN.implemented is False
    assert isinstance(PLUGIN, TopologyPlugin)
    assert PLUGIN.legacy_key not in {definition.legacy_key for definition in registry.list_definitions()}
    assert PLUGIN.build_spec(build_default_inputs()).topology_id == TOPOLOGY_ID

    candidate = PLUGIN.synthesize(PLUGIN.build_spec(build_default_inputs()))
    assert candidate.topology_id == TOPOLOGY_ID
    assert candidate.inductance_h > 0.0

    waveform = PLUGIN.generate_waveforms(candidate)
    assert waveform is not None
    assert waveform.metadata["three_phase_t_type_pd_spwm_waveforms"]["schema_version"] == 1
    with pytest.raises(NotImplementedError, match="step 5"):
        PLUGIN.extract_stress(candidate)  # type: ignore[arg-type]
    with pytest.raises(NotImplementedError, match="step 5"):
        PLUGIN.evaluate(candidate)  # type: ignore[arg-type]
    with pytest.raises(NotImplementedError, match="step 5"):
        PLUGIN.build_report(PLUGIN.build_spec(build_default_inputs()), candidate)  # type: ignore[arg-type]


def test_t_type_import_and_contract_serialization_do_not_write_or_mutate_runtime_state(tmp_path: Path) -> None:
    # A fresh interpreter actually executes the import; cached re-imports cannot
    # establish import isolation. Audit all writes, including absolute paths.
    script = '''
import dataclasses, json, os, sys
sys.path.insert(0, sys.argv[1])
from pe_claw_gui.topologies.base.registry import build_default_registry
before = [dataclasses.asdict(d) for d in build_default_registry().list_definitions()]
before_pipeline = {name for name in sys.modules if name.startswith("pe_claw_gui.pipeline")}
def audit(event, args):
    if event == "open":
        mode, flags = args[1], args[2]
        if (mode and any(c in mode for c in "wax+")) or (flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)):
            raise AssertionError("Import attempted a filesystem write")
    if event in {"os.mkdir", "os.remove", "os.rmdir", "os.rename", "subprocess.Popen", "os.system"}:
        raise AssertionError("Import attempted a mutation or subprocess")
sys.addaudithook(audit)
import pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter as module
assert [dataclasses.asdict(d) for d in build_default_registry().list_definitions()] == before
assert not module.PLUGIN.implemented
assert {name for name in sys.modules if name.startswith("pe_claw_gui.pipeline")} == before_pipeline
payload = module.PLUGIN.build_spec({}).metadata["t_type_contract"]
print(json.dumps(payload, allow_nan=False))
'''
    result = subprocess.run(
        [sys.executable, "-B", "-c", script, str(ROOT / "src")],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["switch_position_count"] == 12
    assert list(tmp_path.iterdir()) == []
