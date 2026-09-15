"""Operator recovery loop, independent of Celery so Redis downtime cannot disable it."""
import argparse
import logging
import time
from .store import store

def recover_once():
    import os
    from pe_claw_web.workers.tasks import design_buck_task
    ids = store.recover(int(os.getenv('PE_CLAW_LEASE_SECONDS', '120')))
    for job_id in ids:
        design_buck_task.delay(job_id)
    return len(ids)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['recover', 'cleanup'])
    parser.add_argument('--loop', action='store_true')
    args = parser.parse_args()
    while True:
        try:
            if args.operation == 'recover':
                print(f'Queued for recovery: {recover_once()}', flush=True)
            else:
                from .cleanup import cleanup_artifacts
                print(f'Removed expired job directories: {cleanup_artifacts()}', flush=True)
        except Exception:
            if not args.loop:
                raise
            logging.exception('Maintenance failed; retrying in 30 seconds')
        if not args.loop:
            break
        time.sleep(30)

if __name__ == '__main__':
    main()
