"""Generate and validate the Step 2 runtime environment evidence."""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path(r"C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw")
EVIDENCE_ROOT = ROOT / "migration" / "evidence" / "20260824" / "step2_environment"

sys.path.insert(0, str(ROOT / "src"))

from pe_claw_gui.runtime import environment_snapshot  # noqa: E402


def git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def main() -> int:
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    target = environment_snapshot(project_root=ROOT)
    source = {
        "project_root": str(SOURCE_ROOT),
        "git_commit": git(SOURCE_ROOT, "rev-parse", "HEAD"),
        "git_branch": git(SOURCE_ROOT, "branch", "--show-current"),
        "git_status_porcelain": git(SOURCE_ROOT, "status", "--porcelain") or "",
        "pyproject_sha256": _sha256(SOURCE_ROOT / "pyproject.toml"),
    }
    source_dependencies = _project_dependencies(SOURCE_ROOT / "pyproject.toml")
    target_dependencies = _project_dependencies(ROOT / "pyproject.toml")
    target.update(
        {
            "git_commit": git(ROOT, "rev-parse", "HEAD"),
            "git_branch": git(ROOT, "branch", "--show-current"),
            "git_status_porcelain": git(ROOT, "status", "--porcelain") or "",
            "pyproject_sha256": _sha256(ROOT / "pyproject.toml"),
        }
    )
    (EVIDENCE_ROOT / "environment_manifest_1.json").write_text(json.dumps(target, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    (EVIDENCE_ROOT / "environment_manifest_2.json").write_text(json.dumps(source, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    result = {
        "contract_version": "pe_claw_step2_environment_validation_v1",
        "target_runtime_contract": target["contract_version"],
        "target_python": target["python_version"],
        "target_dependencies": target["runtime_packages"],
        "source_git_commit": source["git_commit"],
        "target_git_commit": target["git_commit"],
        "source_declared_dependencies": source_dependencies,
        "target_declared_dependencies": target_dependencies,
        "declared_dependencies_match": source_dependencies == target_dependencies,
        "policy_environment": target["deterministic_environment"],
        "validation_pass": source_dependencies == target_dependencies and all(target["deterministic_environment"].get(name) == value for name, value in {
            "PYTHONHASHSEED": "0",
            "TZ": "UTC",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
            "BLIS_NUM_THREADS": "1",
        }.items()),
    }
    (EVIDENCE_ROOT / "step2_validation.json").write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["validation_pass"] else 2


def _project_dependencies(path: Path) -> list[str]:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    dependencies = payload["project"]["dependencies"]
    optional = payload["project"].get("optional-dependencies", {}).get("maintenance-pdf", [])
    return sorted([*dependencies, *optional])


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    import hashlib

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


if __name__ == "__main__":
    raise SystemExit(main())
