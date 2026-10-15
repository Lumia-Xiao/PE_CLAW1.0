from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys
from importlib import import_module
from pathlib import Path

import pytest

from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import PLUGIN
import pe_claw_gui.topology_capabilities as capabilities
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.app.shell.state_store import AppStateStore
from pe_claw_gui.app.controllers.run_design_controller import RunDesignController
from pe_claw_gui.app.controllers.efficiency_sweep_controller import EfficiencySweepController

ID = PLUGIN.topology_id
KEY = 'three_phase_t_type_pd_spwm_waveforms'
ROOT = Path(__file__).resolve().parents[1]


def test_previous_twenty_registry_and_capability_contracts_unchanged():
    frozen = json.loads((ROOT/'tests/fixtures/t_type_step6_previous_registry.json').read_text(encoding='utf-8'))
    registry = build_default_registry()
    assert len(registry.list_definitions()) == 21
    assert len(registry.list_definitions('dc_ac')) == 4
    assert set(frozen) == {d.topology_id for d in registry.list_definitions()} - {ID}
    for topology_id, record in frozen.items():
        current = {'definition':dataclasses.asdict(registry.get_definition(topology_id)),
                   'capability':dataclasses.asdict(registry.get_capability(topology_id)),
                   'helpers':{n:getattr(capabilities,n)(topology_id) for n in record['helpers']}}
        assert json.loads(json.dumps(current)) == record
    assert ID not in capabilities.FIRST_PASS_TOPOLOGY_ONLY_IDS
    assert capabilities.has_semiconductor_selection_path(ID)
    assert registry.resolve_topology_id(PLUGIN.legacy_key) == ID


def test_full_pipeline_and_direct_controller_guards_skip_downstream(monkeypatch,tmp_path):
    def forbidden(*a,**kw):
        pytest.fail('T-type must not execute unconnected component or loss stages')
    full = import_module('pe_claw_gui.pipeline.run_full_pipeline')
    for name in ('run_capacitor_pipeline','run_magnetic_pipeline','run_loss_pipeline','run_thermal_pipeline','run_geometry_pipeline'):
        monkeypatch.setattr(full,name,forbidden)
    report = run_full_pipeline(PLUGIN,{},include_waveforms=False,output_root=tmp_path)
    assert report.device is not None and report.device.selected_devices
    assert report.loss is report.capacitor is report.magnetic is None
    refresh = import_module('pe_claw_gui.pipeline.run_operating_point_refresh')
    from pe_claw_gui.models.operating_point import OperatingPoint
    for name in ('run_device_operating_point_refresh','run_capacitor_operating_point_refresh','run_loss_pipeline','run_thermal_pipeline'):
        monkeypatch.setattr(refresh,name,forbidden)
    refreshed = refresh.run_operating_point_refresh(report,PLUGIN,OperatingPoint(vin_v=700,load_ratio=1,power_factor=1))
    assert refreshed.candidate is report.candidate
    assert refreshed.waveform is not None
    assert refreshed.device is report.device
    assert refreshed.capacitor is refreshed.magnetic is refreshed.loss is None
    store = AppStateStore(registry=build_default_registry(),selected_topology_id=ID,active_plugin=PLUGIN,design_report=report)
    controller = RunDesignController(store)
    mod = import_module('pe_claw_gui.app.controllers.run_design_controller')
    for name in ('run_capacitor_pipeline','run_magnetic_pipeline','run_loss_pipeline','run_thermal_pipeline','run_geometry_pipeline'):
        monkeypatch.setattr(mod,name,forbidden)
    sweep = import_module('pe_claw_gui.app.controllers.efficiency_sweep_controller')
    monkeypatch.setattr(sweep,'run_efficiency_sweep',forbidden)
    monkeypatch.setattr(sweep,'build_and_generate_hardware_overview',forbidden)
    for call in (EfficiencySweepController(store).run_active_efficiency_sweep,):
        with pytest.raises(RuntimeError,match='unavailable'):
            call()
        assert store.design_report is report
        assert report.run_context.stage_status['semiconductor_design']=='succeeded'
        assert all(s=='not_started' for k,s in report.run_context.stage_status.items() if k not in ('design','semiconductor_design'))


