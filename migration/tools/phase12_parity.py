"""Compare deterministic default topology contracts between two checkouts."""

from __future__ import annotations

import argparse
from dataclasses import fields, is_dataclass
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


COLLECTOR = r'''
from dataclasses import fields, is_dataclass
from importlib import import_module
import json
import math
from typing import Any

from pe_claw_gui.topologies.base.registry import build_default_registry


def encode(value: Any):
    if is_dataclass(value):
        return {field.name: encode(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {str(key): encode(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [encode(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            return str(value)
        return round(value, 8)
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    return repr(value)


registry = build_default_registry()
records = []
for definition in registry.list_definitions():
    plugin = registry.get_plugin(definition.topology_id)
    module = import_module(plugin.__module__)
    raw_input = module.build_default_inputs()
    spec = plugin.build_spec(raw_input)
    candidate = plugin.synthesize(spec)
    result = plugin.evaluate(candidate)
    form_class = registry.get_form_class(definition.topology_id)
    records.append({
        "definition": encode(definition),
        "form_fields": [
            {"key": field.key, "default": field.default, "choices": list(field.choices)}
            for field in form_class.get_design_fields()
        ],
        "raw_input_keys": sorted(raw_input),
        "spec": encode(spec),
        "candidate": encode(candidate),
        "topology_result": encode(result),
    })
print(json.dumps(records, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
'''


def _collect(root: Path) -> list[dict[str, Any]]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-B", "-c", COLLECTOR],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(result.stdout)


def _compare(source: Any, target: Any, path: str = "root") -> list[str]:
    if type(source) is not type(target):
        return [f"{path}: type {type(source).__name__} != {type(target).__name__}"]
    if isinstance(source, dict):
        differences = []
        for key in sorted(set(source) | set(target)):
            if key not in source or key not in target:
                differences.append(f"{path}.{key}: field presence mismatch")
            else:
                differences.extend(_compare(source[key], target[key], f"{path}.{key}"))
        return differences
    if isinstance(source, list):
        if len(source) != len(target):
            return [f"{path}: length {len(source)} != {len(target)}"]
        differences = []
        for index, (left, right) in enumerate(zip(source, target)):
            differences.extend(_compare(left, right, f"{path}[{index}]"))
        return differences
    if isinstance(source, (int, float)) and isinstance(target, (int, float)):
        if not math.isclose(float(source), float(target), rel_tol=1e-7, abs_tol=1e-8):
            return [f"{path}: {source!r} != {target!r}"]
        return []
    if source != target:
        return [f"{path}: {source!r} != {target!r}"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    source = _collect(args.source_root.resolve())
    target = _collect(args.target_root.resolve())
    backend_source = [
        {key: value for key, value in record.items() if key != "form_fields"}
        for record in source
    ]
    backend_target = [
        {key: value for key, value in record.items() if key != "form_fields"}
        for record in target
    ]
    differences = _compare(backend_source, backend_target)
    gui_form_differences = _compare(
        [record["form_fields"] for record in source],
        [record["form_fields"] for record in target],
    )
    report = {
        "source_root": str(args.source_root.resolve()),
        "target_root": str(args.target_root.resolve()),
        "topology_count": len(target),
        "topology_ids": [item["definition"]["topology_id"] for item in target],
        "differences": differences,
        "gui_form_differences": gui_form_differences,
        "parity": not differences,
    }
    payload = json.dumps(report, ensure_ascii=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if not differences else 1


if __name__ == "__main__":
    raise SystemExit(main())
