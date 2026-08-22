from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys


LEGACY_AI_PATHS = {
    "src/pe_claw_gui/app/ai_design_page.py",
    "src/pe_claw_gui/app/controllers/ai_design_controller.py",
    "src/pe_claw_gui/app/result_views/ai_design_view.py",
    "src/pe_claw_gui/models/ai_design_report.py",
    "src/pe_claw_gui/pipeline/run_ai_design_pipeline.py",
}

AGENTIC_PREFIXES = (
    "src/pe_claw_gui/agentic/",
    "src/pe_claw_gui/agents/",
    "skills/",
    "design_requests/",
    "reports/evidence/agentic/",
)

AGENTIC_PATH_TERMS = (
    "agentic",
    "ai_design",
    "design_request",
    "phase17",
    "skill_loader",
    "session_output",
    "pe_claw_design_intake",
)

PROHIBITED_CONTENT_TERMS = (
    "pe_claw_gui.agentic",
    "pe_claw_gui.agents",
    "ai_design",
    "design_request_import",
    "design_request_runner",
    "design_request_parser_bridge",
    "run_design_assessment_pipeline",
    "skill_loader",
    "session_output",
)

GENERATED_PREFIXES = (
    "output/",
    "outputs/",
    "reports/",
    "topology_design_comparisons/",
)

LEGACY_PLACEHOLDER_PREFIXES = (
    "src/pe_claw_gui/topologies/ac_ac/",
    "src/pe_claw_gui/topologies/cllc/",
    "src/pe_claw_gui/topologies/dab/",
    "src/pe_claw_gui/topologies/llc/",
    "src/pe_claw_gui/topologies/psfb/",
)

OUT_OF_SCOPE_RUNTIME_PREFIXES = (
    "src/pe_claw_gui/engines/assessment/",
    "src/pe_claw_gui/engines/magnetics/openmagnetics_step",
    "src/pe_claw_gui/engines/magnetics/openmagnetics_v2_regression_audit.py",
    "src/pe_claw_gui/engines/magnetics/openmagnetics_v2_role_runner.py",
    "src/pe_claw_gui/pipeline/run_design_assessment_pipeline.py",
)

RUNTIME_PREFIXES = tuple(
    f"src/pe_claw_gui/{name}/"
    for name in (
        "app",
        "topologies",
        "pipeline",
        "models",
        "engines",
        "libraries",
        "visualization",
        "core",
        "devices",
        "losses",
        "optimization",
        "parsers",
        "schemes",
        "utils",
        "waveform",
    )
)

RUNTIME_ROOT_FILES = {
    "src/pe_claw_gui/__init__.py",
    "src/pe_claw_gui/__main__.py",
    "src/pe_claw_gui/main.py",
    "src/pe_claw_gui/ui.py",
    "src/pe_claw_gui/topology_capabilities.py",
    "pyproject.toml",
    "requirements.txt",
    "run_pe_claw_gui.bat",
}

TEXT_SUFFIXES = {
    ".cfg",
    ".ini",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def tree_entries(root: Path, ref: str) -> list[tuple[str, str]]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-tree", "-r", "-z", ref],
        check=True,
        capture_output=True,
    )
    entries: list[tuple[str, str]] = []
    for item in result.stdout.split(b"\0"):
        if not item:
            continue
        metadata, raw_path = item.split(b"\t", 1)
        object_id = metadata.split()[2].decode("ascii")
        entries.append((raw_path.decode("utf-8"), object_id))
    return sorted(entries)


def read_text(raw: bytes, suffix: str) -> str:
    if suffix.lower() not in TEXT_SUFFIXES:
        return ""
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return raw.decode("utf-16")
        except UnicodeDecodeError:
            return ""
    if raw.startswith(b"\xef\xbb\xbf"):
        try:
            return raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            return ""
    for encoding in ("utf-8", "utf-8-sig", "utf-16"):
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return ""


def prohibited_terms(text: str) -> list[str]:
    lowered = text.lower()
    return [term for term in PROHIBITED_CONTENT_TERMS if term in lowered]


def is_agentic_path(path: str) -> bool:
    lowered = path.lower()
    if lowered.startswith(AGENTIC_PREFIXES):
        return True
    return any(term in lowered for term in AGENTIC_PATH_TERMS)


def is_generated_path(path: str) -> bool:
    lowered = path.lower()
    return lowered.startswith(GENERATED_PREFIXES) or any(
        part in {"__pycache__", ".pytest_cache", ".idea", ".vscode"}
        for part in lowered.split("/")
    )


