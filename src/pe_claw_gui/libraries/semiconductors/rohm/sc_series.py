"""ROHM SC-series SiC MOSFET, SiC SBD, and DOT-247 module registrations.

PDFs are used only for static-parameter and package-dimension auditing. The
runtime library keeps XML files only and extracts electrical loss/thermal data
from the ROHM PLECS XML models.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re
from typing import Sequence

from ..sic_module_models import PlecsSiCSemiconductorLossModel

DATA_SUBDIR = Path(__file__).resolve().parent / "data_sc"


@dataclass(frozen=True)
class RohmSCStaticRecord:
    vendor: str
    part_number: str
    device_type: str
    package: str
    voltage_rating_V: float
    current_rating_A: float
    pulse_current_A: float
    vgs_min_V: float
    vgs_max_V: float
    tj_min_C: float
    tj_max_C: float
    rth_jc_K_per_W: float
    length_mm: float
    width_mm: float
    height_mm: float
    mass_g: float
    xml_filename: str
    datasheet_filename: str
    static_note: str = "static fields inferred from XML and datasheet package family"


class RohmSCDevice:
    """Runtime wrapper for one ROHM SC SiC MOSFET, module, or SBD XML model."""

    def __init__(self, static: RohmSCStaticRecord, loss_model: PlecsSiCSemiconductorLossModel):
        self.static = static
        self.loss_model = loss_model

    @property
    def part_number(self) -> str:
        return self.static.part_number

    @property
    def is_diode(self) -> bool:
        device_type = self.static.device_type.lower()
        return "mosfet" not in device_type and (
            "diode" in device_type
            or "sbd" in device_type
            or "schottky" in device_type
        )

    @property
    def is_mosfet(self) -> bool:
        return "mosfet" in self.static.device_type.lower()

    def eon_mJ(self, current_A: float, voltage_V: float, tj_C: float, rg_on_Ohm: float = 0.0) -> float:
        if self.loss_model.turn_on is None:
            return 0.0
        e_j = self.loss_model.turn_on.energy_J(
            current_A,
            voltage_V,
            tj_C,
            variables={"Rg": rg_on_Ohm, "Rg_on": rg_on_Ohm, "RgOn": rg_on_Ohm, "RGOn": rg_on_Ohm},
            custom_tables_3d=self.loss_model.custom_tables_3d,
            custom_tables_2d=self.loss_model.custom_tables_2d,
        )
        return max(0.0, e_j * 1000.0)

    def eoff_mJ(self, current_A: float, voltage_V: float, tj_C: float, rg_off_Ohm: float = 0.0) -> float:
        if self.loss_model.turn_off is None:
            return 0.0
        e_j = self.loss_model.turn_off.energy_J(
            current_A,
            voltage_V,
            tj_C,
            variables={"Rg": rg_off_Ohm, "Rg_off": rg_off_Ohm, "RgOff": rg_off_Ohm, "RGOff": rg_off_Ohm},
            custom_tables_3d=self.loss_model.custom_tables_3d,
            custom_tables_2d=self.loss_model.custom_tables_2d,
        )
        return max(0.0, e_j * 1000.0)

    def conduction_voltage_V(self, current_A: float, tj_C: float) -> float:
        cond = self.loss_model.conduction
        if cond is None:
            return 0.0
        try:
            return max(0.0, cond.lookup(abs(current_A), tj_C))
        except TypeError:
            return max(0.0, cond.lookup(abs(current_A), tj_C, variables={"sw": 1.0}))

    def vds_on_V(self, id_A: float, tj_C: float) -> float:
        return self.conduction_voltage_V(id_A, tj_C)

    def vf_V(self, if_A: float, tj_C: float) -> float:
        return self.conduction_voltage_V(if_A, tj_C)

    def conduction_loss_W(self, current_waveform_A: Sequence[float], tj_C: float) -> float:
        samples = [max(0.0, float(i)) for i in current_waveform_A]
        if not samples:
            return 0.0
        return sum(self.conduction_voltage_V(i, tj_C) * i for i in samples) / len(samples)

    def switching_loss_W(
        self,
        fsw_Hz: float,
        current_A: float,
        voltage_V: float,
        tj_C: float,
        rg_on_Ohm: float = 0.0,
        rg_off_Ohm: float = 0.0,
    ) -> float:
        return fsw_Hz * (self.eon_mJ(current_A, voltage_V, tj_C, rg_on_Ohm) + self.eoff_mJ(current_A, voltage_V, tj_C, rg_off_Ohm)) / 1000.0

    def estimate_junction_temperature_C(self, loss_W: float, case_temp_C: float) -> dict[str, float]:
        delta = float(loss_W) * self.static.rth_jc_K_per_W
        return {"tj_C": case_temp_C + delta, "delta_t_K": delta, "rth_jc_K_per_W": self.static.rth_jc_K_per_W}

    def zth_jc_K_per_W(self, time_s: float) -> float:
        tm = self.loss_model.thermal
        return tm.zth_K_per_W(time_s) if tm is not None else self.static.rth_jc_K_per_W

    def build_geometry_proxy(self) -> dict[str, object]:
        return {
            "shape": "package_box",
            "body": {
                "length_mm": self.static.length_mm,
                "width_mm": self.static.width_mm,
                "height_mm": self.static.height_mm,
                "material": "rohm_sc_sic_package",
            },
            "label": self.static.part_number,
            "package": self.static.package,
            "mass_g": self.static.mass_g,
        }


def _variable_max(model: PlecsSiCSemiconductorLossModel, *names: str, default: float = 0.0) -> float:
    lower = {k.lower(): v for k, v in model.variables.items()}
    for name in names:
        val = lower.get(name.lower())
        if val and val[2] is not None:
            return float(val[2])
    return default


def _thermal_rth(model: PlecsSiCSemiconductorLossModel) -> float:
    if model.thermal is not None and model.thermal.steady_state_K_per_W > 0:
        return model.thermal.steady_state_K_per_W
    return 1.0


def _clean_part_for_package(part: str) -> str:
    p = part.upper()
    if p.endswith("_MOS"):
        p = p[:-4]
    return p


def _package_geometry(part: str, package_class: str) -> tuple[str, float, float, float, float]:
    """Return package label and simplified PDF-envelope dimensions.

    Dimensions are package-envelope values used for PE-Claw visualization and
    volume screening. They are not a pin-level CAD replacement.
    """

    p = _clean_part_for_package(part)

    # ROHM SCZ40xxDTx/KTx DOT-247 half-bridge molded modules.
    # The datasheets use SCZ4004DTA/SCZ4006KTA style names while XML uses DTx/KTx.
    if p.startswith("SCZ"):
        return "DOT-247-7L half-bridge module", 26.45, 31.50, 5.25, 10.0

    # SCS SiC SBD packages.
    if package_class.lower() == "diode" or p.startswith("SCS"):
        if p.endswith("AM"):
            return "TO-220FM-2L", 10.00, 15.87, 4.70, 2.0
        if p.endswith("AJ"):
            return "TO-263-2L", 10.16, 15.30, 4.60, 1.6
        if p.endswith("AG") or p.endswith("AGHR"):
            return "TO-220AC-2L", 10.16, 15.35, 4.44, 2.0
        # KE/KG/KN/KE2 and HR variants are TO-247-class SBD packages.
        return "TO-247-2L", 15.94, 20.95, 5.02, 6.0

    # SCT SiC MOSFETs.  Most SC-series MOSFETs in this data set are TO-247-class
    # packages; suffixes determine lead count/Kelvin option.
    if p.endswith(("DLL", "DWA", "DWAHR", "KWA", "KWAHR", "AW7", "DW7", "DW7HR", "KW7", "KW7HR")):
        return "TO-247-4L / 7L Kelvin", 15.94, 20.95, 5.02, 6.0
    if p.endswith(("KG", "KGHR", "KN", "KNHR", "KR", "KRHR", "KL", "KLHR")):
        return "TO-247N-4L Kelvin", 15.94, 20.95, 5.02, 6.0
    if p.endswith(("DE", "DEHR", "DR", "DRHR", "KE", "KEHR", "KE2", "KE2HR", "AR")):
        return "TO-247N-3L", 15.94, 20.95, 5.02, 6.0
    if p.endswith(("NWB", "NWC", "NZ")):
        return "TO-247N family", 15.94, 20.95, 5.02, 6.0
    return "ROHM SC package", 15.94, 20.95, 5.02, 6.0


def _pdf_name_for_xml_part(part: str) -> str:
    p = part
    pu = p.upper()
    if pu.endswith("DTX_MOS"):
        return p[:-7] + "DTA.pdf"
    if pu.endswith("KTX_MOS"):
        return p[:-7] + "KTA.pdf"
    return p + ".pdf"


def _static_part_number(xml_stem: str) -> str:
    # Keep original XML model part for lookup, including SCZ4004DTx_MOS.
    return xml_stem


def _build_static_from_xml(xml_path: Path, model: PlecsSiCSemiconductorLossModel) -> RohmSCStaticRecord:
    part = _static_part_number(xml_path.stem)
    package, length, width, height, mass = _package_geometry(part, model.package_class)
    is_diode = model.package_class.lower() == "diode" or part.upper().startswith("SCS")
    is_module = part.upper().startswith("SCZ")
    if is_diode:
        device_type = "SiC Schottky barrier diode"
    elif is_module:
        device_type = "SiC MOSFET module section with body diode"
    else:
        device_type = "SiC MOSFET with body diode"
    voltage = _variable_max(model, "v", "V", "Vds", "Vce", default=0.0)
    current = _variable_max(model, "i", "I", "Id", "Is", default=0.0)
    if current <= 0 and model.conduction is not None and hasattr(model.conduction, "current_axis"):
        current = max(model.conduction.current_axis)
    static = RohmSCStaticRecord(
        vendor="ROHM",
        part_number=part,
        device_type=device_type,
        package=package,
        voltage_rating_V=voltage if voltage > 0 else (650.0 if part.upper().startswith("SCS") else 1200.0),
        current_rating_A=current if current > 0 else 1.0,
        pulse_current_A=max(current * 2.0, current if current > 0 else 1.0),
        vgs_min_V=-10.0 if not is_diode else 0.0,
        vgs_max_V=25.0 if not is_diode else 0.0,
        tj_min_C=-55.0,
        tj_max_C=175.0,
        rth_jc_K_per_W=_thermal_rth(model),
        length_mm=length,
        width_mm=width,
        height_mm=height,
        mass_g=mass,
        xml_filename=xml_path.name,
        datasheet_filename=_pdf_name_for_xml_part(part),
    )
    return static


def _iter_xml_paths() -> list[Path]:
    if not DATA_SUBDIR.exists():
        return []
    return sorted(DATA_SUBDIR.glob("*.xml"))


@lru_cache(maxsize=1)
def build_rohm_sc_devices() -> list[RohmSCDevice]:
    devices: list[RohmSCDevice] = []
    for xml_path in _iter_xml_paths():
        model = PlecsSiCSemiconductorLossModel.from_xml(xml_path)
        static = _build_static_from_xml(xml_path, model)
        devices.append(RohmSCDevice(static, model))
    return devices


def build_rohm_sc_device(part_number: str) -> RohmSCDevice:
    key = part_number.upper().replace(".XML", "")
    for dev in build_rohm_sc_devices():
        if dev.part_number.upper() == key:
            return dev
    raise KeyError(f"ROHM SC-series device not found: {part_number}")


__all__ = [
    "DATA_SUBDIR",
    "RohmSCStaticRecord",
    "RohmSCDevice",
    "build_rohm_sc_device",
    "build_rohm_sc_devices",
]
