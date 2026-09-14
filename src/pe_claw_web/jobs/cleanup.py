from __future__ import annotations
import os,shutil
from datetime import datetime,timedelta,timezone
from pathlib import Path
from pe_claw_web.jobs.artifacts import ARTIFACT_ROOT
def cleanup_artifacts(root:Path|None=None,retention_hours:int|None=None,now:datetime|None=None)->int:
 base=root or ARTIFACT_ROOT; cutoff=(now or datetime.now(timezone.utc))-timedelta(hours=retention_hours if retention_hours is not None else int(os.getenv('PE_CLAW_ARTIFACT_RETENTION_HOURS','168'))); n=0
 if not base.exists(): return 0
 for p in base.iterdir():
  if p.is_dir() and datetime.fromtimestamp(p.stat().st_mtime,timezone.utc)<cutoff: shutil.rmtree(p); n+=1
 return n
