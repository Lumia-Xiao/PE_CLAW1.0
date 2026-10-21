"""HTTP contracts used by React, with an actual Buck run and isolated storage."""

import asyncio
import json
import hashlib
from pathlib import Path

import httpx
import pytest

from pe_claw_web.schemas import (
    BuckDesignRequest, DesignError, DesignResultResponse, TopologyDesignRequest,
)

FIXTURES = Path(__file__).resolve().parents[1] / 'web/frontend/tests/fixtures'
API_EXAMPLE = Path(__file__).resolve().parents[1] / 'docs/web-api-v1-buck-request.json'
INPUT = dict(vin_min=36, vin_max=60, vout=12, pout=120, fs_khz=100,
             ripple_current_ratio=.3, ripple_voltage_ratio_percent=1)


@pytest.fixture
def api(tmp_path, monkeypatch):
    monkeypatch.setenv('PE_CLAW_DATABASE_URL', f'sqlite:///{tmp_path / "jobs.db"}')
    import pe_claw_web.api.main as main
    import pe_claw_web.jobs.artifacts as artifacts
    import pe_claw_web.workers.tasks as tasks
    from pe_claw_web.jobs.store import JobStore
    store = JobStore()
    from unittest.mock import MagicMock
    monkeypatch.setattr(main.celery_app, 'connection_for_write', MagicMock())
    monkeypatch.setattr(main, 'store', store)
    monkeypatch.setattr(tasks, 'store', store)
    for module in (main, tasks, artifacts):
        monkeypatch.setattr(module, 'ARTIFACT_ROOT', tmp_path / 'artifacts')
    yield main, tasks, store
    store.engine.dispose()


def call(api, method, path, **kwargs):
    if path.startswith('/api/v1/design') and 'Authorization' not in kwargs.get('headers', {}):
        token, _ = auth_identity(api.store)
        kwargs.setdefault('headers', {})['Authorization'] = f'Bearer {token}'
    async def send():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api.app), base_url='http://test') as client:
            return await client.request(method, path, **kwargs)
    return asyncio.run(send())


def auth_identity(store):
    if not hasattr(store, '_contract_auth'):
        authenticated = store.authenticate_credentials('contract-user', 'contract-password-1234')
        if authenticated is None:
            store.create_user('contract-user', 'contract-password-1234')
            authenticated = store.authenticate_credentials('contract-user', 'contract-password-1234')
        token, _, user = authenticated
        store._contract_auth = (token, user.user_id)
    return store._contract_auth


def test_catalog_matches_browser_fixture_and_gui_defaults(api):
    main, _, _ = api
    response = call(main, 'GET', '/api/v1/topologies')
    assert response.status_code == 200
    assert 'module_path' not in response.text and 'form_path' not in response.text
    from pe_claw_gui.topologies.base.registry import build_default_registry
    registry = build_default_registry()
    topologies = response.json()['topologies']
    assert len(topologies) == 19
    assert all(item['web_enabled'] for item in topologies)
    assert [item['id'] for item in topologies] == [
        definition.topology_id for definition in registry.list_definitions()
    ]
    for item in topologies:
        gui_fields = registry.get_form_class(item['id']).get_design_fields()
        assert [field['key'] for field in item['fields']] == [field.key for field in gui_fields]
        assert [field['gui_label'] for field in item['fields']] == [field.label for field in gui_fields]
        assert [field['default'] for field in item['fields']] == [field.default for field in gui_fields]
        assert [field['choices'] for field in item['fields']] == [list(field.choices) for field in gui_fields]
        assert all(field['input_type'] in {'number', 'select', 'text'} for field in item['fields'])
        operating_keys = [field['key'] for field in item['operating_point']['fields']]
        if item['category_id'] == 'ac_dc':
            assert operating_keys == ['load_ratio']
        elif item['category_id'] == 'dc_ac':
            assert operating_keys == ['load_ratio', 'power_factor']
        elif item['id'].startswith('llc_resonant_converter_'):
            assert operating_keys == ['vin_v', 'vout_v', 'load_ratio']
        else:
            assert operating_keys == ['vin_v', 'load_ratio']
        assert item['operating_point']['defaults']['vin_v'] > 0


