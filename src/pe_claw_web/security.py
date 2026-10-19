"""Password and bearer-session primitives with no plaintext credential storage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import base64
import hashlib
import hmac
import os
import re
import secrets


USERNAME_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]{2,63}$")
PASSWORD_ITERATIONS = 600_000


def _encoded_hash(password: str, salt: bytes) -> str:
    result = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PASSWORD_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PASSWORD_ITERATIONS,
        base64.urlsafe_b64encode(salt).decode().rstrip("="),
        base64.urlsafe_b64encode(result).decode().rstrip("="),
    )


DUMMY_PASSWORD_HASH = _encoded_hash("not-a-real-user-password", b"\x00" * 16)


@dataclass(frozen=True)
class Principal:
    user_id: str
    username: str
    role: str
    session_hash: str
    expires_at: datetime

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


def normalize_username(value: str) -> str:
    username = value.strip().lower()
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError("Username must be 3-64 lowercase letters, digits, dot, dash or underscore")
    return username


def validate_password(value: str) -> None:
    if not 12 <= len(value) <= 256:
        raise ValueError("Password must contain 12-256 characters")


def password_hash(password: str) -> str:
    validate_password(password)
    return _encoded_hash(password, os.urandom(16))


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_text, expected_text = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256" or not 1 <= len(password) <= 256:
            return False
        salt = base64.urlsafe_b64decode(salt_text + "=" * (-len(salt_text) % 4))
        expected = base64.urlsafe_b64decode(expected_text + "=" * (-len(expected_text) % 4))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
