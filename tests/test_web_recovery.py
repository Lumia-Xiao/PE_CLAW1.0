"""Durable recovery contracts shared by SQLite and optional isolated PostgreSQL."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from dataclasses import replace
import json
from pathlib import Path
import pytest
from sqlalchemy import inspect, text

from pe_claw_web.schemas import BuckDesignRequest, DesignJobCreate
from pe_claw_web.jobs.store import JobStore, JobRow, LeaseLost, utcnow, digest
from pe_claw_web.jobs.checkpoints import snapshot, restore, encode, CheckpointIncompatible, checksum
from pe_claw_web.jobs.cleanup import cleanup_artifacts

INPUT = dict(vin_min=36, vin_max=60, vout=12, pout=120, fs_khz=100, ripple_current_ratio=.3, ripple_voltage_ratio_percent=1)

@pytest.fixture
def repo(tmp_path):
    instance = JobStore(f'sqlite:///{tmp_path / "jobs.db"}')
    yield instance
    instance.engine.dispose()

def test_migration_adopts_legacy_without_losing_rows(tmp_path):
    import sqlite3
    database = tmp_path/'legacy.db'
    with sqlite3.connect(database) as conn:
        conn.execute('CREATE TABLE design_jobs (job_id VARCHAR(64) PRIMARY KEY, topology VARCHAR(128), request_json JSON, status VARCHAR(20), progress INTEGER, stage VARCHAR(64), created_at DATETIME, started_at DATETIME, finished_at DATETIME, error_json JSON, result_json JSON)')
        conn.execute('INSERT INTO design_jobs(job_id,topology,request_json,status,progress,created_at) VALUES(?,?,?,?,?,?)', ('legacy','buck_diode_rectified_unidirectional',json.dumps(INPUT),'succeeded',100,'2026-09-01 00:00:00'))
        conn.execute('CREATE TABLE design_actions (action_id VARCHAR(64) PRIMARY KEY)')
    repo = JobStore(f'sqlite:///{database}')
    assert repo.get('legacy')[0].status == 'succeeded'
    assert 'idempotency_key' in {c['name'] for c in inspect(repo.engine).get_columns('design_actions')}
    with repo.engine.connect() as conn:
        assert conn.scalar(text('SELECT version_num FROM alembic_version')) == '0003_request_keys'
    from pe_claw_web.jobs.migrate import upgrade
    upgrade(repo.engine)
    assert repo.get('legacy')[0].job_id == 'legacy'
    repo.engine.dispose()

def test_concurrent_idempotency_claim_and_retry(repo):
    payload = DesignJobCreate(request=BuckDesignRequest(**INPUT), client_request_id='client-1')
    with ThreadPoolExecutor(max_workers=4) as pool:
        submitted = list(pool.map(lambda _: repo.create_complete(payload), range(4)))
    assert len({p[0].job_id for p in submitted}) == 1
    assert sum(created for _, created in submitted) == 1
    job_id = submitted[0][0].job_id
    with pytest.raises(ValueError):
        repo.create_complete(payload.model_copy(update={'request': BuckDesignRequest(**{**INPUT, 'pout': 130})}))
    with ThreadPoolExecutor(max_workers=4) as pool:
        tokens = list(pool.map(lambda _: repo.claim(job_id), range(4)))
    assert len([token for token in tokens if token]) == 1
    assert repo.retry(job_id) is False
    alias = payload.model_copy(update={'client_request_id':'alias-2'})
    assert repo.create_complete(alias)[0].job_id == job_id
    with pytest.raises(ValueError):
        repo.create_complete(alias.model_copy(update={'request':BuckDesignRequest(**{**INPUT,'pout':150})}))

def test_queue_outage_is_durable_without_clobbering_claim(repo):
    item = repo.create(BuckDesignRequest(**INPUT))
    repo.queue_unavailable(item.job_id)
    assert item.job_id in repo.recover()
    token = repo.claim(item.job_id)
    repo.queue_unavailable(item.job_id)
    assert repo.get(item.job_id)[0].status == 'running'
    assert repo.get(item.job_id)[0].error is None
    repo.heartbeat(item.job_id, token)

def test_stale_worker_is_fenced_and_checkpoints_survive_reopen(repo):
    item = repo.create(BuckDesignRequest(**INPUT))
    old = repo.claim(item.job_id)
    repo.owned_update(item.job_id, old, checkpoint_json={'test': 'durable'}, stage='magnetics', heartbeat_at=utcnow()-timedelta(minutes=10))
    reopened = JobStore(repo.engine.url.render_as_string(hide_password=False))
    assert item.job_id in reopened.recover(1)
    new = reopened.claim(item.job_id)
    assert new != old
    with pytest.raises(LeaseLost):
        repo.owned_update(item.job_id, old, checkpoint_json={'test': 'overwritten'})
    with pytest.raises(LeaseLost):
        repo.publish(item.job_id, old, lambda: {'bad': True})
    assert reopened.get_checkpoint(item.job_id) == {'test': 'durable'}
    assert reopened.get(item.job_id)[0].attempt == 2
    reopened.engine.dispose()

def test_database_outage_leaves_last_committed_checkpoint(repo, monkeypatch, real_report):
    from sqlalchemy.exc import OperationalError
    import pe_claw_web.workers.tasks as tasks
    from pe_claw_web.api.complete import result_of
    monkeypatch.setattr(tasks, 'store', repo)
    item = repo.create(BuckDesignRequest(**INPUT))
    partial = result_of(real_report, item.topology)
    original = repo.owned_update
    def disconnected(*args, **kwargs):
        raise OperationalError('checkpoint write', {}, ConnectionError('database unavailable'))
    def execute(request, **kwargs):
        kwargs['on_checkpoint']('topology', {'durable':1}, partial)
        monkeypatch.setattr(repo, 'owned_update', disconnected)
        kwargs['on_checkpoint']('devices', {'uncommitted':1}, partial)
    monkeypatch.setattr(tasks, 'run_complete_buck_design', execute)
    with pytest.raises(OperationalError): tasks.design_buck_task.run(item.job_id)
    monkeypatch.setattr(repo, 'owned_update', original)
    assert repo.get_checkpoint(item.job_id)=={'durable':1}
    repo.update(item.job_id, heartbeat_at=utcnow()-timedelta(minutes=5))
    assert item.job_id in repo.recover(1)

def test_cleanup_protects_active_and_unknown_folders(repo, tmp_path):
    root = tmp_path/'artifacts'
    root.mkdir()
    (root/'user-output').mkdir()
    for status in ('running','queued','succeeded','failed'):
        item = repo.create(BuckDesignRequest(**INPUT))
        (root/item.job_id).mkdir()
        repo.update(item.job_id, status=status, finished_at=utcnow()-timedelta(days=9))
    assert cleanup_artifacts(root, 24, repository=repo) == 2
    assert len(list(root.iterdir())) == 3
    assert (root/'user-output').exists()

@pytest.fixture
def real_report(tmp_path):
    from pe_claw_gui.pipeline.run_topology_pipeline import run_topology_pipeline
    from pe_claw_gui.topologies.base.registry import build_default_registry
    from pe_claw_gui.topologies.dc_dc.buck_diode_rectified_unidirectional.input_schema import build_default_inputs
    plugin = build_default_registry().get_plugin(BuckDesignRequest(**INPUT).topology)
    return run_topology_pipeline(plugin, raw_input=build_default_inputs(), output_root=tmp_path/'pipeline').report

def test_snapshot_roundtrip_and_tamper_rejection(real_report):
    from pe_claw_gui.models.device_result import DeviceSelectionResult
    from pe_claw_gui.models.inductor import FixedInductorDesignCandidate
    from pe_claw_gui.models.magnetic_result import MagneticResult
    report = replace(real_report, device=DeviceSelectionResult(selected_devices={'switch':'selected-device'}), magnetic=MagneticResult(chosen_designs=[FixedInductorDesignCandidate(candidate_id='chosen',turns=12)]))
    data = json.loads(json.dumps(snapshot(report, 'magnetics', 'input-key')))
    restored, stage = restore(data, 'input-key')
    assert stage == 'magnetics'
    assert restored.device.selected_devices == report.device.selected_devices
    assert restored.magnetic.chosen_designs == report.magnetic.chosen_designs
    assert restored.candidate == report.candidate
    assert encode(restored) == encode(report)
    with pytest.raises(CheckpointIncompatible): restore(data, 'wrong-input')
    with pytest.raises(CheckpointIncompatible): restore({**data, 'pipeline_version':'old'}, 'input-key')
    body = {**data, 'report': {'kind':'dataclass','type':'os:system','fields':{'command':'bad'}}}
    body['sha256'] = checksum({k:v for k,v in body.items() if k != 'sha256'})
    with pytest.raises(CheckpointIncompatible): restore(body, 'input-key')

def test_resume_skips_selection_and_preserves_hardware(real_report, monkeypatch, tmp_path):
    import pe_claw_web.api.complete as complete
    from pe_claw_gui.models.device_result import DeviceSelectionResult
    from pe_claw_gui.models.magnetic_result import MagneticResult
    from pe_claw_gui.models.inductor import FixedInductorDesignCandidate
    from pe_claw_gui.models.efficiency_sweep import EfficiencySweepResult
    request = BuckDesignRequest(**INPUT)
    point = {'vin_v': 48.0, 'load_ratio': 0.75}
    report = replace(real_report, device=DeviceSelectionResult(selected_devices={'switch':'fixed'}), magnetic=MagneticResult(chosen_designs=[FixedInductorDesignCandidate(candidate_id='fixed-core',turns=10)]))
    key = digest({'request': request.model_dump(mode='json'), 'operating_point':point})
    data = snapshot(report, 'magnetics', key)
    def forbidden(*args, **kwargs): raise AssertionError('selection re-executed')
    for name in ('run_topology_pipeline','run_device_pipeline','run_capacitor_pipeline','run_magnetic_pipeline'):
        monkeypatch.setattr(complete, name, forbidden)
    calls=[]
    def refresh(current, plugin, operating_point, **kwargs):
        assert current.device.selected_devices == {'switch':'fixed'}
        assert current.magnetic.chosen_designs[0].candidate_id == 'fixed-core'
        calls.append('refresh')
        return replace(current, operating_point=operating_point)
    def sweep(current, **kwargs):
        assert current.magnetic.chosen_designs[0].turns == 10
        calls.append('sweep')
        return EfficiencySweepResult(status='blocked', blocked_reason='test-only absent loss data')
    monkeypatch.setattr(complete, 'run_operating_point_refresh', refresh)
    monkeypatch.setattr(complete, 'run_geometry_pipeline', lambda report, **kw: report)
    monkeypatch.setattr(complete, 'run_efficiency_sweep', sweep)
    progress=[]
    result=complete.run_complete(request, output_root=tmp_path/'resume', operating_point=point, checkpoint=data, on_stage=lambda stage,p: progress.append(stage))
    assert calls == ['refresh','sweep']
    assert progress == ['operating_point','efficiency_sweep','report']
    assert result.summary['efficiency_sweep']['status'] == 'blocked'

def test_worker_failure_retry_keeps_partial_result(repo, monkeypatch, real_report):
    import pe_claw_web.workers.tasks as tasks
    from pe_claw_web.api.complete import result_of
    monkeypatch.setattr(tasks, 'store', repo)
    monkeypatch.setattr(tasks, 'ARTIFACT_ROOT', Path(repo.engine.url.database).parent/'artifacts')
    item = repo.create(BuckDesignRequest(**INPUT))
    partial = result_of(real_report, item.topology)
    def fail(request, **kwargs):
        kwargs['on_stage']('topology', 5)
        kwargs['on_checkpoint']('topology', {'saved':True}, partial)
        kwargs['on_stage']('devices',18)
        raise RuntimeError('private stack')
    monkeypatch.setattr(tasks, 'run_complete_buck_design', fail)
    with pytest.raises(RuntimeError): tasks.design_buck_task.run(item.job_id)
    status, _, result = repo.get(item.job_id)
    assert status.status == 'failed' and status.stage == 'devices'
    assert status.retryable and result['job_id'] == item.job_id
    assert 'private stack' not in status.error.message
    assert repo.retry(item.job_id)
    def finish(request, **kwargs):
        assert kwargs['checkpoint'] == {'saved':True}
        return partial
    monkeypatch.setattr(tasks, 'run_complete_buck_design', finish)
    tasks.design_buck_task.run(item.job_id)
    assert repo.get(item.job_id)[0].status == 'succeeded'
    assert repo.get(item.job_id)[0].attempt == 2
    tasks.design_buck_task.run(item.job_id)
    assert repo.get(item.job_id)[0].attempt == 2
