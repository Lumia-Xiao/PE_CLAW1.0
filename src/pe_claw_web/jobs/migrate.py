"""The same Alembic revisions serve local SQLite and deployed PostgreSQL."""
from pathlib import Path
from alembic import command
from alembic.config import Config

def upgrade(engine):
    root = Path(__file__).resolve().parents[3]
    config = Config(str(root / 'alembic.ini'))
    config.set_main_option('script_location', str(root / 'migrations'))
    with engine.connect() as conn:
        if conn.dialect.name == 'sqlite':
            conn.exec_driver_sql('BEGIN IMMEDIATE')
        else:
            conn.begin()
            conn.exec_driver_sql('SELECT pg_advisory_xact_lock(742951)')
        config.attributes['connection'] = conn
        try:
            command.upgrade(config, 'head')
            conn.commit()
        except Exception:
            conn.rollback()
            raise