def test_real_buck_sync_http_matches_topology_fixture(api, tmp_path, monkeypatch):
    main, _, _ = api
    from pe_claw_web.api.runner import run_buck_design
    monkeypatch.setattr(main, 'run_buck_design', lambda request: run_buck_design(request, output_root=tmp_path / 'pipeline'))
    response = call(main, 'POST', '/api/v1/design/buck', json=json.loads(API_EXAMPLE.read_text(encoding='utf-8')))
    assert response.status_code == 200, response.text
    result = DesignResultResponse.model_validate(response.json())
    golden = json.loads((FIXTURES / 'result.json').read_text(encoding='utf-8'))
    assert result.summary['candidate'] == golden['summary']['candidate']
    # GUI entries are strings ("36"); Pydantic normalizes numbers ("36.0").
    # Compare their numeric meaning and every other raw default independently.
    for key, value in golden['summary']['request'].items():
        if key != 'raw_input':
            assert result.summary['request'][key] == value
    raw = result.summary['request']['raw_input']
    assert raw.keys() == golden['summary']['request']['raw_input'].keys()
    for key, value in golden['summary']['request']['raw_input'].items():
        assert float(raw[key]) == float(value) if key in INPUT else raw[key] == value

    # Step 6 freezes the synchronous Web route to the same report contract as
    # the GUI Run Design action, including devices, units, and status fields.
    for key in (
        'schema_version',
        'topology',
        'candidate',
        'ripple',
        'status',
    ):
        assert result.summary[key] == golden['summary'][key]
    assert result.summary['semiconductor_voltage_checks'] == {}
    semiconductor = result.summary['hardware']['semiconductor']
    assert semiconductor['selection_status'] == 'pass'
    assert set(semiconductor['selected_devices']) == {'main_switch', 'rectifier_diode'}
    assert result.summary['candidate']['inductance']['unit'] == 'H'
    assert result.summary['candidate']['capacitance']['unit'] == 'F'
    assert result.summary['candidate']['switching_frequency']['unit'] == 'Hz'
    for key in ('available', 'switch', 'rectifier'):
        assert result.summary['stress'][key] == golden['summary']['stress'][key]


def test_all_topologies_web_input_matches_tkinter_topology_numerics(tmp_path):
    from pe_claw_gui.pipeline.run_topology_pipeline import run_topology_pipeline
    from pe_claw_gui.reports import build_structured_report
    from pe_claw_gui.topologies.base.registry import build_default_registry

    registry = build_default_registry()
    evidence = {}
    for definition in registry.list_definitions():
        fields = registry.get_form_class(definition.topology_id).get_design_fields()
        tkinter_raw = {field.key: field.default for field in fields}
        web_request = TopologyDesignRequest(
            topology=definition.topology_id,
            raw_input=tkinter_raw,
        )
        tkinter_report = run_topology_pipeline(
            registry.get_plugin(definition.topology_id),
            raw_input=tkinter_raw,
            include_waveforms=False,
            output_root=tmp_path / 'tkinter' / definition.topology_id,
        ).report
        web_report = run_topology_pipeline(
            registry.get_plugin(definition.topology_id),
            raw_input=web_request.pipeline_input(),
            include_waveforms=False,
            output_root=tmp_path / 'web' / definition.topology_id,
        ).report
        tkinter_payload = build_structured_report(tkinter_report)
        web_payload = build_structured_report(web_report)
        for section in ('candidate', 'ripple', 'stress', 'topology', 'status'):
            assert web_payload[section] == tkinter_payload[section], (
                definition.topology_id, section
            )
        evidence[definition.topology_id] = {
            'field_count': len(fields),
            'sections': ['candidate', 'ripple', 'stress', 'topology', 'status'],
        }
    assert len(evidence) == 19


