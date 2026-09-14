from datetime import datetime,timedelta,timezone
from pe_claw_web.jobs.cleanup import cleanup_artifacts
def test_cleanup(tmp_path):
 stale=tmp_path/'old'; stale.mkdir(); t=(datetime.now(timezone.utc)-timedelta(hours=10)).timestamp(); import os; os.utime(stale,(t,t)); assert cleanup_artifacts(tmp_path,1)==1
