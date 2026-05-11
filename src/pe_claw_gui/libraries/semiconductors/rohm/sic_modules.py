"""ROHM BSM SiC module registrations."""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from pathlib import Path
import re
from typing import Mapping, Sequence
try:
    from ..sic_module_models import SiCModuleStaticRecord, PlecsSiCSemiconductorLossModel, validate_sic_module_static_record
except ImportError:
    from pe_claw_gui.libraries.semiconductors.sic_module_models import SiCModuleStaticRecord, PlecsSiCSemiconductorLossModel, validate_sic_module_static_record  # type: ignore
_DEVICE_PACKAGE="pe_claw_gui.libraries.semiconductors.rohm"
ROHM_BSM_XML_SUBDIR="data"
def _record(part_number, device_type, topology, package, vdss, id_cont, id_pulse, tj_min, tj_max, tj_abs, vds25, vds125, vds150, vf25, vf125, vf150, eon, eoff, err, rth_mos, rth_sbd, rth_cs, length, width, height, mass, datasheet, switch_xml, sbd_xml):
    return SiCModuleStaticRecord(vendor="ROHM",part_number=part_number,device_type=device_type,topology=topology,package=package,vdss_max_V=vdss,id_cont_A=id_cont,id_pulse_A=id_pulse,is_cont_A=id_cont,is_pulse_A=id_pulse,vgs_min_V=-6.0,vgs_max_V=22.0,vgs_drive_on_V=18.0,vgs_drive_off_V=0.0,tj_min_C=tj_min,tj_max_C=tj_max,tj_abs_max_C=tj_abs,vds_on_typ_25C_V=max(vds25,0.001),vds_on_typ_125C_V=max(vds125,0.001),vds_on_typ_150C_V=max(vds150,0.001),sbd_vf_typ_25C_V=max(vf25,0.001),sbd_vf_typ_125C_V=max(vf125,0.001),sbd_vf_typ_150C_V=max(vf150,0.001),eon_ref_mJ=max(eon,0.001),eoff_ref_mJ=max(eoff,0.001),err_ref_mJ=max(err,0.001),rth_jc_mosfet_K_per_W=max(rth_mos,0.001),rth_jc_sbd_K_per_W=max(rth_sbd,0.001),rth_cs_module_K_per_W=max(rth_cs,0.001),module_length_mm=length,module_width_mm=width,module_height_mm=height,mass_g=mass,datasheet_filename=datasheet,mosfet_xml_filename=switch_xml,sbd_xml_filename=sbd_xml)
