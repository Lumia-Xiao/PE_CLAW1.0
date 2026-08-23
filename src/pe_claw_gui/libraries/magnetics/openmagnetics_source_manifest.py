"""Build and verify immutable provenance for packaged OpenMagnetics data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any


SOURCE_MANIFEST_NAME = "source_manifest.json"
SOURCE_MANIFEST_CONTRACT_VERSION = "openmagnetics_source_manifest_v1"
NORMALIZER_VERSION = "openmagnetics-normalized-v1"

_DATA_DIR = Path(__file__).resolve().parent / "openmagnetics_data"
_LFS_HEADER = b"version https://git-lfs.github.com/spec/v1"
_LFS_OID_RE = re.compile(r"^oid sha256:([0-9a-f]{64})\r?$", re.MULTILINE)
_LFS_SIZE_RE = re.compile(r"^size ([0-9]+)\r?$", re.MULTILINE)

# The legacy files first entered the PE-Claw repository in this immutable
# commit. Their original upstream MAS commit was not stored in the files.
LOCAL_SNAPSHOT_REPOSITORY = "https://github.com/Lumia-Xiao/PE-Claw_2.0.git"
LOCAL_SNAPSHOT_COMMIT = "dda025b8bb8aa17e39cca94e8dc6007656a5cba6"

# This set is pinned at the PyOpenMagnetics 1.6.2 release boundary. The MKF
# commit is the last MKF commit before that release, and the MAS commit is the
# gitlink recorded by that MKF commit.
PINNED_REFERENCE_STACK: dict[str, dict[str, str]] = {
    "pyopenmagnetics": {
        "repository": "https://github.com/OpenMagnetics/PyOpenMagnetics.git",
        "commit": "b960e88109a12c4455bbded5d11bb80c9d8fc114",
        "version": "1.6.2",
        "commit_date_utc": "2026-07-12T16:33:10Z",
    },
    "mkf": {
        "repository": "https://github.com/OpenMagnetics/MKF.git",
        "commit": "8d3bad38297ddca92a2aafe9c88a4fc93ef75d5b",
        "commit_date_utc": "2026-07-08T18:15:46Z",
    },
    "mas": {
        "repository": "https://github.com/OpenMagnetics/MAS.git",
        "commit": "e3ccea8ca9772b11a56d90ef63db35ef872b2684",
        "commit_date_utc": "2026-07-08T18:14:56Z",
    },
}


class OpenMagneticsGitLfsPointerError(RuntimeError):
    """Raised when a Git LFS pointer is requested as engineering data."""


@dataclass(frozen=True)
class SourceManifestIssue:
    """One deterministic source-manifest validation issue."""

    code: str
    path: str | None
    message: str

    def to_dict(self) -> dict[str, str | None]:
        return {"code": self.code, "path": self.path, "message": self.message}


@dataclass(frozen=True)
class SourceFileVerification:
    """Readback status for one manifest source file."""

    path: str
    status: str
    byte_count: int | None
    record_count: int | None
    sha256: str | None
    git_lfs_pointer: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "status": self.status,
            "byte_count": self.byte_count,
            "record_count": self.record_count,
            "sha256": self.sha256,
            "git_lfs_pointer": self.git_lfs_pointer,
        }


@dataclass(frozen=True)
class SourceManifestVerification:
    """Structured result from an offline manifest verification."""

    ok: bool
    manifest_path: Path
    files: tuple[SourceFileVerification, ...]
    issues: tuple[SourceManifestIssue, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "contract_version": "openmagnetics_source_manifest_verification_v1",
            "ok": self.ok,
            "manifest_path": str(self.manifest_path),
            "file_count": len(self.files),
            "issue_count": len(self.issues),
            "files": [item.to_dict() for item in self.files],
            "issues": [item.to_dict() for item in self.issues],
        }


def get_source_manifest_path(data_dir: Path | None = None) -> Path:
    """Return the source manifest location for a packaged data directory."""

    return (data_dir or _DATA_DIR) / SOURCE_MANIFEST_NAME


def is_git_lfs_pointer_file(path: Path) -> bool:
    """Return True when *path* is a Git LFS pointer, not its payload."""

    try:
        with path.open("rb") as stream:
            return stream.read(len(_LFS_HEADER)) == _LFS_HEADER
    except OSError:
        return False


def build_source_manifest(
    data_dir: Path | None = None,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic manifest payload from local NDJSON files."""

    resolved = (data_dir or _DATA_DIR).resolve()
    source_files = [_source_file_entry(path) for path in sorted(resolved.glob("*.ndjson"))]
    pointer_files = [
        str(item["path"])
        for item in source_files
        if bool(item["git_lfs_status"]["is_pointer"])
    ]
    timestamp = generated_at or datetime.now(timezone.utc).isoformat()
    return {
        "contract_version": SOURCE_MANIFEST_CONTRACT_VERSION,
        "generated_at": timestamp,
        "source_repository": LOCAL_SNAPSHOT_REPOSITORY,
        "source_commit": LOCAL_SNAPSHOT_COMMIT,
        "source_snapshot_status": "legacy_snapshot_pinned_by_local_commit_and_file_hashes",
        "upstream_repository": "https://github.com/OpenMagnetics/MAS.git",
        "upstream_source_commit": None,
        "upstream_provenance_status": "not_recorded_in_legacy_snapshot",
        "schema_repository": "https://github.com/OpenMagnetics/MAS.git",
        "schema_commit": PINNED_REFERENCE_STACK["mas"]["commit"],
        "schema_version": "MAS schema at pinned reference commit",
        "schema_binding_status": "reference_stack_only_not_proven_for_legacy_snapshot",
        "normalizer_version": NORMALIZER_VERSION,
        "reference_stack": {
            "compatibility_basis": (
                "PyOpenMagnetics 1.6.2 release boundary; MKF tip immediately "
                "preceding the release; MAS gitlink recorded by that MKF commit"
            ),
            **{name: dict(details) for name, details in PINNED_REFERENCE_STACK.items()},
        },
        "git_lfs_status": {
            "status": "contains_unresolved_pointer" if pointer_files else "all_payloads_present",
            "pointer_file_count": len(pointer_files),
            "pointer_files": pointer_files,
        },
        "source_files": source_files,
    }


