"""Registry used by the runtime GUI and controllers."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module

from .category import ConverterCategory
from .interface import TopologyPlugin
from .metadata import CONVERTER_CATEGORY_BY_ID, list_converter_categories


@dataclass(frozen=True)
class TopologyDefinition:
    """One topology option exposed to the GUI."""

    category_id: str
    category_display_name: str
    topology_id: str
    display_name: str
    module_path: str
    form_path: str | None = None
    form_class: str | None = None
    implemented: bool = False
    legacy_key: str | None = None


class TopologyRegistry:
    """Lookup and cache topology plugins and their form classes."""

    def __init__(self) -> None:
        self._categories: dict[str, ConverterCategory] = {
            category.category_id: category for category in list_converter_categories()
        }
        self._definitions: dict[str, TopologyDefinition] = {}
        self._plugin_cache: dict[str, TopologyPlugin] = {}
        self._form_cache: dict[str, type] = {}

    def register(self, definition: TopologyDefinition) -> None:
        """Register a topology definition."""
        if definition.category_id not in self._categories:
            raise ValueError(f"Unsupported converter category: {definition.category_id}")
        self._definitions[definition.topology_id] = definition

    def list_categories(self) -> list[ConverterCategory]:
        """Return supported top-level converter categories."""
        return list(self._categories.values())

    def get_category(self, category_id: str) -> ConverterCategory:
        """Return the registered converter category."""
        try:
            return self._categories[category_id]
        except KeyError as exc:
            raise ValueError(f"Unsupported converter category: {category_id}") from exc

    def list_definitions(self, category_id: str | None = None) -> list[TopologyDefinition]:
        """Return registered topology definitions, optionally filtered by category."""
        definitions = list(self._definitions.values())
        if category_id is not None:
            definitions = [definition for definition in definitions if definition.category_id == category_id]
        return definitions

    def list_topologies(self, category_id: str) -> list[TopologyDefinition]:
        """Return topology definitions for a selected converter category."""
        self.get_category(category_id)
        return self.list_definitions(category_id=category_id)

    def get_definition(self, topology_id: str) -> TopologyDefinition:
        """Return the registered definition for a topology id."""
        try:
            return self._definitions[topology_id]
        except KeyError as exc:
            raise ValueError(f"Unsupported topology: {topology_id}") from exc

    def get_plugin(self, topology_id: str) -> TopologyPlugin:
        """Load and cache the plugin instance for a topology."""
        if topology_id not in self._plugin_cache:
            definition = self.get_definition(topology_id)
            module = import_module(definition.module_path)
            self._plugin_cache[topology_id] = getattr(module, "PLUGIN")
        return self._plugin_cache[topology_id]

    def get_form_class(self, topology_id: str) -> type:
        """Load and cache the form class for a topology."""
        if topology_id not in self._form_cache:
            definition = self.get_definition(topology_id)
            if definition.form_path is None or definition.form_class is None:
                raise ValueError(f"No form registered for topology: {topology_id}")
            module = import_module(definition.form_path)
            self._form_cache[topology_id] = getattr(module, definition.form_class)
        return self._form_cache[topology_id]


def build_default_registry() -> TopologyRegistry:
    """Create the runtime topology registry."""
    registry = TopologyRegistry()
    dc_dc_category = CONVERTER_CATEGORY_BY_ID["dc_dc"]
    registry.register(
        TopologyDefinition(
            category_id=dc_dc_category.category_id,
            category_display_name=dc_dc_category.display_name,
            topology_id="buck_diode_rectified_unidirectional",
            display_name="Buck Diode Rectified Unidirectional",
            module_path="pe_claw_gui.topologies.dc_dc.buck_diode_rectified_unidirectional",
            form_path="pe_claw_gui.app.topology_forms.buck_diode_rectified_unidirectional_form",
            form_class="BuckDiodeRectifiedUnidirectionalForm",
            implemented=True,
            legacy_key="Buck_CCM_DiodeRectified_Unidirectional",
        )
    )
    registry.register(
        TopologyDefinition(
            category_id=dc_dc_category.category_id,
            category_display_name=dc_dc_category.display_name,
            topology_id="buck_synchronous_rectified_unidirectional",
            display_name="Buck Synchronous Rectified Unidirectional",
            module_path="pe_claw_gui.topologies.dc_dc.buck_synchronous_rectified_unidirectional",
            form_path="pe_claw_gui.app.topology_forms.buck_synchronous_rectified_unidirectional_form",
            form_class="BuckSynchronousRectifiedUnidirectionalForm",
            implemented=True,
            legacy_key="Buck_SynchronousRectified_Unidirectional",
        )
    )
    registry.register(
        TopologyDefinition(
            category_id=dc_dc_category.category_id,
            category_display_name=dc_dc_category.display_name,
            topology_id="buck_boost_diode_rectified_unidirectional",
            display_name="Buck-Boost Diode Rectified Unidirectional",
            module_path="pe_claw_gui.topologies.dc_dc.buck_boost_diode_rectified_unidirectional",
            form_path="pe_claw_gui.app.topology_forms.buck_boost_diode_rectified_unidirectional_form",
            form_class="BuckBoostDiodeRectifiedUnidirectionalForm",
            implemented=True,
            legacy_key="BuckBoost_DiodeRectified_Unidirectional",
        )
    )
    registry.register(
        TopologyDefinition(
            category_id=dc_dc_category.category_id,
            category_display_name=dc_dc_category.display_name,
            topology_id="four_switch_buck_boost_simplified_four_mode",
            display_name="Four-Switch Buck-Boost Simplified Four-Mode",
            module_path="pe_claw_gui.topologies.dc_dc.four_switch_buck_boost_simplified_four_mode",
            form_path="pe_claw_gui.app.topology_forms.four_switch_buck_boost_simplified_four_mode_form",
            form_class="FourSwitchBuckBoostSimplifiedFourModeForm",
            implemented=True,
            legacy_key="FourSwitchBuckBoost_SimplifiedFourMode",
        )
    )
    registry.register(
        TopologyDefinition(
            category_id=dc_dc_category.category_id,
            category_display_name=dc_dc_category.display_name,
            topology_id="three_level_tzcm_fixed_frequency",
            display_name="Three-Level DC-DC TZCM Fixed Frequency",
            module_path="pe_claw_gui.topologies.dc_dc.three_level_tzcm_fixed_frequency",
            form_path="pe_claw_gui.app.topology_forms.three_level_tzcm_fixed_frequency_form",
            form_class="ThreeLevelTZCMFixedFrequencyForm",
            implemented=True,
            legacy_key="ThreeLevelTZCM_FixedFrequency",
        )
    )
    registry.register(
        TopologyDefinition(
            category_id=dc_dc_category.category_id,
            category_display_name=dc_dc_category.display_name,
            topology_id="boost_diode_rectified_unidirectional",
            display_name="Boost Diode Rectified Unidirectional",
            module_path="pe_claw_gui.topologies.dc_dc.boost_diode_rectified_unidirectional",
            form_path="pe_claw_gui.app.topology_forms.boost_diode_rectified_unidirectional_form",
            form_class="BoostDiodeRectifiedUnidirectionalForm",
            implemented=True,
            legacy_key="Boost_DiodeRectified_Unidirectional",
        )
    )
    registry.register(
        TopologyDefinition(
            category_id=dc_dc_category.category_id,
            category_display_name=dc_dc_category.display_name,
            topology_id="boost_synchronous_rectified_unidirectional",
            display_name="Boost Synchronous Rectified Unidirectional",
            module_path="pe_claw_gui.topologies.dc_dc.boost_synchronous_rectified_unidirectional",
            form_path="pe_claw_gui.app.topology_forms.boost_synchronous_rectified_unidirectional_form",
            form_class="BoostSynchronousRectifiedUnidirectionalForm",
            implemented=True,
            legacy_key="Boost_SynchronousRectified_Unidirectional",
        )
    )
    return registry
