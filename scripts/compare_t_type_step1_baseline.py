"""Compare preserved old engineering payloads with explicit additive-field policy."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import re
from validate_t_type_engineering_step0 import write_json

def compare(old, new):
    records = []
    def visit(a,b,path):
        if isinstance(a,dict) and isinstance(b,dict):
            for key in sorted(set(a)|set(b)):
                if key not in a or key not in b:
                    records.append({'path':path+'/'+key,'source':a.get(key),'target':b.get(key),'category':'field_presence'})
                else:
                    visit(a[key],b[key],path+'/'+key)
        elif isinstance(a,list) and isinstance(b,list):
            if len(a)!=len(b):
                records.append({'path':path,'source':len(a),'target':len(b),'category':'list_length'})
            else:
                for i,(x,y) in enumerate(zip(a,b)):
                    visit(x,y,path+'/'+str(i))
        elif a != b:
            record={'path':path,'source':a,'target':b,'category':'value','tolerance':0,'basis':'normalized current-code preservation','owner':path.split('/')[1]}
            if isinstance(a,(int,float)) and isinstance(b,(int,float)):
                record.update(absolute_error=abs(b-a),relative_error=abs(b-a)/abs(a) if a else None)
            records.append(record)
    visit(old,new,'')
    return records

def main():
    old_root,new_root=map(Path,sys.argv[1:3])
    results=[]
    for case in ('npc_full','two_level_devices','full_bridge_devices'):
        old=json.loads((old_root/f'{case}_normalized.json').read_text(encoding='utf-8'))
        new=json.loads((new_root/f'{case}_normalized.json').read_text(encoding='utf-8'))
        assert 't_type_engineering' not in old['report']
        assert new['report'].pop('t_type_engineering') is None
        diffs=compare(old,new)
        engineering_diffs=[]
        for diff in diffs:
            path=diff['path']
            timing=False
            if path.startswith('/report/capacitor/') and '/diagnostics/' in path and path.rsplit('/',1)[1] in {
                'design_point_waveform_preparation_time_s','geometry_artifact_generation_time_s','input_artifact_csv_time_s','input_artifact_png_time_s','input_artifact_total_time_s','input_selection_time_s','output_artifact_csv_time_s','output_artifact_png_time_s','output_artifact_total_time_s','output_selection_time_s','registry_loading_time_s','run_capacitor_time_before_geometry_s','total_run_capacitor_time_s','artifact_csv_time_s','artifact_png_time_s','artifact_total_time_s','selection_time_s'}:
                timing=True
            elif path.startswith('/report/capacitor/') and '/notes/' in path and isinstance(diff['source'],str) and isinstance(diff['target'],str):
                def remove_time(text):
                    return re.sub(r'(selection time=|CSV writing=|PF PNG generation=|total=|preparation time: |before geometry: |generation time: |Total Run Capacitor time: )\d+\.\d+ s',r'\1$TIME s',text)
                timing=remove_time(diff['source'])==remove_time(diff['target'])
            if timing:
                diff['category']='explicit_runtime_timing'
                diff['excluded_from_engineering_verdict']=True
            else:
                engineering_diffs.append(diff)
        results.append({'case':case,'passed':not engineering_diffs,'difference_count':len(diffs),'engineering_difference_count':len(engineering_diffs),'differences':diffs,'source_evidence':str(old_root/f'{case}_normalized.json'),'target_evidence':str(new_root/f'{case}_normalized.json')})
        print(case,len(diffs),len(engineering_diffs))
    receipt={'policy':'Step0 normalization plus optional None field; explicitly enumerated capacitor diagnostic timings and anchored timing-only note substitutions. All raw differences retained; electrical values/status/hardware/selection diagnostics unchanged.','cases':results,'passed':all(r['passed'] for r in results)}
    write_json(new_root/'step1_comparison_verified.json',receipt)
    raise SystemExit(0 if receipt['passed'] else 1)

if __name__=='__main__':
    main()
