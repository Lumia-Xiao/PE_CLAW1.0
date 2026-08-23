"""Offline Step 20 source gate for an explicit MAS checkout.

This module is intentionally separate from the packaged legacy manifest. It
validates a caller-provided MAS checkout and never downloads or mutates source
data. A missing or inconsistent checkout is represented as a blocked audit.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any

from .openmagnetics_source_manifest import is_git_lfs_pointer_file


STEP20_SOURCE_MANIFEST_CONTRACT = "openmagnetics_step20_source_manifest_v1"
STEP20_AUDIT_CONTRACT = "openmagnetics_step20_source_audit_v1"
STEP20_NORMALIZER_VERSION = "openmagnetics-normalized-v2-step20"
STEP20_CACHE_BUILDER_VERSION = "openmagnetics-v2-cache-builder-step20"
TARGET_MAS_COMMIT = "881cceaf1d91ee88c8c5b5b611a0703e6126e825"
TARGET_MATERIAL_COUNT = 647
TARGET_RECORD_COUNTS = {
    "materials": 647,
    "shapes": 890,
    "commercial_cores": 10318,
    "stock_cores": 1573,
    "wires": 4352,
}

# These are the files consumed by the v2 material/component normalizers.
# MAS publishes the complete 647-record material inventory in
# core_materials.ndjson. advanced_core_materials.ndjson is a separate,
# Git-LFS-backed BH-cycle supplement (348 records at the Step 20 pin), not a
# replacement for the complete material inventory.
REQUIRED_SOURCE_FILES: dict[str, tuple[str, ...]] = {
    "materials": ("core_materials.ndjson",),
    "advanced_material_supplement": ("advanced_core_materials.ndjson",),
    "shapes": ("core_shapes.ndjson",),
    "commercial_cores": ("cores.ndjson",),
    "stock_cores": ("cores_stock.ndjson",),
    "wires": ("wires.ndjson",),
    "bobbins": ("bobbins.ndjson",),
    "insulation_materials": ("insulation_materials.ndjson",),
    "wire_materials": ("wire_materials.ndjson",),
}

_LFS_OID_RE = re.compile(r"^oid sha256:([0-9a-f]{64})\r?$", re.MULTILINE)
_LFS_SIZE_RE = re.compile(r"^size ([0-9]+)\r?$", re.MULTILINE)
_FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class Step20SourceIssue:
    code: str
    path: str | None
    message: str

    def to_dict(self) -> dict[str, str | None]:
        return {"code": self.code, "path": self.path, "message": self.message}


@dataclass(frozen=True)
class Step20SourceFile:
    role: str | None
    path: str
    byte_count: int | None
    record_count: int | None
    sha256: str | None
    is_lfs_pointer: bool
    lfs_oid_sha256: str | None
    lfs_expected_byte_count: int | None
    payload_present: bool
    payload_sha256: str | None
    payload_byte_count: int | None
    source_refresh_allowed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "path": self.path,
            "byte_count": self.byte_count,
            "record_count": self.record_count,
            "sha256": self.sha256,
            "git_lfs_status": {
                "is_pointer": self.is_lfs_pointer,
                "oid_sha256": self.lfs_oid_sha256,
                "expected_byte_count": self.lfs_expected_byte_count,
                "engineering_data_available": not self.is_lfs_pointer,
                "pointer_detected": self.is_lfs_pointer,
                "payload_present": self.payload_present,
                "payload_sha256": self.payload_sha256,
                "payload_byte_count": self.payload_byte_count,
                "source_refresh_allowed": self.source_refresh_allowed,
            },
        }


@dataclass(frozen=True)
class Step20SourceAudit:
    status: str
    source_root: str
    expected_mas_commit: str
    observed_mas_commit: str | None
    mkf_commit: str
    pyopenmagnetics_version: str
    files: tuple[Step20SourceFile, ...]
    selected_files: tuple[tuple[str, str], ...]
    record_counts: tuple[tuple[str, int | None], ...]
    issues: tuple[Step20SourceIssue, ...]

    @property
    def ok(self) -> bool:
        return self.status == "ready"

    def to_dict(self) -> dict[str, object]:
        return {
            "contract_version": STEP20_AUDIT_CONTRACT,
            "status": self.status,
            "source_root": self.source_root,
            "expected_mas_commit": self.expected_mas_commit,
            "observed_mas_commit": self.observed_mas_commit,
            "mkf_commit": self.mkf_commit,
            "pyopenmagnetics_version": self.pyopenmagnetics_version,
            "normalizer_version": STEP20_NORMALIZER_VERSION,
            "cache_builder_version": STEP20_CACHE_BUILDER_VERSION,
            "files": [item.to_dict() for item in self.files],
            "selected_files": dict(self.selected_files),
            "record_counts": dict(self.record_counts),
            "issues": [item.to_dict() for item in self.issues],
            "issue_count": len(self.issues),
            "production_loader_changed": False,
            "production_cache_changed": False,
        }


def build_step20_source_manifest(
    source_root: Path,
    *,
    mas_commit: str,
    mkf_commit: str,
    pyopenmagnetics_version: str,
) -> dict[str, object]:
    """Build a deterministic manifest for an explicit source checkout."""

    audit = audit_step20_source(
        source_root,
        mas_commit=mas_commit,
        mkf_commit=mkf_commit,
        pyopenmagnetics_version=pyopenmagnetics_version,
    )
    return {
        "contract_version": STEP20_SOURCE_MANIFEST_CONTRACT,
        "source_kind": "target_mas_881cceaf_647",
        "project": "OpenMagnetics/MAS",
        "commit": mas_commit,
        "observed_commit": audit.observed_mas_commit,
        "mkf_commit": mkf_commit,
        "pyopenmagnetics_version": pyopenmagnetics_version,
        "source_schema_version": "MAS schema at explicitly pinned source revision",
        "normalizer_version": STEP20_NORMALIZER_VERSION,
        "cache_builder_version": STEP20_CACHE_BUILDER_VERSION,
        "source_root_identity": {"mas_commit": audit.observed_mas_commit},
        "selected_files": dict(audit.selected_files),
        "source_files": [item.to_dict() for item in audit.files],
        "record_counts": dict(audit.record_counts),
        "status": audit.status,
        "issues": [item.to_dict() for item in audit.issues],
    }


def audit_step20_source(
    source_root: Path,
    *,
    mas_commit: str,
    mkf_commit: str,
    pyopenmagnetics_version: str,
) -> Step20SourceAudit:
    """Validate source identity, required files, LFS state and record counts."""

    issues: list[Step20SourceIssue] = []
    root = source_root.expanduser().resolve()
    if not _valid_sha(mas_commit):
        issues.append(Step20SourceIssue("mas_commit_invalid", None, "MAS commit must be a full 40-character SHA."))
    if mas_commit != TARGET_MAS_COMMIT:
        issues.append(Step20SourceIssue("mas_commit_not_target", None, "MAS commit does not match the Step 20 target revision."))
    if not _valid_sha(mkf_commit):
        issues.append(Step20SourceIssue("mkf_commit_invalid", None, "MKF commit must be a full 40-character SHA."))
    if not pyopenmagnetics_version.strip():
        issues.append(Step20SourceIssue("pyopenmagnetics_version_missing", None, "PyOpenMagnetics version or source SHA is required."))
    if not root.is_dir():
        issues.append(Step20SourceIssue("source_root_missing", root.as_posix(), "Explicit MAS source checkout does not exist."))
        return _audit("blocked", root, mas_commit, None, mkf_commit, pyopenmagnetics_version, (), (), (), issues)

    observed_commit = _git_head(root)
    if observed_commit is None:
        issues.append(Step20SourceIssue("source_not_git_checkout", root.as_posix(), "Source root is not a readable Git checkout."))
    elif observed_commit != mas_commit:
        issues.append(Step20SourceIssue("mas_commit_mismatch", None, "Checkout HEAD does not match --mas-commit."))

    all_paths = sorted(root.rglob("*.ndjson"), key=lambda path: path.relative_to(root).as_posix())
    files: list[Step20SourceFile] = []
    by_name: dict[str, list[Path]] = {}
    for path in all_paths:
        by_name.setdefault(path.name, []).append(path)
        files.append(_scan_file(root, path, issues))
    selected: dict[str, str] = {}
    counts: dict[str, int | None] = {}
    for role, candidates in REQUIRED_SOURCE_FILES.items():
        matches = [path for name in candidates for path in by_name.get(name, [])]
        if len(matches) != 1:
            code = "source_file_missing" if not matches else "source_file_ambiguous"
            issues.append(Step20SourceIssue(code, role, f"Expected exactly one source file for role {role}; found {len(matches)}."))
            continue
        relative = matches[0].relative_to(root).as_posix()
        selected[role] = relative
        entry = next(item for item in files if item.path == relative)
        counts[role] = entry.record_count
        if entry.is_lfs_pointer:
            issues.append(Step20SourceIssue("source_lfs_pointer", relative, "Git-LFS pointer is not engineering data."))
            if not entry.payload_present:
                issues.append(Step20SourceIssue("source_lfs_payload_missing", relative, "Git-LFS payload is not present in the explicit checkout."))
        expected_count = TARGET_RECORD_COUNTS.get(role)
        if expected_count is not None and entry.record_count != expected_count:
            issues.append(
                Step20SourceIssue(
                    "target_record_count_mismatch",
                    relative,
                    f"Expected {expected_count} records for {role}; observed {entry.record_count}.",
                )
            )
    # The generic required-role gate above validates the BH-cycle supplement
    # independently. It is retained in provenance but not used as the material
    # inventory.
    role_by_path = {relative: role for role, relative in selected.items()}
    files = [replace(item, role=role_by_path.get(item.path)) for item in files]
    material_count = counts.get("materials")
    if material_count != TARGET_MATERIAL_COUNT:
        issues.append(Step20SourceIssue("target_material_count_mismatch", selected.get("materials"), f"Expected {TARGET_MATERIAL_COUNT} materials; observed {material_count}."))
    duplicate_names = sorted(name for name, paths in by_name.items() if len(paths) > 1)
    for name in duplicate_names:
        issues.append(Step20SourceIssue("source_filename_ambiguous", name, "Multiple NDJSON files share the same basename."))
    status = "ready" if not issues else "blocked"
    return _audit(status, root, mas_commit, observed_commit, mkf_commit, pyopenmagnetics_version, files, selected, counts, issues)


def write_step20_source_manifest(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_canonical_json(payload), encoding="ascii", newline="\n")


def write_step20_source_audit(path: Path, audit: Step20SourceAudit) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_canonical_json(audit.to_dict()), encoding="ascii", newline="\n")


def _scan_file(root: Path, path: Path, issues: list[Step20SourceIssue]) -> Step20SourceFile:
    relative = path.relative_to(root).as_posix()
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if is_git_lfs_pointer_file(path):
        text = data.decode("ascii", errors="replace")
        oid = _LFS_OID_RE.search(text)
        size = _LFS_SIZE_RE.search(text)
        oid_value = oid.group(1) if oid else None
        expected_bytes = int(size.group(1)) if size else None
        payload_path = _lfs_object_path(root, oid_value)
        payload_present = bool(payload_path and payload_path.is_file())
        payload_digest = _sha256(payload_path) if payload_present and payload_path is not None else None
        payload_size = payload_path.stat().st_size if payload_present and payload_path is not None else None
        return Step20SourceFile(
            None, relative, len(data), None, digest, True, oid_value, expected_bytes,
            payload_present, payload_digest, payload_size, False,
        )
    count = 0
    line_number = 0
    try:
        for line_number, line in enumerate(data.decode("utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError("record is not an object")
            count += 1
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        issues.append(Step20SourceIssue("ndjson_invalid", relative, f"Invalid NDJSON at line {line_number}: {exc}"))
        count = None
    return Step20SourceFile(None, relative, len(data), count, digest, False, None, None, True, digest, len(data), True)


def _lfs_object_path(root: Path, oid: str | None) -> Path | None:
    """Locate a local LFS object without invoking network or checkout mutation."""

    if not oid or len(oid) != 64:
        return None
    git_path = root / ".git"
    if git_path.is_file():
        text = git_path.read_text(encoding="utf-8", errors="replace").strip()
        if text.startswith("gitdir:"):
            git_path = (root / text.split(":", 1)[1].strip()).resolve()
    candidate = git_path / "lfs" / "objects" / oid[:2] / oid[2:4] / oid
    return candidate


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _audit(status: str, root: Path, mas: str, observed: str | None, mkf: str, py: str, files: tuple[Step20SourceFile, ...] | list[Step20SourceFile], selected: dict[str, str] | tuple[tuple[str, str], ...], counts: dict[str, int | None] | tuple[tuple[str, int | None], ...], issues: list[Step20SourceIssue]) -> Step20SourceAudit:
    return Step20SourceAudit(status, root.as_posix(), mas, observed, mkf, py, tuple(files), tuple(sorted(dict(selected).items())), tuple(sorted(dict(counts).items())), tuple(sorted(issues, key=lambda issue: (issue.code, issue.path or "", issue.message))))


def _git_head(root: Path) -> str | None:
    try:
        result = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=False, capture_output=True, text=True)
    except OSError:
        return None
    value = result.stdout.strip().lower()
    return value if result.returncode == 0 and _valid_sha(value) else None


def _valid_sha(value: str) -> bool:
    return bool(_FULL_SHA_RE.fullmatch(value.lower()))


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":")) + "\n"


__all__ = [
    "REQUIRED_SOURCE_FILES",
    "STEP20_AUDIT_CONTRACT",
    "STEP20_SOURCE_MANIFEST_CONTRACT",
    "TARGET_MAS_COMMIT",
    "TARGET_MATERIAL_COUNT",
    "TARGET_RECORD_COUNTS",
    "Step20SourceAudit",
    "Step20SourceFile",
    "Step20SourceIssue",
    "audit_step20_source",
    "build_step20_source_manifest",
    "write_step20_source_audit",
    "write_step20_source_manifest",
]
