"""Run real PostgreSQL acceptance in an owned, loopback-only temporary cluster.

Requires PostgreSQL binaries and the project's web-test dependencies. Does not
install services, change existing databases, or remove retained test evidence.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--postgres-bin', type=Path, required=True)
    parser.add_argument('--redis-server', required=True)
    parser.add_argument('--timeout', type=int, default=900)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    binaries = args.postgres_bin.resolve()
    suffix = '.exe' if os.name == 'nt' else ''
    for name in ('initdb', 'pg_ctl', 'postgres'):
        if not (binaries / (name + suffix)).is_file():
            parser.error(f'Missing PostgreSQL executable: {name}')
    root = project / 'pytest_temp' / ('postgres-deployment-' + uuid.uuid4().hex[:8])
    root.mkdir(parents=True)
    data = root / 'data'
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    password = secrets.token_urlsafe(32)
    pwfile = root / 'init-password.txt'
    pwfile.write_text(password, encoding='utf-8')
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    evidence = {'database': 'postgresql', 'directory': str(root), 'port': port}
    initialized = False
    admin = None

    def run(command, name, *, check=True):
        with (root / name).open('a', encoding='utf-8') as log:
            return subprocess.run(command, cwd=project, stdout=log,
                stderr=subprocess.STDOUT, creationflags=flags, check=check,
                timeout=args.timeout)

    def control(*command):
        return run([str(binaries / ('pg_ctl' + suffix)), '-D', str(data),
            '-w', '-t', '60', *command], 'pg-control.log')

    def start():
        control('-l', str(root / 'postgres.log'), 'start')

    try:
        run([str(binaries / ('initdb' + suffix)), '-D', str(data),
            '-U', 'pe_claw_test', '--auth=scram-sha-256', '--encoding=UTF8',
            '--locale=C', '--pwfile', str(pwfile)], 'initdb.log')
        initialized = True
        pwfile.unlink()
        with (data / 'postgresql.conf').open('a', encoding='utf-8') as config:
            config.write(f"\nlisten_addresses = '127.0.0.1'\nport = {port}\nmax_connections = 40\n")
        start()
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import DBAPIError
        base = f'postgresql+psycopg://pe_claw_test:{password}@127.0.0.1:{port}'
        admin = create_engine(base + '/postgres', isolation_level='AUTOCOMMIT', pool_pre_ping=True)
        with admin.connect() as connection:
            evidence['server_version'] = connection.scalar(text('SELECT version()'))
            connection.execute(text('CREATE DATABASE pe_claw_smoke'))
        env = os.environ.copy()
        env['PE_CLAW_TEST_POSTGRES_URL'] = base + '/postgres'
        with (root / 'pytest.log').open('w', encoding='utf-8') as log:
            subprocess.run([sys.executable, '-m', 'pytest', '-q',
                'tests/test_web_postgres_recovery.py', '--basetemp', str(root / 'pytest'),
                '--junitxml', str(root / 'pytest.xml')], cwd=project, env=env,
                stdout=log, stderr=subprocess.STDOUT, creationflags=flags,
                check=True, timeout=args.timeout)
        evidence['postgres_tests'] = 'passed'
        print('PostgreSQL migration/concurrency/reconnect tests passed; starting real recovery smoke', flush=True)

        def restart_database(engine):
            control('stop', '-m', 'fast')
            started_at = time.monotonic()
            try:
                with engine.connect() as connection:
                    connection.execute(text('SELECT 1'))
            except DBAPIError:
                evidence['database_outage_observed'] = True
                evidence['database_outage_error_seconds'] = round(time.monotonic()-started_at, 2)
                assert evidence['database_outage_error_seconds'] < 20
            else:
                raise AssertionError('Database remained reachable after owned cluster stopped')
            finally:
                start()
            with engine.connect() as connection:
                assert connection.scalar(text('SELECT 1')) == 1
            evidence['existing_pool_reconnected'] = True

        from verify_web_recovery import main as smoke
        evidence['recovery'] = smoke(['--redis-server', args.redis_server,
            '--database-url', base + '/pe_claw_smoke', '--timeout', str(args.timeout)],
            restart_database=restart_database)
        evidence['status'] = 'passed'
    except Exception as exc:
        # Do not serialize SQLAlchemy connection URLs or generated credentials.
        evidence.update(status='failed', error_type=type(exc).__name__)
        raise
    finally:
        if admin is not None:
            admin.dispose()
        if initialized:
            result = run([str(binaries / ('pg_ctl' + suffix)), '-D', str(data),
                '-w', '-t', '60', 'stop', '-m', 'fast'], 'pg-control.log', check=False)
            evidence['cluster_stopped'] = result.returncode == 0
        if pwfile.exists():
            pwfile.unlink()
        (root / 'evidence.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
        print(json.dumps(evidence, indent=2), flush=True)


if __name__ == '__main__':
    main()
