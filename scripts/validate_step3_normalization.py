"""Compare PE-Claw 1.0 normalization with the frozen PE-Claw 2.0 bridge."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


def _load_target_parser(repo_root: Path):
    path = repo_root / "src" / "pe_claw_gui" / "parsers" / "design_request.py"
    spec = importlib.util.spec_from_file_location("pe_claw_1_parser", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load target parser: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _source_parser(source_root: Path):
    sys.path.insert(0, str(source_root / "src"))
    from pe_claw_gui.agentic.design_request_import import import_design_request_markdown
    from pe_claw_gui.agentic.design_request_parser_bridge import bridge_design_request_to_requirement_parser

    return import_design_request_markdown, bridge_design_request_to_requirement_parser


def _is_standard_request(path: Path) -> bool:
    return any(part[:2].isdigit() and len(part) > 2 and part[2] == "_" for part in path.parts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--requests-root", type=Path, required=True)
    parser.add_argument("--golden", type=Path)
    args = parser.parse_args()

    target = _load_target_parser(args.repo_root)
    importer, bridge = _source_parser(args.source_root)
    files = sorted(p for p in args.requests_root.glob("*/**/design_request.md") if _is_standard_request(p))
    rows: list[dict[str, Any]] = []
    mismatch_count = 0
    for path in files:
        expected = bridge(importer(path).to_dict()).to_dict()["normalized_requirement"]
        actual = target.normalize_design_request_file(path)
        mismatch = expected != actual
        mismatch_count += int(mismatch)
        rows.append({"request": str(path.relative_to(args.requests_root)), "normalized_requirement": actual, "exact_match": not mismatch})
    result = {
        "contract_version": target.NORMALIZED_REQUEST_CONTRACT_VERSION,
        "request_count": len(files),
        "exact_match_count": len(files) - mismatch_count,
        "mismatch_count": mismatch_count,
        "requests": rows,
    }
    if args.golden:
        args.golden.parent.mkdir(parents=True, exist_ok=True)
        args.golden.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("contract_version", "request_count", "exact_match_count", "mismatch_count")}, sort_keys=True))
    return 0 if mismatch_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