BSM080D12P2C008_STATIC = _record('BSM080D12P2C008', 'SiC MOSFET module with SBD', 'half_bridge', 'rohm_bsm_sic_module', 1200, 80, 160, -40.0, 175, 175, 2.813, 4.249, 4.82, 1.668, 2.16, 2.312, 1.534, 0.32, 0.001, 0.24558, 0.31428, 0.01, 108, 62, 30, 120, 'BSM080D12P2C008.pdf', 'BSM080D12P2C008_DMOS.xml', 'BSM080D12P2C008_SBD.xml')
BSM120C12P2C201_STATIC = _record('BSM120C12P2C201', 'SiC MOSFET module with SBD', 'half_bridge', 'rohm_bsm_sic_module', 1200, 120, 240, -40.0, 175, 175, 0, 0, 0, 1.698, 2.206, 2.398, 2.299, 1.2, 0.001, 0.15823, 0.2074, 0.01, 108, 62, 30, 120, 'BSM120C12P2C201.pdf', 'BSM120C12P2C201_DMOS.xml', 'BSM120C12P2C201_SBD.xml')
BSM120D12P2C005_STATIC = _record('BSM120D12P2C005', 'SiC MOSFET module with SBD', 'half_bridge', 'rohm_bsm_sic_module', 1200, 120, 240, -40.0, 175, 175, 2.1, 3.058, 3.442, 1.698, 2.206, 2.398, 3.07, 1.024, 0.001, 0.15766, 0.2069, 0.01, 108, 62, 30, 120, 'BSM120D12P2C005.pdf', 'BSM120D12P2C005_DMOS.xml', 'BSM120D12P2C005_SBD.xml')
BSM180C12P2E202_STATIC = _record('BSM180C12P2E202', 'SiC MOSFET module with SBD', 'half_bridge', 'rohm_bsm_sic_module', 1200, 180, 360, -40.0, 175, 175, 0, 0, 0, 1.565, 2.0204, 2.1658, 5.641, 1.589, 0.001, 0.10812, 0.1376, 0.01, 122, 62, 35, 250, 'BSM180C12P2E202.pdf', 'BSM180C12P2E202_DMOS.xml', 'BSM180C12P2E202_SBD.xml')
BSM180C12P3C202_STATIC = _record('BSM180C12P3C202', 'SiC MOSFET module with SBD', 'half_bridge', 'rohm_bsm_sic_module', 1200, 180, 360, -40.0, 175, 175, 0, 0, 0, 2.0752, 2.9162, 3.228, 2.695, 4.1, 0.001, 0.16309, 0.13767, 0.01, 108, 62, 30, 120, 'BSM180C12P3C202.pdf', 'BSM180C12P3C202_UMOS.xml', 'BSM180C12P3C202_SBD.xml')
BSM180D12P2C101_STATIC = _record('BSM180D12P2C101', 'SiC MOSFET module', 'half_bridge', 'rohm_bsm_sic_module', 1200, 180, 360, -40.0, 175, 175, 0, 0, 0, 0, 0, 0, 9.566, 2.135, 0.001, 0.1082321, 0.1082321, 0.01, 108, 62, 30, 120, 'BSM180D12P2C101.pdf', 'BSM180D12P2C101_DMOS.xml', 'BSM180D12P2C101_DMOS.xml')
BSM180D12P2E002_STATIC = _record('BSM180D12P2E002', 'SiC MOSFET module with SBD', 'half_bridge', 'rohm_bsm_sic_module', 1200, 180, 360, -40.0, 175, 175, 2.215, 3.119, 3.521, 1.565, 2.0204, 2.1658, 5.641, 1.589, 0.001, 0.10812, 0.1376, 0.01, 122, 62, 35, 250, 'BSM180D12P2E002.pdf', 'BSM180D12P2E002_DMOS.xml', 'BSM180D12P2E002_SBD.xml')
BSM180D12P3C007_STATIC = _record('BSM180D12P3C007', 'SiC MOSFET module with SBD', 'half_bridge', 'rohm_bsm_sic_module', 1200, 180, 360, -40.0, 175, 175, 1.82, 2.737, 3.099, 2.1162, 2.729, 2.915, 8.74, 4.38, 0.001, 0.16928, 0.20912, 0.01, 108, 62, 30, 120, 'BSM180D12P3C007.pdf', 'BSM180D12P3C007_UMOS.xml', 'BSM180D12P3C007_SBD.xml')
BSM250D17P2E004_STATIC = _record('BSM250D17P2E004', 'SiC MOSFET module with SBD', 'half_bridge', 'rohm_bsm_sic_module', 1700, 250, 500, -40.0, 175, 175, 1.986, 3.191, 3.659, 2.28225, 3.2295, 3.4935, 17.88, 10.48, 0.001, 0.08268, 0.11355, 0.01, 122, 62, 35, 250, 'BSM250D17P2E004.pdf', 'BSM250D17P2E004_DMOS.xml', 'BSM250D17P2E004_SBD.xml')
BSM300C12P3E201_STATIC = _record('BSM300C12P3E201', 'SiC MOSFET module with SBD', 'half_bridge', 'rohm_bsm_sic_module', 1200, 300, 600, -40.0, 175, 175, 0, 0, 0, 1.577, 2.19, 2.339, 4.72, 6.58, 0.001, 0.13245, 0.13245, 0.01, 122, 62, 35, 250, 'BSM300C12P3E201.pdf', 'BSM300C12P3E201_UMOS.xml', 'BSM300C12P3E201_SBD.xml')
BSM300C12P3E301_STATIC = _record('BSM300C12P3E301', 'SiC MOSFET module with SBD', 'half_bridge', 'rohm_bsm_sic_module', 1200, 300, 600, -40.0, 175, 175, 0, 0, 0, 1.577, 2.19, 2.339, 6.15, 9.14, 0.001, 0.13245, 0.13245, 0.01, 122, 62, 35, 250, 'BSM300C12P3E301.pdf', 'BSM300C12P3E301_UMOS.xml', 'BSM300C12P3E301_SBD.xml')
BSM300D12P2E001_STATIC = _record('BSM300D12P2E001', 'SiC MOSFET module with SBD', 'half_bridge', 'rohm_bsm_sic_module', 1200, 300, 600, -40.0, 175, 175, 2.182, 3.007, 3.362, 1.577, 2.19, 2.339, 12.5, 13.07, 0.001, 0.079685, 0.101927, 0.01, 122, 62, 35, 250, 'BSM300D12P2E001.pdf', 'BSM300D12P2E001_DMOS.xml', 'BSM300D12P2E001_SBD.xml')
BSM300D12P3E005_STATIC = _record('BSM300D12P3E005', 'SiC MOSFET module with SBD', 'half_bridge', 'rohm_bsm_sic_module', 1200, 300, 600, -40.0, 175, 175, 1.665, 2.457, 2.776, 2.04, 2.608, 2.771, 11.4, 8.79, 0.001, 0.11758, 0.15676, 0.01, 122, 62, 35, 250, 'BSM300D12P3E005.pdf', 'BSM300D12P3E005_UMOS.xml', 'BSM300D12P3E005_SBD.xml')
BSM300D12P4G101_STATIC = _record('BSM300D12P4G101', 'SiC MOSFET module', 'half_bridge', 'rohm_bsm_sic_module', 1200, 300, 600, -40.0, 175, 175, 0, 0, 0, 0, 0, 0, 4.6, 5.34, 0.001, 0.156596, 0.156596, 0.01, 152, 75, 35, 450, 'BSM300D12P4G101.pdf', 'BSM300D12P4G101_UMOS.xml', 'BSM300D12P4G101_UMOS.xml')
BSM400D12P2G003_STATIC = _record('BSM400D12P2G003', 'SiC MOSFET module with SBD', 'half_bridge', 'rohm_bsm_sic_module', 1200, 400, 800, -40.0, 175, 175, 2.3, 3.321, 3.773, 1.755, 2.262, 2.432, 16.25, 10.33, 0.001, 0.061, 0.08, 0.01, 152, 75, 35, 450, 'BSM400D12P2G003.pdf', 'BSM400D12P2G003_DMOS.xml', 'BSM400D12P2G003_SBD.xml')
BSM400D12P3G002_STATIC = _record('BSM400D12P3G002', 'SiC MOSFET module with SBD', 'half_bridge', 'rohm_bsm_sic_module', 1200, 400, 800, -40.0, 175, 175, 1.793, 2.627, 2.967, 2.121, 2.783, 2.968, 13.5, 10.61, 0.001, 0.09601, 0.12699, 0.01, 152, 75, 35, 450, 'BSM400D12P3G002.pdf', 'BSM400D12P3G002_UMOS.xml', 'BSM400D12P3G002_SBD.xml')
BSM450D12P4G102_STATIC = _record('BSM450D12P4G102', 'SiC MOSFET module', 'half_bridge', 'rohm_bsm_sic_module', 1200, 450, 900, -40.0, 175, 175, 0, 0, 0, 0, 0, 0, 11.105, 15.57, 0.001, 0.099025, 0.099025, 0.01, 152, 75, 35, 450, 'BSM450D12P4G102.pdf', 'BSM450D12P4G102_UMOS.xml', 'BSM450D12P4G102_UMOS.xml')
BSM600D12P3G001_STATIC = _record('BSM600D12P3G001', 'SiC MOSFET module with SBD', 'half_bridge', 'rohm_bsm_sic_module', 1200, 600, 1200, -40.0, 175, 175, 1.848, 2.559, 2.878, 2.012, 2.653, 2.845, 21.78, 24.75, 0.001, 0.061, 0.08, 0.01, 152, 75, 35, 450, 'BSM600D12P3G001.pdf', 'BSM600D12P3G001_UMOS.xml', 'BSM600D12P3G001_SBD.xml')
BSM600D12P4G103_STATIC = _record('BSM600D12P4G103', 'SiC MOSFET module', 'half_bridge', 'rohm_bsm_sic_module', 1200, 600, 1200, -40.0, 175, 175, 0, 0, 0, 0, 0, 0, 17.09, 19.48, 0.001, 0.080855, 0.080855, 0.01, 152, 75, 35, 450, 'BSM600D12P4G103.pdf', 'BSM600D12P4G103_UMOS.xml', 'BSM600D12P4G103_UMOS.xml')
BSM400C12P3G202_STATIC = _record('BSM400C12P3G202', 'SiC MOSFET module with SBD', 'chopper', 'rohm_bsm_sic_module', 1200, 400, 800, -40.0, 150, 175, 2.5, 2.6, 3.0, 1.7, 2.0, 2.1, 7.72, 11.67, 0.001, 0.096, 0.080, 0.015, 152, 75, 35, 450, 'BSM400C12P3G202.pdf', 'BSM400C12P3G202_DMOS.xml', 'BSM400C12P3G202_SBD.xml')
BSM600C12P3G201_STATIC = _record('BSM600C12P3G201', 'SiC MOSFET module with SBD', 'chopper', 'rohm_bsm_sic_module', 1200, 600, 1200, -40.0, 150, 175, 1.8, 2.6, 2.9, 1.8, 2.4, 2.6, 9.58, 25.28, 0.001, 0.061, 0.061, 0.015, 152, 75, 35, 450, 'BSM600C12P3G201.pdf', 'BSM600C12P3G201_DMOS.xml', 'BSM600C12P3G201_SBD.xml')
ROHM_BSM_STATIC_MANIFEST: tuple[SiCModuleStaticRecord, ...] = (
    BSM080D12P2C008_STATIC, BSM120C12P2C201_STATIC, BSM120D12P2C005_STATIC, BSM180C12P2E202_STATIC, BSM180C12P3C202_STATIC, BSM180D12P2C101_STATIC, BSM180D12P2E002_STATIC, BSM180D12P3C007_STATIC, BSM250D17P2E004_STATIC, BSM300C12P3E201_STATIC, BSM300C12P3E301_STATIC, BSM300D12P2E001_STATIC, BSM300D12P3E005_STATIC, BSM300D12P4G101_STATIC, BSM400C12P3G202_STATIC, BSM400D12P2G003_STATIC, BSM400D12P3G002_STATIC, BSM450D12P4G102_STATIC, BSM600C12P3G201_STATIC, BSM600D12P3G001_STATIC, BSM600D12P4G103_STATIC,
)
def normalize_rohm_bsm_part_number(filename_or_part: str) -> str:
    stem=Path(filename_or_part).stem.upper(); stem=re.sub(r"_(DMOS|UMOS|SBD|MOSFET|DIODE)$","",stem); clean=re.sub(r"[^A-Z0-9]","",stem); known={re.sub(r"[^A-Z0-9]","",r.part_number):r.part_number for r in ROHM_BSM_STATIC_MANIFEST}; return known.get(clean,clean)