def test_generic_topology_job_is_queued_and_restored_with_its_typed_request(api, monkeypatch):
    main, _, store = api
    from pe_claw_gui.topologies.base.registry import build_default_registry

    definition = build_default_registry().get_definition('three_phase_two_level_voltage_source_inverter')
    form = build_default_registry().get_form_class(definition.topology_id)
    raw_input = {field.key: field.default for field in form.get_design_fields()}
    queued = []
    monkeypatch.setattr(main.design_buck_task, 'delay', queued.append)
    response = call(main, 'POST', '/api/v1/design-jobs', json={
        'request': {'topology': definition.topology_id, 'raw_input': raw_input},
    })
    assert response.status_code == 202, response.text
    job_id = response.json()['job_id']
    assert queued == [job_id]
    restored = store.get(job_id)
    assert isinstance(restored[1], TopologyDesignRequest)
    assert restored[1].topology == definition.topology_id
    assert restored[1].pipeline_input() == raw_input


@pytest.mark.parametrize('topology_id', [
    'single_phase_diode_bridge_rectifier_capacitor_filter',
    'single_phase_full_bridge_inverter',
])
def test_nonbuck_web_complete_pipeline_respects_core_capability_boundaries(
    topology_id, tmp_path,
):
    from pe_claw_gui.topologies.base.registry import build_default_registry
    from pe_claw_web.api.complete import STAGES, run_complete

    registry = build_default_registry()
    fields = registry.get_form_class(topology_id).get_design_fields()
    request = TopologyDesignRequest(
        topology=topology_id,
        raw_input={field.key: field.default for field in fields},
    )
    visited = []
    result = run_complete(
        request,
        output_root=tmp_path / topology_id,
        on_stage=lambda stage, _progress: visited.append(stage),
    )
    assert visited == list(STAGES)
    assert result.topology == topology_id
    assert result.summary['candidate']['available'] is True
    assert result.summary['stress']['available'] is True
    assert result.summary['status']['feasible'] in {True, False}


def test_sync_pipeline_failure_is_sanitized(api, monkeypatch):
    main, _, _ = api
    private_detail = r'C:\\private\\student\\design.py API_TOKEN=do-not-leak'

    def fail(_request):
        raise RuntimeError(private_detail)

    monkeypatch.setattr(main, 'run_buck_design', fail)
    response = call(main, 'POST', '/api/v1/design/buck', json=INPUT)

    assert response.status_code == 500
    error = DesignError.model_validate(response.json())
    assert error.code == 'DESIGN_FAILED'
    assert error.message == 'Design calculation failed.'
    assert error.correlation_id
    assert private_detail not in response.text
    assert 'RuntimeError' not in response.text
    assert 'Traceback' not in response.text


def test_job_worker_result_download_across_store_instances(api, tmp_path, monkeypatch):
    main, tasks, store = api
    from pe_claw_web.jobs.store import JobStore
    queued = []
    monkeypatch.setattr(main.design_buck_task, 'delay', queued.append)
    response = call(main, 'POST', '/api/v1/design-jobs', json={'request': INPUT})
    assert response.status_code == 202
    job_id = response.json()['job_id']
    assert queued == [job_id]
    path = f'/api/v1/design-jobs/{job_id}'
    assert call(main, 'GET', path).json()['status'] == 'queued'
    assert call(main, 'GET', path + '/result').status_code == 404
    fixture = DesignResultResponse.model_validate_json((FIXTURES / 'result.json').read_text(encoding='utf-8'))
    monkeypatch.setattr(tasks, 'run_complete_buck_design', lambda request, **kwargs: fixture)
    tasks.design_buck_task.run(job_id)
    reopened = JobStore()
    try:
        monkeypatch.setattr(main, 'store', reopened)
        assert call(main, 'GET', path).json()['status'] == 'succeeded'
        result = call(main, 'GET', path + '/result').json()
        assert result['job_id'] == job_id
        manifest = call(main, 'GET', path + '/artifacts').json()
        downloaded = call(main, 'GET', manifest[0]['download_url'])
        assert downloaded.status_code == 200
        assert downloaded.json()['job_id'] == job_id
        assert downloaded.json()['summary'] == result['summary']
        assert len(downloaded.content) == manifest[0]['size']
        assert manifest[0]['schema_version'] == '1.0'
        assert manifest[0]['stage'] == 'report'
        assert len(manifest[0]['sha256']) == 64
        assert 'attachment' in downloaded.headers['content-disposition']
    finally:
        reopened.engine.dispose()


