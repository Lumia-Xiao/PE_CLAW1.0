"""LLC synchronous-rectifier FHA form."""

from __future__ import annotations

from ...libraries.semiconductors.metadata import (
    ANY_ACTIVE_SWITCH_CATEGORY,
    DIODE_BINDING_POLICY_INPUT_KEY,
    DIODE_RECTIFIED_MAIN_SWITCH_CATEGORY_OPTIONS,
    MAIN_SWITCH_CATEGORY_INPUT_KEY,
    PRIMARY_SWITCH_DEVICE_TYPE_INPUT_KEY,
    PRIMARY_SWITCH_MANUFACTURER_INPUT_KEY,
    SEMICONDUCTOR_DEVICE_TYPE_INPUT_KEY,
    SEMICONDUCTOR_MANUFACTURER_INPUT_KEY,
    SEMICONDUCTOR_MANUFACTURER_OPTIONS,
    SYNCHRONOUS_SWITCH_CATEGORY_OPTIONS,
    SYNC_SWITCH_CATEGORY_INPUT_KEY,
)
from ...topologies.dc_dc.llc_resonant_converter_synchronous_rectifier.input_schema import (
    SECONDARY_SYNC_SWITCH_DEVICE_TYPE_INPUT_KEY,
    SECONDARY_SYNC_SWITCH_MANUFACTURER_INPUT_KEY,
    SYNCHRONOUS_RECTIFIER_TIMING_MODE_INPUT_KEY,
)
from .base_form import TopologyField
from .llc_resonant_converter_diode_rectifier_form import LLCResonantConverterDiodeRectifierForm


class LLCResonantConverterSynchronousRectifierForm(LLCResonantConverterDiodeRectifierForm):
    """Input form for first-pass FHA-based LLC synchronous-rectifier design."""

    topology_id = "llc_resonant_converter_synchronous_rectifier"
    display_name = "LLC Resonant Converter Synchronous Rectifier"
    design_fields = (
        *LLCResonantConverterDiodeRectifierForm.design_fields[:-1],
        TopologyField(
            "secondary_rectifier_type",
            "Secondary rectifier type",
            "full_bridge_synchronous_rectifier",
            ("full_bridge_synchronous_rectifier",),
        ),
    )
    semiconductor_filter_fields = (
        TopologyField(
            PRIMARY_SWITCH_DEVICE_TYPE_INPUT_KEY,
            "Primary switch type",
            ANY_ACTIVE_SWITCH_CATEGORY,
            DIODE_RECTIFIED_MAIN_SWITCH_CATEGORY_OPTIONS,
        ),
        TopologyField(
            PRIMARY_SWITCH_MANUFACTURER_INPUT_KEY,
            "Primary switch manufacturer",
            "Any",
            SEMICONDUCTOR_MANUFACTURER_OPTIONS,
        ),
        TopologyField(
            SECONDARY_SYNC_SWITCH_DEVICE_TYPE_INPUT_KEY,
            "Secondary sync switch type",
            ANY_ACTIVE_SWITCH_CATEGORY,
            SYNCHRONOUS_SWITCH_CATEGORY_OPTIONS,
        ),
        TopologyField(
            SECONDARY_SYNC_SWITCH_MANUFACTURER_INPUT_KEY,
            "Secondary sync switch manufacturer",
            "Any",
            SEMICONDUCTOR_MANUFACTURER_OPTIONS,
        ),
    )

    def get_raw_input(self) -> dict[str, str]:
        raw_input = {key: var.get() for key, var in self.design_vars.items()}
        primary_type = raw_input.get(PRIMARY_SWITCH_DEVICE_TYPE_INPUT_KEY, ANY_ACTIVE_SWITCH_CATEGORY)
        sync_type = raw_input.get(SECONDARY_SYNC_SWITCH_DEVICE_TYPE_INPUT_KEY, ANY_ACTIVE_SWITCH_CATEGORY)
        raw_input["secondary_rectifier_type"] = "full_bridge_synchronous_rectifier"
        raw_input[SYNCHRONOUS_RECTIFIER_TIMING_MODE_INPUT_KEY] = "ideal_complementary_first_pass"
        raw_input[SYNC_SWITCH_CATEGORY_INPUT_KEY] = sync_type
        raw_input[MAIN_SWITCH_CATEGORY_INPUT_KEY] = primary_type
        raw_input.setdefault(SEMICONDUCTOR_DEVICE_TYPE_INPUT_KEY, "Any")
        raw_input.setdefault(SEMICONDUCTOR_MANUFACTURER_INPUT_KEY, "Any")
        raw_input[DIODE_BINDING_POLICY_INPUT_KEY] = "independent"
        return raw_input


__all__ = ["LLCResonantConverterSynchronousRectifierForm"]
