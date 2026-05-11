"""Discrete IGBT/FRD static records and helpers for ROHM RG series."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import math
from typing import Mapping, Sequence
try:
    from .sic_module_models import PlecsSiCSemiconductorLossModel
except ImportError:
    from pe_claw_gui.libraries.semiconductors.sic_module_models import PlecsSiCSemiconductorLossModel  # type: ignore

@dataclass(frozen=True)
class IGBTDiscreteStaticRecord:
    vendor: str
    part_number: str
    device_type: str
    package: str
    topology: str
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
    rth_jc_igbt_K_per_W: float
    rth_jc_frd_K_per_W: float
    rth_cs_K_per_W: float
    module_length_mm: float
    module_width_mm: float
    module_height_mm: float
    mass_g: float
    datasheet_filename: str
    igbt_xml_filename: str
    frd_xml_filename: str
    has_frd_xml: bool = True

def validate_igbt_discrete_static_record(r: IGBTDiscreteStaticRecord) -> None:
    for n in ['vendor','part_number','device_type','package','topology','datasheet_filename','igbt_xml_filename','frd_xml_filename']:
        if not isinstance(getattr(r,n), str) or not getattr(r,n).strip():
            raise ValueError(f'{r.part_number}: {n} is empty')
    for n in ['vces_max_V','ic_cont_A','ic_pulse_A','ie_cont_A','ie_pulse_A','tj_abs_max_C','rth_jc_igbt_K_per_W','rth_jc_frd_K_per_W','module_length_mm','module_width_mm','module_height_mm','mass_g']:
        v=float(getattr(r,n))
        if not math.isfinite(v) or v<=0:
            raise ValueError(f'{r.part_number}: {n} must be positive')
    if r.ic_pulse_A < r.ic_cont_A or r.ie_pulse_A < r.ie_cont_A:
        raise ValueError(f'{r.part_number}: pulse rating below continuous rating')
    if r.tj_min_C >= r.tj_max_C or r.tj_abs_max_C < r.tj_max_C:
        raise ValueError(f'{r.part_number}: invalid temperature range')

@dataclass(frozen=True)
class RohmRGIGBTDevice:
    static: IGBTDiscreteStaticRecord
    igbt_loss_model: PlecsSiCSemiconductorLossModel
    frd_loss_model: PlecsSiCSemiconductorLossModel | None = None

    @property
    def has_frd(self) -> bool:
        return self.frd_loss_model is not None

    def eon_mJ(self, ic_A: float, vce_V: float, tj_C: float, rg_on_Ohm: float) -> float:
        if self.igbt_loss_model.turn_on is None:
            return 0.0
        return 1000.0 * self.igbt_loss_model.turn_on.energy_J(ic_A, vce_V, tj_C, variables={'Rg_on': rg_on_Ohm, 'Rg': rg_on_Ohm}, custom_tables_3d=self.igbt_loss_model.custom_tables_3d, custom_tables_2d=self.igbt_loss_model.custom_tables_2d)

    def eoff_mJ(self, ic_A: float, vce_V: float, tj_C: float, rg_off_Ohm: float) -> float:
        if self.igbt_loss_model.turn_off is None:
            return 0.0
        return 1000.0 * self.igbt_loss_model.turn_off.energy_J(ic_A, vce_V, tj_C, variables={'Rg_off': rg_off_Ohm, 'Rg': rg_off_Ohm}, custom_tables_3d=self.igbt_loss_model.custom_tables_3d, custom_tables_2d=self.igbt_loss_model.custom_tables_2d)

    def vce_sat_V(self, ic_A: float, tj_C: float) -> float:
        if self.igbt_loss_model.conduction is None:
            raise ValueError(f'{self.static.part_number}: missing IGBT conduction table')
        return abs(self.igbt_loss_model.conduction.lookup(max(0.0, float(ic_A)), tj_C))

    def frd_vf_V(self, ie_A: float, tj_C: float) -> float:
        if self.frd_loss_model is None or self.frd_loss_model.conduction is None:
            return 0.0
        return abs(self.frd_loss_model.conduction.lookup(max(0.0, float(ie_A)), tj_C))

    def err_mJ(self, ie_A: float, vce_V: float, tj_C: float, rg_on_Ohm: float) -> float:
        if self.frd_loss_model is None or self.frd_loss_model.turn_off is None:
            return 0.0
        return 1000.0 * self.frd_loss_model.turn_off.energy_J(ie_A, vce_V, tj_C, variables={'Rg_on': rg_on_Ohm, 'Rg': rg_on_Ohm}, custom_tables_3d=self.frd_loss_model.custom_tables_3d, custom_tables_2d=self.frd_loss_model.custom_tables_2d)

    def igbt_conduction_loss_W(self, current_waveform_A: Sequence[float], tj_C: float, dt_s=None) -> float:
        return _average([self.vce_sat_V(max(0.0,float(i)), tj_C)*max(0.0,float(i)) for i in current_waveform_A], dt_s)

    def frd_conduction_loss_W(self, current_waveform_A: Sequence[float], tj_C: float, dt_s=None) -> float:
        return _average([self.frd_vf_V(max(0.0,float(i)), tj_C)*max(0.0,float(i)) for i in current_waveform_A], dt_s)

    def igbt_switching_loss_W(self, fsw_Hz: float, ic_A: float, vce_V: float, tj_C: float, rg_on_Ohm: float, rg_off_Ohm: float) -> float:
        return fsw_Hz * (self.eon_mJ(ic_A, vce_V, tj_C, rg_on_Ohm) + self.eoff_mJ(ic_A, vce_V, tj_C, rg_off_Ohm)) / 1000.0

    def frd_reverse_recovery_loss_W(self, fsw_Hz: float, ie_A: float, vce_V: float, tj_C: float, rg_on_Ohm: float) -> float:
        return fsw_Hz * self.err_mJ(ie_A, vce_V, tj_C, rg_on_Ohm) / 1000.0

    def estimate_junction_temperature_C(self, losses: Mapping[str, float], case_temp_C: float, pulse_time_s=None, use_transient: bool=False) -> dict[str, float]:
        p_igbt=float(losses.get('p_igbt_W', losses.get('p_igbt_cond_W',0.0)+losses.get('p_igbt_sw_W',0.0)))
        p_frd=float(losses.get('p_frd_W', losses.get('p_frd_cond_W',0.0)+losses.get('p_frd_rr_W',0.0)))
        r_igbt=self.static.rth_jc_igbt_K_per_W
        r_frd=self.static.rth_jc_frd_K_per_W
        if use_transient and pulse_time_s is not None:
            if self.igbt_loss_model.thermal is not None:
                r_igbt=self.igbt_loss_model.thermal.zth_K_per_W(pulse_time_s)
            if self.frd_loss_model is not None and self.frd_loss_model.thermal is not None:
                r_frd=self.frd_loss_model.thermal.zth_K_per_W(pulse_time_s)
        return {'tj_igbt_C':case_temp_C+p_igbt*r_igbt, 'tj_frd_C':case_temp_C+p_frd*r_frd, 'delta_t_igbt_K':p_igbt*r_igbt, 'delta_t_frd_K':p_frd*r_frd}

    def build_geometry_proxy(self) -> dict:
        terminals = ['C','G','E'] if self.static.package == 'TO-247-3L' else ['C','G','E','Kelvin E']
        return {'shape':'to247_discrete_package', 'body':{'length_mm':self.static.module_length_mm,'width_mm':self.static.module_width_mm,'height_mm':self.static.module_height_mm,'material':'ROHM RG discrete IGBT simplified PDF envelope'}, 'terminals':terminals, 'label':self.static.part_number, 'mass_g':self.static.mass_g}

def _average(values, dt_s):
    if not values:
        return 0.0
    if dt_s is None or isinstance(dt_s, (int,float)):
        return sum(values)/len(values)
    w=[float(x) for x in dt_s]
    if len(w)!=len(values):
        raise ValueError('dt_s sequence must match waveform length')
    total=sum(w)
    if total<=0:
        raise ValueError('sum(dt_s) must be positive')
    return sum(v*x for v,x in zip(values,w))/total