def test_queue_failure_and_invalid_request_have_http_errors(api, monkeypatch):
    main, _, _ = api
    def unavailable(*args):
        raise ConnectionError('internal broker address')
    monkeypatch.setattr(main.design_buck_task, 'delay', unavailable)
    response = call(main, 'POST', '/api/v1/design-jobs', json={'request': INPUT})
    assert response.status_code == 503
    assert 'internal broker address' not in response.text
    response = call(main, 'POST', '/api/v1/design-jobs', json={'request': {**INPUT, 'vin_min': 80}})
    assert response.status_code == 422
    missing = dict(INPUT)
    missing.pop('pout')
    response = call(main, 'POST', '/api/v1/design/buck', json=missing)
    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'] == ['body', 'pout']
    response = call(main, 'POST', '/api/v1/design/buck', json={**INPUT, 'pout': 0})
    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'] == ['body', 'pout']
    response = call(main, 'POST', '/api/v1/design/buck', json={**INPUT, 'topology': 'unsupported'})
    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'] == ['body', 'topology']
    assert call(main, 'GET', '/api/v1/design-jobs/not-a-job/artifacts/result-json').status_code == 422


def test_failed_job_never_exposes_artifact(api, monkeypatch):
    main, tasks, store = api
    item = store.create(BuckDesignRequest(**INPUT), owner_user_id=auth_identity(store)[1])
    folder = main.ARTIFACT_ROOT / item.job_id
    folder.mkdir(parents=True)
    (folder / 'result.json').write_text('{}')
    def fail(*args, **kwargs):
        raise RuntimeError('calculation failed')
    monkeypatch.setattr(tasks, 'run_complete_buck_design', fail)
    with pytest.raises(RuntimeError):
        tasks.design_buck_task.run(item.job_id)
    path = f'/api/v1/design-jobs/{item.job_id}'
    assert call(main, 'GET', path).json()['status'] == 'failed'
    assert call(main, 'GET', path + '/artifacts/result-json').status_code == 404


def test_unified_exports_download_bytes_and_isolation(api):
    main, _, store = api
    from pe_claw_web.jobs.artifacts import save_result
    item = store.create(BuckDesignRequest(**INPUT), owner_user_id=auth_identity(store)[1])
    summary = {
        'waveform': {'available': True, 'samples': {'time_s': [0, .001, .002], 'inductor_current_a': [1, 2, 1]}},
        'efficiency_sweep': {'available': True, 'status': 'available', 'points': [
            {'load_ratio': {'value': .1, 'unit': 'p.u.'}, 'efficiency': {'value': .85, 'unit': 'ratio'}},
            {'load_ratio': {'value': 1, 'unit': 'p.u.'}, 'efficiency': {'value': .92, 'unit': 'ratio'}},
        ]},
        'capacitor': {'available': True, 'capacitance': {'value': 1e-6, 'unit': 'F', 'source': 'fixture'}},
        'magnetic': {'available': False, 'status': 'blocked'},
    }
    result = DesignResultResponse(job_id=item.job_id, topology=item.topology, summary=summary)
    files = save_result(item.job_id, result)
    result_with_artifacts = DesignResultResponse.model_validate({
        **result.model_dump(mode='json', exclude={'artifacts'}),
        'artifacts': files,
    })
    store.update(item.job_id, status='succeeded', result_json=result_with_artifacts.model_dump(mode='json'))
    assert {f['id'] for f in files} == {'result-json', 'capacitor-csv', 'waveform-csv', 'efficiency_sweep-csv', 'waveform-png', 'efficiency-png'}
    for entry in files:
        downloaded = call(main, 'GET', entry['download_url'])
        assert downloaded.status_code == 200
        assert hashlib.sha256(downloaded.content).hexdigest() == entry['sha256']
        assert len(downloaded.content) == entry['size']
        if entry['media_type'] == 'image/png':
            assert downloaded.content.startswith(b'\x89PNG')
    csv_entry = next(f for f in files if f['id'] == 'capacitor-csv')
    assert 'capacitance,1e-06,F,fixture' in call(main, 'GET', csv_entry['download_url']).text
    assert call(main, 'GET', files[0]['download_url']).json()['artifacts'] == files[1:]
    other = store.create(BuckDesignRequest(**INPUT), owner_user_id=auth_identity(store)[1])
    store.update(other.job_id, status='succeeded', result_json={'artifacts': []})
    assert call(main, 'GET', csv_entry['download_url'].replace(item.job_id, other.job_id)).status_code == 404
    assert call(main, 'GET', f'/api/v1/design-jobs/{item.job_id}/artifacts/private-log').status_code == 404
    (main.ARTIFACT_ROOT / item.job_id / 'exports' / 'capacitor.csv').write_text('tampered')
    assert call(main, 'GET', csv_entry['download_url']).status_code == 404
    store.update(item.job_id, status='expired')
    assert call(main, 'GET', files[0]['download_url']).status_code == 404
    assert call(main, 'GET', f'/api/v1/design-jobs/{item.job_id}/result').status_code == 404
    assert call(main, 'GET', f'/api/v1/design-jobs/{item.job_id}/artifacts').status_code == 404


