"""ROHM RG series IGBT registrations.

PDFs are used for static/package audit only. Runtime data keeps XML files only.
"""
from __future__ import annotations
from functools import lru_cache
from importlib import resources
from pathlib import Path
import re
try:
    from ..igbt_discrete_models import IGBTDiscreteStaticRecord, RohmRGIGBTDevice, validate_igbt_discrete_static_record
    from ..sic_module_models import PlecsSiCSemiconductorLossModel
except ImportError:
    from pe_claw_gui.libraries.semiconductors.igbt_discrete_models import IGBTDiscreteStaticRecord, RohmRGIGBTDevice, validate_igbt_discrete_static_record  # type: ignore
    from pe_claw_gui.libraries.semiconductors.sic_module_models import PlecsSiCSemiconductorLossModel  # type: ignore
_DEVICE_PACKAGE = "pe_claw_gui.libraries.semiconductors.rohm"
ROHM_RG_XML_SUBDIR = "data_rg"

def _record(part_number, package, vces, ic, ipulse, rth_igbt, rth_frd, length, width, height, mass, datasheet, igbt_xml, frd_xml, has_frd, ie_cont=None, ie_pulse=None):
    if ie_cont is None:
        ie_cont = ic
    if ie_pulse is None:
        ie_pulse = ipulse
    return IGBTDiscreteStaticRecord(vendor="ROHM", part_number=part_number, device_type=("IGBT with FRD" if has_frd else "IGBT"), package=package, topology="discrete_switch", vces_max_V=float(vces), ic_cont_A=float(ic), ic_pulse_A=float(ipulse), ie_cont_A=float(ie_cont), ie_pulse_A=float(ie_pulse), vge_min_V=-10.0, vge_max_V=22.0, vge_drive_on_V=15.0, vge_drive_off_V=0.0, tj_min_C=-40.0, tj_max_C=175.0, tj_abs_max_C=175.0, rth_jc_igbt_K_per_W=float(rth_igbt), rth_jc_frd_K_per_W=float(rth_frd), rth_cs_K_per_W=0.0, module_length_mm=float(length), module_width_mm=float(width), module_height_mm=float(height), mass_g=float(mass), datasheet_filename=datasheet, igbt_xml_filename=igbt_xml, frd_xml_filename=frd_xml, has_frd_xml=bool(has_frd))

