"""IGBT module data records and PLECS loss-table helpers.

This module is intentionally separate from MOSFET/GaN static records.
IGBT modules use VCEsat/VEC based conduction models and IGBT/FWD
switching-energy tables rather than Rds(on)-based MOSFET models.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import re
from typing import Iterable, Mapping, Sequence
from xml.etree import ElementTree as ET


PLECS_NS = {"p": "http://www.plexim.com/xml/semiconductors/"}


@dataclass(frozen=True)
class IGBTStaticRecord:
    """Static datasheet-level record for an IGBT module with FWDs."""

    vendor: str
    part_number: str
    device_type: str
    topology: str
    package: str

    vces_max_V: float
    ic_cont_A: float
    ic_pulse_A: float
    ie_cont_A: float
    ie_pulse_A: float

    vge_min_V: float
    vge_max_V: float
    vge_drive_on_V: float
    vge_drive_off_V: float

    tj_min_C: float
    tj_max_C: float
    tj_abs_max_C: float

    vce_sat_typ_25C_V: float
    vce_sat_typ_125C_V: float
    vce_sat_typ_150C_V: float

    vec_typ_25C_V: float
    vec_typ_125C_V: float
    vec_typ_150C_V: float

    eon_ref_mJ: float
    eoff_ref_mJ: float
    err_ref_mJ: float

    qrr_typ_uC: float
    trr_typ_ns: float
    rg_int_typ_Ohm: float

    rth_jc_igbt_K_per_W: float
    rth_jc_fwd_K_per_W: float
    rth_cs_module_K_per_W: float

    module_length_mm: float
    module_width_mm: float
    module_height_mm: float
    mass_g: float

    datasheet_filename: str
    igbt_xml_filename: str
    diode_xml_filename: str


def validate_igbt_static_record(record: IGBTStaticRecord) -> None:
    """Validate an IGBT static record and raise ValueError on bad fields."""

    text_fields = [
        "vendor",
        "part_number",
        "device_type",
        "topology",
        "package",
        "datasheet_filename",
        "igbt_xml_filename",
        "diode_xml_filename",
    ]
    for name in text_fields:
        value = getattr(record, name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{record.part_number}: {name} must be a non-empty string")

    positive_fields = [
        "vces_max_V",
        "ic_cont_A",
        "ic_pulse_A",
        "ie_cont_A",
        "ie_pulse_A",
        "tj_abs_max_C",
        "vce_sat_typ_25C_V",
        "vce_sat_typ_125C_V",
        "vce_sat_typ_150C_V",
        "vec_typ_25C_V",
        "vec_typ_125C_V",
        "vec_typ_150C_V",
        "eon_ref_mJ",
        "eoff_ref_mJ",
        "err_ref_mJ",
        "qrr_typ_uC",
        "trr_typ_ns",
        "rth_jc_igbt_K_per_W",
        "rth_jc_fwd_K_per_W",
        "rth_cs_module_K_per_W",
        "module_length_mm",
        "module_width_mm",
        "module_height_mm",
        "mass_g",
    ]
    for name in positive_fields:
        value = float(getattr(record, name))
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{record.part_number}: {name} must be positive, got {value}")

    if not math.isfinite(float(record.rg_int_typ_Ohm)) or float(record.rg_int_typ_Ohm) < 0:
        raise ValueError(f"{record.part_number}: rg_int_typ_Ohm must be non-negative")

    if record.ic_pulse_A < record.ic_cont_A:
        raise ValueError(f"{record.part_number}: pulse collector current is below continuous current")
    if record.ie_pulse_A < record.ie_cont_A:
        raise ValueError(f"{record.part_number}: pulse emitter/FWD current is below continuous current")
    if record.vge_min_V >= record.vge_max_V:
        raise ValueError(f"{record.part_number}: invalid gate voltage range")
    if record.tj_min_C >= record.tj_max_C:
        raise ValueError(f"{record.part_number}: invalid continuous junction temperature range")
    if record.tj_abs_max_C < record.tj_max_C:
        raise ValueError(f"{record.part_number}: absolute maximum Tj is below continuous maximum Tj")


@dataclass(frozen=True)
class FosterThermalModel:
    """Foster thermal impedance network."""

    r_values_K_per_W: tuple[float, ...]
    tau_values_s: tuple[float, ...]

    def zth_K_per_W(self, time_s: float) -> float:
        """Return transient thermal impedance at time_s."""

        if time_s <= 0:
            return 0.0
        return sum(r * (1.0 - math.exp(-time_s / tau)) for r, tau in zip(self.r_values_K_per_W, self.tau_values_s))

    @property
    def steady_state_K_per_W(self) -> float:
        return sum(self.r_values_K_per_W)


@dataclass(frozen=True)
class LossTable3D:
    """PLECS 3-D loss table with current, voltage and temperature axes."""

    current_axis: tuple[float, ...]
    voltage_axis: tuple[float, ...]
    temperature_axis: tuple[float, ...]
    values: tuple[tuple[tuple[float, ...], ...], ...]  # T -> V -> I
    scale: float = 1.0

    def lookup(self, current_A: float, voltage_V: float, temperature_C: float, *, clamp: bool = True) -> float:
        voltage_query = _map_voltage_query(voltage_V, self.voltage_axis)
        return _interp3(
            self.current_axis,
            self.voltage_axis,
            self.temperature_axis,
            self.values,
            current_A,
            voltage_query,
            temperature_C,
            clamp=clamp,
        ) * self.scale


@dataclass(frozen=True)
class ConductionTable2D:
    """PLECS 2-D conduction-voltage table with current and temperature axes."""

    current_axis: tuple[float, ...]
    temperature_axis: tuple[float, ...]
    values: tuple[tuple[float, ...], ...]  # T -> I
    scale: float = 1.0

    def lookup(self, current_A: float, temperature_C: float, *, clamp: bool = True) -> float:
        return _interp2(
            self.current_axis,
            self.temperature_axis,
            self.values,
            current_A,
            temperature_C,
            clamp=clamp,
        ) * self.scale


@dataclass(frozen=True)
class PlecsFormulaCorrection:
    """Simple PLECS correction of the form lookup('Table', variable)*(1/ref)*E."""

    table_name: str
    variable_name: str
    reference_value: float

    def factor(self, custom_tables: Mapping[str, tuple[tuple[float, ...], tuple[float, ...]]], variable_value: float) -> float:
        axis, values = custom_tables[self.table_name]
        correction = _interp1(axis, values, variable_value, clamp=True)
        if self.reference_value == 0:
            return 1.0
        return correction / self.reference_value


@dataclass(frozen=True)
class PlecsSwitchingLoss:
    """Switching energy model stored in Joules internally."""

    table: LossTable3D
    formula: PlecsFormulaCorrection | None = None

    def energy_J(
        self,
        current_A: float,
        voltage_V: float,
        temperature_C: float,
        *,
        variables: Mapping[str, float] | None = None,
        custom_tables: Mapping[str, tuple[tuple[float, ...], tuple[float, ...]]] | None = None,
        clamp: bool = True,
    ) -> float:
        base = self.table.lookup(current_A, voltage_V, temperature_C, clamp=clamp)
        if self.formula is None:
            return base
        variables = variables or {}
        custom_tables = custom_tables or {}
        var_value = variables.get(self.formula.variable_name)
        if var_value is None:
            return base
        return base * self.formula.factor(custom_tables, var_value)


@dataclass(frozen=True)
class PlecsSemiconductorLossModel:
    """Parsed PLECS semiconductor loss model for IGBT or Diode XML assets."""

    package_class: str
    vendor: str
    part_number: str
    variables: Mapping[str, tuple[float, float, float]]
    custom_tables: Mapping[str, tuple[tuple[float, ...], tuple[float, ...]]]
    turn_on: PlecsSwitchingLoss | None
    turn_off: PlecsSwitchingLoss | None
    conduction: ConductionTable2D | None
    thermal: FosterThermalModel | None

    @classmethod
    def from_xml(cls, xml_path: str | Path) -> "PlecsSemiconductorLossModel":
        path = Path(xml_path)
        root = ET.parse(path).getroot()
        package = root.find("p:Package", PLECS_NS)
        if package is None:
            raise ValueError(f"{path}: missing PLECS Package element")

        variables: dict[str, tuple[float, float, float]] = {}
        for var in package.findall("p:Variables/p:Variable", PLECS_NS):
            name = var.findtext("p:Name", namespaces=PLECS_NS)
            if not name:
                continue
            try:
                default = _float_text(var, "p:DefaultValue", path)
                min_value = _float_text(var, "p:MinValue", path)
                max_value = _float_text(var, "p:MaxValue", path)
            except ValueError:
                # Some Mitsubishi MOSFET PLECS files declare variables only
                # implicitly through formula/custom-table names. Keep parsing
                # the loss tables; runtime interpolation remains table-driven.
                continue
            variables[name] = (default, min_value, max_value)

        custom_tables = _parse_custom_tables(package)
        sem_data = package.find("p:SemiconductorData", PLECS_NS)
        if sem_data is None:
            raise ValueError(f"{path}: missing SemiconductorData")

        turn_on = _parse_switching_loss(sem_data.find("p:TurnOnLoss", PLECS_NS), path)
        turn_off = _parse_switching_loss(sem_data.find("p:TurnOffLoss", PLECS_NS), path)
        conduction = _parse_conduction_loss(sem_data.find("p:ConductionLoss", PLECS_NS), path)
        thermal = _parse_thermal_model(package.find("p:ThermalModel", PLECS_NS))

        return cls(
            package_class=package.attrib.get("class", ""),
            vendor=package.attrib.get("vendor", ""),
            part_number=package.attrib.get("partnumber", ""),
            variables=variables,
            custom_tables=custom_tables,
            turn_on=turn_on,
            turn_off=turn_off,
            conduction=conduction,
            thermal=thermal,
        )


def _parse_switching_loss(element: ET.Element | None, path: Path) -> PlecsSwitchingLoss | None:
    if element is None:
        return None
    current_axis = _float_tuple(_required_text(element, "p:CurrentAxis", path))
    voltage_axis = _float_tuple(_required_text(element, "p:VoltageAxis", path))
    temperature_axis = _float_tuple(_required_text(element, "p:TemperatureAxis", path))
    energy_element = element.find("p:Energy", PLECS_NS)
    if energy_element is None:
        raise ValueError(f"{path}: switching loss is missing Energy")
    scale = float(energy_element.attrib.get("scale", "1"))
    values: list[tuple[tuple[float, ...], ...]] = []
    for temp_element in energy_element.findall("p:Temperature", PLECS_NS):
        voltage_rows = []
        for voltage_element in temp_element.findall("p:Voltage", PLECS_NS):
            voltage_rows.append(_float_tuple(voltage_element.text or ""))
        values.append(tuple(voltage_rows))
    _validate_3d_shape(current_axis, voltage_axis, temperature_axis, tuple(values), path)
    formula = _parse_formula(element.findtext("p:Formula", default="", namespaces=PLECS_NS))
    return PlecsSwitchingLoss(
        table=LossTable3D(current_axis, voltage_axis, temperature_axis, tuple(values), scale=scale),
        formula=formula,
    )


def _parse_conduction_loss(element: ET.Element | None, path: Path) -> ConductionTable2D | None:
    if element is None:
        return None
    current_axis = _float_tuple(_required_text(element, "p:CurrentAxis", path))
    temperature_axis = _float_tuple(_required_text(element, "p:TemperatureAxis", path))
    voltage_drop = element.find("p:VoltageDrop", PLECS_NS)
    if voltage_drop is None:
        raise ValueError(f"{path}: conduction loss is missing VoltageDrop")
    scale = float(voltage_drop.attrib.get("scale", "1"))
    values = tuple(_float_tuple(temp.text or "") for temp in voltage_drop.findall("p:Temperature", PLECS_NS))
    _validate_2d_shape(current_axis, temperature_axis, values, path)
    return ConductionTable2D(current_axis, temperature_axis, values, scale=scale)


def _parse_custom_tables(package: ET.Element) -> dict[str, tuple[tuple[float, ...], tuple[float, ...]]]:
    tables: dict[str, tuple[tuple[float, ...], tuple[float, ...]]] = {}
    for table in package.findall("p:CustomTables/p:Table1D", PLECS_NS):
        name = table.findtext("p:Name", namespaces=PLECS_NS)
        x_axis = table.findtext("p:XAxis", namespaces=PLECS_NS)
        values = table.find("p:FunctionValues", PLECS_NS)
        if not name or not x_axis or values is None:
            continue
        scale = float(values.attrib.get("scale", "1"))
        tables[name] = (_float_tuple(x_axis), tuple(v * scale for v in _float_tuple(values.text or "")))
    return tables


def _parse_thermal_model(element: ET.Element | None) -> FosterThermalModel | None:
    if element is None:
        return None
    branch = element.find("p:Branch", PLECS_NS)
    if branch is None or branch.attrib.get("type", "").lower() != "foster":
        return None
    r_values = []
    tau_values = []
    for item in branch.findall("p:RTauElement", PLECS_NS):
        r_values.append(float(item.attrib["R"]))
        tau_values.append(float(item.attrib["Tau"]))
    if not r_values:
        return None
    return FosterThermalModel(tuple(r_values), tuple(tau_values))


def _parse_formula(formula: str) -> PlecsFormulaCorrection | None:
    if not formula:
        return None
    match = re.search(r"lookup\('([^']+)'\s*,\s*([A-Za-z0-9_]+)\)\s*\*\s*\(1/([0-9.eE+\-]+)\)\s*\*\s*E", formula)
    if not match:
        return None
    return PlecsFormulaCorrection(
        table_name=match.group(1),
        variable_name=match.group(2),
        reference_value=float(match.group(3)),
    )


def _interp1(axis: Sequence[float], values: Sequence[float], x: float, *, clamp: bool = True) -> float:
    x0_idx, x1_idx, fx = _bounds(axis, x, clamp=clamp)
    return values[x0_idx] * (1.0 - fx) + values[x1_idx] * fx


def _interp2(
    x_axis: Sequence[float],
    y_axis: Sequence[float],
    values_yx: Sequence[Sequence[float]],
    x: float,
    y: float,
    *,
    clamp: bool = True,
) -> float:
    x0, x1, fx = _bounds(x_axis, x, clamp=clamp)
    y0, y1, fy = _bounds(y_axis, y, clamp=clamp)
    v00 = values_yx[y0][x0]
    v10 = values_yx[y0][x1]
    v01 = values_yx[y1][x0]
    v11 = values_yx[y1][x1]
    vx0 = v00 * (1.0 - fx) + v10 * fx
    vx1 = v01 * (1.0 - fx) + v11 * fx
    return vx0 * (1.0 - fy) + vx1 * fy


def _interp3(
    current_axis: Sequence[float],
    voltage_axis: Sequence[float],
    temperature_axis: Sequence[float],
    values_tvi: Sequence[Sequence[Sequence[float]]],
    current: float,
    voltage: float,
    temperature: float,
    *,
    clamp: bool = True,
) -> float:
    i0, i1, fi = _bounds(current_axis, current, clamp=clamp)
    v0, v1, fv = _bounds(voltage_axis, voltage, clamp=clamp)
    t0, t1, ft = _bounds(temperature_axis, temperature, clamp=clamp)

    def at(t_idx: int, v_idx: int, i_idx: int) -> float:
        return values_tvi[t_idx][v_idx][i_idx]

    c000 = at(t0, v0, i0)
    c100 = at(t0, v0, i1)
    c010 = at(t0, v1, i0)
    c110 = at(t0, v1, i1)
    c001 = at(t1, v0, i0)
    c101 = at(t1, v0, i1)
    c011 = at(t1, v1, i0)
    c111 = at(t1, v1, i1)

    c00 = c000 * (1.0 - fi) + c100 * fi
    c10 = c010 * (1.0 - fi) + c110 * fi
    c01 = c001 * (1.0 - fi) + c101 * fi
    c11 = c011 * (1.0 - fi) + c111 * fi
    c0 = c00 * (1.0 - fv) + c10 * fv
    c1 = c01 * (1.0 - fv) + c11 * fv
    return c0 * (1.0 - ft) + c1 * ft


def _bounds(axis: Sequence[float], x: float, *, clamp: bool) -> tuple[int, int, float]:
    if len(axis) < 2:
        raise ValueError("Interpolation axis must contain at least two points")
    if x <= axis[0]:
        if not clamp and x < axis[0]:
            raise ValueError(f"Query {x} is below interpolation axis minimum {axis[0]}")
        return 0, 0, 0.0
    if x >= axis[-1]:
        if not clamp and x > axis[-1]:
            raise ValueError(f"Query {x} is above interpolation axis maximum {axis[-1]}")
        return len(axis) - 1, len(axis) - 1, 0.0
    for idx in range(len(axis) - 1):
        left = axis[idx]
        right = axis[idx + 1]
        if left <= x <= right:
            if right == left:
                return idx, idx + 1, 0.0
            return idx, idx + 1, (x - left) / (right - left)
    raise ValueError(f"Could not interpolate query {x} on axis {axis}")


def _map_voltage_query(voltage_V: float, voltage_axis: Sequence[float]) -> float:
    """Map user-positive blocking voltage onto PLECS axes that may be negative for diode Err."""

    if voltage_axis[-1] <= 0:
        return -abs(voltage_V)
    if voltage_axis[0] >= 0:
        return abs(voltage_V)
    return voltage_V


def _required_text(element: ET.Element, path_expr: str, path: Path) -> str:
    value = element.findtext(path_expr, namespaces=PLECS_NS)
    if value is None:
        raise ValueError(f"{path}: missing required XML element {path_expr}")
    return value.strip()


def _float_text(element: ET.Element, path_expr: str, path: Path) -> float:
    return float(_required_text(element, path_expr, path))


def _float_tuple(text: str) -> tuple[float, ...]:
    return tuple(float(part) for part in text.split())


def _validate_3d_shape(
    current_axis: Sequence[float],
    voltage_axis: Sequence[float],
    temperature_axis: Sequence[float],
    values: Sequence[Sequence[Sequence[float]]],
    path: Path,
) -> None:
    if len(values) != len(temperature_axis):
        raise ValueError(f"{path}: energy table temperature dimension mismatch")
    for temp_rows in values:
        if len(temp_rows) != len(voltage_axis):
            raise ValueError(f"{path}: energy table voltage dimension mismatch")
        for row in temp_rows:
            if len(row) != len(current_axis):
                raise ValueError(f"{path}: energy table current dimension mismatch")


def _validate_2d_shape(
    current_axis: Sequence[float],
    temperature_axis: Sequence[float],
    values: Sequence[Sequence[float]],
    path: Path,
) -> None:
    if len(values) != len(temperature_axis):
        raise ValueError(f"{path}: conduction table temperature dimension mismatch")
    for row in values:
        if len(row) != len(current_axis):
            raise ValueError(f"{path}: conduction table current dimension mismatch")


def require_file(path: str | Path) -> Path:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    return p
