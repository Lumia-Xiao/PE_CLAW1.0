"""Build and exercise an isolated Compose stack; retain volumes and test evidence.

Requires a running Linux Docker engine. No production project, database, Redis,
or frontend port is used. A missing engine is recorded as blocked, never passed.
"""
import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
import uuid

from verify_web_recovery import hardware_signature


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compose-executable', help='Optional standalone Docker Compose binary')
    parser.add_argument('--timeout', type=int, default=1200)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    name = 'pe-claw-f5-' + uuid.uuid4().hex[:8]
    root = project / 'pytest_temp' / name
    root.mkdir(parents=True)
    compose = [args.compose_executable] if args.compose_executable else ['docker', 'compose']
    command = compose + ['--project-name', name, '-f', str(project / 'docker-compose.web.yml')]
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    env = os.environ.copy()
    env.update(PE_CLAW_POSTGRES_PASSWORD=secrets.token_urlsafe(32), PE_CLAW_WEB_PORT=str(port))
    # Test-only faster recovery; production defaults remain unchanged.
    override = root / 'override.json'
    override.write_text(json.dumps({'services': {service: {'environment': {
        'PE_CLAW_LEASE_SECONDS': '30', 'PE_CLAW_HEARTBEAT_SECONDS': '2'}}
        for service in ('api', 'worker', 'recovery')}}), encoding='utf-8')
    command += ['-f', str(override)]
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    evidence = {'project': name, 'directory': str(root), 'frontend_port': port,
        'status': 'blocked', 'container_acceptance': False}
    launched = False
    http = None

    def run(*parts, check=True):
        result = subprocess.run(command + list(parts), cwd=project, env=env,
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            creationflags=flags, timeout=args.timeout)
        with (root / 'compose.log').open('a', encoding='utf-8') as log:
            # Do not log command text: exec snippets can include internal data.
            log.write((result.stdout + result.stderr).replace(env['PE_CLAW_POSTGRES_PASSWORD'], '[redacted]'))
        if check and result.returncode:
            raise RuntimeError(f'Compose {parts[0]} failed; see compose.log')
        return result

    def wait_until(check, timeout=None):
        deadline = time.monotonic() + (timeout or args.timeout)
        while time.monotonic() < deadline:
            value = check()
            if value:
                return value
            time.sleep(1)
        raise TimeoutError('Compose acceptance timed out')

    def state(job_id):
        code = "from pe_claw_web.jobs.store import store\nimport json\n" + inspect.getsource(hardware_signature)
        code += f"\npair=store.get({job_id!r})\ncp=store.get_checkpoint({job_id!r})\n"
        code += "print(json.dumps({'state':pair[0].model_dump(mode='json'),'checkpoint_sha256':cp['sha256'] if cp else None,'completed_stage':cp['completed_stage'] if cp else None,'hardware':hardware_signature(cp) if cp else None}))"
        return json.loads(run('exec', '-T', 'api', 'python', '-c', code).stdout)

    def assert_downloads(job_id):
        response = http.get(f'/api/v1/design-jobs/{job_id}/result')
        response.raise_for_status()
        result = response.json()
        manifest = http.get(f'/api/v1/design-jobs/{job_id}/artifacts')
        manifest.raise_for_status()
        assert manifest.json() == result['artifacts']
        assert result['artifacts']
        for artifact in result['artifacts']:
            download = http.get(artifact['download_url'])
            download.raise_for_status()
            assert hashlib.sha256(download.content).hexdigest() == artifact['sha256']
        assert result['summary']['waveform']['samples']['time_s']
        assert result['summary']['efficiency_sweep']['points']
        return result

    try:
        version = run('version', check=False)
        evidence['compose_version'] = version.stdout.strip()
        run('config', '--quiet')
        evidence['compose_config'] = 'passed'
        engine = run('ps', '--format', 'json', check=False)
        if engine.returncode:
            evidence['reason'] = 'Docker engine unavailable; see compose.log'
            return 2
        evidence['status'] = 'failed'
        launched = True
        run('up', '--build', '-d')
        import httpx
        http = httpx.Client(base_url=f'http://127.0.0.1:{port}', timeout=60)

        def healthy():
            try:
                return http.get('/api/v1/health').status_code == 200
            except httpx.HTTPError:
                return False
        wait_until(healthy)
        page = http.get('/')
        assert page.status_code == 200 and '<div id="root">' in page.text
        evidence['frontend_and_proxy'] = True
        payload = {'execution_profile': 'complete', 'request': dict(vin_min=36,
            vin_max=60, vout=12, pout=120, fs_khz=100, ripple_current_ratio=.3,
            ripple_voltage_ratio_percent=1)}
        response = http.post('/api/v1/design-jobs', json=payload)
        assert response.status_code == 202, response.text
        job_id = response.json()['job_id']
        evidence['job_id'] = job_id
        assert http.post('/api/v1/design-jobs', json=payload).json()['job_id'] == job_id

        def saved():
            current = state(job_id)
            if current['state']['status'] in ('failed', 'succeeded'):
                raise AssertionError('Job terminated before interruption at capacitor checkpoint')
            return current if current['completed_stage'] == 'capacitor' else None
        checkpoint = wait_until(saved)
        run('kill', '-s', 'SIGKILL', 'worker')
        run('stop', 'postgres', 'redis')
        run('start', 'postgres', 'redis')
        wait_until(lambda: run('exec', '-T', 'postgres', 'pg_isready', '-U', 'pe_claw',
            '-d', 'pe_claw', check=False).returncode == 0, timeout=90)
        assert state(job_id)['checkpoint_sha256'] == checkpoint['checkpoint_sha256']
        run('start', 'worker')

        def finished():
            response = http.get(f'/api/v1/design-jobs/{job_id}')
            response.raise_for_status()
            current = response.json()
            if current['status'] == 'failed':
                raise AssertionError(f"Design failed at {current['stage']}")
            return current if current['status'] == 'succeeded' else None
        result_state = wait_until(finished)
        assert result_state['attempt'] == 2
        assert state(job_id)['hardware'] == checkpoint['hardware']
        result = assert_downloads(job_id)
        run('exec', '-T', 'api', 'python', '-c',
            f'from pe_claw_web.workers.tasks import design_buck_task; design_buck_task.delay({job_id!r})')
        time.sleep(3)
        assert state(job_id)['state']['attempt'] == 2
        # Stop and start the same owned stack; database and artifacts must survive.
        run('stop')
        run('up', '-d')
        wait_until(healthy)
        assert assert_downloads(job_id)['artifacts'] == result['artifacts']
        evidence.update(status='passed', container_acceptance=True, attempts=2,
            hardware_preserved=True, postgres_redis_worker_restart=True,
            independent_recovery=True, stack_restart_persistence=True,
            artifacts=len(result['artifacts']))
        return 0
    except FileNotFoundError:
        evidence['reason'] = 'Docker/Compose executable unavailable'
        return 2
    except Exception as exc:
        evidence.update(status='failed', error_type=type(exc).__name__)
        raise
    finally:
        if http is not None:
            http.close()
        if launched:
            try:
                run('logs', '--no-color', check=False)
            finally:
                # Keep named volumes for diagnosis. Never run down --volumes.
                evidence['containers_stopped'] = run('down', check=False).returncode == 0
        (root / 'evidence.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
        print(json.dumps(evidence, indent=2), flush=True)


if __name__ == '__main__':
    sys.exit(main())