def test_exports_do_not_publish_stale_files_or_blocked_curves(tmp_path):
    from pe_claw_web.jobs.exports import write_exports
    (tmp_path / 'efficiency.png').write_bytes(b'old run')
    ids = write_exports({'efficiency_sweep': {'available': True, 'status': 'blocked', 'points': []}}, tmp_path)
    assert ids == []


def test_download_rejects_symlink_escape(api, tmp_path):
    main, _, store = api
    item = store.create(BuckDesignRequest(**INPUT), owner_user_id=auth_identity(store)[1])
    folder = main.ARTIFACT_ROOT / item.job_id
    folder.mkdir(parents=True)
    outside = tmp_path / 'private.json'
    outside.write_text('{}')
    try:
        (folder / 'result.json').symlink_to(outside)
    except OSError:
        pytest.skip('Symlink creation requires Windows developer mode')
    store.update(item.job_id, status='succeeded', result_json={'artifacts': [{'id': 'result-json', 'size': 2}]})
    assert call(main, 'GET', f'/api/v1/design-jobs/{item.job_id}/artifacts/result-json').status_code == 404


def test_public_waveform_uses_real_buck_samples(tmp_path):
    from pe_claw_gui.pipeline.run_topology_pipeline import run_topology_pipeline
    from pe_claw_gui.topologies.base.registry import build_default_registry
    from pe_claw_gui.topologies.dc_dc.buck_diode_rectified_unidirectional.input_schema import build_default_inputs
    from pe_claw_gui.reports import build_structured_report
    from pe_claw_web.jobs.exports import public_summary, write_exports
    plugin = build_default_registry().get_plugin(BuckDesignRequest(**INPUT).topology)
    report = run_topology_pipeline(plugin, raw_input=build_default_inputs(), include_waveforms=True, output_root=tmp_path / 'pipeline').report
    summary = public_summary(report, build_structured_report(report))
    assert summary['waveform']['samples']['time_s'] == list(report.waveform.time_s)
    assert summary['waveform']['samples']['inductor_current_a'] == list(report.waveform.inductor_current_a)
    ids = write_exports(summary, tmp_path / 'public')
    assert 'waveform-png' in ids
    assert 'efficiency-png' not in ids


