"""Role-specific artifact contracts for separated LLC magnetic PF results."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Iterable

from ..models.magnetic_result import LlcPfArtifactContract


LLC_PF_ROLES = ("transformer", "external_lr")
REQUIRED_ARTIFACT_NAMES = {
    "transformer": {
        "pareto_png_path": "llc_transformer_pareto_front.png",
        "pareto_csv_path": "llc_transformer_pareto_front.csv",
        "feasible_csv_path": "llc_transformer_feasible_candidates.csv",
        "chosen_csv_path": "llc_transformer_chosen_candidates.csv",
    },
    "external_lr": {
        "pareto_png_path": "llc_external_resonant_inductor_pareto_front.png",
        "pareto_csv_path": "llc_external_resonant_inductor_pareto_front.csv",
        "feasible_csv_path": "llc_external_resonant_inductor_feasible_candidates.csv",
        "chosen_csv_path": "llc_external_resonant_inductor_chosen_candidates.csv",
    },
}


def build_llc_pf_artifact_contract(
    *,
    role: str,
    artifact_paths: Iterable[str | Path],
    run_id: str,
    topology_id: str,
    run_root: str | Path | None,
    recommended_design_id: str | None,
) -> LlcPfArtifactContract:
    """Build and validate one role-specific PF artifact contract."""

    if role not in REQUIRED_ARTIFACT_NAMES:
        raise ValueError(f"Unknown LLC PF artifact role: {role!r}")
    paths_by_name: dict[str, Path] = {}
    for raw_path in artifact_paths:
        path = Path(raw_path).resolve()
        paths_by_name.setdefault(path.name, path)
    selected = {
        field: str(paths_by_name[name]) if name in paths_by_name else None
        for field, name in REQUIRED_ARTIFACT_NAMES[role].items()
    }
    diagnostics: list[str] = []
    root = Path(run_root).resolve() if run_root else None
    for field, value in selected.items():
        if value is None:
            diagnostics.append(f"missing required artifact: {field}")
            continue
        path = Path(value)
        if root is not None and root not in path.parents:
            diagnostics.append(f"artifact is outside current run root: {field}")
        if not path.is_file():
            diagnostics.append(f"artifact is missing: {field}")
        elif path.stat().st_size <= 0:
            diagnostics.append(f"artifact is empty: {field}")
    if not run_id:
        diagnostics.append("run_id is unavailable")
    if not topology_id:
        diagnostics.append("topology_id is unavailable")
    if not recommended_design_id:
        diagnostics.append("recommended design ID is unavailable")
    return LlcPfArtifactContract(
        role=role,
        run_id=run_id,
        topology_id=topology_id,
        recommended_design_id=recommended_design_id,
        status="available" if not diagnostics else "blocked",
        diagnostics=tuple(diagnostics),
        **selected,
    )


def validate_llc_pf_artifact_contracts(
    contracts: dict[str, LlcPfArtifactContract],
    *,
    run_id: str,
    topology_id: str,
) -> dict[str, Any]:
    """Validate both role contracts against the current run identity."""

    diagnostics: list[str] = []
    for role in LLC_PF_ROLES:
        contract = contracts.get(role)
        if contract is None:
            diagnostics.append(f"missing role contract: {role}")
            continue
        try:
            contract.validate_identity(run_id=run_id, topology_id=topology_id)
        except ValueError as exc:
            diagnostics.append(f"{role}: {exc}")
        diagnostics.extend(f"{role}: {item}" for item in contract.diagnostics)
    return {"valid": not diagnostics, "reason": "; ".join(diagnostics), "diagnostics": diagnostics}


def llc_pf_artifact_payload(
    contracts: dict[str, LlcPfArtifactContract],
) -> dict[str, dict[str, Any]]:
    """Serialize role contracts with auditable file state and hashes."""

    payload: dict[str, dict[str, Any]] = {}
    for role in LLC_PF_ROLES:
        contract = contracts.get(role)
        if contract is None:
            payload[role] = {
                "status": "unavailable",
                "diagnostics": [f"missing role contract: {role}"],
                "files": {},
            }
            continue
        files: dict[str, Any] = {}
        for field in REQUIRED_ARTIFACT_NAMES[role]:
            raw_path = getattr(contract, field)
            path = Path(raw_path) if raw_path else None
            exists = bool(path and path.is_file())
            files[field] = {
                "path": str(path) if path else None,
                "exists": exists,
                "non_empty": bool(exists and path.stat().st_size > 0),
                "size_bytes": path.stat().st_size if exists else 0,
                "sha256": _sha256(path) if exists else None,
            }
        payload[role] = {
            **contract.to_dict(),
            "files": files,
        }
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
