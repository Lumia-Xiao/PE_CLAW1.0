"""Deterministic runtime and comparison primitives for migration replay.

The design calculations remain owned by the topology and pipeline modules. This
module only makes process settings and structured comparison semantics explicit.
"""

from __future__ import annotations

import hashlib
import json
import locale
import os
import platform
import re
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any


RUNTIME_CONTRACT_VERSION = "pe_claw_runtime_reproducibility_v1"
DETERMINISTIC_ENVIRONMENT = {
    "PYTHONHASHSEED": "0",
    "TZ": "UTC",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
    "BLIS_NUM_THREADS": "1",
}
VOLATILE_KEYS = frozenset(
    {
        "generated_at",
        "timestamp",
        "started_at",
        "finished_at",
        "created_at",
        "duration_s",
        "process_duration_s",
        "session_root",
        "output_root",
        "checkpoint_dir",
        "temp_path",
        "temporary_path",
        "artifact_path",
        "report_path",
    }
)
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")
_MISSING = object()


def configure_deterministic_runtime(*, override_environment: bool = True) -> dict[str, str]:
    """Apply the shared process policy and return the values that were applied.

    ``PYTHONHASHSEED`` cannot change hashing in the already running interpreter,
    but setting it here makes child processes reproducible. The other variables
    control numerical library thread pools and are effective for child imports.
    """

    applied: dict[str, str] = {}
    for name, value in DETERMINISTIC_ENVIRONMENT.items():
        if override_environment or name not in os.environ:
            os.environ[name] = value
        applied[name] = os.environ[name]
    try:
        locale.setlocale(locale.LC_ALL, "C")
    except locale.Error:
        pass
    return applied


def canonicalize_for_comparison(value: Any, *, key: str | None = None) -> Any:
    """Return a JSON-safe value with volatile metadata removed recursively."""

    if key is not None and key.casefold() in {item.casefold() for item in VOLATILE_KEYS}:
        return _MISSING
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for item_key, item_value in sorted(value.items(), key=lambda item: str(item[0])):
            canonical_value = canonicalize_for_comparison(item_value, key=str(item_key))
            if canonical_value is not _MISSING:
                result[str(item_key)] = canonical_value
        return result
    if isinstance(value, (list, tuple)):
        return [
            canonical_value
            for item in value
            if (canonical_value := canonicalize_for_comparison(item)) is not _MISSING
        ]
    if isinstance(value, Path):
        return _canonical_path(str(value))
    if isinstance(value, str):
        return _canonical_path(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def stable_json_bytes(value: Any) -> bytes:
    """Encode a comparison payload with stable key ordering and separators."""

    canonical = canonicalize_for_comparison(value)
    return json.dumps(
        canonical,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def stable_json_fingerprint(value: Any) -> str:
    """Return the SHA-256 fingerprint of the canonical comparison payload."""

    return hashlib.sha256(stable_json_bytes(value)).hexdigest()


def environment_snapshot(*, project_root: str | Path | None = None) -> dict[str, Any]:
    """Return an auditable snapshot of the runtime policy and dependency versions."""

    root = Path(project_root).resolve() if project_root is not None else None
    packages: dict[str, str | None] = {}
    for name in ("matplotlib", "numpy", "pandas", "scipy", "pypdf"):
        try:
            packages[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            packages[name] = None
    return {
        "contract_version": RUNTIME_CONTRACT_VERSION,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "project_root": str(root) if root else None,
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "locale": locale.setlocale(locale.LC_ALL, None),
        "preferred_encoding": locale.getpreferredencoding(False),
        "filesystem_encoding": sys.getfilesystemencoding(),
        "timezone": os.environ.get("TZ", ""),
        "deterministic_environment": {name: os.environ.get(name) for name in DETERMINISTIC_ENVIRONMENT},
        "runtime_packages": packages,
    }


def _canonical_path(value: str) -> str:
    if _WINDOWS_ABSOLUTE.match(value) or value.startswith("\\\\"):
        return "<ABSOLUTE_PATH>"
    return value