def test_public_summary_exposes_specialized_web_view_data_without_paths():
    from types import SimpleNamespace
    from pe_claw_web.jobs.exports import public_summary

    capacitor_candidate = SimpleNamespace(
        part_number='CAP-1', manufacturer='Maker', series='Series-A',
    )
    capacitor_entry = SimpleNamespace(
        candidate=capacitor_candidate, series_count=1, parallel_count=2,
        total_capacitor_count=2, equivalent_capacitance_f=220e-6,
        total_volume_cm3=12.5, p_total_w=0.7, ripple_total_pp_v=0.2,
        hotspot_temp_c=54.0, feasible=True, representative_label='recommended',
        recommended_flag=True,
    )
    capacitor_side = SimpleNamespace(
        pareto_front=[capacitor_entry], recommended=capacitor_entry,
        min_volume=capacitor_entry, min_loss=capacitor_entry,
        compromise=capacitor_entry,
    )
    magnetic_candidate = SimpleNamespace(
        candidate_id='L-1', assembly_type='single_core', stack_count=1,
        core_name='Core-A', material_name='Material-A', wire_name='Wire-A',
        turns=12, parallel_bundles=1, gap_m=0.001, inductance_h=100e-6,
        fill_factor=0.3, total_volume_m3=2e-6, reference_total_loss_w=1.2,
        b_peak_design_t=0.18,
    )
    layout = SimpleNamespace(
        template_name='E-core', core_family='E', core_name='Core-A',
        material_name='Material-A', wire_name='Wire-A', turns=12, parallels=1,
        outer_width_mm=30.0, outer_height_mm=24.0, outer_depth_mm=18.0,
        window_width_mm=12.0, window_height_mm=8.0,
        winding_block_width_mm=10.0, winding_block_height_mm=7.0,
        overall_width_mm=34.0, overall_height_mm=28.0, overall_depth_mm=20.0,
        gap_mm=1.0, geometry_dimension_source='library', geometry_warning='',
    )
    waveform = SimpleNamespace(**{
        'time_s': [0.0, 1e-6],
        'switch_node_voltage_v': [0.0, 48.0],
        'inductor_current_a': [9.0, 11.0],
        'capacitor_current_a': [-1.0, 1.0],
        'output_voltage_v': [12.0, 12.1],
        'switch_current_a': [0.0, 11.0],
        'diode_current_a': [9.0, 0.0],
        'input_source_current_a': [0.0, 11.0],
        'inductor_voltage_v': [-12.0, 36.0],
        'vox_voltage_v': [], 'output_ripple_v': [-0.05, 0.05],
        'gate_s1': [0.0, 1.0], 'gate_s2': [], 'gate_s3': [], 'gate_s4': [],
    })
    report = SimpleNamespace(
        waveform=waveform,
        capacitor=SimpleNamespace(
            input_selection=capacitor_side,
            output_selection=capacitor_side,
        ),
        magnetic=SimpleNamespace(
            compressed_candidates=[magnetic_candidate],
            chosen_designs=[magnetic_candidate],
            design_requirements={'target_inductance_h': 100e-6},
        ),
        geometry=SimpleNamespace(targets=[SimpleNamespace(layout=layout)]),
        efficiency_sweep=None,
    )
    summary = {
        'waveform': {},
        'capacitor': {'input': {}, 'output': {}},
        'magnetic': {},
        'geometry': {'targets': [{'artifact_paths': ['D:/private/geometry.png']}]},
    }

    exposed = public_summary(report, summary)

    assert set(exposed['waveform']['samples']) >= {
        'time_s', 'switch_current_a', 'diode_current_a', 'gate_s1',
    }
    assert exposed['capacitor']['input']['pareto'][0]['part_number'] == 'CAP-1'
    assert exposed['magnetic']['candidate_comparison'][0]['design_id'] == 'L-1'
    assert exposed['geometry']['targets'][0]['layout']['overall_width_mm'] == 34.0
    assert 'artifact_paths' not in exposed['geometry']['targets'][0]


def test_retry_http_and_partial_result(api, monkeypatch):
    main, tasks, store = api
    from datetime import datetime, timezone
    item = store.create(BuckDesignRequest(**INPUT), owner_user_id=auth_identity(store)[1])
    partial = DesignResultResponse(job_id=item.job_id, topology=item.topology, summary={'candidate': {'available':True}})
    store.update(item.job_id, status='failed', finished_at=datetime.now(timezone.utc), stage='magnetics',
                 checkpoint_json={'saved':True}, result_json=partial.model_dump(mode='json'))
    path=f'/api/v1/design-jobs/{item.job_id}'
    assert call(main,'GET',path+'/result').status_code == 200
    assert call(main,'GET',path+'/artifacts').status_code == 404
    queued=[]
    monkeypatch.setattr(main.design_buck_task,'delay',queued.append)
    response=call(main,'POST',path+'/retry')
    assert response.status_code == 202 and response.json()['status']=='queued'
    assert queued == [item.job_id]
    assert store.get_checkpoint(item.job_id)=={'saved':True}
    assert call(main,'POST',path+'/retry').status_code == 409


