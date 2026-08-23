"""Parser for the limited PLECS semiconductor XML schema used in PE-Claw."""

from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

from .lookup_table import LookupTable2D, LookupTable3D
from .models import DeviceDynamicModel, ThermalRcElement


_NS = {"plecs": "http://www.plexim.com/xml/semiconductors/"}


def _parse_axis_values(text: str | None) -> tuple[float, ...]:
    return tuple(float(token) for token in (text or "").split())


def _parse_scale(node: ET.Element | None) -> float:
    if node is None:
        return 1.0
    scale_text = node.attrib.get("scale")
    if scale_text is None:
        return 1.0
    return float(scale_text)


def _parse_table_3d(node: ET.Element, *, x_name: str, y_name: str, z_name: str, unit: str) -> LookupTable3D:
    name = node.findtext("plecs:Name", default="", namespaces=_NS)
    x_values = _parse_axis_values(node.findtext("plecs:XAxis", namespaces=_NS))
    y_values = _parse_axis_values(node.findtext("plecs:YAxis", namespaces=_NS))
    z_values = _parse_axis_values(node.findtext("plecs:ZAxis", namespaces=_NS))
    function_values = node.find("plecs:FunctionValues", _NS)
    if function_values is None:
        raise ValueError(f"Missing FunctionValues for 3D table {name}.")

    raw_values: list[list[list[float]]] = []
    for z_dimension in function_values.findall("plecs:ZDimension", _NS):
        y_rows = [_parse_axis_values(y_dimension.text) for y_dimension in z_dimension.findall("plecs:YDimension", _NS)]
        raw_values.append([list(row) for row in y_rows])

    raw_array = np.asarray(raw_values, dtype=float) * _parse_scale(function_values)
    if raw_array.shape != (len(z_values), len(y_values), len(x_values)):
        raise ValueError(f"Unexpected shape for 3D table {name}: {raw_array.shape}.")

    value_array = np.transpose(raw_array, (2, 1, 0))
    values = tuple(
        tuple(tuple(float(item) for item in yz_slice) for yz_slice in x_slice)
        for x_slice in value_array
    )
    return LookupTable3D(
        name=name,
        x_name=x_name,
        y_name=y_name,
        z_name=z_name,
        x_values=x_values,
        y_values=y_values,
        z_values=z_values,
        values=values,
        unit=unit,
    )


def _parse_table_2d(node: ET.Element, *, x_name: str, y_name: str, unit: str) -> LookupTable2D:
    name = node.findtext("plecs:Name", default="", namespaces=_NS)
    x_values = _parse_axis_values(node.findtext("plecs:XAxis", namespaces=_NS))
    y_values = _parse_axis_values(node.findtext("plecs:YAxis", namespaces=_NS))
    function_values = node.find("plecs:FunctionValues", _NS)
    if function_values is None:
        raise ValueError(f"Missing FunctionValues for 2D table {name}.")

    raw_rows = [_parse_axis_values(y_dimension.text) for y_dimension in function_values.findall("plecs:YDimension", _NS)]
    raw_array = np.asarray(raw_rows, dtype=float) * _parse_scale(function_values)
    if raw_array.shape != (len(y_values), len(x_values)):
        raise ValueError(f"Unexpected shape for 2D table {name}: {raw_array.shape}.")

    value_array = np.transpose(raw_array, (1, 0))
    values = tuple(tuple(float(item) for item in y_slice) for y_slice in value_array)
    return LookupTable2D(
        name=name,
        x_name=x_name,
        y_name=y_name,
        x_values=x_values,
        y_values=y_values,
        values=values,
        unit=unit,
    )


def _parse_optional_table_2d(
    table_by_name: dict[str, ET.Element],
    table_name: str,
    *,
    x_name: str,
    y_name: str,
    unit: str,
    notes: list[str],
) -> LookupTable2D | None:
    node = table_by_name.get(table_name)
    if node is None:
        return None
    try:
        return _parse_table_2d(node, x_name=x_name, y_name=y_name, unit=unit)
    except ValueError as exc:
        message = str(exc)
        if table_name == "Eoss" and "Unexpected shape for 2D table Eoss: (0,)" in message:
            notes.append("Eoss table is empty; static Coss fallback remains active.")
            return None
        raise