def test_real_tk_card_buttons_current_readback_and_failure_invalidation(monkeypatch,tmp_path):
    from pe_claw_gui.app.shell.main_window import PEClawMainWindow
    from pe_claw_gui.app.topology_card_assets import get_topology_image_resource
    full = import_module('pe_claw_gui.app.controllers.run_design_controller')
    actual_run = full.run_full_pipeline
    count = 0
    def scoped_run(**kwargs):
        nonlocal count
        count += 1
        return actual_run(**kwargs,output_root=tmp_path/f'run-{count}')
    monkeypatch.setattr(full,'run_full_pipeline',scoped_run)
    shell = import_module('pe_claw_gui.app.shell.main_window')
    errors = []
    monkeypatch.setattr(shell.messagebox,'showerror',lambda title,message:errors.append((title,message)))
    monkeypatch.setattr(shell.messagebox,'showwarning',lambda title,message:errors.append((title,message)))
    app = PEClawMainWindow()
    app.withdraw()
    try:
        app._on_category_selected('dc_ac')
        assert get_topology_image_resource(ID).is_file()
        app.workspace.active_page._topology_buttons[ID].invoke()
        app.update_idletasks()
        form = app.workspace.active_form
        assert form.topology_id == ID
        assert set(form.design_vars) == {f.key for f in form.get_design_fields()}
        assert form.get_runtime_overrides() == {'ambient_temp_c': '25', 'target_junction_temp_c': '100'}
        assert str(form.run_capacitor_button.cget('state')) == 'normal'
        assert str(form.run_efficiency_sweep_button.cget('state')) == 'disabled'
        assert str(form.run_magnetics_button.cget('state')) == 'normal'
        assert 'operating_vdc_v' not in form.get_raw_input()
        form.run_design_button.invoke()
        assert not errors
        report = app.state_store.design_report
        assert report.candidate.inductance_h == pytest.approx(1.0716517624676405e-3,rel=1e-9)
        assert report.stress.switch.current_rms_a is None
        device_text=app.workspace.device_view.summary_text.get('1.0','end')
        assert 'conduction only' in device_text
        assert all(part in device_text for part in report.device.selected_devices.values())
        summary = app.workspace.summary_view.text.get('1.0','end')
        assert 'Cdc per-bank proxy = 81.632653 uF' in summary
        assert 'Vdc_nom = 700.000000 V' in summary
        assert 'Pout = 10000.000000 W' in summary
        assert 'Semiconductor selection = available (conduction only; see Devices).' in summary
        assert 'Component selection, losses and system efficiency unavailable' not in summary
        assert 'design_estimate' in summary
        form.generate_waveforms_button.invoke()
        app.update_idletasks()
        assert not errors
        report = app.state_store.design_report
        data = report.waveform.metadata[KEY]
        summary = app.workspace.summary_view.text.get('1.0','end')
        stress = app.workspace.stress_view.text.get('1.0','end')
        assert f"Operating I_phase rms (A phase, including PWM ripple) = {data['diagnostics']['phase_statistics']['a']['rms_a']:.6f} A" in summary
        assert '12 position metrics' not in summary
        assert 'Topology evaluation' not in summary
        assert len(summary.splitlines()) < 75
        assert 'Operating DC bus = 700.000000 V' in summary
        assert 'waveform_actual' in summary
        loss = app.workspace.loss_view.text.get('1.0','end')
        assert 'T-type scoped system unavailable' in loss
        assert report.t_type_engineering.system is None and report.loss is None
        assert '100%' not in loss and '100.0' not in loss
        assert 'Efficiency unavailable' in app.workspace.efficiency_view.message.cget('text')
        assert 'Main switches (6 positions)' in stress and 'Midpoint switches (6 positions)' in stress
        assert 'Static blocking maximum = 700.000000 V' in stress
        assert 'Static blocking maximum = 350.000000 V' in stress
        assert 'clamp' not in stress.lower()
        for key,metrics in data['stress']['positions'].items():
            assert key in stress
            for path in ('signed','channel','diode'):
                line = f"{path}: peak={metrics[path+'_peak_a']:.6f} A, RMS={metrics[path+'_rms_a']:.6f} A, average={metrics[path+'_avg_a']:.6f} A"
                assert line in stress
        axes = app.workspace.waveform_view.figure.axes
        assert len(axes) == 6
        curves = [{line.get_label():list(line.get_ydata()) for line in axis.lines} for axis in axes]
        for index,phase in enumerate(('a','b','c')):
            assert curves[0][f'v_{phase}N PWM'] == data['phases'][phase]['phase_neutral_voltage_v']
            assert curves[0][f'v_{phase} grid'] == data['phases'][phase]['grid_voltage_v']
            assert curves[1][f'i_{phase}'] == data['phases'][phase]['current_a']
            assert curves[2][f'v_{phase}O'] == data['phases'][phase]['pole_to_o_voltage_v']
            for role in ('QP','QN','QA','QO'):
                assert curves[3+index][f'{phase}_{role}'] == data['phases'][phase]['gates'][role]
        for pair in ('ab','bc','ca'):
            assert curves[2][f'v_{pair}'] == data['line_line_voltage_v'][pair]
        assert all(list(line.get_xdata()) == [t*1e3 for t in data['time_s']] for axis in axes for line in axis.lines)
        assert axes[-1].get_xlabel() == 'Time [ms]'
        app.workspace.waveform_view.figure.savefig(tmp_path/'t_type_waveform.png')
        (tmp_path/'gui_readback.json').write_text(json.dumps({'summary':summary,'stress':stress,'basis':data['basis'],'run_id':report.run_context.run_id}),encoding='utf-8')
        # A failed point must retain the candidate for recovery and clear current results.
        saved_candidate = report.candidate
        form.operating_vars['power_factor'].set('0.01')
        form.generate_waveforms_button.invoke()
        app.update_idletasks()
        assert errors and 'modulation' in errors[-1][1]
        assert app.state_store.design_report.candidate is saved_candidate
        assert app.state_store.design_report.waveform is None
        assert app.state_store.design_report.stress is None
        assert all(not axis.lines for axis in app.workspace.waveform_view.figure.axes)
        assert '21.935573 A' not in app.workspace.stress_view.text.get('1.0','end')
        form.operating_vars['power_factor'].set('1.0')
        form.generate_waveforms_button.invoke()
        assert app.state_store.design_report.waveform is not None
        form.operating_vars['load_ratio'].set('nan')
        form.generate_waveforms_button.invoke()
        assert 'finite' in errors[-1][1]
        assert app.state_store.design_report.candidate is saved_candidate
        assert app.state_store.design_report.waveform is None
        assert app.state_store.design_report.stress is None
        assert all(not axis.lines for axis in app.workspace.waveform_view.figure.axes)
        form.design_vars['pout_w'].set('9000')
        assert app.state_store.design_report is None
        app._on_topology_selected('three_phase_three_level_npc_inverter')
        assert app.state_store.design_report is None
    finally:
        app.destroy()


