"""Bind every client request ID, including aliases of an existing identical job."""
from alembic import op
import sqlalchemy as sa
revision = '0003_request_keys'
down_revision = '0002_complete_jobs'

def upgrade():
    if 'design_request_keys' not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table('design_request_keys',
            sa.Column('client_key', sa.String(128), primary_key=True),
            sa.Column('job_id', sa.String(64), nullable=False),
            sa.Column('input_key', sa.String(64), nullable=False))
        op.create_index('ix_design_request_keys_job_id', 'design_request_keys', ['job_id'])

def downgrade():
    raise RuntimeError('Request keys are durable; restore the pre-upgrade database backup to roll back.')