def _part_data_subdir(part_number: str) -> str: return normalize_rohm_bsm_part_number(part_number).lower()
def resolve_rohm_bsm_data_path(record: SiCModuleStaticRecord, filename: str) -> Path:
    subdir=_part_data_subdir(record.part_number)
    try: return Path(str(resources.files(_DEVICE_PACKAGE).joinpath(ROHM_BSM_XML_SUBDIR,subdir,filename)))
    except Exception: return Path(__file__).resolve().parent/ROHM_BSM_XML_SUBDIR/subdir/filename
@dataclass(frozen=True)
class RohmSiCModule:
    static: SiCModuleStaticRecord; mosfet_loss_model: PlecsSiCSemiconductorLossModel; sbd_loss_model: PlecsSiCSemiconductorLossModel|None=None
    @property
    def has_separate_sbd_xml(self)->bool: return self.sbd_loss_model is not None and self.static.sbd_xml_filename!=self.static.mosfet_xml_filename
    def eon_mJ(self,id_A,vds_V,tj_C,rg_on_Ohm):
        if self.mosfet_loss_model.turn_on is None: return 0.0
        return 1000*self.mosfet_loss_model.turn_on.energy_J(id_A,vds_V,tj_C,variables={'Rg_on':rg_on_Ohm,'RgOn':rg_on_Ohm,'RGOn':rg_on_Ohm,'Rg':rg_on_Ohm},custom_tables_3d=self.mosfet_loss_model.custom_tables_3d,custom_tables_2d=self.mosfet_loss_model.custom_tables_2d)
    def eoff_mJ(self,id_A,vds_V,tj_C,rg_off_Ohm):
        if self.mosfet_loss_model.turn_off is None: return 0.0
        return 1000*self.mosfet_loss_model.turn_off.energy_J(id_A,vds_V,tj_C,variables={'Rg_off':rg_off_Ohm,'RgOff':rg_off_Ohm,'RGOff':rg_off_Ohm,'Rg':rg_off_Ohm},custom_tables_3d=self.mosfet_loss_model.custom_tables_3d,custom_tables_2d=self.mosfet_loss_model.custom_tables_2d)
    def vds_on_V(self,id_A,tj_C):
        if self.mosfet_loss_model.conduction is None: raise ValueError(f"{self.static.part_number}: missing MOSFET conduction table")
        return abs(self.mosfet_loss_model.conduction.lookup(max(0.0,float(id_A)),tj_C))
    def sbd_vf_V(self,is_A,tj_C):
        if self.sbd_loss_model is None or self.sbd_loss_model.conduction is None: return self.vds_on_V(is_A,tj_C)
        return abs(self.sbd_loss_model.conduction.lookup(max(0.0,float(is_A)),tj_C))
    def err_mJ(self,is_A,vds_V,tj_C,rg_on_Ohm):
        if self.sbd_loss_model is None or self.sbd_loss_model.turn_off is None: return 0.0
        return 1000*self.sbd_loss_model.turn_off.energy_J(is_A,vds_V,tj_C,variables={'Rg_on':rg_on_Ohm,'Rg':rg_on_Ohm},custom_tables_3d=self.sbd_loss_model.custom_tables_3d,custom_tables_2d=self.sbd_loss_model.custom_tables_2d)
    def mosfet_conduction_loss_W(self,current_waveform_A:Sequence[float],tj_C,dt_s=None): return _average([self.vds_on_V(max(0.0,float(i)),tj_C)*max(0.0,float(i)) for i in current_waveform_A],dt_s)
    def sbd_conduction_loss_W(self,current_waveform_A:Sequence[float],tj_C,dt_s=None): return _average([self.sbd_vf_V(max(0.0,float(i)),tj_C)*max(0.0,float(i)) for i in current_waveform_A],dt_s)
    def mosfet_switching_loss_W(self,fsw_Hz,id_A,vds_V,tj_C,rg_on_Ohm,rg_off_Ohm): return fsw_Hz*(self.eon_mJ(id_A,vds_V,tj_C,rg_on_Ohm)+self.eoff_mJ(id_A,vds_V,tj_C,rg_off_Ohm))/1000.0
    def sbd_reverse_recovery_loss_W(self,fsw_Hz,is_A,vds_V,tj_C,rg_on_Ohm): return fsw_Hz*self.err_mJ(is_A,vds_V,tj_C,rg_on_Ohm)/1000.0
    def estimate_junction_temperature_C(self,losses:Mapping[str,float],case_temp_C,pulse_time_s=None,use_transient=False):
        pm=float(losses.get('p_mosfet_W',losses.get('p_mosfet_cond_W',0.0)+losses.get('p_mosfet_sw_W',0.0))); ps=float(losses.get('p_sbd_W',losses.get('p_sbd_cond_W',0.0)+losses.get('p_sbd_rr_W',0.0)))
        rm=self.static.rth_jc_mosfet_K_per_W; rs=self.static.rth_jc_sbd_K_per_W
        if use_transient and pulse_time_s is not None:
            if self.mosfet_loss_model.thermal is not None: rm=self.mosfet_loss_model.thermal.zth_K_per_W(pulse_time_s)
            if self.sbd_loss_model is not None and self.sbd_loss_model.thermal is not None: rs=self.sbd_loss_model.thermal.zth_K_per_W(pulse_time_s)
        return {'tj_mosfet_C':case_temp_C+pm*rm,'tj_sbd_C':case_temp_C+ps*rs,'delta_t_mosfet_K':pm*rm,'delta_t_sbd_K':ps*rs}
    def build_geometry_proxy(self): return {'shape':'box_with_power_terminals','body':{'length_mm':self.static.module_length_mm,'width_mm':self.static.module_width_mm,'height_mm':self.static.module_height_mm,'material':'ROHM BSM SiC module simplified envelope'},'terminals':['DC+','AC','DC-','G','S','SBD'],'label':self.static.part_number,'mass_g':self.static.mass_g}
