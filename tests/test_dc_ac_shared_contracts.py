from __future__ import annotations

import tomllib
from importlib import import_module
from pathlib import Path

from pe_claw_gui.models import DesignReport, OperatingPoint, WaveformSet
from pe_claw_gui.topologies import TopologyCapability, build_default_registry, get_topology_capability
from pe_claw_gui.topologies.base.capabilities import PLUGIN_HOOKS


ROOT = Path(__file__).resolve().parents[1]
DC_AC_TOPOLOGY_IDS = (
    "single_phase_full_bridge_inverter",
    "three_phase_two_level_voltage_source_inverter",
    "three_phase_three_level_npc_inverter",
)


def test_dc_ac_capabilities_are_public_and_match_registry() -> None:
    registry = build_default_registry()
    definitions = {item.topology_id: item for item in registry.list_topologies("dc_ac")}

    assert set(definitions) == set(DC_AC_TOPOLOGY_IDS)
    assert all(isinstance(get_topology_capability(topology_id), TopologyCapability) for topology_id in definitions)
    assert {item.category_id for item in definitions.values()} == {"dc_ac"}

    for topology_id in DC_AC_TOPOLOGY_IDS:
        definition = definitions[topology_id]
        capability = registry.get_capability(topology_id)
        plugin = registry.get_plugin(topology_id)

        assert capability.topology_id == topology_id
        assert capability.category_id == definition.category_id
        assert capability.display_name
        assert "DC-AC" in capability.display_name
        assert capability.hooks == PLUGIN_HOOKS
        assert all(callable(getattr(plugin, hook)) for hook in capability.hooks)
        assert set(capability.required_fields) >= {"pout_w", "power_factor", "ambient_temp_c"}


def test_dc_ac_shared_models_preserve_waveform_and_operating_point_contract() -> None:
    operating_point = OperatingPoint(
        vin_v=700.0,
        load_ratio=0.75,
        vout_v=230.0,
        power_factor=0.95,
        switching_frequency_hz=20_000.0,
    )
    waveform = WaveformSet(
        time_s=[0.0, 1.0e-6],
        switch_node_voltage_v=[0.0, 700.0],
        inductor_current_a=[-1.0, 1.0],
        capacitor_current_a=[1.0, -1.0],
        output_voltage_v=[-230.0, 230.0],
        operating_vin_v=700.0,
        operating_vout_v=230.0,
        duty=0.5,
        load_ratio=0.75,
        switching_period_s=50.0e-6,
        time_span_s=50.0e-6,
        inductor_current_min_a=-1.0,
        inductor_current_max_a=1.0,
        gate_s1=[1.0, 0.0],
        gate_s2=[0.0, 1.0],
        metadata={"dc_ac_contract_test": True},
    )

    assert operating_point.power_factor == 0.95
    assert operating_point.switching_frequency_hz == 20_000.0
    assert waveform.metadata["dc_ac_contract_test"] is True
    plugin = build_default_registry().get_plugin(DC_AC_TOPOLOGY_IDS[0])
    module = import_module(plugin.__module__)
    report = DesignReport(
        spec=plugin.build_spec(module.build_default_inputs()),
        operating_point=operating_point,
        waveform=waveform,
    )
    assert report.waveform is waveform


def test_dc_ac_package_data_declares_topology_assets() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    patterns = set(pyproject["tool"]["setuptools"]["package-data"]["pe_claw_gui"])
    assert "app/assets/topologies/dc_ac/*.png" in patterns
    assets = ROOT / "src" / "pe_claw_gui" / "app" / "assets" / "topologies" / "dc_ac"
    assert sorted(path.stem for path in assets.glob("*.png")) == sorted(
        topology_id for topology_id in DC_AC_TOPOLOGY_IDS
    )