def test_t_type_controls_reachable_at_default_and_minimum_window_size():
    script = '''
from pe_claw_gui.app.shell.main_window import PEClawMainWindow

def check():
    def contained(widget, parent):
        x = widget.winfo_rootx() - parent.winfo_rootx()
        y = widget.winfo_rooty() - parent.winfo_rooty()
        return (0 <= x and 0 <= y
                and x + widget.winfo_width() <= parent.winfo_width()
                and y + widget.winfo_height() <= parent.winfo_height())
    app = PEClawMainWindow()
    try:
        app._on_topology_selected('three_phase_three_level_t_type_inverter')
        for size in ('1400x860', '1240x760'):
            app.geometry(size)
            app.update()
            canvas = app.workspace.form_canvas
            form = app.workspace.active_form
            assert canvas is not None
            canvas.yview_moveto(1)
            app.update()
            assert contained(canvas, app)
            assert contained(form.generate_waveforms_button, canvas), size
            assert contained(form.run_efficiency_sweep_button, canvas), size
            canvas.yview_moveto(0)
            app.update()
            assert contained(form.run_design_button.master.winfo_children()[0], canvas), size
    finally:
        app.destroy()

check()
'''
    env = os.environ.copy()
    env['PYTHONPATH'] = str(ROOT / 'src')
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    result = subprocess.run([sys.executable, '-B', '-c', script], cwd=ROOT,
                            env=env, capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 0, result.stderr or result.stdout