def _average(values,dt_s):
    if not values: return 0.0
    if dt_s is None or isinstance(dt_s,(int,float)): return sum(values)/len(values)
    w=[float(x) for x in dt_s]
    if len(w)!=len(values): raise ValueError('dt_s sequence must match waveform length')
    total=sum(w)
    if total<=0: raise ValueError('sum(dt_s) must be positive')
    return sum(v*x for v,x in zip(values,w))/total
def build_rohm_bsm_static_record(part_number: str) -> SiCModuleStaticRecord:
    norm=normalize_rohm_bsm_part_number(part_number)
    for r in ROHM_BSM_STATIC_MANIFEST:
        if r.part_number==norm: return r
    raise KeyError(f"ROHM BSM SiC module not found: {part_number}")
def build_rohm_bsm_module(part_number: str) -> RohmSiCModule:
    r=build_rohm_bsm_static_record(part_number); validate_sic_module_static_record(r); mp=resolve_rohm_bsm_data_path(r,r.mosfet_xml_filename); sp=resolve_rohm_bsm_data_path(r,r.sbd_xml_filename)
    if not mp.exists(): raise FileNotFoundError(f"{r.part_number}: MOSFET XML resource not found: {mp}")
    mm=PlecsSiCSemiconductorLossModel.from_xml(mp); sm=PlecsSiCSemiconductorLossModel.from_xml(sp) if sp.exists() and r.sbd_xml_filename!=r.mosfet_xml_filename else None
    return RohmSiCModule(r,mm,sm)