RGA80TSX2EHR_STATIC = _record('RGA80TSX2EHR', 'TO-247-4L', 1200, 69, 120, 0.32, 0.56, 15.9, 20.95, 5.3, 6.2, 'RGA80TSX2EHR.pdf', 'RGA80TSX2EHR_IGBT.xml', 'RGA80TSX2EHR_FRD.xml', True, 56, 120)
RGA80TSX2HR_STATIC = _record('RGA80TSX2HR', 'TO-247-4L', 1200, 69, 120, 0.32, 0.32, 15.9, 20.95, 5.3, 6.2, 'RGA80TSX2HR.pdf', 'RGA80TSX2HR_IGBT.xml', 'RGA80TSX2HR_IGBT.xml', False)
RGH00TRX2_STATIC = _record('RGH00TRX2', 'TO-247-3L', 1200, 57, 200, 0.44, 0.44, 15.9, 20.95, 5.3, 6.0, 'RGH00TRX2.pdf', 'RGH00TRX2_IGBT.xml', 'RGH00TRX2_IGBT.xml', False)
RGH00TRX2EF_STATIC = _record('RGH00TRX2EF', 'TO-247-3L', 1200, 57, 200, 0.44, 0.54, 15.9, 20.95, 5.3, 6.0, 'RGH00TRX2EF.pdf', 'RGH00TRX2EF_IGBT.xml', 'RGH00TRX2EF_FRD.xml', True, 52, 200)
RGH00TSX2_STATIC = _record('RGH00TSX2', 'TO-247-3L', 1200, 57, 200, 0.44, 0.44, 15.9, 20.95, 5.3, 6.0, 'RGH00TSX2.pdf', 'RGH00TSX2_IGBT.xml', 'RGH00TSX2_IGBT.xml', False)
RGH00TSX2EF_STATIC = _record('RGH00TSX2EF', 'TO-247-3L', 1200, 57, 200, 0.44, 0.54, 15.9, 20.95, 5.3, 6.0, 'RGH00TSX2EF.pdf', 'RGH00TSX2EF_IGBT.xml', 'RGH00TSX2EF_FRD.xml', True, 52, 200)
RGH00TSX2EFHR_STATIC = _record('RGH00TSX2EFHR', 'TO-247-4L', 1200, 57, 200, 0.44, 0.54, 15.9, 20.95, 5.3, 6.2, 'RGH00TSX2EFHR.pdf', 'RGH00TSX2EFHR_IGBT.xml', 'RGH00TSX2EFHR_FRD.xml', True, 52, 200)
RGH00TSX2HR_STATIC = _record('RGH00TSX2HR', 'TO-247-4L', 1200, 57, 200, 0.44, 0.44, 15.9, 20.95, 5.3, 6.2, 'RGH00TSX2HR.pdf', 'RGH00TSX2HR_IGBT.xml', 'RGH00TSX2HR_IGBT.xml', False)
RGH80TRX2_STATIC = _record('RGH80TRX2', 'TO-247-3L', 1200, 49, 160, 0.5, 0.5, 15.9, 20.95, 5.3, 6.0, 'RGH80TRX2.pdf', 'RGH80TRX2_IGBT.xml', 'RGH80TRX2_IGBT.xml', False)
RGH80TRX2EF_STATIC = _record('RGH80TRX2EF', 'TO-247-3L', 1200, 49, 160, 0.5, 0.65, 15.9, 20.95, 5.3, 6.0, 'RGH80TRX2EF.pdf', 'RGH80TRX2EF_IGBT.xml', 'RGH80TRX2EF_FRD.xml', True, 41, 160)
RGH80TSX2_STATIC = _record('RGH80TSX2', 'TO-247-3L', 1200, 49, 160, 0.5, 0.5, 15.9, 20.95, 5.3, 6.0, 'RGH80TSX2EF.pdf', 'RGH80TSX2_IGBT.xml', 'RGH80TSX2_IGBT.xml', False)
RGH80TSX2EF_STATIC = _record('RGH80TSX2EF', 'TO-247-3L', 1200, 49, 160, 0.5, 0.65, 15.9, 20.95, 5.3, 6.0, 'RGH80TSX2EF.pdf', 'RGH80TSX2EF_IGBT.xml', 'RGH80TSX2EF_FRD.xml', True, 41, 160)
RGH80TSX2EFHR_STATIC = _record('RGH80TSX2EFHR', 'TO-247-4L', 1200, 49, 160, 0.5, 0.65, 15.9, 20.95, 5.3, 6.2, 'RGH80TSX2EFHR.pdf', 'RGH80TSX2EFHR_IGBT.xml', 'RGH80TSX2EFHR_FRD.xml', True, 41, 160)
RGH80TSX2HR_STATIC = _record('RGH80TSX2HR', 'TO-247-4L', 1200, 49, 160, 0.5, 0.5, 15.9, 20.95, 5.3, 6.2, 'RGH80TSX2HR.pdf', 'RGH80TSX2HR_IGBT.xml', 'RGH80TSX2HR_IGBT.xml', False)
RGHX5TRX2_STATIC = _record('RGHX5TRX2', 'TO-247-3L', 1200, 79, 300, 0.33, 0.33, 15.9, 20.95, 5.3, 6.0, 'RGHX5TRX2.pdf', 'RGHX5TRX2_IGBT.xml', 'RGHX5TRX2_IGBT.xml', False)
RGHX5TRX2DF_STATIC = _record('RGHX5TRX2DF', 'TO-247-3L', 1200, 79, 300, 0.33, 0.46, 15.9, 20.95, 5.3, 6.0, 'RGHX5TRX2DF.pdf', 'RGHX5TRX2DF_IGBT.xml', 'RGHX5TRX2DF_FRD.xml', True, 61, 300)
RGHX5TSX2_STATIC = _record('RGHX5TSX2', 'TO-247-3L', 1200, 79, 300, 0.33, 0.33, 15.9, 20.95, 5.3, 6.0, 'RGHX5TSX2.pdf', 'RGHX5TSX2_IGBT.xml', 'RGHX5TSX2_IGBT.xml', False)
RGHX5TSX2DF_STATIC = _record('RGHX5TSX2DF', 'TO-247-3L', 1200, 79, 300, 0.33, 0.46, 15.9, 20.95, 5.3, 6.0, 'RGHX5TSX2DF.pdf', 'RGHX5TSX2DF_IGBT.xml', 'RGHX5TSX2DF_FRD.xml', True, 61, 300)
RGHX5TSX2DFHR_STATIC = _record('RGHX5TSX2DFHR', 'TO-247-4L', 1200, 79, 300, 0.33, 0.46, 15.9, 20.95, 5.3, 6.2, 'RGHX5TSX2DFHR.pdf', 'RGHX5TSX2DFHR_IGBT.xml', 'RGHX5TSX2DFHR_FRD.xml', True, 61, 300)
RGHX5TSX2HR_STATIC = _record('RGHX5TSX2HR', 'TO-247-4L', 1200, 79, 300, 0.33, 0.33, 15.9, 20.95, 5.3, 6.2, 'RGHX5TSX2HR.pdf', 'RGHX5TSX2HR_IGBT.xml', 'RGHX5TSX2HR_IGBT.xml', False)
RGS50TSX2DHR_STATIC = _record('RGS50TSX2DHR', 'TO-247-4L', 1200, 25, 75, 0.38, 0.8, 15.9, 20.95, 5.3, 6.2, 'RGS50TSX2DHR.pdf', 'RGS50TSX2DHR_IGBT.xml', 'RGS50TSX2DHR_FRD.xml', True, 25, 75)
RGW00TS65EHR_STATIC = _record('RGW00TS65EHR', 'TO-247-4L', 650, 50, 200, 0.59, 0.8, 15.9, 20.95, 5.3, 6.2, 'RGW00TS65EHR.pdf', 'RGW00TS65EHR_IGBT.xml', 'RGW00TS65EHR_FRD.xml', True, 50, 200)
RGW80TS65EHR_STATIC = _record('RGW80TS65EHR', 'TO-247-4L', 650, 40, 160, 0.7, 0.93, 15.9, 20.95, 5.3, 6.2, 'RGW80TS65EHR.pdf', 'RGW80TS65EHR_IGBT.xml', 'RGW80TS65EHR_FRD.xml', True, 43, 160)
RGWX5TS65EHR_STATIC = _record('RGWX5TS65EHR', 'TO-247-4L', 650, 75, 300, 0.43, 0.57, 15.9, 20.95, 5.3, 6.2, 'RGWX5TS65EHR.pdf', 'RGWX5TS65EHR_IGBT.xml', 'RGWX5TS65EHR_FRD.xml', True, 80, 300)
ROHM_RG_STATIC_MANIFEST: tuple[IGBTDiscreteStaticRecord, ...] = (
    RGA80TSX2EHR_STATIC, RGA80TSX2HR_STATIC, RGH00TRX2_STATIC, RGH00TRX2EF_STATIC, RGH00TSX2_STATIC, RGH00TSX2EF_STATIC, RGH00TSX2EFHR_STATIC, RGH00TSX2HR_STATIC, RGH80TRX2_STATIC, RGH80TRX2EF_STATIC, RGH80TSX2_STATIC, RGH80TSX2EF_STATIC, RGH80TSX2EFHR_STATIC, RGH80TSX2HR_STATIC, RGHX5TRX2_STATIC, RGHX5TRX2DF_STATIC, RGHX5TSX2_STATIC, RGHX5TSX2DF_STATIC, RGHX5TSX2DFHR_STATIC, RGHX5TSX2HR_STATIC, RGS50TSX2DHR_STATIC, RGW00TS65EHR_STATIC, RGW80TS65EHR_STATIC, RGWX5TS65EHR_STATIC,
)


