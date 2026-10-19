"""Create the first Web administrator or a local user without exposing passwords."""

from __future__ import annotations

import argparse
from getpass import getpass
import sys

from pe_claw_web.jobs.store import JobStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument("--role", choices=("user", "admin"), default="user")
    parser.add_argument(
        "--password-stdin",
        action="store_true",
        help="Read one password line from stdin for a protected automation pipe.",
    )
    args = parser.parse_args()
    if args.password_stdin:
        if sys.stdin.isatty():
            raise SystemExit("--password-stdin requires redirected stdin")
        password = sys.stdin.readline().rstrip("\r\n")
    else:
        password = getpass("Password (12-256 characters): ")
        confirmation = getpass("Confirm password: ")
        if password != confirmation:
            raise SystemExit("Passwords do not match")
    repository = JobStore()
    try:
        user = repository.create_user(args.username, password, role=args.role)
        print(f"created user_id={user.user_id} username={user.username} role={user.role}")
    finally:
        repository.engine.dispose()


if __name__ == "__main__":
    main()
