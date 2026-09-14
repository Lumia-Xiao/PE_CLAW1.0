"""HTTP contracts used by React, with an actual Buck run and isolated storage."""

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from pe_claw_web.schemas import BuckDesignRequest, DesignResultResponse

FIXTURES = Path(__file__).resolve().parents[1] / 'web/frontend/tests/fixtures'
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
    monkeypatch.setattr(main, 'store', store)
    monkeypatch.setattr(tasks, 'store', store)
    for module in (main, tasks, artifacts):
        monkeypatch.setattr(module, 'ARTIFACT_ROOT', tmp_path / 'artifacts')
    yield main, tasks, store
    store.engine.dispose()


def call(api, method, path, **kwargs):
    async def send():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api.app), base_url='http://test') as client:
            return await client.request(method, path, **kwargs)
    return asyncio.run(send())


def test_catalog_matches_browser_fixture_and_gui_defaults(api):
    main, _, _ = api
    response = call(main, 'GET', '/api/v1/topologies')
    assert response.status_code == 200
    assert response.json() == json.loads((FIXTURES / 'catalog.json').read_text(encoding='utf-8'))
    assert 'module_path' not in response.text and 'form_path' not in response.text
    assert [t['id'] for t in response.json()['topologies'] if t['web_enabled']] == ['buck_diode_rectified_unidirectional']


def test_real_buck_sync_http_matches_topology_fixture(api, tmp_path, monkeypatch):
    main, _, _ = api
    from pe_claw_web.api.runner import run_buck_design
    monkeypatch.setattr(main, 'run_buck_design', lambda request: run_buck_design(request, output_root=tmp_path / 'pipeline'))
    response = call(main, 'POST', '/api/v1/design/buck', json=INPUT)
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
    monkeypatch.setattr(tasks, 'run_buck_design', lambda request, **kwargs: fixture)
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
    assert call(main, 'GET', '/api/v1/design-jobs/not-a-job/artifacts/result-json').status_code == 422


def test_failed_job_never_exposes_artifact(api, monkeypatch):
    main, tasks, store = api
    item = store.create(BuckDesignRequest(**INPUT))
    folder = main.ARTIFACT_ROOT / item.job_id
    folder.mkdir(parents=True)
    (folder / 'result.json').write_text('{}')
    def fail(*args, **kwargs):
        raise RuntimeError('calculation failed')
    monkeypatch.setattr(tasks, 'run_buck_design', fail)
    with pytest.raises(RuntimeError):
        tasks.design_buck_task.run(item.job_id)
    path = f'/api/v1/design-jobs/{item.job_id}'
    assert call(main, 'GET', path).json()['status'] == 'failed'
    assert call(main, 'GET', path + '/artifacts/result-json').status_code == 404
