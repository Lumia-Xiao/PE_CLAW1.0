"""Archive round-trip and rejection tests; no electrical pipeline execution."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import zipfile

import pytest

SPEC = importlib.util.spec_from_file_location("evidence_archive", Path(__file__).resolve().parents[1] / "scripts/archive_validation_evidence.py")
archive = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(archive)


def fixture_tree(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=Archive Test", "-c", "user.email=archive@example.invalid",
                    "commit", "--allow-empty", "-qm", "fixture"], check=True)
    (tmp_path / ".tt-first/empty-dir").mkdir(parents=True)
    (tmp_path / ".pytest-tmp-second").mkdir()
    (tmp_path / ".tt-first/结果.json").write_bytes(b'{"status":"failed"}\n')
    (tmp_path / ".pytest-tmp-second/copy.json").write_bytes(b'{"status":"failed"}\n')
    (tmp_path / ".tt-first/empty.bin").write_bytes(b"")
    (tmp_path / ".tt-receipt.xml").write_bytes(b"<testsuite errors='1'/>")
    (tmp_path / "outputs").mkdir()
    (tmp_path / "outputs/user.json").write_bytes(b"untouched")
    return tmp_path


def test_exact_roundtrip_dedup_failure_records_and_protected_output(tmp_path):
    root = fixture_tree(tmp_path)
    destination = root / "archives/run"
    receipt = archive.create(root, destination)
    assert receipt["files"] == 4 and receipt["unique_objects"] == 3
    assert receipt["source_tree_verified"]
    with zipfile.ZipFile(destination / "evidence.zip") as zipped:
        assert len(zipped.namelist()) == 4  # Three unique objects plus manifest.
    assert (root / "outputs/user.json").read_bytes() == b"untouched"
    restored = root / "restored"
    assert archive.restore(destination / "evidence.zip", restored)["files"] == 4
    assert (restored / ".tt-first/结果.json").read_bytes() == b'{"status":"failed"}\n'
    assert (restored / ".tt-receipt.xml").read_bytes() == b"<testsuite errors='1'/>"
    assert (restored / ".tt-first/empty-dir").is_dir()
    assert (restored / ".tt-first/empty.bin").stat().st_size == 0
    assert (restored / ".tt-first/结果.json").stat().st_mtime_ns == (root / ".tt-first/结果.json").stat().st_mtime_ns
    single = root / "single"
    assert archive.restore(destination / "evidence.zip", single, ".tt-receipt.xml")["files"] == 1
    assert not (single / ".tt-first").exists()


def test_changed_source_is_detected_without_removal(tmp_path):
    root = fixture_tree(tmp_path)
    archive.create(root, root / "archives/run")
    (root / ".tt-first/结果.json").write_bytes(b"changed")
    with pytest.raises(ValueError, match="source tree differs"):
        archive.verify(root / "archives/run/evidence.zip", root)
    assert (root / ".tt-first/结果.json").read_bytes() == b"changed"


def test_tracked_evidence_rejected(tmp_path):
    root = fixture_tree(tmp_path)
    subprocess.run(["git", "-C", str(root), "add", "--", ".tt-receipt.xml"], check=True)
    with pytest.raises(ValueError, match="Tracked evidence"):
        archive.create(root, root / "archives/run")
    assert not (root / "archives/run").exists()


@pytest.mark.parametrize("path", ["../outside", "/absolute", "C:/outside", "a/../b", "a\\b"])
def test_unsafe_paths_rejected(path):
    with pytest.raises(ValueError, match="Unsafe archived path"):
        archive.safe_relative(path)


def test_tampered_archive_and_overwrite_are_rejected(tmp_path):
    root = fixture_tree(tmp_path)
    archive.create(root, root / "archives/run")
    original = root / "archives/run/evidence.zip"
    with pytest.raises(ValueError, match="must be new"):
        archive.restore(original, root / "outputs")
    tampered = root / "tampered.zip"
    with zipfile.ZipFile(original) as src, zipfile.ZipFile(tampered, "w") as dst:
        for entry in src.namelist():
            dst.writestr(entry, b"bad bytes" if entry.startswith("objects/") else src.read(entry))
    with pytest.raises(ValueError, match="Archived bytes differ"):
        archive.verify(tampered)
    assert (root / "outputs/user.json").read_bytes() == b"untouched"


def test_manifest_path_traversal_rejected(tmp_path):
    root = fixture_tree(tmp_path)
    archive.create(root, root / "archives/run")
    with zipfile.ZipFile(root / "archives/run/evidence.zip") as zipped:
        manifest = json.loads(zipped.read("manifest.json"))
    manifest["files"][0]["path"] = "../outside"
    with pytest.raises(ValueError, match="Unsafe archived path"):
        archive.validate_manifest(manifest)


def test_inventory_accepts_relocated_long_windows_paths(tmp_path):
    root = tmp_path / "long-archive-staging"
    root.mkdir()
    extended = Path("\\\\?\\" + str(root.resolve())) if os.name == "nt" else root
    nested = extended / ".tt-gui" / ("a" * 90) / ("b" * 90) / ("c" * 90)
    nested.mkdir(parents=True)
    (nested / "receipt.json").write_bytes(b"exact evidence")
    roots, directories, files = archive.source_inventory(root)
    assert roots == [".tt-gui"]
    assert len(files) == 1 and files[0]["bytes"] == len(b"exact evidence")
    assert files[0]["path"].endswith("receipt.json")