def _parse_turn_loss(node: ET.Element, name: str, notes: list[str] | None = None) -> LookupTable3D:
    current_axis = _parse_axis_values(node.findtext("plecs:CurrentAxis", namespaces=_NS))
    voltage_axis = _parse_axis_values(node.findtext("plecs:VoltageAxis", namespaces=_NS))
    temperature_axis = _parse_axis_values(node.findtext("plecs:TemperatureAxis", namespaces=_NS))
    energy_node = node.find("plecs:Energy", _NS)
    if energy_node is None:
        raise ValueError(f"Missing Energy block for {name}.")

    raw_values: list[list[list[float]]] = []
    for temperature in energy_node.findall("plecs:Temperature", _NS):
        voltage_rows = [_parse_axis_values(voltage.text) for voltage in temperature.findall("plecs:Voltage", _NS)]
        raw_values.append([list(row) for row in voltage_rows])

    temperature_axis, raw_values = _remove_adjacent_duplicate_temperature_planes(
        temperature_axis,
        raw_values,
        name,
        notes,
    )
    raw_array = np.asarray(raw_values, dtype=float) * _parse_scale(energy_node)
    if raw_array.shape != (len(temperature_axis), len(voltage_axis), len(current_axis)):
        raise ValueError(f"Unexpected shape for {name}: {raw_array.shape}.")

    value_array = np.transpose(raw_array, (2, 1, 0))
    values = tuple(
        tuple(tuple(float(item) for item in vz_slice) for vz_slice in i_slice)
        for i_slice in value_array
    )
    return LookupTable3D(
        name=name,
        x_name="current_A",
        y_name="voltage_V",
        z_name="temperature_C",
        x_values=current_axis,
        y_values=voltage_axis,
        z_values=temperature_axis,
        values=values,
        unit="J",
    )


def _remove_adjacent_duplicate_temperature_planes(
    temperature_axis: tuple[float, ...],
    raw_values: list[list[list[float]]],
    table_name: str,
    notes: list[str] | None,
) -> tuple[tuple[float, ...], list[list[list[float]]]]:
    if len(temperature_axis) != len(raw_values):
        return temperature_axis, raw_values

    keep_indices: list[int] = []
    removed_values: list[float] = []
    previous: float | None = None
    for index, value in enumerate(temperature_axis):
        if previous is not None and value == previous:
            removed_values.append(value)
            continue
        keep_indices.append(index)
        previous = value

    if not removed_values:
        return temperature_axis, raw_values

    repaired_axis = tuple(temperature_axis[index] for index in keep_indices)
    repaired_values = [raw_values[index] for index in keep_indices]
    if notes is not None:
        removed = ", ".join(f"{value:g}" for value in removed_values)
        notes.append(f"{table_name}: removed duplicate temperature-axis point(s) {removed} and corresponding data plane(s).")
    return repaired_axis, repaired_values


def _parse_conduction_loss(node: ET.Element, name: str) -> LookupTable2D:
    current_axis = _parse_axis_values(node.findtext("plecs:CurrentAxis", namespaces=_NS))
    temperature_axis = _parse_axis_values(node.findtext("plecs:TemperatureAxis", namespaces=_NS))
    voltage_drop_node = node.find("plecs:VoltageDrop", _NS)
    if voltage_drop_node is None:
        raise ValueError(f"Missing VoltageDrop block for {name}.")

    raw_rows = [_parse_axis_values(temperature.text) for temperature in voltage_drop_node.findall("plecs:Temperature", _NS)]
    raw_array = np.asarray(raw_rows, dtype=float) * _parse_scale(voltage_drop_node)
    if raw_array.shape != (len(temperature_axis), len(current_axis)):
        raise ValueError(f"Unexpected shape for {name}: {raw_array.shape}.")

    # Some vendor XMLs provide formula-only conduction models and use a single zero-valued
    # placeholder table while the real conduction behavior lives in vendor-specific lookup
    # formulas that are not part of the current PE-Claw runtime schema. Treat those sentinels
    # as unavailable so the existing static-record fallback path stays active.
    computation_method = (node.findtext("plecs:ComputationMethod", default="", namespaces=_NS) or "").strip().casefold()
    if (
        computation_method == "formula only"
        and raw_array.shape == (1, 1)
        and len(current_axis) == 1
        and len(temperature_axis) == 1
        and abs(float(current_axis[0])) < 1e-12
        and np.allclose(raw_array, 0.0)
    ):
        raise ValueError(f"{name}: formula-only placeholder table is not directly usable.")

    value_array = np.transpose(raw_array, (1, 0))
    values = tuple(tuple(float(item) for item in t_slice) for t_slice in value_array)
    return LookupTable2D(
        name=name,
        x_name="current_A",
        y_name="temperature_C",
        x_values=current_axis,
        y_values=temperature_axis,
        values=values,
        unit="V",
    )


