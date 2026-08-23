"""Deterministic Step 16 manifest for seven-role core-loss A/B reruns."""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any, Mapping, Sequence


STEP16_CONTRACT_VERSION = "openmagnetics-step16-ab-rerun-manifest-v1"
REQUIRED_ROLES = (
    "buck_main_inductor",
    "boost_main_inductor",
    "flyback_coupled_inductor_transformer",
    "llc_transformer",
    "llc_external_resonant_inductor",
    "generic_main_inductor_stacked_core_competitor",
    "single_phase_rectifier_dc_link_reactor",
)


def build_ab_rerun_manifest(
    *,
    baseline_cases: Sequence[Mapping[str, Any]],
    v2_cache_dir: str | Path,
    current_records: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Create a manifest that distinguishes pending, invalid, and ready evidence."""
    baseline_by_role = {
        str(item.get("role")): item for item in baseline_cases if item.get("role")
    }
    current_by_role = {
        str(item.get("role")): item for item in current_records if item.get("role")
    }
    records: list[dict[str, Any]] = []
    for role in REQUIRED_ROLES:
        baseline = baseline_by_role.get(role)
        current = current_by_role.get(role)
        if baseline is None:
            status = "missing_baseline"
        elif current is None:
            status = "pending_rerun"
        elif not _has_required_current_fields(current):
            status = "invalid_current_evidence"
        else:
            status = "ready_for_step14_comparison"
        records.append(
            {
                "role": role,
                "case_id": str((baseline or {}).get("case_id") or role),
                "baseline_session_id": (baseline or {}).get("session_id"),
                "current_record_present": current is not None,
                "status": status,
                "required_current_fields": [
                    "selected_design_id",
                    "material",
                    "turns",
                    "core_loss_w",
                    "copper_loss_w",
                ],
            }
        )
    return {
        "contract_version": STEP16_CONTRACT_VERSION,
        "v2_cache_dir": Path(v2_cache_dir).resolve().as_posix(),
        "required_role_count": len(REQUIRED_ROLES),
        "records": records,
        "status_counts": {
            status: sum(item["status"] == status for item in records)
            for status in ("ready_for_step14_comparison", "pending_rerun", "missing_baseline", "invalid_current_evidence")
        },
        "all_ready": all(item["status"] == "ready_for_step14_comparison" for item in records),
        "production_promotion_allowed": False,
    }


def _has_required_current_fields(record: Mapping[str, Any]) -> bool:
    return all(record.get(field) is not None for field in ("selected_design_id", "material", "turns", "core_loss_w", "copper_loss_w"))


def write_ab_rerun_manifest(path: str | Path, payload: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(dict(payload), sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n", encoding="utf-8")


__all__ = ["REQUIRED_ROLES", "STEP16_CONTRACT_VERSION", "build_ab_rerun_manifest", "write_ab_rerun_manifest"]