def normalize_rohm_rg_part_number(filename_or_part: str) -> str:
    stem = Path(filename_or_part).stem.upper()
    stem = re.sub(r"_(IGBT|FRD)$", "", stem)
    clean = re.sub(r"[^A-Z0-9]", "", stem)
    known = {re.sub(r"[^A-Z0-9]", "", r.part_number): r.part_number for r in ROHM_RG_STATIC_MANIFEST}
    return known.get(clean, clean)

def _part_data_subdir(part_number: str) -> str:
    return normalize_rohm_rg_part_number(part_number).lower()

def resolve_rohm_rg_data_path(record: IGBTDiscreteStaticRecord, filename: str) -> Path:
    subdir = _part_data_subdir(record.part_number)
    try:
        return Path(str(resources.files(_DEVICE_PACKAGE).joinpath(ROHM_RG_XML_SUBDIR, subdir, filename)))
    except Exception:
        return Path(__file__).resolve().parent / ROHM_RG_XML_SUBDIR / subdir / filename

def build_rohm_rg_static_record(part_number: str) -> IGBTDiscreteStaticRecord:
    norm = normalize_rohm_rg_part_number(part_number)
    for record in ROHM_RG_STATIC_MANIFEST:
        if record.part_number == norm:
            return record
    raise KeyError(f"ROHM RG IGBT not found: {part_number}")

