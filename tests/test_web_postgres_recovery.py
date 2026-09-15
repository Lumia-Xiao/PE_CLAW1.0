"""Opt-in real PostgreSQL validation, using an isolated per-test schema."""
import os
import uuid
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

def test_postgres_migration_claim_and_reconnect():
    url = os.getenv('PE_CLAW_TEST_POSTGRES_URL')
    if not url:
        pytest.skip('Set PE_CLAW_TEST_POSTGRES_URL to enable real PostgreSQL migration/reconnect test')
    from pe_claw_web.jobs.store import JobStore
    from pe_claw_web.schemas import BuckDesignRequest, DesignJobCreate
    schema = 'f5_' + uuid.uuid4().hex
    admin = create_engine(url)
    repository = None
    try:
        with admin.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA {schema}'))
        scoped = make_url(url).update_query_dict({'options': f'-csearch_path={schema}'})
        repository = JobStore(scoped.render_as_string(hide_password=False), initialize=True)
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
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS {schema} CASCADE'))
        admin.dispose()
