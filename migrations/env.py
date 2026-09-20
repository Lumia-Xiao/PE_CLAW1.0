import os
from alembic import context
from sqlalchemy import create_engine, pool
from pe_claw_web.jobs.models import Base

config = context.config
url = os.getenv('PE_CLAW_DATABASE_URL', config.get_main_option('sqlalchemy.url'))

def migrate(connection):
    context.configure(connection=connection, target_metadata=Base.metadata, render_as_batch=connection.dialect.name == 'sqlite')
    with context.begin_transaction():
        context.run_migrations()

if config.attributes.get('connection') is not None:
    migrate(config.attributes['connection'])
elif context.is_offline_mode():
    raise RuntimeError('Legacy schema adoption requires an online migration')
else:
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.begin() as connection:
        if connection.dialect.name == 'postgresql':
            connection.exec_driver_sql('SELECT pg_advisory_xact_lock(742951)')
        migrate(connection)
    engine.dispose()