def write_source_manifest(
    data_dir: Path | None = None,
    *,
    generated_at: str | None = None,
    output_path: Path | None = None,
) -> Path:
    """Write a newly built source manifest and return its path."""

    target = output_path or get_source_manifest_path(data_dir)
    payload = build_source_manifest(data_dir, generated_at=generated_at)
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def verify_source_manifest(
    data_dir: Path | None = None,
    *,
    manifest_path: Path | None = None,
) -> SourceManifestVerification:
    """Verify manifest structure, file hashes, counts, and LFS state offline."""

    resolved = (data_dir or _DATA_DIR).resolve()
    target = manifest_path or get_source_manifest_path(resolved)
    issues: list[SourceManifestIssue] = []
    files: list[SourceFileVerification] = []
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError:
        issues.append(_issue("manifest_missing", None, f"Source manifest is missing: {target}"))
        return SourceManifestVerification(False, target, (), tuple(issues))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(_issue("manifest_invalid", None, f"Source manifest is unreadable: {exc}"))
        return SourceManifestVerification(False, target, (), tuple(issues))

    _validate_manifest_header(payload, issues)
    entries = payload.get("source_files")
    if not isinstance(entries, list):
        issues.append(_issue("source_files_invalid", None, "source_files must be a list."))
        entries = []

    manifest_names: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            issues.append(_issue("source_file_entry_invalid", None, "Each source_files entry must be an object."))
            continue
        name = entry.get("path")
        if not isinstance(name, str) or not name or Path(name).name != name:
            issues.append(_issue("source_file_path_invalid", str(name), "Source paths must be direct file names."))
            continue
        if name in manifest_names:
            issues.append(_issue("source_file_duplicate", name, "Source file appears more than once."))
            continue
        manifest_names.add(name)
        verification = _verify_source_file(resolved, name, entry, issues)
        files.append(verification)

    actual_names = {path.name for path in resolved.glob("*.ndjson")}
    for name in sorted(actual_names - manifest_names):
        issues.append(_issue("source_file_unlisted", name, "Packaged NDJSON is not listed in the manifest."))
    for name in sorted(manifest_names - actual_names):
        issues.append(_issue("source_file_missing", name, "Manifest source file is missing."))

    _validate_lfs_summary(payload, files, issues)
    return SourceManifestVerification(not issues, target, tuple(files), tuple(issues))


def _source_file_entry(path: Path) -> dict[str, Any]:
    byte_count = path.stat().st_size
    sha256 = _sha256(path)
    pointer = _read_lfs_pointer(path)
    if pointer is not None:
        return {
            "path": path.name,
            "sha256": sha256,
            "byte_count": byte_count,
            "record_count": None,
            "git_lfs_status": {
                "is_pointer": True,
                "oid_sha256": pointer[0],
                "expected_byte_count": pointer[1],
                "engineering_data_available": False,
            },
        }
    return {
        "path": path.name,
        "sha256": sha256,
        "byte_count": byte_count,
        "record_count": _count_ndjson_records(path),
        "git_lfs_status": {
            "is_pointer": False,
            "oid_sha256": None,
            "expected_byte_count": None,
            "engineering_data_available": True,
        },
    }


