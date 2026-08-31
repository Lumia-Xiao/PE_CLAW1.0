from __future__ import annotations

from pathlib import Path

from pe_claw_gui.app.category_views.dc_ac_page import _TOPOLOGY_HINTS
from pe_claw_gui.app.topology_card_assets import get_topology_image_resource, topology_image_filename
from pe_claw_gui.topologies.base.capabilities import PLUGIN_HOOKS
from pe_claw_gui.topologies.base.registry import build_default_registry


ROOT = Path(__file__).resolve().parents[1]
DC_AC_TOPOLOGY_IDS = (
    "single_phase_full_bridge_inverter",
    "three_phase_two_level_voltage_source_inverter",
    "three_phase_three_level_npc_inverter",
)


def test_dc_ac_registry_definitions_are_complete_and_unique() -> None:
    registry = build_default_registry()
    definitions = registry.list_topologies("dc_ac")

    assert [definition.topology_id for definition in definitions] == list(DC_AC_TOPOLOGY_IDS)
    assert all(definition.category_id == "dc_ac" for definition in definitions)
    assert all(definition.implemented for definition in definitions)
    assert len({definition.legacy_key for definition in definitions}) == len(definitions)

    for definition in definitions:
        plugin = registry.get_plugin(definition.topology_id)
        form_class = registry.get_form_class(definition.topology_id)

        assert plugin.topology_id == definition.topology_id
        assert plugin.display_name == definition.display_name
        assert plugin.implemented is True
        assert form_class.topology_id == definition.topology_id
        assert form_class.implemented is True
        assert all(callable(getattr(plugin, hook)) for hook in PLUGIN_HOOKS)
        assert definition.topology_id in _TOPOLOGY_HINTS


def test_dc_ac_card_resources_are_packaged_and_topology_specific() -> None:
    registry = build_default_registry()
    asset_root = ROOT / "src" / "pe_claw_gui" / "app" / "assets" / "topologies" / "dc_ac"

    for definition in registry.list_topologies("dc_ac"):
        resource = get_topology_image_resource(definition.topology_id)
        assert resource.is_file()
        assert resource.name == topology_image_filename(definition.topology_id)
        assert resource.name == f"{definition.topology_id}.png"
        assert (asset_root / resource.name).is_file()


def test_dc_ac_registry_and_card_paths_do_not_reference_source_workspace() -> None:
    source_workspace = "PE_Claw260517_1_extracted"
    target_paths = [
        ROOT / "src" / "pe_claw_gui" / "topologies" / "base" / "registry.py",
        ROOT / "src" / "pe_claw_gui" / "app" / "category_views" / "dc_ac_page.py",
        ROOT / "src" / "pe_claw_gui" / "app" / "topology_card_assets.py",
    ]

    assert all(source_workspace not in path.read_text(encoding="utf-8") for path in target_paths)