def test_duplicate_complete_submission_publishes_once(api, monkeypatch):
    main, tasks, store=api
    queued=[]
    monkeypatch.setattr(main.design_buck_task,'delay',queued.append)
    first=call(main,'POST','/api/v1/design-jobs',json={'request':INPUT})
    second=call(main,'POST','/api/v1/design-jobs',json={'request':INPUT,'operating_point':{'vin_v':48,'load_ratio':1}})
    assert first.status_code==second.status_code==202
    assert first.json()['job_id']==second.json()['job_id']
    assert queued == [first.json()['job_id']]


def test_nonbuck_default_operating_point_is_idempotent(api, monkeypatch):
    main, _, _ = api
    from pe_claw_gui.topologies.base.registry import build_default_registry

    topology = 'single_phase_full_bridge_inverter'
    fields = build_default_registry().get_form_class(topology).get_design_fields()
    raw_input = {field.key: field.default for field in fields}
    request = {'topology': topology, 'raw_input': raw_input}
    queued = []
    monkeypatch.setattr(main.design_buck_task, 'delay', queued.append)

    first = call(main, 'POST', '/api/v1/design-jobs', json={'request': request})
    second = call(main, 'POST', '/api/v1/design-jobs', json={
        'request': request,
        'operating_point': {'vin_v': float(raw_input['vdc_nom']), 'load_ratio': 1},
    })

    assert first.status_code == second.status_code == 202
    assert first.json()['job_id'] == second.json()['job_id']
    assert queued == [first.json()['job_id']]


def test_waveform_action_http_enforces_owned_succeeded_job_and_design_range(api, monkeypatch):
    main, _, store = api
    _, owner_user_id = auth_identity(store)
    item = store.create(BuckDesignRequest(**INPUT), owner_user_id=owner_user_id)
    store.update(item.job_id, status='succeeded', progress=100, stage='finalize')
    queued = []
    monkeypatch.setattr(main.run_action_task, 'delay', queued.append)
    path = f'/api/v1/design-jobs/{item.job_id}/actions/waveforms'
    payload = {
        'job_id': item.job_id,
        'action': 'waveforms',
        'operating_point': {'vin_v': 42, 'load_ratio': 0.5},
    }

    response = call(main, 'POST', path, json=payload)

    assert response.status_code == 202
    assert response.json()['action'] == 'waveforms'
    assert queued == [response.json()['action_id']]
    assert call(main, 'POST', path, json={
        **payload,
        'operating_point': {'vin_v': 80, 'load_ratio': 0.5},
    }).status_code == 422
    assert call(main, 'POST', path, json={**payload, 'action': 'magnetics'}).status_code == 422


@pytest.mark.parametrize(('route_name', 'action_name'), [
    ('capacitor', 'capacitor'),
    ('magnetics', 'magnetics'),
    ('efficiency-sweep', 'efficiency_sweep'),
])
def test_derived_stage_action_http_routes(api, monkeypatch, route_name, action_name):
    main, _, store = api
    _, owner_user_id = auth_identity(store)
    item = store.create(BuckDesignRequest(**INPUT), owner_user_id=owner_user_id)
    store.update(item.job_id, status='succeeded', progress=100, stage='finalize')
    queued = []
    monkeypatch.setattr(main.run_action_task, 'delay', queued.append)

    response = call(
        main,
        'POST',
        f'/api/v1/design-jobs/{item.job_id}/actions/{route_name}',
        json={'job_id': item.job_id, 'action': action_name},
    )

    assert response.status_code == 202
    assert response.json()['action'] == action_name
    assert queued == [response.json()['action_id']]