def build_rohm_rg_igbt(part_number: str) -> RohmRGIGBTDevice:
    record = build_rohm_rg_static_record(part_number)
    validate_igbt_discrete_static_record(record)
    igbt_path = resolve_rohm_rg_data_path(record, record.igbt_xml_filename)
    if not igbt_path.exists():
        raise FileNotFoundError(f"{record.part_number}: IGBT XML missing: {igbt_path}")
    igbt_model = PlecsSiCSemiconductorLossModel.from_xml(igbt_path)
    frd_model = None
    if record.has_frd_xml:
        frd_path = resolve_rohm_rg_data_path(record, record.frd_xml_filename)
        if not frd_path.exists():
            raise FileNotFoundError(f"{record.part_number}: FRD XML missing: {frd_path}")
        frd_model = PlecsSiCSemiconductorLossModel.from_xml(frd_path)
    return RohmRGIGBTDevice(record, igbt_model, frd_model)

@lru_cache(maxsize=1)
def build_rohm_rg_igbts() -> list[RohmRGIGBTDevice]:
    _validate_manifest()
    return [build_rohm_rg_igbt(record.part_number) for record in ROHM_RG_STATIC_MANIFEST]


def build_rohm_rg_igbt_devices() -> list[RohmRGIGBTDevice]:
    """Compatibility alias using the registry-facing plural naming pattern."""

    return build_rohm_rg_igbts()

def _validate_manifest() -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for record in ROHM_RG_STATIC_MANIFEST:
        if record.part_number in seen:
            duplicates.append(record.part_number)
        seen.add(record.part_number)
        validate_igbt_discrete_static_record(record)
        igbt_path = resolve_rohm_rg_data_path(record, record.igbt_xml_filename)
        if not igbt_path.exists():
            raise FileNotFoundError(f"{record.part_number}: IGBT XML missing: {igbt_path}")
        if record.has_frd_xml:
            frd_path = resolve_rohm_rg_data_path(record, record.frd_xml_filename)
            if not frd_path.exists():
                raise FileNotFoundError(f"{record.part_number}: FRD XML missing: {frd_path}")
    if duplicates:
        raise ValueError("Duplicate ROHM RG manifest parts: " + ", ".join(sorted(duplicates)))

__all__ = [
    "ROHM_RG_STATIC_MANIFEST",
    "ROHM_RG_XML_SUBDIR",
    "RohmRGIGBTDevice",
    "build_rohm_rg_igbt",
    "build_rohm_rg_igbt_devices",
    "build_rohm_rg_igbts",
    "build_rohm_rg_static_record",
    "normalize_rohm_rg_part_number",
    "resolve_rohm_rg_data_path",
]
