"""Adopt legacy tables and add durable recovery state without deleting jobs."""
from alembic import op
import sqlalchemy as sa

revision = '0002_complete_jobs'
down_revision = '0001_design_jobs'

def upgrade():
    conn = op.get_bind()
    columns = {c['name'] for c in sa.inspect(conn).get_columns('design_jobs')}
    for column in [
        sa.Column('execution_json', sa.JSON(), nullable=True),
        sa.Column('input_key', sa.String(64), nullable=True),
        sa.Column('client_key', sa.String(128), nullable=True),
        sa.Column('attempt', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('lease_token', sa.String(64), nullable=True),
        sa.Column('heartbeat_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('checkpoint_json', sa.JSON(), nullable=True),
        sa.Column('stages_json', sa.JSON(), nullable=True),
    ]:
        if column.name not in columns:
            op.add_column('design_jobs', column)
    indexes = {i['name'] for i in sa.inspect(conn).get_indexes('design_jobs')}
    for field in ('input_key', 'client_key'):
        name = 'uq_design_jobs_' + field
        if name not in indexes:
            op.create_index(name, 'design_jobs', [field], unique=True)
    if 'design_actions' not in sa.inspect(conn).get_table_names():
        op.create_table('design_actions',
            sa.Column('action_id', sa.String(64), primary_key=True),
            sa.Column('job_id', sa.String(64), nullable=False),
            sa.Column('action', sa.String(32), nullable=False),
            sa.Column('idempotency_key', sa.String(128), nullable=False),
            sa.Column('request_json', sa.JSON(), nullable=False),
            sa.Column('status', sa.String(20), nullable=False),
            sa.Column('progress', sa.Integer(), nullable=False),
            sa.Column('stage', sa.String(64)),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('started_at', sa.DateTime(timezone=True)),
            sa.Column('finished_at', sa.DateTime(timezone=True)),
            sa.Column('error_json', sa.JSON()), sa.Column('result_json', sa.JSON()))
        op.create_index('ix_design_actions_job_id', 'design_actions', ['job_id'])
    elif 'idempotency_key' not in {c['name'] for c in sa.inspect(conn).get_columns('design_actions')}:
        op.add_column('design_actions', sa.Column('idempotency_key', sa.String(128), nullable=False, server_default=''))

def downgrade():
    raise RuntimeError('Restore a database backup for rollback; destructive checkpoint downgrade is disabled.')
