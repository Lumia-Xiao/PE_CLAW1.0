"""Public GUI metadata; never expose registry module paths to the browser."""

import re

from pe_claw_gui.topologies.base.registry import build_default_registry


_BRACKETED_UNIT = re.compile(r"\s*\[([^]]+)]\s*$")
_PAREN_UNIT = re.compile(r"\s*\((C)\)\s*$")


def _field_contract(field) -> dict:
    match = _BRACKETED_UNIT.search(field.label) or _PAREN_UNIT.search(field.label)
    unit = match.group(1) if match else ""
    label = field.label[:match.start()].strip() if match else field.label
    if field.choices:
        input_type = "select"
    else:
        try:
            float(field.default)
            input_type = "number"
        except ValueError:
            input_type = "text"
    return {
        "key": field.key,
        "label": label,
        "gui_label": field.label,
        "unit": unit,
        "default": field.default,
        "input_type": input_type,
        "required": field.default != "",
        "choices": list(field.choices),
        "exclusive_minimum": None,
    }


def _operating_point_contract(definition, form_class) -> dict:
    raw = {field.key: field.default for field in form_class.get_design_fields()}
    if 'vin_nom' in raw:
        vin_v = float(raw['vin_nom'])
    elif 'vdc_nom' in raw:
        vin_v = float(raw['vdc_nom'])
    elif 'vac_rms' in raw:
        vin_v = float(raw['vac_rms'])
    elif 'vll_rms' in raw:
        vin_v = float(raw['vll_rms'])
    elif 'vac_ll_rms' in raw:
        vin_v = float(raw['vac_ll_rms'])
    else:
        vin_v = (float(raw['vin_min']) + float(raw['vin_max'])) / 2
    defaults = {'vin_v': vin_v, 'load_ratio': 1.0}
    editable = ['load_ratio']
    if definition.category_id == 'dc_dc':
        editable.insert(0, 'vin_v')
    if definition.category_id == 'dc_ac':
        defaults['power_factor'] = float(raw.get('power_factor', '1.0'))
        editable.append('power_factor')
    if definition.topology_id.startswith('llc_resonant_converter_'):
        defaults['vout_v'] = float(raw['vout_nom'])
        editable.insert(1, 'vout_v')
    fields = {
        'vin_v': {'key': 'vin_v', 'label': 'Operating input voltage', 'unit': 'V', 'minimum': 0.0},
        'vout_v': {'key': 'vout_v', 'label': 'Operating output voltage', 'unit': 'V', 'minimum': 0.0},
        'load_ratio': {'key': 'load_ratio', 'label': 'Load ratio', 'unit': 'p.u.', 'minimum': 0.0},
        'power_factor': {'key': 'power_factor', 'label': 'Power factor', 'unit': '', 'minimum': -1.0, 'maximum': 1.0},
    }
    return {'defaults': defaults, 'fields': [fields[key] for key in editable]}


def topology_catalog() -> dict:
    registry = build_default_registry()
    return {
        "categories": [
            {"id": c.category_id, "name": c.display_name, "description": c.description}
            for c in registry.list_categories()
        ],
        "topologies": [
            {
                "id": d.topology_id,
                "name": d.display_name,
                "category_id": d.category_id,
                "web_enabled": d.implemented,
                "fields": [
                    _field_contract(field)
                    for field in registry.get_form_class(d.topology_id).get_design_fields()
                ],
                "operating_point": _operating_point_contract(
                    d, registry.get_form_class(d.topology_id)
                ),
            }
            for d in registry.list_definitions()
        ],
    }
