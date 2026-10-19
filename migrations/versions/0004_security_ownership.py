"""Add users, bearer sessions, ownership and append-only security audit events."""

from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone


revision = '0004_security_ownership'
down_revision = '0003_request_keys'


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = set(inspector.get_table_names())
    if 'web_users' not in tables:
        op.create_table(
            'web_users',
            sa.Column('user_id', sa.String(64), primary_key=True),
            sa.Column('username', sa.String(64), nullable=False),
            sa.Column('password_hash', sa.String(512), nullable=False),
            sa.Column('role', sa.String(20), nullable=False),
            sa.Column('active', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index('ix_web_users_username', 'web_users', ['username'], unique=True)
    if 'web_sessions' not in tables:
        op.create_table(
            'web_sessions',
            sa.Column('token_hash', sa.String(64), primary_key=True),
            sa.Column('user_id', sa.String(64), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('revoked_at', sa.DateTime(timezone=True)),
        )
        op.create_index('ix_web_sessions_user_id', 'web_sessions', ['user_id'])
        op.create_index('ix_web_sessions_expires_at', 'web_sessions', ['expires_at'])
    if 'web_audit_events' not in tables:
        op.create_table(
            'web_audit_events',
            sa.Column('event_id', sa.String(64), primary_key=True),
            sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('actor_user_id', sa.String(64)),
            sa.Column('action', sa.String(64), nullable=False),
            sa.Column('resource_type', sa.String(32), nullable=False),
            sa.Column('resource_id', sa.String(128)),
            sa.Column('outcome', sa.String(20), nullable=False),
            sa.Column('details_json', sa.JSON()),
        )
        for field in ('occurred_at', 'actor_user_id', 'action', 'resource_id'):
            op.create_index('ix_web_audit_events_' + field, 'web_audit_events', [field])

    columns = {column['name'] for column in sa.inspect(conn).get_columns('design_jobs')}
    if 'owner_user_id' not in columns:
        op.add_column('design_jobs', sa.Column('owner_user_id', sa.String(64), nullable=True))
    if 'project_id' not in columns:
        op.add_column('design_jobs', sa.Column('project_id', sa.String(64), nullable=True))
    conn.execute(
        sa.text(
            "INSERT INTO web_users (user_id, username, password_hash, role, active, created_at) "
            "SELECT :user_id, :username, :password_hash, :role, :active, :created_at "
            "WHERE NOT EXISTS (SELECT 1 FROM web_users WHERE user_id = :user_id)"
        ),
        {
            'user_id': 'legacy-system',
            'username': 'legacy-system',
            'password_hash': '!login-disabled',
            'role': 'system',
            'active': False,
            'created_at': datetime(1970, 1, 1, tzinfo=timezone.utc),
        },
    )
    conn.execute(
        sa.text(
            "UPDATE design_jobs SET owner_user_id = 'legacy-system' "
            "WHERE owner_user_id IS NULL"
        )
    )
    conn.execute(
        sa.text(
            "UPDATE design_jobs SET project_id = owner_user_id "
            "WHERE project_id IS NULL"
        )
    )
    indexes = {index['name'] for index in sa.inspect(conn).get_indexes('design_jobs')}
    for field in ('owner_user_id', 'project_id'):
        name = 'ix_design_jobs_' + field
        if name not in indexes:
            op.create_index(name, 'design_jobs', [field])


def downgrade():
    raise RuntimeError('Security ownership is durable; restore a pre-upgrade backup to roll back.')