def is_legacy_placeholder(path: str) -> bool:
    return path.lower().startswith(LEGACY_PLACEHOLDER_PREFIXES)


def is_out_of_scope_runtime_tool(path: str) -> bool:
    return path.lower().startswith(OUT_OF_SCOPE_RUNTIME_PREFIXES)


def initial_runtime_scope(path: str, source_text: str) -> bool:
    if (
        path in LEGACY_AI_PATHS
        or is_agentic_path(path)
        or is_generated_path(path)
        or is_legacy_placeholder(path)
        or is_out_of_scope_runtime_tool(path)
    ):
        return False
    if path in RUNTIME_ROOT_FILES or path.startswith(RUNTIME_PREFIXES):
        return True
    if path.startswith("tests/") and path.endswith(".py"):
        return "pe_claw_gui" in source_text
    return False


def module_name_for_path(path: str) -> str | None:
    if not path.startswith("src/") or not path.endswith(".py"):
        return None
    parts = path.removeprefix("src/").removesuffix(".py").split("/")
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def resolve_imports(path: str, text: str, module_map: dict[str, str]) -> list[tuple[str, str]]:
    try:
        tree = ast.parse(text, filename=path)
    except SyntaxError as exc:
        return [(f"<parse-error:{exc.lineno}>", "parse_error")]

    importer_module = module_name_for_path(path)
    if importer_module is None:
        return []
    package = importer_module if path.endswith("/__init__.py") else importer_module.rpartition(".")[0]
    imports: list[tuple[str, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((alias.name, "import") for alias in node.names)
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level:
            relative = "." * node.level + (node.module or "")
            try:
                base = importlib.util.resolve_name(relative, package)
            except (ImportError, ValueError):
                base = relative
        else:
            base = node.module or ""
        for alias in node.names:
            candidate = f"{base}.{alias.name}" if base else alias.name
            imports.append((candidate if candidate in module_map else base, "from"))
    return imports


def close_runtime_scope(
    source_paths: list[str], source_texts: dict[str, str]
) -> tuple[set[str], dict[str, str]]:
    module_map = {
        module: path
        for path in source_paths
        if (module := module_name_for_path(path)) is not None
    }
    selected = {
        path for path in source_paths if initial_runtime_scope(path, source_texts.get(path, ""))
    }
    changed = True
    while changed:
        changed = False
        for path in tuple(selected):
            if not path.endswith(".py"):
                continue
            for module, _kind in resolve_imports(path, source_texts.get(path, ""), module_map):
                imported_path = module_map.get(module)
                if imported_path is None or imported_path in selected:
                    continue
                if (
                    imported_path in LEGACY_AI_PATHS
                    or is_agentic_path(imported_path)
                    or is_legacy_placeholder(imported_path)
                    or is_out_of_scope_runtime_tool(imported_path)
                ):
                    continue
                selected.add(imported_path)
                changed = True
    return selected, module_map


def snapshot(
    root: Path, ref: str
) -> tuple[list[dict[str, object]], dict[str, str]]:
    entries = tree_entries(root, ref)
    rows: list[dict[str, object]] = []
    texts: dict[str, str] = {}
    process = subprocess.Popen(
        ["git", "-C", str(root), "cat-file", "--batch"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    try:
        for path, object_id in entries:
            process.stdin.write(object_id.encode("ascii") + b"\n")
            process.stdin.flush()
            header = process.stdout.readline().decode("ascii").strip().split()
            if len(header) != 3 or header[1] != "blob":
                raise RuntimeError(f"Unexpected git cat-file response for {path}: {header}")
            size = int(header[2])
            content = process.stdout.read(size)
            if process.stdout.read(1) != b"\n":
                raise RuntimeError(f"Missing git cat-file separator for {path}")
            suffix = Path(path).suffix.lower()
            rows.append(
                {
                    "path": path,
                    "size_bytes": size,
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "suffix": suffix,
                }
            )
            texts[path] = read_text(content, suffix)
    finally:
        process.stdin.close()
        return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"git cat-file failed with exit code {return_code}")
    return rows, texts


def classify(
    path: str,
    source_record: dict[str, object] | None,
    target_record: dict[str, object] | None,
    selected: set[str],
    source_terms: list[str],
    target_terms: list[str],
) -> tuple[str, str]:
    if path in LEGACY_AI_PATHS:
        return "remove_legacy_ai", "Legacy 1.0 AI Design runtime file is excluded."
    if is_legacy_placeholder(path):
        return "remove_legacy_placeholder", "Unregistered legacy placeholder package is replaced by registered 2.0 topology packages."
    if is_agentic_path(path):
        return "exclude_agentic", "Path belongs to the excluded AI/agentic/skills scope."
    if is_generated_path(path):
        return "exclude_generated", "Generated output, evidence, cache, or comparison artifact."
    if path in selected:
        if source_terms:
            return "adapt_in_target", "Selected source file references excluded functionality."
        if source_record and target_record:
            if source_record["sha256"] == target_record["sha256"]:
                return "keep_from_1_0", "Source and target content are identical."
            return "replace_from_2_0", "Selected deterministic runtime file changed in 2.0."
        if source_record:
            return "add_from_2_0", "Selected deterministic runtime file exists only in 2.0."
        return "keep_from_1_0", "Target-only deterministic file retained pending caller migration."
    if target_record:
        if target_terms:
            return "adapt_in_target", "Target support file references excluded functionality."
        return "keep_from_1_0", "Target-owned file is outside the 2.0 runtime copy set."
    return "exclude_out_of_scope", "Source-only file is outside the deterministic GUI runtime scope."


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def registry_snapshot(root: Path) -> list[dict[str, str]]:
    code = r'''
import json
from pe_claw_gui.topologies.base import build_default_registry

registry = build_default_registry()
rows = []
for definition in registry.list_definitions():
    row = {
        "category": definition.category_id,
        "topology_id": definition.topology_id,
        "module_path": definition.module_path,
        "form_path": definition.form_path,
        "plugin_import": "pass",
        "form_import": "pass",
    }
    try:
        registry.get_plugin(definition.topology_id)
    except Exception as exc:
        row["plugin_import"] = f"fail: {type(exc).__name__}: {exc}"
    try:
        registry.get_form_class(definition.topology_id)
    except Exception as exc:
        row["form_import"] = f"fail: {type(exc).__name__}: {exc}"
    rows.append(row)
print(json.dumps(rows))
'''
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-ref", default="HEAD")
    parser.add_argument("--target-ref", default="HEAD")
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    target_root = args.target_root.resolve()
    output_dir = args.output_dir.resolve()
    if source_root == target_root:
        raise ValueError("Source and target roots must differ.")

    source_commit = run_git(source_root, "rev-parse", args.source_ref)
    target_commit = run_git(target_root, "rev-parse", args.target_ref)
    source_inventory, source_texts = snapshot(source_root, source_commit)
    target_inventory, target_texts = snapshot(target_root, target_commit)
    source_paths = [str(row["path"]) for row in source_inventory]
    target_paths = [str(row["path"]) for row in target_inventory]
    source_by_path = {str(row["path"]): row for row in source_inventory}
    target_by_path = {str(row["path"]): row for row in target_inventory}
    selected, module_map = close_runtime_scope(source_paths, source_texts)

    matrix_rows: list[dict[str, object]] = []
    for path in sorted(set(source_paths) | set(target_paths)):
        source_record = source_by_path.get(path)
        target_record = target_by_path.get(path)
        source_terms = prohibited_terms(source_texts.get(path, ""))
        target_terms = prohibited_terms(target_texts.get(path, ""))
        classification, reason = classify(
            path,
            source_record,
            target_record,
            selected,
            source_terms,
            target_terms,
        )
        matrix_rows.append(
            {
                "path": path,
                "source_exists": bool(source_record),
                "target_exists": bool(target_record),
                "source_size_bytes": source_record["size_bytes"] if source_record else "",
                "target_size_bytes": target_record["size_bytes"] if target_record else "",
                "source_sha256": source_record["sha256"] if source_record else "",
                "target_sha256": target_record["sha256"] if target_record else "",
                "same_content": bool(
                    source_record
                    and target_record
                    and source_record["sha256"] == target_record["sha256"]
                ),
                "runtime_scope": path in selected,
                "source_prohibited_terms": ";".join(source_terms),
                "target_prohibited_terms": ";".join(target_terms),
                "classification": classification,
                "reason": reason,
            }
        )

    edge_rows: list[dict[str, object]] = []
    for importer in sorted(path for path in selected if path.endswith(".py") and path in source_texts):
        for imported_module, import_kind in resolve_imports(
            importer, source_texts[importer], module_map
        ):
            resolved_path = module_map.get(imported_module, "")
            if import_kind == "parse_error":
                status = "parse_error"
            elif imported_module.startswith("pe_claw_gui"):
                if not resolved_path:
                    status = "unresolved_internal"
                elif is_agentic_path(resolved_path) or resolved_path in LEGACY_AI_PATHS:
                    status = "excluded_agentic_dependency"
                elif is_out_of_scope_runtime_tool(resolved_path):
                    status = "excluded_out_of_scope_dependency"
                elif resolved_path in selected:
                    status = "included_internal"
                else:
                    status = "internal_out_of_scope"
            else:
                status = "external_or_stdlib"
            edge_rows.append(
                {
                    "importer_path": importer,
                    "import_kind": import_kind,
                    "imported_module": imported_module,
                    "resolved_path": resolved_path,
                    "status": status,
                }
            )

    exclusion_rows = [
        {
            "path": row["path"],
            "action": row["classification"],
            "source_prohibited_terms": row["source_prohibited_terms"],
            "target_prohibited_terms": row["target_prohibited_terms"],
            "reason": row["reason"],
        }
        for row in matrix_rows
        if row["classification"] in {"exclude_agentic", "remove_legacy_ai", "adapt_in_target"}
    ]

    source_topologies = registry_snapshot(source_root)
    target_topologies = {
        row["topology_id"]: row for row in registry_snapshot(target_root)
    }
    topology_rows: list[dict[str, object]] = []
    for source_row in source_topologies:
        topology_id = source_row["topology_id"]
        target_row = target_topologies.get(topology_id)
        topology_rows.append(
            {
                "category": source_row["category"],
                "topology_id": topology_id,
                "source_registered": True,
                "source_plugin_import": source_row["plugin_import"],
                "source_form_import": source_row["form_import"],
                "target_registered_baseline": bool(target_row),
                "target_plugin_import_baseline": target_row["plugin_import"] if target_row else "not registered",
                "target_form_import_baseline": target_row["form_import"] if target_row else "not registered",
                "migration_registration": "pending",
                "migration_form": "pending",
                "migration_plugin": "pending",
                "migration_pipeline": "pending",
                "migration_gui_results": "pending",
                "migration_parity": "pending",
                "status": "pending",
                "notes": "Baseline only; no 2.0 runtime code copied in Phase 1.",
            }
        )

    write_csv(
        output_dir / "source_2_0_inventory.csv",
        source_inventory,
        ["path", "size_bytes", "sha256", "suffix"],
    )
    write_csv(
        output_dir / "target_1_0_inventory.csv",
        target_inventory,
        ["path", "size_bytes", "sha256", "suffix"],
    )
    write_csv(
        output_dir / "file_migration_matrix.csv",
        matrix_rows,
        [
            "path",
            "source_exists",
            "target_exists",
            "source_size_bytes",
            "target_size_bytes",
            "source_sha256",
            "target_sha256",
            "same_content",
            "runtime_scope",
            "source_prohibited_terms",
            "target_prohibited_terms",
            "classification",
            "reason",
        ],
    )
    write_csv(
        output_dir / "runtime_dependency_edges.csv",
        edge_rows,
        ["importer_path", "import_kind", "imported_module", "resolved_path", "status"],
    )
    write_csv(
        output_dir / "agentic_exclusion_list.csv",
        exclusion_rows,
        ["path", "action", "source_prohibited_terms", "target_prohibited_terms", "reason"],
    )
    write_csv(
        output_dir / "topology_acceptance_matrix.csv",
        topology_rows,
        [
            "category",
            "topology_id",
            "source_registered",
            "source_plugin_import",
            "source_form_import",
            "target_registered_baseline",
            "target_plugin_import_baseline",
            "target_form_import_baseline",
            "migration_registration",
            "migration_form",
            "migration_plugin",
            "migration_pipeline",
            "migration_gui_results",
            "migration_parity",
            "status",
            "notes",
        ],
    )

    summary = {
        "schema_version": "pe_claw_gui_migration_phase1_v1",
        "source_root": str(source_root),
        "target_root": str(target_root),
        "source_commit": source_commit,
        "target_commit": target_commit,
        "source_tracked_files": len(source_inventory),
        "target_tracked_files": len(target_inventory),
        "matrix_rows": len(matrix_rows),
        "selected_runtime_files": len(selected),
        "dependency_edges": len(edge_rows),
        "classifications": {
            name: sum(row["classification"] == name for row in matrix_rows)
            for name in sorted({str(row["classification"]) for row in matrix_rows})
        },
        "dependency_statuses": {
            name: sum(row["status"] == name for row in edge_rows)
            for name in sorted({str(row["status"]) for row in edge_rows})
        },
        "exclusion_rows": len(exclusion_rows),
        "source_topologies": len(source_topologies),
        "target_topologies_baseline": len(target_topologies),
        "review_required_rows": sum(
            row["classification"] == "review_required" for row in matrix_rows
        ),
    }
    (output_dir / "phase1_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
