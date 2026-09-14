from pe_claw_web.jobs.store import Base
from alembic import context
from sqlalchemy import engine_from_config,pool
config=context.config
def run():
 c=engine_from_config(config.get_section(config.config_ini_section),prefix='sqlalchemy.',poolclass=pool.NullPool)
 with c.connect() as conn: context.configure(connection=conn,target_metadata=Base.metadata); context.run_migrations()
run()
