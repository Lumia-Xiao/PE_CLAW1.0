"""Expire only terminal database jobs; unknown folders and active work are untouched."""
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID
from sqlalchemy import select, update, exists, delete

from .artifacts import ARTIFACT_ROOT
from .models import JobRow, ActionRow, RequestKeyRow
from .store import store

def cleanup_artifacts(root=None, retention_hours=None, now=None, repository=None):
    base = Path(root or ARTIFACT_ROOT).resolve()
    repo = repository or store
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(hours=retention_hours if retention_hours is not None else int(os.getenv('PE_CLAW_ARTIFACT_RETENTION_HOURS', '168')))
    active_action = exists(select(ActionRow.action_id).where(ActionRow.job_id == JobRow.job_id, ActionRow.status.in_(['queued', 'running'])))
    with repo.Session() as s:
        candidates = list(s.scalars(select(JobRow.job_id).where(JobRow.status.in_(['succeeded', 'failed', 'cancelled', 'expired']), JobRow.finished_at < cutoff, ~active_action)))
    count = 0
    for job_id in candidates:
        try:
            UUID(job_id)
        except ValueError:
            continue
        folder = base / job_id
        if folder.is_symlink() or (hasattr(folder, 'is_junction') and folder.is_junction()) or folder.resolve().parent != base:
            continue
        with repo.Session.begin() as s:
            changed = s.execute(update(JobRow).where(JobRow.job_id == job_id, JobRow.status.in_(['succeeded', 'failed', 'cancelled', 'expired']), JobRow.finished_at < cutoff, ~active_action).values(status='expired', lease_token=None))
            if changed.rowcount != 1:
                continue
            # Keep the row lock until deletion finishes, fencing manual retry.
            if folder.exists():
                shutil.rmtree(folder)
                count += 1
            s.execute(update(JobRow).where(JobRow.job_id == job_id).values(checkpoint_json=None, result_json=None, input_key=None, client_key=None))
            s.execute(delete(RequestKeyRow).where(RequestKeyRow.job_id == job_id))
            s.execute(update(ActionRow).where(ActionRow.job_id == job_id).values(status='expired', result_json=None))
    return count
