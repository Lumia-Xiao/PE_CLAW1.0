from alembic import op
import sqlalchemy as sa
revision='0001_design_jobs'; down_revision=None
def upgrade():
 op.create_table('design_jobs',sa.Column('job_id',sa.String(64),primary_key=True),sa.Column('topology',sa.String(128)),sa.Column('request_json',sa.JSON()),sa.Column('status',sa.String(20)),sa.Column('progress',sa.Integer()),sa.Column('stage',sa.String(64)),sa.Column('created_at',sa.DateTime(timezone=True)),sa.Column('started_at',sa.DateTime(timezone=True)),sa.Column('finished_at',sa.DateTime(timezone=True)),sa.Column('error_json',sa.JSON()),sa.Column('result_json',sa.JSON()))
def downgrade(): op.drop_table('design_jobs')