def _verify_source_file(
    data_dir: Path,
    name: str,
    entry: dict[str, Any],
    issues: list[SourceManifestIssue],
) -> SourceFileVerification:
    path = data_dir / name
    if not path.is_file():
        return SourceFileVerification(name, "missing", None, None, None, False)

    byte_count = path.stat().st_size
    sha256 = _sha256(path)
    pointer = _read_lfs_pointer(path)
    record_count = None if pointer is not None else _count_ndjson_records(path)
    if entry.get("byte_count") != byte_count:
        issues.append(_issue("byte_count_mismatch", name, "Source byte count does not match the manifest."))
    if str(entry.get("sha256") or "").lower() != sha256:
        issues.append(_issue("sha256_mismatch", name, "Source SHA-256 does not match the manifest."))
    if entry.get("record_count") != record_count:
        issues.append(_issue("record_count_mismatch", name, "Source record count does not match the manifest."))

    lfs_status = entry.get("git_lfs_status")
    if not isinstance(lfs_status, dict):
        issues.append(_issue("git_lfs_status_invalid", name, "git_lfs_status must be an object."))
        lfs_status = {}
    manifest_pointer = lfs_status.get("is_pointer") is True
    actual_pointer = pointer is not None
    if manifest_pointer != actual_pointer:
        issues.append(_issue("git_lfs_state_mismatch", name, "Git LFS pointer state does not match the manifest."))
    if actual_pointer and pointer is not None:
        if lfs_status.get("oid_sha256") != pointer[0]:
            issues.append(_issue("git_lfs_oid_mismatch", name, "Git LFS object ID does not match the manifest."))
        if lfs_status.get("expected_byte_count") != pointer[1]:
            issues.append(_issue("git_lfs_size_mismatch", name, "Git LFS payload size does not match the manifest."))
        if lfs_status.get("engineering_data_available") is not False:
            issues.append(_issue("git_lfs_availability_invalid", name, "An LFS pointer cannot be marked as engineering data."))

    status = "git_lfs_pointer" if actual_pointer else "verified"
    return SourceFileVerification(name, status, byte_count, record_count, sha256, actual_pointer)


def _validate_manifest_header(payload: Any, issues: list[SourceManifestIssue]) -> None:
    if not isinstance(payload, dict):
        issues.append(_issue("manifest_root_invalid", None, "Manifest root must be an object."))
        return
    required = (
        "contract_version",
        "generated_at",
        "source_repository",
        "source_commit",
        "schema_commit",
        "schema_version",
        "git_lfs_status",
        "normalizer_version",
        "reference_stack",
        "source_files",
    )
    for field in required:
        if field not in payload:
            issues.append(_issue("manifest_field_missing", None, f"Required field is missing: {field}"))
    if payload.get("contract_version") != SOURCE_MANIFEST_CONTRACT_VERSION:
        issues.append(_issue("contract_version_invalid", None, "Unsupported source manifest contract version."))
    if payload.get("source_repository") != LOCAL_SNAPSHOT_REPOSITORY:
        issues.append(_issue("source_repository_invalid", None, "Legacy snapshot repository is not the pinned PE-Claw repository."))
    if payload.get("source_commit") != LOCAL_SNAPSHOT_COMMIT:
        issues.append(_issue("source_commit_invalid", None, "Legacy snapshot source commit is not the pinned PE-Claw import commit."))
    if payload.get("schema_commit") != PINNED_REFERENCE_STACK["mas"]["commit"]:
        issues.append(_issue("schema_commit_invalid", None, "Schema commit is not the pinned reference MAS commit."))
    if payload.get("normalizer_version") != NORMALIZER_VERSION:
        issues.append(_issue("normalizer_version_invalid", None, "Normalizer version is not the pinned v1 baseline."))
    reference = payload.get("reference_stack")
    if not isinstance(reference, dict):
        issues.append(_issue("reference_stack_invalid", None, "reference_stack must be an object."))
    else:
        for name, expected in PINNED_REFERENCE_STACK.items():
            actual = reference.get(name)
            if not isinstance(actual, dict) or actual.get("commit") != expected["commit"]:
                issues.append(_issue("reference_stack_commit_invalid", name, f"Pinned {name} commit is missing or changed."))


def _validate_lfs_summary(
    payload: Any,
    files: list[SourceFileVerification],
    issues: list[SourceManifestIssue],
) -> None:
    if not isinstance(payload, dict):
        return
    summary = payload.get("git_lfs_status")
    if not isinstance(summary, dict):
        issues.append(_issue("git_lfs_summary_invalid", None, "git_lfs_status must be an object."))
        return
    actual = sorted(item.path for item in files if item.git_lfs_pointer)
    if summary.get("pointer_file_count") != len(actual):
        issues.append(_issue("git_lfs_pointer_count_mismatch", None, "LFS pointer count does not match source files."))
    if sorted(summary.get("pointer_files") or []) != actual:
        issues.append(_issue("git_lfs_pointer_list_mismatch", None, "LFS pointer file list does not match source files."))


def _read_lfs_pointer(path: Path) -> tuple[str, int] | None:
    if not is_git_lfs_pointer_file(path):
        return None
    text = path.read_text(encoding="ascii")
    oid_match = _LFS_OID_RE.search(text)
    size_match = _LFS_SIZE_RE.search(text)
    if oid_match is None or size_match is None:
        return None
    return oid_match.group(1), int(size_match.group(1))


def _count_ndjson_records(path: Path) -> int:
    with path.open("r", encoding="utf-8") as stream:
        return sum(1 for line in stream if line.strip())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _issue(code: str, path: str | None, message: str) -> SourceManifestIssue:
    return SourceManifestIssue(code=code, path=path, message=message)
