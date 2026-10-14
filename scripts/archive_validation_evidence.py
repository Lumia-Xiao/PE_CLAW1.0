"""Archive root-local validation evidence by content; never remove source files."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import zipfile

CONTRACT = "pe_claw_validation_archive_v1"
BLOCK = 4 * 1024 * 1024


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(BLOCK), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def safe_relative(value):
    p = PurePosixPath(value)
    if (not value or p.is_absolute() or ".." in p.parts or "\\" in value
            or ":" in value or p.as_posix() != value):
        raise ValueError(f"Unsafe archived path: {value}")
    return p


def selected_name(name):
    return name.startswith((".tt", ".pytest-"))


def source_inventory(root):
    root = Path(root).resolve()
    # Relocation adds path segments to historical Windows GUI artifacts.
    # Extended paths keep inspection independent of the legacy 260-char limit.
    if os.name == "nt" and not str(root).startswith("\\\\?\\"):
        root = Path("\\\\?\\" + str(root))
    targets = sorted((p for p in root.iterdir() if selected_name(p.name)), key=lambda p: p.name)
    files, directories = [], []
    for target in targets:
        pending = [target]
        while pending:
            path = pending.pop()
            if path.is_symlink() or path.is_junction():
                raise ValueError(f"Link requires a separate archive policy: {path}")
            rel = path.relative_to(root).as_posix()
            if path.is_dir():
                directories.append(rel)
                pending.extend(sorted(path.iterdir(), reverse=True))
            elif path.is_file():
                before = path.stat()
                sha = digest(path)
                after = path.stat()
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    raise ValueError(f"Source changed while hashing: {path}")
                files.append(dict(path=rel, bytes=before.st_size, sha256=sha,
                    mtime_ns=before.st_mtime_ns, mode=stat.S_IMODE(before.st_mode)))
            else:
                raise ValueError(f"Unsupported evidence entry: {path}")
    return [p.name for p in targets], sorted(directories), sorted(files, key=lambda r: r["path"])


def validate_manifest(manifest):
    if manifest.get("contract") != CONTRACT:
        raise ValueError("Unknown archive contract")
    paths = set()
    for name in manifest["original_roots"]:
        if len(safe_relative(name).parts) != 1 or not selected_name(name):
            raise ValueError("Archive root is outside local validation evidence")
    roots = set(manifest["original_roots"])
    for record in manifest["files"]:
        rel = safe_relative(record["path"])
        if rel.parts[0] not in roots or record["path"] in paths:
            raise ValueError("Duplicate or out-of-scope archived file")
        paths.add(record["path"])
        sha = record["sha256"]
        if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha) or record["bytes"] < 0:
            raise ValueError("Invalid archived content identity")
    for directory in manifest["directories"]:
        if safe_relative(directory).parts[0] not in roots or directory in paths:
            raise ValueError("Conflicting archived directory")


def verify(archive, source_root=None):
    archive = Path(archive)
    with zipfile.ZipFile(archive) as zipped:
        names = zipped.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP entries")
        manifest = json.loads(zipped.read("manifest.json"))
        validate_manifest(manifest)
        objects = {}
        for record in manifest["files"]:
            previous = objects.setdefault(record["sha256"], record["bytes"])
            if previous != record["bytes"]:
                raise ValueError("Inconsistent object size")
        if set(names) != {"manifest.json", *("objects/" + sha for sha in objects)}:
            raise ValueError("Missing or unexpected archive entries")
        for sha, size in sorted(objects.items()):
            h, count = hashlib.sha256(), 0
            with zipped.open("objects/" + sha) as stream:
                for block in iter(lambda: stream.read(BLOCK), b""):
                    h.update(block)
                    count += len(block)
            if h.hexdigest() != sha or count != size:
                raise ValueError(f"Archived bytes differ: {sha}")
    if source_root is not None:
        roots, directories, files = source_inventory(source_root)
        if (roots, directories, files) != (manifest["original_roots"], manifest["directories"], manifest["files"]):
            raise ValueError("Current source tree differs from archive manifest")
    return dict(status="verified", original_roots=len(manifest["original_roots"]),
        files=len(manifest["files"]), unique_objects=len(objects),
        source_bytes=sum(r["bytes"] for r in manifest["files"]),
        unique_content_bytes=sum(objects.values()), archive_bytes=archive.stat().st_size,
        archive_sha256=digest(archive), source_tree_verified=source_root is not None)


def create(root, destination):
    root, destination = Path(root).resolve(), Path(destination).resolve()
    if not destination.is_relative_to(root) or selected_name(destination.relative_to(root).parts[0]):
        raise ValueError("Archive destination must be inside a separate workspace directory")
    if destination.exists():
        raise ValueError("Archive destination must be new")
    roots, directories, files = source_inventory(root)
    if not files:
        raise ValueError("No validation evidence files found")
    tracked = set(subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")) - {""}
    if any(r["path"] in tracked for r in files):
        raise ValueError("Tracked evidence cannot be moved by this tool")
    manifest = dict(contract=CONTRACT, source_root=str(root),
        source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip(),
        original_roots=roots, directories=directories, files=files)
    validate_manifest(manifest)
    destination.mkdir(parents=True)
    write_json(destination / "manifest.json", manifest)
    archive = destination / "evidence.zip"
    seen, processed = set(), 0
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as zipped:
        zipped.write(destination / "manifest.json", "manifest.json")
        for record in files:
            if record["sha256"] in seen:
                continue
            zipped.write(root / record["path"], "objects/" + record["sha256"])
            seen.add(record["sha256"])
            processed += record["bytes"]
            if record["bytes"] >= 20 * 1024 * 1024:
                print(f"Archived {len(seen)} unique objects; {processed / 1048576:.1f} MiB", flush=True)
    receipt = verify(archive, source_root=root)
    receipt["manifest_sha256"] = digest(destination / "manifest.json")
    write_json(destination / "verification.json", receipt)
    counts = Counter(r["sha256"] for r in files)
    write_json(destination / "duplicates.json", [dict(sha256=sha, copies=count,
        paths=[r["path"] for r in files if r["sha256"] == sha]) for sha, count in sorted(counts.items()) if count > 1])
    return receipt


def restore(archive, destination, original_path=None):
    archive, destination = Path(archive).resolve(), Path(destination).resolve()
    verify(archive)
    if destination.exists():
        raise ValueError("Restore destination must be new; existing files are never overwritten")
    if original_path is not None:
        safe_relative(original_path)
    with zipfile.ZipFile(archive) as zipped:
        manifest = json.loads(zipped.read("manifest.json"))
        def wanted(path):
            return original_path is None or path == original_path or path.startswith(original_path + "/")
        selected = [r for r in manifest["files"] if wanted(r["path"])]
        directories = [p for p in manifest["directories"] if wanted(p)]
        if not selected and not directories:
            raise ValueError("Original path is absent from archive")
        destination.mkdir(parents=True)
        for directory in directories:
            (destination / directory).mkdir(parents=True, exist_ok=True)
        for record in selected:
            target = destination / record["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            with zipped.open("objects/" + record["sha256"]) as source, target.open("xb") as output:
                for block in iter(lambda: source.read(BLOCK), b""):
                    output.write(block)
            if digest(target) != record["sha256"]:
                raise ValueError(f"Restored content differs: {target}")
            os.chmod(target, record["mode"])
            os.utime(target, ns=(record["mtime_ns"], record["mtime_ns"]))
    return dict(status="restored", files=len(selected), directories=len(directories))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("create")
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--destination", type=Path, required=True)
    p = commands.add_parser("verify")
    p.add_argument("archive", type=Path)
    p.add_argument("--source-root", type=Path)
    p = commands.add_parser("restore")
    p.add_argument("archive", type=Path)
    p.add_argument("--destination", type=Path, required=True)
    p.add_argument("--path", dest="original_path")
    args = vars(parser.parse_args())
    command = args.pop("command")
    print(json.dumps({"create": create, "verify": verify, "restore": restore}[command](**args), indent=2))


if __name__ == "__main__":
    main()
