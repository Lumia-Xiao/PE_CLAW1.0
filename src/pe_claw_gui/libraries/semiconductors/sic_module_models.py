"""ROHM SiC module static records and PLECS loss-table helpers.

This helper is intentionally generic for ROHM BSM SiC modules whose PLECS files
may encode MOSFET/UMOS conduction as formula-only lookup tables.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import math, re
from typing import Mapping, Sequence
from xml.etree import ElementTree as ET

PLECS_NS={"p":"http://www.plexim.com/xml/semiconductors/"}

@dataclass(frozen=True)
class SiCModuleStaticRecord:
    vendor:str; part_number:str; device_type:str; topology:str; package:str
    vdss_max_V:float; id_cont_A:float; id_pulse_A:float; is_cont_A:float; is_pulse_A:float
    vgs_min_V:float; vgs_max_V:float; vgs_drive_on_V:float; vgs_drive_off_V:float
    tj_min_C:float; tj_max_C:float; tj_abs_max_C:float
    vds_on_typ_25C_V:float; vds_on_typ_125C_V:float; vds_on_typ_150C_V:float
    sbd_vf_typ_25C_V:float; sbd_vf_typ_125C_V:float; sbd_vf_typ_150C_V:float
    eon_ref_mJ:float; eoff_ref_mJ:float; err_ref_mJ:float
    rth_jc_mosfet_K_per_W:float; rth_jc_sbd_K_per_W:float; rth_cs_module_K_per_W:float
    module_length_mm:float; module_width_mm:float; module_height_mm:float; mass_g:float
    datasheet_filename:str; mosfet_xml_filename:str; sbd_xml_filename:str

def validate_sic_module_static_record(r:SiCModuleStaticRecord)->None:
    for n in ['vendor','part_number','device_type','topology','package','datasheet_filename','mosfet_xml_filename','sbd_xml_filename']:
        if not isinstance(getattr(r,n),str) or not getattr(r,n).strip(): raise ValueError(f"{r.part_number}: {n} empty")
    for n in ['vdss_max_V','id_cont_A','id_pulse_A','is_cont_A','is_pulse_A','tj_abs_max_C','vds_on_typ_25C_V','vds_on_typ_125C_V','vds_on_typ_150C_V','sbd_vf_typ_25C_V','sbd_vf_typ_125C_V','sbd_vf_typ_150C_V','eon_ref_mJ','eoff_ref_mJ','err_ref_mJ','rth_jc_mosfet_K_per_W','rth_jc_sbd_K_per_W','rth_cs_module_K_per_W','module_length_mm','module_width_mm','module_height_mm','mass_g']:
        v=float(getattr(r,n))
        if not math.isfinite(v) or v<=0: raise ValueError(f"{r.part_number}: {n} must be positive")
    if r.id_pulse_A<r.id_cont_A or r.is_pulse_A<r.is_cont_A: raise ValueError(f"{r.part_number}: pulse below continuous current")
    if r.vgs_min_V>=r.vgs_max_V or r.tj_min_C>=r.tj_max_C or r.tj_abs_max_C<r.tj_max_C: raise ValueError(f"{r.part_number}: invalid ranges")

@dataclass(frozen=True)
class ThermalModel:
    network_type:str; r_values_K_per_W:tuple[float,...]; tau_or_c_values:tuple[float,...]
    @property
    def steady_state_K_per_W(self)->float: return sum(self.r_values_K_per_W)
    def zth_K_per_W(self,t:float)->float:
        if t<=0: return 0.0
        if self.network_type.lower()=='foster': return sum(r*(1-math.exp(-t/tau)) for r,tau in zip(self.r_values_K_per_W,self.tau_or_c_values))
        return self.steady_state_K_per_W

@dataclass(frozen=True)
class Table2D:
    x_axis:tuple[float,...]; y_axis:tuple[float,...]; values_yx:tuple[tuple[float,...],...]; scale:float=1.0
    def lookup(self,x:float,y:float,*,clamp:bool=True)->float:
        return _interp2(self.x_axis,self.y_axis,self.values_yx,x,y,clamp=clamp)*self.scale

@dataclass(frozen=True)
class Table3D:
    x_axis:tuple[float,...]; y_axis:tuple[float,...]; z_axis:tuple[float,...]; values_zyx:tuple[tuple[tuple[float,...],...],...]; scale:float=1.0
    def lookup(self,x:float,y:float,z:float,*,clamp:bool=True)->float: return _interp3(self.x_axis,self.y_axis,self.z_axis,self.values_zyx,x,y,z,clamp=clamp)*self.scale

@dataclass(frozen=True)
class LossTable3D:
    current_axis:tuple[float,...]; voltage_axis:tuple[float,...]; temperature_axis:tuple[float,...]; values_tvi:tuple[tuple[tuple[float,...],...],...]; scale:float=1.0
    def lookup(self,i:float,v:float,t:float,*,clamp:bool=True)->float: return _interp3(self.current_axis,self.voltage_axis,self.temperature_axis,self.values_tvi,i,_map_voltage_query(v,self.voltage_axis),t,clamp=clamp)*self.scale

@dataclass(frozen=True)
class ConductionTable2D:
    current_axis:tuple[float,...]; temperature_axis:tuple[float,...]; values_ti:tuple[tuple[float,...],...]; scale:float=1.0
    def lookup(self,i:float,t:float,*,clamp:bool=True)->float: return _interp2(self.current_axis,self.temperature_axis,self.values_ti,i,t,clamp=clamp)*self.scale

@dataclass(frozen=True)
class FormulaConductionLoss:
    formula:str; custom_tables_2d:Mapping[str,Table2D]
    def lookup(self,i:float,t:float,*,variables:Mapping[str,float]|None=None,clamp:bool=True)->float:
        variables=variables or {}
        sw=float(variables.get('sw', 1.0))
        table_name=None
        if 'Von_VG18V' in self.formula and sw!=0:
            table_name=_find_table_name(self.custom_tables_2d,'Von_VG18V')
        elif 'Von_VG0V' in self.formula:
            table_name=_find_table_name(self.custom_tables_2d,'Von_VG0V')
        if table_name is None:
            names=re.findall(r"lookup\('([^']+)'", self.formula)
            table_name=names[0] if names else None
        table=self.custom_tables_2d.get(table_name or '')
        if table is None:
            return 0.0
        return table.lookup(i,t,clamp=clamp)

@dataclass(frozen=True)
class FormulaSwitchingLoss:
    table_name:str|None; arg_names:tuple[str,...]; voltage_reference_V:float; output_scale_to_J:float; direct_table:LossTable3D|None=None
    def energy_J(self,current_A:float,voltage_V:float,temperature_C:float,*,variables:Mapping[str,float]|None=None,custom_tables_3d:Mapping[str,Table3D]|None=None,custom_tables_2d:Mapping[str,Table2D]|None=None,clamp:bool=True)->float:
        if self.direct_table is not None: return self.direct_table.lookup(current_A,voltage_V,temperature_C,clamp=clamp)
        if self.table_name is None: return 0.0
        variables=variables or {}; table3d=(custom_tables_3d or {}).get(self.table_name); table2d=(custom_tables_2d or {}).get(self.table_name)
        if table3d is None and table2d is None: return 0.0
        vals=[]
        for name in self.arg_names:
            l=name.lower()
            if l in {'i','id','ic','ie'}: vals.append(current_A)
            elif l in {'t','tj'}: vals.append(temperature_C)
            elif l in {'v','vds','vce'}: vals.append(voltage_V)
            else: vals.append(float(variables.get(name, variables.get(name.replace('Rg_','RG'), variables.get('Rg',0.0)))))
        voltage_scale = (abs(voltage_V)/self.voltage_reference_V if self.voltage_reference_V>0 else 1.0)
        if table3d is not None:
            while len(vals)<3: vals.append(0.0)
            return table3d.lookup(vals[0],vals[1],vals[2],clamp=clamp)*voltage_scale*self.output_scale_to_J
        while len(vals)<2: vals.append(0.0)
        return table2d.lookup(vals[0],vals[1],clamp=clamp)*voltage_scale*self.output_scale_to_J

@dataclass(frozen=True)
class PlecsSiCSemiconductorLossModel:
    package_class:str; vendor:str; part_number:str; variables:Mapping[str,tuple[float|None,float|None,float|None]]
    custom_tables_3d:Mapping[str,Table3D]; turn_on:FormulaSwitchingLoss|None; turn_off:FormulaSwitchingLoss|None
    conduction:ConductionTable2D|FormulaConductionLoss|None; thermal:ThermalModel|None
    custom_tables_2d:Mapping[str,Table2D]|None=None
    @classmethod
    def from_xml(cls,xml_path:str|Path)->'PlecsSiCSemiconductorLossModel':
        path=Path(xml_path); root=ET.parse(path).getroot(); pkg=root.find('p:Package',PLECS_NS)
        if pkg is None: raise ValueError(f'{path}: missing Package')
        vars={}
        for var in pkg.findall('p:Variables/p:Variable',PLECS_NS):
            name=var.findtext('p:Name',namespaces=PLECS_NS)
            if name: vars[name]=(_of(var.findtext('p:DefaultValue',namespaces=PLECS_NS)),_of(var.findtext('p:MinValue',namespaces=PLECS_NS)),_of(var.findtext('p:MaxValue',namespaces=PLECS_NS)))
        tables_2d,tables_3d=_parse_custom_tables(pkg,path); sem=pkg.find('p:SemiconductorData',PLECS_NS)
        if sem is None: raise ValueError(f'{path}: missing SemiconductorData')
        return cls(pkg.attrib.get('class',''),pkg.attrib.get('vendor',''),pkg.attrib.get('partnumber',''),vars,tables_3d,_parse_switching_loss(sem.find('p:TurnOnLoss',PLECS_NS),path),_parse_switching_loss(sem.find('p:TurnOffLoss',PLECS_NS),path),_parse_conduction_loss(sem.find('p:ConductionLoss',PLECS_NS),path,tables_2d),_parse_thermal_model(pkg.find('p:ThermalModel',PLECS_NS)),tables_2d)

def _parse_custom_tables(pkg,path):
    out2={}; out3={}; custom=pkg.find('p:CustomTables',PLECS_NS)
    if custom is None: return out2,out3
    for table in custom.findall('p:Table2D',PLECS_NS):
        name=table.findtext('p:Name',namespaces=PLECS_NS); x=table.findtext('p:XAxis',namespaces=PLECS_NS); y=table.findtext('p:YAxis',namespaces=PLECS_NS); vals=table.find('p:FunctionValues',PLECS_NS)
        if not name or not x or not y or vals is None: continue
        rows=tuple(_ft(ye.text or '') for ye in vals.findall('p:YDimension',PLECS_NS))
        obj=Table2D(_ft(x),_ft(y),rows,float(vals.attrib.get('scale','1'))); _v2(obj.x_axis,obj.y_axis,obj.values_yx,path); out2[name]=obj
    for table in custom.findall('p:Table3D',PLECS_NS):
        name=table.findtext('p:Name',namespaces=PLECS_NS); x=table.findtext('p:XAxis',namespaces=PLECS_NS); y=table.findtext('p:YAxis',namespaces=PLECS_NS); z=table.findtext('p:ZAxis',namespaces=PLECS_NS); vals=table.find('p:FunctionValues',PLECS_NS)
        if not name or not x or not y or not z or vals is None: continue
        value=[]
        for ze in vals.findall('p:ZDimension',PLECS_NS): value.append(tuple(_ft(ye.text or '') for ye in ze.findall('p:YDimension',PLECS_NS)))
        obj=Table3D(_ft(x),_ft(y),_ft(z),tuple(value),float(vals.attrib.get('scale','1'))); _v3(obj.x_axis,obj.y_axis,obj.z_axis,obj.values_zyx,path); out3[name]=obj
    return out2,out3

def _parse_switching_loss(el,path):
    if el is None: return None
    formula=el.findtext('p:Formula',default='',namespaces=PLECS_NS).strip(); parsed=_parse_formula(formula)
    if parsed is not None: return parsed
    ca=_ft(_req(el,'p:CurrentAxis',path)); va=_ft(_req(el,'p:VoltageAxis',path)); ta=_ft(_req(el,'p:TemperatureAxis',path)); energy=el.find('p:Energy',PLECS_NS)
    if energy is None: return None
    values=[]
    for te in energy.findall('p:Temperature',PLECS_NS): values.append(tuple(_ft(ve.text or '') for ve in te.findall('p:Voltage',PLECS_NS)))
    _v3(ca,va,ta,tuple(values),path); return FormulaSwitchingLoss(None,tuple(),1.0,1.0,LossTable3D(ca,va,ta,tuple(values),float(energy.attrib.get('scale','1'))))

def _parse_formula(formula):
    if not formula or 'lookup' not in formula: return None
    s=formula.replace(' ',''); m=re.search(r"lookup\('([^']+)'(?:,([^)]*))?\)",s)
    if not m: return None
    args=tuple(a for a in (m.group(2) or '').split(',') if a); vref=1.0
    vr=re.search(r'\*v/([0-9.eE+\-]+)',s)
    if vr: vref=float(vr.group(1))
    scale=1.0
    # PLECS formula-only ROHM files often store switching-energy tables in
    # microjoules or millijoules and apply a numeric multiplier, for example
    # lookup(...)*v/600*1e-06 or lookup(...)*0.001.  Preserve that multiplier
    # instead of treating the raw table values as joules.
    for factor_text in re.findall(r'\*([0-9]+(?:\.[0-9]+)?(?:[eE][+\-]?\d+)?)', s):
        try:
            factor = float(factor_text)
        except ValueError:
            continue
        if 0.0 < factor < 1.0:
            scale *= factor
    if '*1/1000' in s:
        scale *= 1e-3
    return FormulaSwitchingLoss(m.group(1),args,vref,scale)

def _parse_conduction_loss(el,path,tables_2d):
    if el is None: return None
    formula=el.findtext('p:Formula',default='',namespaces=PLECS_NS).strip()
    method=el.findtext('p:ComputationMethod',default='',namespaces=PLECS_NS).strip().lower()
    if formula and 'lookup' in formula and ('formula' in method or tables_2d):
        return FormulaConductionLoss(formula,tables_2d)
    ca=_ft(_req(el,'p:CurrentAxis',path)); ta=_ft(_req(el,'p:TemperatureAxis',path)); vd=el.find('p:VoltageDrop',PLECS_NS)
    if vd is None: return None
    values=tuple(_ft(t.text or '') for t in vd.findall('p:Temperature',PLECS_NS)); _v2(ca,ta,values,path); return ConductionTable2D(ca,ta,values,float(vd.attrib.get('scale','1')))

def _parse_thermal_model(el):
    if el is None: return None
    br=el.find('p:Branch',PLECS_NS)
    if br is None: return None
    typ=br.attrib.get('type',''); rs=[]; second=[]
    if typ.lower()=='cauer':
        for it in br.findall('p:RCElement',PLECS_NS): rs.append(float(it.attrib['R'])); second.append(float(it.attrib.get('C','0')))
    else:
        for it in br.findall('p:RTauElement',PLECS_NS): rs.append(float(it.attrib['R'])); second.append(float(it.attrib.get('Tau','0')))
    return ThermalModel(typ,tuple(rs),tuple(second)) if rs else None

def _find_table_name(tables:Mapping[str,Table2D], prefix:str)->str|None:
    for name in tables:
        if name.startswith(prefix): return name
    return None

def _interp2(xa,ya,vals,x,y,*,clamp=True):
    x0,x1,fx=_bounds(xa,x,clamp=clamp); y0,y1,fy=_bounds(ya,y,clamp=clamp); v00=vals[y0][x0]; v10=vals[y0][x1]; v01=vals[y1][x0]; v11=vals[y1][x1]; return (v00*(1-fx)+v10*fx)*(1-fy)+(v01*(1-fx)+v11*fx)*fy

def _interp3(xa,ya,za,vals,x,y,z,*,clamp=True):
    x0,x1,fx=_bounds(xa,x,clamp=clamp); y0,y1,fy=_bounds(ya,y,clamp=clamp); z0,z1,fz=_bounds(za,z,clamp=clamp)
    def at(zi,yi,xi): return vals[zi][yi][xi]
    c000=at(z0,y0,x0); c100=at(z0,y0,x1); c010=at(z0,y1,x0); c110=at(z0,y1,x1); c001=at(z1,y0,x0); c101=at(z1,y0,x1); c011=at(z1,y1,x0); c111=at(z1,y1,x1)
    c00=c000*(1-fx)+c100*fx; c10=c010*(1-fx)+c110*fx; c01=c001*(1-fx)+c101*fx; c11=c011*(1-fx)+c111*fx; return (c00*(1-fy)+c10*fy)*(1-fz)+(c01*(1-fy)+c11*fy)*fz

def _bounds(axis,x,*,clamp):
    if len(axis)==1: return 0,0,0.0
    if x<=axis[0]:
        if not clamp and x<axis[0]: raise ValueError('below axis')
        return 0,0,0.0
    if x>=axis[-1]:
        if not clamp and x>axis[-1]: raise ValueError('above axis')
        return len(axis)-1,len(axis)-1,0.0
    for i in range(len(axis)-1):
        if axis[i]<=x<=axis[i+1]: return i,i+1,(x-axis[i])/(axis[i+1]-axis[i]) if axis[i+1]!=axis[i] else 0.0
    raise ValueError('axis interpolation failed')

def _map_voltage_query(v,axis):
    if axis[-1]<=0: return -abs(v)
    if axis[0]>=0: return abs(v)
    return v

def _req(el,path_expr,path):
    v=el.findtext(path_expr,namespaces=PLECS_NS)
    if v is None: raise ValueError(f'{path}: missing {path_expr}')
    return v.strip()

def _of(t): return None if t is None or not str(t).strip() else float(t)
def _ft(t): return tuple(float(x) for x in t.split())

def _v3(xa,ya,za,vals,path):
    if len(vals)!=len(za): raise ValueError(f'{path}: z dimension mismatch')
    for z in vals:
        if len(z)!=len(ya): raise ValueError(f'{path}: y dimension mismatch')
        for row in z:
            if len(row)!=len(xa): raise ValueError(f'{path}: x dimension mismatch')

def _v2(xa,ya,vals,path):
    if len(vals)!=len(ya): raise ValueError(f'{path}: t dimension mismatch')
    for row in vals:
        if len(row)!=len(xa): raise ValueError(f'{path}: i dimension mismatch')
