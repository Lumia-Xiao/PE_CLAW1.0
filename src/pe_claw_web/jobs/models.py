from datetime import datetime
from sqlalchemy import JSON, DateTime, String, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase): pass
class RequestKeyRow(Base):
    __tablename__ = 'design_request_keys'
    client_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    input_key: Mapped[str] = mapped_column(String(64), nullable=False)

class JobRow(Base):
    __tablename__='design_jobs'
    __table_args__ = (Index('uq_design_jobs_input_key', 'input_key', unique=True), Index('uq_design_jobs_client_key', 'client_key', unique=True))
    input_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    client_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    attempt: Mapped[int] = mapped_column(default=0, server_default='0')
    lease_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    checkpoint_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    stages_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    job_id: Mapped[str]=mapped_column(String(64),primary_key=True); topology: Mapped[str]=mapped_column(String(128)); request_json: Mapped[dict]=mapped_column(JSON); execution_json: Mapped[dict|None]=mapped_column(JSON,nullable=True); status: Mapped[str]=mapped_column(String(20)); progress: Mapped[int]=mapped_column(); stage: Mapped[str|None]=mapped_column(String(64),nullable=True); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True)); started_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); finished_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); error_json: Mapped[dict|None]=mapped_column(JSON,nullable=True); result_json: Mapped[dict|None]=mapped_column(JSON,nullable=True)
class ActionRow(Base):
    __tablename__='design_actions'
    action_id: Mapped[str]=mapped_column(String(64),primary_key=True); job_id: Mapped[str]=mapped_column(String(64),index=True); action: Mapped[str]=mapped_column(String(32)); idempotency_key: Mapped[str]=mapped_column(String(128),index=True); request_json: Mapped[dict]=mapped_column(JSON); status: Mapped[str]=mapped_column(String(20)); progress: Mapped[int]=mapped_column(); stage: Mapped[str|None]=mapped_column(String(64),nullable=True); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True)); started_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); finished_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); error_json: Mapped[dict|None]=mapped_column(JSON,nullable=True); result_json: Mapped[dict|None]=mapped_column(JSON,nullable=True)
