"""Opt-in real PostgreSQL validation, using an isolated per-test schema."""
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

@pytest.fixture
def postgres_schema():
    url = os.getenv('PE_CLAW_TEST_POSTGRES_URL')
    if not url:
        pytest.skip('Set PE_CLAW_TEST_POSTGRES_URL to enable real PostgreSQL migration/reconnect test')
    schema = 'f5_' + uuid.uuid4().hex
    admin = create_engine(url)
    try:
        with admin.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA {schema}'))
        scoped = make_url(url).update_query_dict({'options': f'-csearch_path={schema}'})
        yield admin, scoped.render_as_string(hide_password=False)
    finally:
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS {schema} CASCADE'))
        admin.dispose()


def test_postgres_migration_claim_and_reconnect(postgres_schema):
    from pe_claw_web.jobs.store import JobStore
    from pe_claw_web.schemas import BuckDesignRequest, DesignJobCreate
    admin, url = postgres_schema
    repository = JobStore(url, initialize=True)
    try:
        request = DesignJobCreate(request=BuckDesignRequest(vin_min=36,vin_max=60,vout=12,pout=120,fs_khz=100,ripple_current_ratio=.3,ripple_voltage_ratio_percent=1))
        first, created = repository.create_complete(request)
        again, duplicate = repository.create_complete(request)
        assert created and not duplicate and first.job_id == again.job_id
        assert repository.claim(first.job_id)
        assert repository.claim(first.job_id) is None
        with repository.engine.connect() as connection:
            own_pid = connection.scalar(text('SELECT pg_backend_pid()'))
        # Only terminate this test's idle pooled connection, never other sessions.
        with admin.begin() as connection:
            connection.execute(text('SELECT pg_terminate_backend(:pid)'), {'pid': own_pid})
        assert repository.get(first.job_id)[0].status == 'running'
        with repository.engine.connect() as connection:
            assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '0003_request_keys'
    finally:
        if repository is not None:
            repository.engine.dispose()


def test_postgres_concurrent_submission_and_stale_lease(postgres_schema):
    from pe_claw_web.jobs.store import JobStore, LeaseLost, utcnow
    from pe_claw_web.schemas import BuckDesignRequest, DesignJobCreate
    repository = JobStore(postgres_schema[1], initialize=True)
    try:
        payload = DesignJobCreate(request=BuckDesignRequest(vin_min=36, vin_max=60,
            vout=12, pout=120, fs_khz=100, ripple_current_ratio=.3,
            ripple_voltage_ratio_percent=1), client_request_id='concurrent-client')
        with ThreadPoolExecutor(max_workers=4) as pool:
            submitted = list(pool.map(lambda _: repository.create_complete(payload), range(8)))
        assert len({item.job_id for item, _ in submitted}) == 1
        assert sum(created for _, created in submitted) == 1
        job_id = submitted[0][0].job_id
        with ThreadPoolExecutor(max_workers=4) as pool:
            claimed = list(pool.map(lambda _: repository.claim(job_id), range(8)))
        assert len([token for token in claimed if token]) == 1
        old = next(token for token in claimed if token)
        repository.owned_update(job_id, old, checkpoint_json={'saved': 'before-loss'},
            heartbeat_at=utcnow()-timedelta(minutes=10))
        assert job_id in repository.recover(1)
        new = repository.claim(job_id)
        assert new and new != old
        with pytest.raises(LeaseLost):
            repository.owned_update(job_id, old, checkpoint_json={'saved': 'stale'})
        with pytest.raises(LeaseLost):
            repository.publish(job_id, old, lambda: {'stale': True})
        assert repository.get_checkpoint(job_id) == {'saved': 'before-loss'}
        alias = payload.model_copy(update={'client_request_id': 'alias-client'})
        assert repository.create_complete(alias)[0].job_id == job_id
        with pytest.raises(ValueError):
            repository.create_complete(alias.model_copy(update={
                'request': payload.request.model_copy(update={'pout': 130})}))
    finally:
        repository.engine.dispose()


@pytest.mark.parametrize('legacy', [False, True], ids=['revision-0001', 'unmanaged-table'])
def test_postgres_upgrade_preserves_old_result(postgres_schema, legacy):
    import json
    from alembic import command
    from alembic.config import Config
    from pathlib import Path
    from pe_claw_web.jobs.store import JobStore
    from pe_claw_web.jobs.migrate import upgrade
    repository = JobStore(postgres_schema[1], initialize=False)
    try:
        config = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
        with repository.engine.begin() as connection:
            config.attributes['connection'] = connection
            command.upgrade(config, '0001_design_jobs')
            connection.execute(text('''INSERT INTO design_jobs
                (job_id, topology, request_json, status, progress, stage, created_at, result_json)
                VALUES ('legacy', 'buck_diode_rectified_unidirectional', CAST(:request AS JSON),
                'succeeded', 100, 'finalize', CURRENT_TIMESTAMP, CAST(:result AS JSON))'''),
                {'request': json.dumps(dict(vin_min=36, vin_max=60, vout=12, pout=120,
                    fs_khz=100, ripple_current_ratio=.3, ripple_voltage_ratio_percent=1)),
                 'result': json.dumps({'summary': {'legacy-value': 123}, 'artifacts': []})})
            if legacy:
                connection.execute(text('DROP TABLE alembic_version'))
        upgrade(repository.engine)
        upgrade(repository.engine)
        state, _, result = repository.get('legacy')
        assert state.status == 'succeeded' and state.attempt == 0
        assert result == {'summary': {'legacy-value': 123}, 'artifacts': []}
        with repository.engine.connect() as connection:
            assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '0003_request_keys'
    finally:
        repository.engine.dispose()
