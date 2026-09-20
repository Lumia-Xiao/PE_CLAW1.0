"""Public GUI metadata; never expose registry module paths to the browser."""

from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_dc.buck_diode_rectified_unidirectional.input_schema import (
    BUCK_TOPOLOGY_ID, build_default_inputs,
)
from pe_claw_web.schemas import BuckDesignRequest


def topology_catalog() -> dict:
    registry = build_default_registry()
    defaults = build_default_inputs()
    labels = {
        "vin_min": ("Vin min", "V"), "vin_max": ("Vin max", "V"),
        "vout": ("Vout", "V"), "pout": ("Pout", "W"),
        "fs_khz": ("Switching frequency", "kHz"),
        "ripple_current_ratio": ("Inductor ripple ratio ΔiL/Iout", "ratio"),
        "ripple_voltage_ratio_percent": ("Voltage ripple ratio", "%"),
    }
    properties = BuckDesignRequest.model_json_schema()["properties"]
    fields = [
        {"key": key, "label": label, "unit": unit, "default": defaults[key],
         "exclusive_minimum": properties[key].get("exclusiveMinimum")}
        for key, (label, unit) in labels.items()
    ]
    return {
        "categories": [
            {"id": c.category_id, "name": c.display_name, "description": c.description}
            for c in registry.list_categories()
        ],
        "topologies": [
            {"id": d.topology_id, "name": d.display_name, "category_id": d.category_id,
             "web_enabled": d.topology_id == BUCK_TOPOLOGY_ID,
             "fields": fields if d.topology_id == BUCK_TOPOLOGY_ID else []}
            for d in registry.list_definitions()
        ],
    }
