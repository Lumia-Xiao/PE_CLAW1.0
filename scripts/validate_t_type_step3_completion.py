"""Verify current-workspace tests and unchanged full NPC step-0 snapshots."""
from __future__ import annotations
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
os.environ.update(PYTHONPATH=os.pathsep.join([str(ROOT / 'src'), str(ROOT / 'tests')]), PYTHONDONTWRITEBYTECODE='1', MPLBACKEND='Agg')
import pe_claw_gui
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter import PLUGIN

def compare_npc(out):
    baseline = ROOT / '.pytest-tmp-tt-r1-s0'
    manifest = json.loads((baseline / 'baseline_manifest.json').read_text(encoding='utf-8'))
    receipts = []
    for case in manifest['cases']:
        source = baseline / case['file']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == case['sha256']
        old = json.loads(source.read_text(encoding='utf-8'))
        raw = old['raw_input']
        spec = PLUGIN.build_spec(raw)
        candidate = PLUGIN.synthesize(spec)
        op = OperatingPoint(**old['operating_point']) if old['operating_point'] else None
        wave = PLUGIN.generate_waveforms(candidate, op)
        stress = PLUGIN.extract_stress(candidate, wave)
        result = PLUGIN.evaluate(candidate, wave, stress)
        payload = {'raw_input': raw, 'spec': dataclasses.asdict(spec), 'candidate': dataclasses.asdict(candidate), 'operating_point': dataclasses.asdict(op) if op else None, 'waveform': dataclasses.asdict(wave), 'stress': dataclasses.asdict(stress), 'result': dataclasses.asdict(result)}
        data = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode('utf-8')
        digest = hashlib.sha256(data).hexdigest()
        (out / case['file']).write_bytes(data)
        receipts.append({'case': case['name'], 'source_sha256': case['sha256'], 'current_sha256': digest, 'exact_full_payload_equal': digest == case['sha256']})
        assert digest == case['sha256'], case['name']
    (out / 'npc_comparison.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
    return receipts

def main():
    out = ROOT / sys.argv[1]
    assert not out.exists(), 'Choose a fresh evidence directory'
    out.mkdir()
    assert Path(pe_claw_gui.__file__).resolve().is_relative_to(ROOT / 'src')
    tests = ['tests/test_t_type_step1_contract.py', 'tests/test_t_type_step2_synthesis.py', 'tests/test_t_type_step3_waveforms.py', 'tests/test_t_type_step4_paths_events.py', 'tests/test_t_type_common_solver.py', 'tests/test_npc_step2_current_reference.py', 'tests/test_npc_step3_average_voltage_target.py', 'tests/test_npc_step4_level_sequence.py', 'tests/test_npc_step4_periodic_warm_start.py', 'tests/test_npc_step5_event_segmented_current.py', 'tests/test_npc_switching_loss_events.py', 'tests/test_phase4_topology_contracts.py::test_phase4_registry_has_unique_ids_and_capabilities', 'tests/test_phase4_topology_contracts.py::test_phase4_router_fails_closed_for_unknown_topology']
    if len(sys.argv) > 2:
        tests.extend(sys.argv[2:])
    receipt = {'python': sys.executable, 'version': sys.version, 'package': pe_claw_gui.__file__, 'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(), 'test_locations': tests, 'test_sha256': {t: hashlib.sha256((ROOT / t.split('::')[0]).read_bytes()).hexdigest() for t in tests}}
    argv = [sys.executable, '-B', '-m', 'pytest', '-o', 'addopts=', '-p', 'no:cacheprovider', '-q', '--basetemp', str(out / 'temp'), '--junitxml', str(out / 'junit.xml'), *tests]
    with (out / 'pytest.log').open('w', encoding='utf-8') as log:
        status = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT).returncode
    receipt.update(argv=argv, exit_code=status)
    (out / 'test_receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print((out / 'pytest.log').read_text(encoding='utf-8'), flush=True)
    if status:
        raise SystemExit(status)
    print(json.dumps(compare_npc(out), indent=2))

if __name__ == '__main__':
    main()