@lru_cache(maxsize=1)
def build_rohm_bsm_modules() -> list[RohmSiCModule]: _validate_manifest(); return [build_rohm_bsm_module(r.part_number) for r in ROHM_BSM_STATIC_MANIFEST]
def _validate_manifest():
    seen=set(); dup=[]
    for r in ROHM_BSM_STATIC_MANIFEST:
        if r.part_number in seen: dup.append(r.part_number)
        seen.add(r.part_number); validate_sic_module_static_record(r); mp=resolve_rohm_bsm_data_path(r,r.mosfet_xml_filename)
        if not mp.exists(): raise FileNotFoundError(f"{r.part_number}: MOSFET XML missing: {mp}")
        sp=resolve_rohm_bsm_data_path(r,r.sbd_xml_filename)
        if r.sbd_xml_filename!=r.mosfet_xml_filename and not sp.exists(): raise FileNotFoundError(f"{r.part_number}: SBD XML missing: {sp}")
    if dup: raise ValueError('Duplicate ROHM BSM manifest parts: '+', '.join(sorted(dup)))
__all__=['ROHM_BSM_STATIC_MANIFEST','ROHM_BSM_XML_SUBDIR','RohmSiCModule','build_rohm_bsm_module','build_rohm_bsm_modules','build_rohm_bsm_static_record','normalize_rohm_bsm_part_number','resolve_rohm_bsm_data_path']
