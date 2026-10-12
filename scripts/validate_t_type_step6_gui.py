"""Run step-6 GUI/registry regressions with isolated design artifacts."""
from __future__ import annotations
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests'), str(ROOT / 'scripts')]
os.environ.update(PYTHONPATH=os.pathsep.join([str(ROOT / 'src'), str(ROOT / 'tests')]),
                  PYTHONDONTWRITEBYTECODE='1', MPLBACKEND='Agg')
import pytest
import pe_claw_gui
from validate_t_type_step3_completion import compare_npc

TESTS = [
    *[f'tests/test_t_type_step{i}_{name}.py' for i, name in enumerate(
        ('contract', 'synthesis', 'waveforms', 'paths_events', 'pipeline', 'gui'), 1)],
    'tests/test_t_type_common_solver.py',
    *[f'tests/{name}.py' for name in (
        'test_npc_step2_current_reference', 'test_npc_step3_average_voltage_target',
        'test_npc_step4_level_sequence', 'test_npc_step4_periodic_warm_start',
        'test_npc_step5_event_segmented_current', 'test_npc_switching_loss_events',
        'test_dc_ac_registry_category', 'test_dc_ac_three_phase_three_level_npc_contract',
        'test_dc_ac_operating_refresh_gui_chain', 'test_dc_ac_packaged_gui_runtime',
        'test_phase10_gui_integration', 'test_phase12_verification',
        'test_two_phase_interleaved_boost_pfc_loss_display_consistency',
        'test_ac_dc_efficiency_gui_end_to_end')],
    'tests/test_phase4_topology_contracts.py::test_phase4_registry_has_unique_ids_and_capabilities',
    'tests/test_phase4_topology_contracts.py::test_phase4_router_fails_closed_for_unknown_topology',
    'tests/test_phase2_gui_bootstrap.py::test_gui_constructs_with_phase7_topology_baseline',
    'tests/test_phase3_shared_contracts.py::test_default_registry_keeps_phase7_resolvable_topology_contracts',
    'tests/test_phase11_ai_isolation.py::test_all_registered_deterministic_topology_plugins_remain_loadable',
    'tests/test_npc_loss_consistency_step1.py::test_npc_result_pages_share_loss_basis_and_totals',
]


def main():
    tests = sys.argv[2:] or TESTS
    out = (ROOT / sys.argv[1]).resolve()
    assert not out.exists(), 'Choose a fresh evidence directory'
    out.mkdir()
    assert Path(pe_claw_gui.__file__).resolve().is_relative_to(ROOT / 'src')
    prefix = '\n'.join([
        'from pe_claw_gui.models.design_run_context import DesignRunContext as _TTContext',
        '_tt_create = _TTContext.create.__func__',
        'def _tt_scoped_create(cls, *args, **kwargs):',
        '    if kwargs.get("output_root") is None and kwargs.get("output_base_root") is None:',
        f'        kwargs["output_base_root"] = {str(out / "outputs")!r}',
        '    return _tt_create(cls, *args, **kwargs)',
        '_TTContext.create = classmethod(_tt_scoped_create)', '',
    ])

    class ScopedOutputs:
        @pytest.fixture(autouse=True)
        def scoped_outputs(self, monkeypatch):
            from pe_claw_gui.models.design_run_context import DesignRunContext
            actual_create = DesignRunContext.create.__func__
            def create(cls, *args, **kwargs):
                if kwargs.get('output_root') is None and kwargs.get('output_base_root') is None:
                    kwargs['output_base_root'] = out / 'outputs'
                return actual_create(cls, *args, **kwargs)
            monkeypatch.setattr(DesignRunContext, 'create', classmethod(create))
            actual_run = subprocess.run
            def run(argv, *args, **kwargs):
                if isinstance(argv, (list, tuple)) and '-c' in argv and Path(str(argv[0])).name.lower().startswith('python'):
                    argv = list(argv)
                    index = argv.index('-c') + 1
                    argv[index] = prefix + argv[index]
                return actual_run(argv, *args, **kwargs)
            monkeypatch.setattr(subprocess, 'run', run)

    receipt = {'python': sys.executable, 'version': sys.version, 'package': pe_claw_gui.__file__,
               'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
               'tests': tests, 'test_sha256': {t: hashlib.sha256((ROOT / t.split('::')[0]).read_bytes()).hexdigest() for t in tests},
               'output_policy': 'Explicit roots preserved; default artifacts redirected to evidence/outputs in parent and Python -c GUI subprocesses'}
    paths = subprocess.check_output(
        ['git', '-c', 'core.longpaths=true', 'diff', '--name-only', '--', 'src', 'tests', 'scripts'],
        text=True,
    ).splitlines()
    paths += [
        'scripts/validate_t_type_step6_gui.py',
        'src/pe_claw_gui/app/topology_forms/three_phase_three_level_t_type_inverter_form.py',
        'src/pe_claw_gui/app/assets/topologies/dc_ac/three_phase_three_level_t_type_inverter.png',
        'tests/test_t_type_step6_gui.py', 'tests/fixtures/t_type_step6_previous_registry.json',
    ]
    receipt['source_sha256'] = {
        p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sorted(set(paths))
        if (ROOT / p).is_file()
    }
    (out / 'preflight.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    argv = ['-o', 'addopts=', '-p', 'no:cacheprovider', '-q', '--basetemp', str(out / 'temp'),
            '--junitxml', str(out / 'junit.xml'), *tests]
    with (out / 'pytest.log').open('w', encoding='utf-8') as log, redirect_stdout(log), redirect_stderr(log):
        status = pytest.main(argv, plugins=[ScopedOutputs()])
    receipt.update(argv=argv, exit_code=int(status))
    (out / 'test_receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print((out / 'pytest.log').read_text(encoding='utf-8'), flush=True)
    if status:
        raise SystemExit(status)
    print(json.dumps(compare_npc(out), indent=2))


if __name__ == '__main__':
    main()
