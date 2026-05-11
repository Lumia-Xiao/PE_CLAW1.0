"""Mitsubishi Electric semiconductor module registrations.

This package keeps the Mitsubishi module library manifest based. It started
as an IGBT/FWD framework and now also registers the Mitsubishi SiC MOSFET
modules found in the supplied source archive through the same PLECS loss-table
runtime interface. Data directories intentionally contain XML models only;
PDF datasheets are used only to curate static records.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from ..metadata import classify_runtime_device_type
from ..models import DeviceDynamicModel, DeviceStaticRecord
from ..power_device import PowerDevice

try:
    from ..igbt_models import IGBTStaticRecord, PlecsSemiconductorLossModel, validate_igbt_static_record
except ImportError:
    from pe_claw_gui.libraries.semiconductors.igbt_models import IGBTStaticRecord, PlecsSemiconductorLossModel, validate_igbt_static_record  # type: ignore

_DEVICE_PACKAGE = "pe_claw_gui.libraries.semiconductors.mitsubishi"
MITSUBISHI_IGBT_XML_SUBDIR = "data"


def _record(
    part_number: str,
    device_type: str,
    topology: str,
    package: str,
    vces: float,
    ic: float,
    ipulse: float,
    tj_min: float,
    tj_max: float,
    tj_abs: float,
    vce25: float,
    vce125: float,
    vce150: float,
    vec25: float,
    vec125: float,
    vec150: float,
    eon: float,
    eoff: float,
    err: float,
    qrr: float,
    trr_ns: float,
    rg: float,
    rth_q: float,
    rth_d: float,
    rth_cs: float,
    length: float,
    width: float,
    height: float,
    mass: float,
    switch_xml: str,
    diode_xml: str,
) -> IGBTStaticRecord:
    is_mosfet = "MOSFET" in device_type
    return IGBTStaticRecord(
        vendor="Mitsubishi Electric",
        part_number=part_number,
        device_type=device_type,
        topology=topology,
        package=package,
        vces_max_V=vces,
        ic_cont_A=ic,
        ic_pulse_A=ipulse,
        ie_cont_A=ic,
        ie_pulse_A=ipulse,
        vge_min_V=-20.0,
        vge_max_V=20.0,
        vge_drive_on_V=17.0 if is_mosfet else 15.0,
        vge_drive_off_V=-5.0 if is_mosfet else -15.0,
        tj_min_C=tj_min,
        tj_max_C=tj_max,
        tj_abs_max_C=tj_abs,
        vce_sat_typ_25C_V=vce25,
        vce_sat_typ_125C_V=vce125,
        vce_sat_typ_150C_V=vce150,
        vec_typ_25C_V=vec25,
        vec_typ_125C_V=vec125,
        vec_typ_150C_V=vec150,
        eon_ref_mJ=max(eon, 0.001),
        eoff_ref_mJ=max(eoff, 0.001),
        err_ref_mJ=max(err, 0.001),
        qrr_typ_uC=max(qrr, 0.001),
        trr_typ_ns=max(trr_ns, 0.001),
        rg_int_typ_Ohm=max(rg, 0.0),
        rth_jc_igbt_K_per_W=max(rth_q, 0.001),
        rth_jc_fwd_K_per_W=max(rth_d, rth_q, 0.001),
        rth_cs_module_K_per_W=max(rth_cs, 0.001),
        module_length_mm=length,
        module_width_mm=width,
        module_height_mm=height,
        mass_g=mass,
        datasheet_filename=f"{part_number}.pdf",
        igbt_xml_filename=switch_xml,
        diode_xml_filename=diode_xml,
    )


CM450DY_24T_STATIC = _record('CM450DY-24T', 'IGBT module with FWD', 'half_bridge', 'dual_switch_half_bridge_module', 1200, 450, 900, -40, 150, 175, 1.55, 1.75, 1.8, 1.65, 1.65, 1.65, 40.9, 47.0, 31.6, 45.0, 400, 1.0, 0.031, 0.054, 0.0133, 108, 62, 30, 260, 'CM450DY-24T_IGBT.xml', 'CM450DY-24T_Diode.xml')

CM600DY_24T_STATIC = _record('CM600DY-24T', 'IGBT module with FWD', 'half_bridge', 'dual_switch_half_bridge_module', 1200, 600, 1200, -40, 150, 175, 1.55, 1.75, 1.8, 1.65, 1.65, 1.65, 56.6, 64.3, 38.2, 60.0, 400, 0.67, 0.024, 0.042, 0.0133, 108, 62, 30, 260, 'CM600DY-24T_IGBT.xml', 'CM600DY-24T_Diode.xml')

CM1200DA_34X_STATIC = _record('CM1200DA-34X', 'HVIGBT module with FWD', 'half_bridge', 'dual_switch_hvigbt_module', 1700, 1200, 2400, -50, 150, 150, 1.8, 2.15, 2.2, 1.8, 1.9, 1.9, 430, 490, 220, 350, 530, 0.0, 0.0165, 0.027, 0.016, 140, 110, 40, 750, 'CM1200DA-34X_IGBT.xml', 'CM1200DA-34X_Diode.xml')

CM1200DC_34S1_STATIC = _record('CM1200DC-34S1', 'HVIGBT module with FWD', 'half_bridge', 'dual_switch_hvigbt_flat_baseplate_module', 1700, 1200, 2400, -50, 150, 150, 1.95, 2.25, 2.3, 2.2, 2.35, 2.35, 380, 400, 240, 420, 450, 0.0, 0.0185, 0.038, 0.016, 140, 130, 38, 800, 'CM1200DC-34S1_IGBT.xml', 'CM1200DC-34S1_Diode.xml')

CM1200DW_24T_STATIC = _record('CM1200DW-24T', 'IGBT module with FWD', 'half_bridge', 'dual_switch_half_bridge_copper_baseplate_module', 1200, 1200, 2400, -40, 150, 175, 1.5, 1.7, 1.75, 1.6, 1.6, 1.6, 179, 145, 70, 93.6, 400, 0.33, 0.029, 0.046, 0.01, 140, 130, 34, 860, 'CM1200DW-24T_IGBT.xml', 'CM1200DW-24T_Diode.xml')

CM1500HG_90X_STATIC = _record('CM1500HG-90X', 'HVIGBT module with FWD', 'single_switch', 'single_switch_hvigbt_module', 4500, 1500, 3000, -50, 150, 150, 2.4, 3.1, 3.2, 2.4, 3.0, 3.1, 7800, 6600, 4500, 2800, 1700, 0.0, 0.0085, 0.013, 0.005, 190, 140, 45, 1500, 'CM1500HG-90X_IGBT.xml', 'CM1500HG-90X_Diode.xml')

CM1800HC_66X_STATIC = _record('CM1800HC-66X', 'HVIGBT module with FWD', 'single_switch', 'single_switch_hvigbt_module', 3300, 1800, 3600, -50, 150, 150, 2.95, 2.5, 2.6, 2.4, 2.4, 2.5, 3400, 3100, 2600, 2600, 1100, 0.0, 0.007, 0.011, 0.005, 190, 140, 45, 1200, 'CM1800HC-66X_IGBT.xml', 'CM1800HC-66X_Diode.xml')

CMH1200DC_34S_STATIC = _record('CMH1200DC-34S', 'SiC hybrid HVIGBT module with FWD', 'half_bridge', 'hybrid_hvigbt_flat_baseplate_module', 1700, 1200, 2400, -50, 150, 150, 1.95, 2.25, 2.3, 1.6, 2.2, 2.3, 160, 400, 0.001, 0.001, 0.001, 0.0, 0.0185, 0.036, 0.016, 140, 130, 38, 800, 'CMH1200DC-34S_IGBT.xml', 'CMH1200DC-34S_Diode.xml')

CT600CJ1A060_A_STATIC = _record('CT600CJ1A060-A', 'IGBT module with FWD', 'six_pack', 'six_in_one_direct_cooling_module', 650, 600, 1200, -40, 150, 175, 1.5, 1.6, 1.6, 1.7, 1.7, 1.7, 21.5, 43.7, 14.5, 34.0, 230, 0.0, 0.212, 0.242, 0.001, 154, 115, 32, 340, 'CT600CJ1A060-A_IGBT.xml', 'CT600CJ1A060-A_Diode.xml')

CT700CJ1A060_A_STATIC = _record('CT700CJ1A060-A', 'IGBT module with FWD', 'six_pack', 'six_in_one_direct_cooling_module', 650, 700, 1400, -40, 150, 175, 1.6, 1.7, 1.7, 1.6, 1.6, 1.6, 34.4, 56.8, 15.9, 50.3, 260, 0.0, 0.194, 0.212, 0.001, 154, 115, 32, 340, 'CT700CJ1A060-A_IGBT.xml', 'CT700CJ1A060-A_Diode.xml')

FMF375DC_66A_STATIC = _record('FMF375DC-66A', 'SiC MOSFET module with JBS diode', 'half_bridge', 'hvmosfet_dual_module', 3300, 375, 750, -40, 175, 175, 1.75, 3.4, 3.9, 2.0, 2.4, 2.4, 260, 0.001, 0.001, 0.001, 0.001, 0.0, 0.0543, 0.0543, 0.005, 140, 110, 40, 750, 'FMF375DC-66A_MOSFET.xml', 'FMF375DC-66A_Diode.xml')

FMF750DC_66A_STATIC = _record('FMF750DC-66A', 'SiC MOSFET module with JBS diode', 'half_bridge', 'hvmosfet_dual_module', 3300, 750, 1500, -40, 175, 175, 1.75, 3.4, 3.9, 2.0, 2.4, 2.4, 600, 250, 0.001, 0.001, 0.001, 0.0, 0.0269, 0.0269, 0.005, 140, 110, 40, 900, 'FMF750DC-66A_MOSFET.xml', 'FMF750DC-66A_Diode.xml')

FMF600DXE_24BN_STATIC = _record('FMF600DXE-24BN', 'SiC MOSFET module with diode', 'half_bridge', 'sic_mosfet_module', 1200, 600, 1200, -40, 175, 175, 1.5, 2.0, 2.5, 1.5, 2.0, 2.5, 25, 15, 0.001, 0.001, 0.001, 0.0, 0.05, 0.05, 0.005, 108, 62, 30, 415, 'FMF600DXE-24BN.xml', 'FMF600DXE-24BN.xml')

FMF600DXE_34BN_STATIC = _record('FMF600DXE-34BN', 'SiC MOSFET module with diode', 'half_bridge', 'sic_mosfet_module', 1700, 600, 1200, -40, 175, 175, 1.5, 2.0, 2.5, 1.5, 2.0, 2.5, 50, 30, 0.001, 0.001, 0.001, 0.0, 0.05, 0.05, 0.005, 108, 62, 30, 415, 'FMF600DXE-34BN.xml', 'FMF600DXE-34BN.xml')

FMF600DXZA_24B_STATIC = _record('FMF600DXZA-24B', 'SiC MOSFET module with diode', 'half_bridge', 'sic_mosfet_module', 1200, 600, 1200, -40, 175, 175, 1.5, 2.0, 2.5, 1.5, 2.0, 2.5, 25, 15, 0.001, 0.001, 0.001, 0.0, 0.05, 0.05, 0.005, 108, 62, 30, 415, 'FMF600DXZA-24B.xml', 'FMF600DXZA-24B.xml')

FMF800DXZA_24B_STATIC = _record('FMF800DXZA-24B', 'SiC MOSFET module with diode', 'half_bridge', 'sic_mosfet_module', 1200, 800, 1600, -40, 175, 175, 1.5, 2.0, 2.5, 1.5, 2.0, 2.5, 35, 20, 0.001, 0.001, 0.001, 0.0, 0.04, 0.04, 0.005, 108, 62, 30, 500, 'FMF800DXZA-24B.xml', 'FMF800DXZA-24B.xml')

MITSUBISHI_IGBT_STATIC_MANIFEST: tuple[IGBTStaticRecord, ...] = (
    CM450DY_24T_STATIC,
    CM600DY_24T_STATIC,
    CM1200DA_34X_STATIC,
    CM1200DC_34S1_STATIC,
    CM1200DW_24T_STATIC,
    CM1500HG_90X_STATIC,
    CM1800HC_66X_STATIC,
    CMH1200DC_34S_STATIC,
    CT600CJ1A060_A_STATIC,
    CT700CJ1A060_A_STATIC,
    FMF375DC_66A_STATIC,
    FMF750DC_66A_STATIC,
    FMF600DXE_24BN_STATIC,
    FMF600DXE_34BN_STATIC,
    FMF600DXZA_24B_STATIC,
    FMF800DXZA_24B_STATIC,
)


def normalize_mitsubishi_igbt_part_number(filename_or_part: str) -> str:
    """Normalize Mitsubishi source names to manifest part numbers."""

    stem = Path(filename_or_part).stem.upper()
    stem = stem.split(",")[0].strip()
    stem = re.sub(r"\(VGS=.*\)", "", stem)
    stem = re.sub(r"_(IGBT|DIODE|MOSFET)$", "", stem)
    clean = re.sub(r"[^A-Z0-9]", "", stem)
    known = {re.sub(r"[^A-Z0-9]", "", r.part_number): r.part_number for r in MITSUBISHI_IGBT_STATIC_MANIFEST}
    return known.get(clean, clean)


def _part_data_subdir(part_number: str) -> str:
    normalized = normalize_mitsubishi_igbt_part_number(part_number)
    return normalized.lower().replace("-", "_")


def resolve_mitsubishi_igbt_data_path(record: IGBTStaticRecord, filename: str) -> Path:
    """Resolve a packaged Mitsubishi XML data file."""

    subdir = _part_data_subdir(record.part_number)
    try:
        resource = resources.files(_DEVICE_PACKAGE).joinpath(MITSUBISHI_IGBT_XML_SUBDIR, subdir, filename)
        return Path(str(resource))
    except Exception:
        return Path(__file__).resolve().parent / MITSUBISHI_IGBT_XML_SUBDIR / subdir / filename


@dataclass(frozen=True)
class MitsubishiIGBTModule:
    """Runtime model for one Mitsubishi switch module and optional diode/FWD model."""

    static: IGBTStaticRecord
    igbt_loss_model: PlecsSemiconductorLossModel
    diode_loss_model: PlecsSemiconductorLossModel | None = None

    @property
    def has_separate_diode_xml(self) -> bool:
        return self.static.diode_xml_filename != self.static.igbt_xml_filename

    def eon_mJ(self, ic_A: float, vce_V: float, tj_C: float, rg_on_Ohm: float) -> float:
        if self.igbt_loss_model.turn_on is None:
            return 0.0
        return 1000.0 * self.igbt_loss_model.turn_on.energy_J(
            ic_A,
            vce_V,
            tj_C,
            variables={"RGOn": rg_on_Ohm, "RG": rg_on_Ohm},
            custom_tables=self.igbt_loss_model.custom_tables,
        )

    def eoff_mJ(self, ic_A: float, vce_V: float, tj_C: float, rg_off_Ohm: float) -> float:
        if self.igbt_loss_model.turn_off is None:
            return 0.0
        return 1000.0 * self.igbt_loss_model.turn_off.energy_J(
            ic_A,
            vce_V,
            tj_C,
            variables={"RGOff": rg_off_Ohm, "RG": rg_off_Ohm},
            custom_tables=self.igbt_loss_model.custom_tables,
        )

    def vce_sat_V(self, ic_A: float, tj_C: float) -> float:
        if self.igbt_loss_model.conduction is None:
            raise ValueError(f"{self.static.part_number}: missing switch conduction table")
        return self.igbt_loss_model.conduction.lookup(max(0.0, ic_A), tj_C)

    def vec_V(self, ie_A: float, tj_C: float) -> float:
        model = self.diode_loss_model if self.diode_loss_model is not None else self.igbt_loss_model
        if model.conduction is None:
            raise ValueError(f"{self.static.part_number}: missing diode/body-diode conduction table")
        return model.conduction.lookup(max(0.0, ie_A), tj_C)

    def err_mJ(self, ie_A: float, vce_V: float, tj_C: float, rg_on_Ohm: float) -> float:
        if not self.has_separate_diode_xml or self.diode_loss_model is None or self.diode_loss_model.turn_off is None:
            return 0.0
        return 1000.0 * self.diode_loss_model.turn_off.energy_J(
            ie_A,
            vce_V,
            tj_C,
            variables={"RGOn": rg_on_Ohm, "RG": rg_on_Ohm},
            custom_tables=self.diode_loss_model.custom_tables,
        )

    def igbt_conduction_loss_W(self, current_waveform_A: Sequence[float], tj_C: float, dt_s: float | Sequence[float] | None = None) -> float:
        values = [self.vce_sat_V(max(0.0, float(i)), tj_C) * max(0.0, float(i)) for i in current_waveform_A]
        return _average(values, dt_s)

    def fwd_conduction_loss_W(self, current_waveform_A: Sequence[float], tj_C: float, dt_s: float | Sequence[float] | None = None) -> float:
        values = [self.vec_V(max(0.0, float(i)), tj_C) * max(0.0, float(i)) for i in current_waveform_A]
        return _average(values, dt_s)

    def igbt_switching_loss_W(self, fsw_Hz: float, ic_A: float, vce_V: float, tj_C: float, rg_on_Ohm: float, rg_off_Ohm: float) -> float:
        return fsw_Hz * (self.eon_mJ(ic_A, vce_V, tj_C, rg_on_Ohm) + self.eoff_mJ(ic_A, vce_V, tj_C, rg_off_Ohm)) / 1000.0

    def fwd_reverse_recovery_loss_W(self, fsw_Hz: float, ie_A: float, vce_V: float, tj_C: float, rg_on_Ohm: float) -> float:
        return fsw_Hz * self.err_mJ(ie_A, vce_V, tj_C, rg_on_Ohm) / 1000.0

    def estimate_junction_temperature_C(self, losses: Mapping[str, float], case_temp_C: float, pulse_time_s: float | None = None, use_foster: bool = False) -> dict[str, float]:
        p_igbt = float(losses.get("p_igbt_W", losses.get("p_igbt_cond_W", 0.0) + losses.get("p_igbt_sw_W", 0.0)))
        p_fwd = float(losses.get("p_fwd_W", losses.get("p_fwd_cond_W", 0.0) + losses.get("p_fwd_rr_W", 0.0)))
        rth_igbt = self.static.rth_jc_igbt_K_per_W
        rth_fwd = self.static.rth_jc_fwd_K_per_W
        if use_foster and pulse_time_s is not None:
            if self.igbt_loss_model.thermal is not None:
                rth_igbt = self.igbt_loss_model.thermal.zth_K_per_W(pulse_time_s)
            if self.diode_loss_model is not None and self.diode_loss_model.thermal is not None:
                rth_fwd = self.diode_loss_model.thermal.zth_K_per_W(pulse_time_s)
        return {
            "p_igbt_W": p_igbt,
            "p_fwd_W": p_fwd,
            "rth_igbt_K_per_W": rth_igbt,
            "rth_fwd_K_per_W": rth_fwd,
            "delta_t_igbt_K": p_igbt * rth_igbt,
            "delta_t_fwd_K": p_fwd * rth_fwd,
            "tj_igbt_C": case_temp_C + p_igbt * rth_igbt,
            "tj_fwd_C": case_temp_C + p_fwd * rth_fwd,
        }

    def build_geometry_proxy(self) -> dict[str, Any]:
        return {
            "shape": "box_with_terminals",
            "label": self.static.part_number,
            "vendor": self.static.vendor,
            "device_type": self.static.device_type,
            "topology": self.static.topology,
            "body": {
                "length_mm": self.static.module_length_mm,
                "width_mm": self.static.module_width_mm,
                "height_mm": self.static.module_height_mm,
                "material": "power_module_with_baseplate",
                "mass_g": self.static.mass_g,
            },
            "source": f"{self.static.part_number} datasheet outline drawing, simplified proxy",
        }


def build_mitsubishi_igbt_module(part_number: str) -> MitsubishiIGBTModule:
    """Build one manifest-backed Mitsubishi module model."""

    normalized = normalize_mitsubishi_igbt_part_number(part_number)
    record = next((item for item in MITSUBISHI_IGBT_STATIC_MANIFEST if normalize_mitsubishi_igbt_part_number(item.part_number) == normalized), None)
    if record is None:
        raise KeyError(f"Mitsubishi module not found: {part_number}")
    validate_igbt_static_record(record)
    switch_xml = resolve_mitsubishi_igbt_data_path(record, record.igbt_xml_filename)
    diode_xml = resolve_mitsubishi_igbt_data_path(record, record.diode_xml_filename)
    if not switch_xml.exists():
        raise FileNotFoundError(f"{record.part_number}: switch XML not found: {switch_xml}")
    if not diode_xml.exists():
        raise FileNotFoundError(f"{record.part_number}: diode XML not found: {diode_xml}")
    switch_model = PlecsSemiconductorLossModel.from_xml(switch_xml)
    diode_model = switch_model if switch_xml == diode_xml else PlecsSemiconductorLossModel.from_xml(diode_xml)
    return MitsubishiIGBTModule(static=record, igbt_loss_model=switch_model, diode_loss_model=diode_model)


@lru_cache(maxsize=1)
def build_mitsubishi_igbt_modules() -> list[MitsubishiIGBTModule]:
    """Build all manifest-backed Mitsubishi modules."""

    _validate_manifest()
    return [build_mitsubishi_igbt_module(record.part_number) for record in MITSUBISHI_IGBT_STATIC_MANIFEST]


@lru_cache(maxsize=1)
def get_mitsubishi_devices() -> list[PowerDevice]:
    """Return Mitsubishi modules through the shared PowerDevice runtime path."""

    devices: list[PowerDevice] = []
    for module in build_mitsubishi_igbt_modules():
        devices.append(_build_runtime_device(module))
    return devices


def build_mitsubishi_devices() -> list[PowerDevice]:
    """Compatibility alias for vendor-level device composition."""

    return get_mitsubishi_devices()


def _validate_manifest() -> None:
    seen: set[str] = set()
    for record in MITSUBISHI_IGBT_STATIC_MANIFEST:
        validate_igbt_static_record(record)
        normalized = normalize_mitsubishi_igbt_part_number(record.part_number)
        if normalized in seen:
            raise ValueError(f"Duplicate Mitsubishi part in manifest: {record.part_number}")
        seen.add(normalized)


def _average(values: Sequence[float], dt_s: float | Sequence[float] | None = None) -> float:
    if not values:
        return 0.0
    if dt_s is None or isinstance(dt_s, (int, float)):
        return sum(values) / len(values)
    weights = [float(x) for x in dt_s]
    if len(weights) != len(values):
        raise ValueError("dt_s sequence length must match waveform length")
    total_time = sum(weights)
    if total_time <= 0:
        raise ValueError("sum(dt_s) must be positive")
    return sum(v * w for v, w in zip(values, weights)) / total_time


def _build_runtime_device(module: MitsubishiIGBTModule) -> PowerDevice:
    record = module.static
    effective_rds_on_25c = max(record.vce_sat_typ_25C_V / max(record.ic_cont_A, 1e-6), 1e-6)
    effective_rds_on_150c = max(record.vce_sat_typ_150C_V / max(record.ic_cont_A, 1e-6), effective_rds_on_25c)
    static_record = DeviceStaticRecord(
        part_number=record.part_number,
        vendor="Mitsubishi",
        device_type=record.device_type,
        technology=_infer_technology(record),
        package=record.package,
        marking=record.part_number,
        vdss_max_V=record.vces_max_V,
        # The shared selector still names these compatibility fields after MOSFET datasheets.
        # For Mitsubishi IGBT modules they intentionally carry the IGBT collector-current limits.
        id_cont_25C_A=record.ic_cont_A,
        id_cont_100C_A=record.ic_cont_A,
        id_pulse_A=record.ic_pulse_A,
        if_cont_A=record.ie_cont_A,
        if_pulse_A=record.ie_pulse_A,
        vgs_static_min_V=record.vge_min_V,
        vgs_static_max_V=record.vge_max_V,
        vgs_dynamic_min_V=record.vge_min_V,
        vgs_dynamic_max_V=record.vge_max_V,
        power_dissipation_25C_W=max(record.vce_sat_typ_125C_V * record.ic_cont_A, 1.0),
        tj_min_C=record.tj_min_C,
        tj_max_C=record.tj_max_C,
        tj_extended_max_C=record.tj_abs_max_C,
        eas_single_mJ=record.eon_ref_mJ + record.eoff_ref_mJ,
        ear_repetitive_mJ=record.err_ref_mJ,
        ias_single_A=record.ic_pulse_A,
        dvdt_mosfet_V_per_ns=0.0,
        dvdt_diode_V_per_ns=0.0,
        didt_diode_A_per_us=0.0,
        vgs_th_min_V=0.0,
        vgs_th_typ_V=0.0,
        vgs_th_max_V=0.0,
        rds_on_typ_25C_Ohm=effective_rds_on_25c,
        rds_on_max_25C_Ohm=effective_rds_on_25c,
        rds_on_typ_150C_Ohm=effective_rds_on_150c,
        rg_int_typ_Ohm=record.rg_int_typ_Ohm,
        ciss_typ_pF=0.0,
        coss_typ_pF=0.0,
        co_er_typ_pF=0.0,
        co_tr_typ_pF=0.0,
        td_on_ns=0.0,
        tr_ns=0.0,
        td_off_ns=0.0,
        tf_ns=0.0,
        qgs_nC=0.0,
        qgd_nC=0.0,
        qg_total_nC=0.0,
        vplateau_V=0.0,
        vsd_typ_V=record.vec_typ_125C_V,
        trr_typ_ns=record.trr_typ_ns,
        trr_max_ns=record.trr_typ_ns,
        qrr_typ_uC=record.qrr_typ_uC,
        qrr_max_uC=record.qrr_typ_uC,
        irrm_typ_A=0.0,
        rth_jc_K_per_W=max(record.rth_jc_igbt_K_per_W, record.rth_jc_fwd_K_per_W),
        rth_ja_K_per_W=max(record.rth_jc_igbt_K_per_W, record.rth_jc_fwd_K_per_W) + record.rth_cs_module_K_per_W,
        datasheet_rev="manifest",
        datasheet_date="",
        rth_cs_K_per_W=record.rth_cs_module_K_per_W,
        family=_infer_family(record.part_number),
        manufacturer="Mitsubishi",
        is_module=True,
        module_length_mm=record.module_length_mm,
        module_width_mm=record.module_width_mm,
        module_height_mm=record.module_height_mm,
        mass_g=record.mass_g,
        diode_subtype="jbs" if "jbs" in record.device_type.casefold() else ("module_diode" if "mosfet" in record.device_type.casefold() else "fwd"),
        module_group_id=record.part_number,
        module_section_role="module_switch",
        has_internal_diode_section=True,
        internal_diode_model_available=module.has_separate_diode_xml,
    )
    dynamic = DeviceDynamicModel(
        source_name=record.igbt_xml_filename,
        notes=[
            f"Mitsubishi module runtime wrapper for {record.part_number}.",
            f"Normalized device type: {classify_runtime_device_type(record.device_type)}.",
        ],
    )
    return PowerDevice(static=static_record, dynamic=dynamic, payload=module)


def _infer_family(part_number: str) -> str:
    match = re.match(r"([A-Z]+)", part_number.upper())
    return match.group(1) if match is not None else ""


def _infer_technology(record: IGBTStaticRecord) -> str:
    device_type = record.device_type.casefold()
    if "sic" in device_type and "mosfet" in device_type:
        return "SiC MOSFET"
    if "hybrid" in device_type:
        return "Hybrid IGBT"
    if "mosfet" in device_type:
        return "MOSFET"
    return "IGBT"


__all__ = [
    "MITSUBISHI_IGBT_STATIC_MANIFEST",
    "MITSUBISHI_IGBT_XML_SUBDIR",
    "MitsubishiIGBTModule",
    "build_mitsubishi_devices",
    "build_mitsubishi_igbt_module",
    "build_mitsubishi_igbt_modules",
    "get_mitsubishi_devices",
    "normalize_mitsubishi_igbt_part_number",
    "resolve_mitsubishi_igbt_data_path",
]