def _parse_thermal_rc_network(package_node: ET.Element, semiconductor_data: ET.Element) -> tuple[ThermalRcElement, ...]:
    thermal_model = package_node.find("plecs:ThermalModel", _NS)
    if thermal_model is not None:
        branch = thermal_model.find("plecs:Branch", _NS)
        if branch is not None:
            return tuple(
                ThermalRcElement(
                    resistance_K_per_W=float(element.attrib["R"]),
                    capacitance_J_per_K=float(element.attrib["C"]),
                )
                for element in branch.findall("plecs:RCElement", _NS)
            )

    thermal_chain = semiconductor_data.find("plecs:ThermalChain", _NS)
    if thermal_chain is not None:
        return tuple(
            ThermalRcElement(
                resistance_K_per_W=float(element.attrib["R"]),
                capacitance_J_per_K=float(element.attrib["C"]),
            )
            for element in thermal_chain.findall("plecs:RCElement", _NS)
        )

    return ()


def _parse_optional_conduction_loss(
    conduction_by_gate: dict[str, ET.Element],
    gate: str,
    name: str,
    notes: list[str],
) -> LookupTable2D | None:
    node = conduction_by_gate.get(gate)
    if node is None:
        return None
    try:
        return _parse_conduction_loss(node, name)
    except ValueError as exc:
        if "formula-only placeholder table is not directly usable" not in str(exc):
            raise
        notes.append(f"{name}: vendor XML uses formula-only conduction data; static fallback remains active.")
        return None


def parse_plecs_xml(xml_path: str | Path) -> DeviceDynamicModel:
    """Parse the first-device PLECS XML format into reusable lookup tables."""

    xml_file = Path(xml_path)
    root = ET.parse(xml_file).getroot()
    package_node = root.find("plecs:Package", _NS)
    if package_node is None:
        raise ValueError(f"Package node not found in {xml_file}.")

    custom_tables = package_node.find("plecs:CustomTables", _NS)
    table_by_name: dict[str, ET.Element] = {}
    if custom_tables is not None:
        for table in custom_tables:
            name = table.findtext("plecs:Name", default="", namespaces=_NS)
            if name:
                table_by_name[name] = table

    semiconductor_data = package_node.find("plecs:SemiconductorData", _NS)
    if semiconductor_data is None:
        raise ValueError(f"SemiconductorData node not found in {xml_file}.")

    conduction_by_gate: dict[str, ET.Element] = {
        node.attrib.get("gate", ""): node for node in semiconductor_data.findall("plecs:ConductionLoss", _NS)
    }
    thermal_rc_network = _parse_thermal_rc_network(package_node, semiconductor_data)

    notes: list[str] = []
    if not thermal_rc_network:
        notes.append("No thermal RC network was found in the device XML.")

    return DeviceDynamicModel(
        eon_rg_on_i_v=_parse_table_3d(table_by_name["Eon_Rg_on_i_v"], x_name="rg_on_Ohm", y_name="current_A", z_name="voltage_V", unit="J")
        if "Eon_Rg_on_i_v" in table_by_name
        else None,
        eoff_rg_off_i_v=_parse_table_3d(table_by_name["Eoff_Rg_off_i_v"], x_name="rg_off_Ohm", y_name="current_A", z_name="voltage_V", unit="J")
        if "Eoff_Rg_off_i_v" in table_by_name
        else None,
        turn_on_energy=_parse_turn_loss(semiconductor_data.find("plecs:TurnOnLoss", _NS), "TurnOnLoss", notes)
        if semiconductor_data.find("plecs:TurnOnLoss", _NS) is not None
        else None,
        turn_off_energy=_parse_turn_loss(semiconductor_data.find("plecs:TurnOffLoss", _NS), "TurnOffLoss", notes)
        if semiconductor_data.find("plecs:TurnOffLoss", _NS) is not None
        else None,
        conduction_on_voltage_drop=_parse_optional_conduction_loss(
            conduction_by_gate,
            "on",
            "ConductionLoss_on",
            notes,
        ),
        conduction_off_voltage_drop=_parse_optional_conduction_loss(
            conduction_by_gate,
            "off",
            "ConductionLoss_off",
            notes,
        ),
        eoss_energy=_parse_optional_table_2d(
            table_by_name,
            "Eoss",
            x_name="voltage_V",
            y_name="temperature_C",
            unit="J",
            notes=notes,
        ),
        thermal_rc_network=thermal_rc_network,
        source_name=xml_file.name,
        notes=notes,
    )
