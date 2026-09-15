"""Isolated real Redis/Celery recovery smoke; never stops user services.

python scripts/verify_web_recovery.py --redis-server <path> [--database-url <dedicated-empty-postgres-url>]
Artifacts/logs/evidence are retained under pytest_temp/recovery-smoke-<uuid>.
"""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import uuid

def hardware_signature(checkpoint):
    from pe_claw_web.jobs.checkpoints import decode, encode, checksum
    report=decode(checkpoint['report'])
    capacitors={}
    if report.capacitor:
        for side in ('input_selection','output_selection'):
            selection=getattr(report.capacitor,side)
            chosen=selection.recommended if selection else None
            if chosen:
                capacitors[side]=(encode(chosen.candidate),chosen.parallel_count,chosen.series_count)
    return checksum({'candidate':encode(report.candidate), 'devices':report.device.selected_devices if report.device else {}, 'capacitors':capacitors})

def wait_until(check, timeout=60):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        value=check()
        if value:
            return value
        time.sleep(.5)
    raise TimeoutError('Recovery smoke timed out')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--redis-server', required=True)
    parser.add_argument('--database-url', help='Dedicated disposable database; never a production URL')
    parser.add_argument('--timeout', type=int, default=900)
    args=parser.parse_args()
    project=Path(__file__).resolve().parents[1]
    root=project/'pytest_temp'/('recovery-smoke-'+uuid.uuid4().hex[:8])
    root.mkdir(parents=True)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); api_port=sock.getsockname()[1]
    os.environ.update(PE_CLAW_DATABASE_URL=args.database_url or 'sqlite:///'+str(root/'jobs.db'),
        PE_CLAW_ARTIFACT_ROOT=str(root/'artifacts'), PE_CLAW_REDIS_URL=f'redis://127.0.0.1:{port}/0',
        PE_CLAW_LEASE_SECONDS='6', PE_CLAW_HEARTBEAT_SECONDS='1')
    import redis
    import httpx
    from sqlalchemy import select, func
    from pe_claw_web.jobs.store import store, JobRow
    from pe_claw_web.jobs.migrate import upgrade
    from pe_claw_web.workers.tasks import design_buck_task
    from pe_claw_web.schemas import BuckDesignRequest, DesignJobCreate
    upgrade(store.engine)
    with store.Session() as session:
        if session.scalar(select(func.count()).select_from(JobRow)):
            raise RuntimeError('Smoke database must be empty')
    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    handles=[]
    children=[]
    def start(command, logfile):
        stream=(root/logfile).open('w'); handles.append(stream)
        proc=subprocess.Popen(command,cwd=project,env=os.environ.copy(),stdout=stream,stderr=subprocess.STDOUT,creationflags=flags)
        children.append(proc)
        return proc
    def redis_start(logfile):
        return start([args.redis_server,'--port',str(port),'--bind','127.0.0.1','--dir',str(root),'--appendonly','yes'],logfile)
    client=redis.Redis(host='127.0.0.1',port=port,socket_connect_timeout=1,socket_timeout=1)
    def ping():
        try: return client.ping()
        except redis.RedisError: return False
    def worker(logfile):
        return start([sys.executable,'-m','celery','-A','pe_claw_web.workers.celery_app:celery_app','worker','--pool=solo','--loglevel=info'],logfile)
    evidence={'directory': str(root), 'database': 'postgresql' if args.database_url else 'sqlite'}
    try:
        broker=redis_start('redis-first.log'); wait_until(ping)
        api=start([sys.executable,'-m','uvicorn','pe_claw_web.api.main:app','--host','127.0.0.1','--port',str(api_port)],'api.log')
        http=httpx.Client(base_url=f'http://127.0.0.1:{api_port}',timeout=30)
        def healthy():
            try: return http.get('/api/v1/health').status_code==200
            except httpx.HTTPError: return False
        wait_until(healthy)
        first=worker('worker-first.log')
        payload=DesignJobCreate(request=BuckDesignRequest(vin_min=36,vin_max=60,vout=12,pout=120,fs_khz=100,ripple_current_ratio=.3,ripple_voltage_ratio_percent=1))
        response=http.post('/api/v1/design-jobs',json=payload.model_dump(mode='json'))
        assert response.status_code==202, response.text
        item=store.get(response.json()['job_id'])[0]; evidence['job_id']=item.job_id
        assert http.post('/api/v1/design-jobs',json=payload.model_dump(mode='json')).json()['job_id']==item.job_id
        def saved():
            state=store.get(item.job_id)[0]
            if state.status=='failed': raise RuntimeError(state.error.message)
            cp=store.get_checkpoint(item.job_id)
            return cp if cp and cp['completed_stage']=='capacitor' else None
        cp=wait_until(saved,args.timeout)
        first.kill(); first.wait(timeout=10)
        evidence['interrupted_after']=cp['completed_stage']
        evidence['checkpoint_sha256']=cp['sha256']
        evidence['selected_hardware_sha256']=hardware_signature(cp)
        broker.terminate(); broker.wait(timeout=10)
        # The durable DB survives the broker restart; only the owned subprocess is stopped.
        assert store.get_checkpoint(item.job_id)['sha256']==cp['sha256']
        time.sleep(7)
        broker=redis_start('redis-restarted.log'); wait_until(ping)
        queued=store.recover(6)
        assert item.job_id in queued
        second=worker('worker-restarted.log')
        design_buck_task.delay(item.job_id)
        def finished():
            state=store.get(item.job_id)[0]
            if state.status=='failed': raise RuntimeError(state.error.message)
            return state if state.status=='succeeded' else None
        state=wait_until(finished,args.timeout)
        result=store.get(item.job_id)[2]
        from pe_claw_web.jobs.artifacts import ARTIFACT_ROOT, resolve_artifact
        for entry in result['artifacts']:
            resolve_artifact(ARTIFACT_ROOT,item.job_id,entry['id'],result['artifacts'])
            import hashlib
            download=http.get(entry['download_url'])
            assert download.status_code==200
            assert hashlib.sha256(download.content).hexdigest()==entry['sha256']
        assert http.get(f'/api/v1/design-jobs/{item.job_id}/result').json()['summary']==result['summary']
        assert hardware_signature(store.get_checkpoint(item.job_id))==evidence['selected_hardware_sha256']
        assert result['summary']['waveform']['samples']['time_s']
        assert result['summary']['efficiency_sweep']['points']
        assert state.attempt==2
        # A late duplicate delivery cannot start a third run.
        design_buck_task.delay(item.job_id)
        time.sleep(2)
        assert store.get(item.job_id)[0].attempt==2
        evidence.update(status='passed',attempts=state.attempt,artifacts=len(result['artifacts']),stages=state.stages,actual_http=True,hardware_preserved=True)
        http.close()
    except Exception as exc:
        evidence.update(status='failed',error=type(exc).__name__+': '+str(exc))
        raise
    finally:
        for proc in children:
            if proc.poll() is None:
                proc.terminate()
                try: proc.wait(timeout=10)
                except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=10)
        for stream in handles: stream.close()
        (root/'evidence.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
        print(json.dumps(evidence,indent=2),flush=True)

if __name__=='__main__': main()
