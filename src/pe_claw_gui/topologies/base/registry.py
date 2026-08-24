"""Registry used by the runtime GUI and controllers."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module

from .category import ConverterCategory
from .capabilities import TopologyCapability, get_topology_capability
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
        if definition.topology_id in self._definitions:
            raise ValueError(f"Duplicate topology id: {definition.topology_id}")
        for existing in self._definitions.values():
            if definition.legacy_key and existing.legacy_key == definition.legacy_key:
                raise ValueError(f"Duplicate topology legacy key: {definition.legacy_key}")
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

    def resolve_topology_id(self, topology_hint: str) -> str:
        """Resolve an explicit topology ID or legacy key without a default fallback."""
        token = str(topology_hint or "").strip()
        if token in self._definitions:
            return token
        folded = token.casefold()
        for definition in self._definitions.values():
            if definition.legacy_key and definition.legacy_key.casefold() == folded:
                return definition.topology_id
        raise ValueError(f"Unsupported topology: {topology_hint}")

    def get_capability(self, topology_id: str) -> TopologyCapability:
        """Return the capability declaration for a registered topology."""
        self.get_definition(topology_id)
        return get_topology_capability(topology_id)

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
    ac_dc_category = CONVERTER_CATEGORY_BY_ID["ac_dc"]
    registry.register(
        TopologyDefinition(
            category_id=ac_dc_category.category_id,
            category_display_name=ac_dc_category.display_name,
            topology_id="single_phase_diode_bridge_rectifier_capacitor_filter",
            display_name="Single-Phase Diode Bridge Rectifier Capacitor Filter",
            module_path="pe_claw_gui.topologies.ac_dc.single_phase_diode_bridge_rectifier_capacitor_filter",
            form_path="pe_claw_gui.app.topology_forms.single_phase_diode_bridge_rectifier_capacitor_filter_form",
            form_class="SinglePhaseDiodeBridgeRectifierCapacitorFilterForm",
            implemented=True,
            legacy_key="SinglePhase_DiodeBridgeRectifier_CapacitorFilter",
        )
    )
    registry.register(
        TopologyDefinition(
            category_id=ac_dc_category.category_id,
            category_display_name=ac_dc_category.display_name,
            topology_id="single_phase_diode_bridge_rectifier_dc_inductor_filter",
            display_name="Single-Phase Diode Bridge Rectifier with DC-Side Inductor",
            module_path="pe_claw_gui.topologies.ac_dc.single_phase_diode_bridge_rectifier_dc_inductor_filter",
            form_path="pe_claw_gui.app.topology_forms.single_phase_diode_bridge_rectifier_dc_inductor_filter_form",
            form_class="SinglePhaseDiodeBridgeRectifierDCInductorFilterForm",
            implemented=True,
            legacy_key="SinglePhase_DiodeBridgeRectifier_DCInductorFilter",
        )
    )
    registry.register(
        TopologyDefinition(
            category_id=ac_dc_category.category_id,
            category_display_name=ac_dc_category.display_name,
            topology_id="three_phase_diode_bridge_rectifier_capacitor_filter",
            display_name="Three-Phase Diode Bridge Rectifier Capacitor Filter",
            module_path="pe_claw_gui.topologies.ac_dc.three_phase_diode_bridge_rectifier_capacitor_filter",
            form_path="pe_claw_gui.app.topology_forms.three_phase_diode_bridge_rectifier_capacitor_filter_form",
            form_class="ThreePhaseDiodeBridgeRectifierCapacitorFilterForm",
            implemented=True,
            legacy_key="ThreePhase_DiodeBridgeRectifier_CapacitorFilter",
        )
    )
    registry.register(
        TopologyDefinition(
            category_id=ac_dc_category.category_id,
            category_display_name=ac_dc_category.display_name,
            topology_id="single_phase_boost_pfc_diode_bridge",
            display_name="Single-Phase Boost PFC Diode Bridge",
            module_path="pe_claw_gui.topologies.ac_dc.single_phase_boost_pfc_diode_bridge",
            form_path="pe_claw_gui.app.topology_forms.single_phase_boost_pfc_diode_bridge_form",
            form_class="SinglePhaseBoostPFCDiodeBridgeForm",
            implemented=True,
            legacy_key="SinglePhase_BoostPFC_DiodeBridge_FirstPass",
        )
    )
    registry.register(
        TopologyDefinition(
            category_id=ac_dc_category.category_id,
            category_display_name=ac_dc_category.display_name,
            topology_id="single_phase_totem_pole_bridgeless_pfc",
            display_name="Single-Phase Totem-Pole Bridgeless PFC",
            module_path="pe_claw_gui.topologies.ac_dc.single_phase_totem_pole_bridgeless_pfc",
            form_path="pe_claw_gui.app.topology_forms.single_phase_totem_pole_bridgeless_pfc_form",
            form_class="SinglePhaseTotemPoleBridgelessPFCForm",
            implemented=True,
            legacy_key="SinglePhase_TotemPole_BridgelessPFC_FirstPass",
        )
    )
    dc_ac_category = CONVERTER_CATEGORY_BY_ID["dc_ac"]
    registry.register(
        TopologyDefinition(
            category_id=dc_ac_category.category_id,
            category_display_name=dc_ac_category.display_name,
            topology_id="single_phase_full_bridge_inverter",
            display_name="Single-Phase Full-Bridge Inverter",
            module_path="pe_claw_gui.topologies.dc_ac.single_phase_full_bridge_inverter",
            form_path="pe_claw_gui.app.topology_forms.single_phase_full_bridge_inverter_form",
            form_class="SinglePhaseFullBridgeInverterForm",
            implemented=True,
            legacy_key="SinglePhase_FullBridge_Inverter",
        )
    )
    registry.register(
        TopologyDefinition(
            category_id=dc_ac_category.category_id,
            category_display_name=dc_ac_category.display_name,
            topology_id="three_phase_two_level_voltage_source_inverter",
            display_name="Three-Phase Two-Level Voltage-Source Inverter",
            module_path="pe_claw_gui.topologies.dc_ac.three_phase_two_level_voltage_source_inverter",
            form_path="pe_claw_gui.app.topology_forms.three_phase_two_level_voltage_source_inverter_form",
            form_class="ThreePhaseTwoLevelVoltageSourceInverterForm",
            implemented=True,
            legacy_key="ThreePhase_TwoLevel_VoltageSource_Inverter",
        )
    )
    registry.register(
        TopologyDefinition(
            category_id=dc_ac_category.category_id,
            category_display_name=dc_ac_category.display_name,
            topology_id="three_phase_three_level_npc_inverter",
            display_name="Three-Phase Three-Level NPC Inverter",
            module_path="pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter",
            form_path="pe_claw_gui.app.topology_forms.three_phase_three_level_npc_inverter_form",
            form_class="ThreePhaseThreeLevelNPCInverterForm",
            implemented=True,
            legacy_key="ThreePhase_ThreeLevel_NPC_Inverter",
        )
    )
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
    registry.register(
        TopologyDefinition(
            category_id=dc_dc_category.category_id,
            category_display_name=dc_dc_category.display_name,
            topology_id="llc_resonant_converter_diode_rectifier",
            display_name="LLC Resonant Converter Diode Rectifier",
            module_path="pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier",
            form_path="pe_claw_gui.app.topology_forms.llc_resonant_converter_diode_rectifier_form",
            form_class="LLCResonantConverterDiodeRectifierForm",
            implemented=True,
            legacy_key="LLC_ResonantConverter_DiodeRectifier_Placeholder",
        )
    )
    registry.register(
        TopologyDefinition(
            category_id=dc_dc_category.category_id,
            category_display_name=dc_dc_category.display_name,
            topology_id="llc_resonant_converter_synchronous_rectifier",
            display_name="LLC Resonant Converter Synchronous Rectifier",
            module_path="pe_claw_gui.topologies.dc_dc.llc_resonant_converter_synchronous_rectifier",
            form_path="pe_claw_gui.app.topology_forms.llc_resonant_converter_synchronous_rectifier_form",
            form_class="LLCResonantConverterSynchronousRectifierForm",
            implemented=True,
            legacy_key="LLC_ResonantConverter_SynchronousRectifier_Placeholder",
        )
    )
    registry.register(
        TopologyDefinition(
            category_id=dc_dc_category.category_id,
            category_display_name=dc_dc_category.display_name,
            topology_id="flyback_diode_rectified_isolated",
            display_name="Flyback Diode Rectified Isolated",
            module_path="pe_claw_gui.topologies.dc_dc.flyback_diode_rectified_isolated",
            form_path="pe_claw_gui.app.topology_forms.flyback_diode_rectified_isolated_form",
            form_class="FlybackDiodeRectifiedIsolatedForm",
            implemented=True,
            legacy_key="Flyback_DiodeRectified_Isolated_FirstPass",
        )
    )
    registry.register(
        TopologyDefinition(
            category_id=dc_dc_category.category_id,
            category_display_name=dc_dc_category.display_name,
            topology_id="phase_shifted_full_bridge_diode_rectifier_isolated",
            display_name="Phase-Shifted Full-Bridge Diode Rectifier Isolated",
            module_path="pe_claw_gui.topologies.dc_dc.phase_shifted_full_bridge_diode_rectifier_isolated",
            form_path="pe_claw_gui.app.topology_forms.psfb_form",
            form_class="PSFBTopologyForm",
            implemented=True,
            legacy_key="PhaseShiftedFullBridge_DiodeRectifier_Isolated_FirstPass",
        )
    )
    return registry
