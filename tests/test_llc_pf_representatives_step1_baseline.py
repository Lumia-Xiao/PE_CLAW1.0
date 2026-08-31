from __future__ import annotations

import csv
import json
import shutil
from uuid import uuid4
from pathlib import Path

from scripts.freeze_llc_pf_representatives_step1_baseline import (
    LLC_TOPOLOGY_ID,
    REQUIRED_ROLES,
    freeze_baseline,
)


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "migration" / "evidence" / "20260831" / "llc_pf_representatives_step1"
CURRENT_RUN = ROOT / "outputs" / "llc_runs" / "b28792595095416f872f5d9a8b8800f6"


def _write_csv(path: Path, headers: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def _write_fixture(root: Path, *, include_external_pf: bool = True, include_min_loss: bool = True) -> Path:
    transformer_dir = root / "transformer_design"
    external_dir = root / "resonant_inductor_design"
    transformer_rows = [
        {"role": "recommended", "candidate_id": "T-recommended", "estimated_volume_cm3": "10", "total_loss_w": "2", "hotspot_c": "40"},
        {"role": "min-volume", "candidate_id": "T-volume", "estimated_volume_cm3": "8", "total_loss_w": "3", "hotspot_c": "45"},
        {"role": "min-loss", "candidate_id": "T-loss", "estimated_volume_cm3": "12", "total_loss_w": "1", "hotspot_c": "38"},
    ]
    if not include_min_loss:
        transformer_rows.pop()
    _write_csv(
        transformer_dir / "llc_transformer_feasible_candidates.csv",
        ["candidate_id", "estimated_volume_cm3", "total_loss_w", "hotspot_c"],
        [{"candidate_id": "T-feasible", "estimated_volume_cm3": "10", "total_loss_w": "2", "hotspot_c": "40"}],
    )
    _write_csv(transformer_dir / "llc_transformer_pareto_front.csv", ["candidate_id"], [{"candidate_id": "T-recommended"}])
    _write_csv(transformer_dir / "llc_transformer_chosen_candidates.csv", list(transformer_rows[0]), transformer_rows)
    (transformer_dir / "llc_transformer_pareto_front.png").write_bytes(b"png")

    external_rows = [
        {"representative_role": "recommended", "design_id": "L-recommended", "estimated_volume_cm3": "10", "total_loss_w": "2", "hotspot_c": "40"},
        {"representative_role": "min-volume", "design_id": "L-volume", "estimated_volume_cm3": "8", "total_loss_w": "3", "hotspot_c": "45"},
        {"representative_role": "min-loss", "design_id": "L-loss", "estimated_volume_cm3": "12", "total_loss_w": "1", "hotspot_c": "38"},
    ]
    _write_csv(
        external_dir / "llc_external_resonant_inductor_feasible_candidates.csv",
        ["design_id", "estimated_volume_cm3", "total_loss_w", "hotspot_c"],
        [{"design_id": "L-feasible", "estimated_volume_cm3": "10", "total_loss_w": "2", "hotspot_c": "40"}],
    )
    _write_csv(external_dir / "llc_external_resonant_inductor_pareto_front.csv", ["design_id"], [{"design_id": "L-recommended"}])
    _write_csv(external_dir / "llc_external_resonant_inductor_chosen_candidates.csv", list(external_rows[0]), external_rows)
    if include_external_pf:
        (external_dir / "llc_external_resonant_inductor_pareto_front.png").write_bytes(b"png")

    payload = {
        "run_id": root.name,
        "topology_id": LLC_TOPOLOGY_ID,
        "status": "available",
        "component_groups": [
            {
                "group_id": "transformer",
                "metadata": {
                    "source_contract": {
                        "vin_nom_v": 400.0,
                        "vout_nom_v": 400.0,
                        "transformer_design_id": "T-recommended",
                        "external_lr_design_id": "L-recommended",
                    }
                },
            }
        ],
        "dependency_diagnostics": {"warnings": []},
    }
    payload_path = root / "hardware_overview" / "hardware_overview_payload.json"
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    payload_path.write_text(json.dumps(payload), encoding="utf-8")
    return root


def test_current_run_baseline_is_complete_and_role_complete() -> None:
    evidence = json.loads((EVIDENCE / "llc_pf_representatives_step1_baseline.json").read_text(encoding="ascii"))
    assert evidence["baseline_status"] == "available"
    assert evidence["run"]["run_id"] == "b28792595095416f872f5d9a8b8800f6"
    assert evidence["run"]["topology_id"] == LLC_TOPOLOGY_ID
    assert evidence["run"]["source_contract"]["vin_nom_v"] == 400.0
    assert evidence["run"]["source_contract"]["vout_nom_v"] == 400.0
    assert evidence["run"]["manifest"]["status"] == "unavailable"
    assert evidence["candidate_stages"]["transformer"]["feasible_count"] == 10269
    assert evidence["candidate_stages"]["transformer"]["pareto_count"] == 16
    assert evidence["candidate_stages"]["external_lr"]["feasible_count"] == 11536
    assert evidence["candidate_stages"]["external_lr"]["pareto_count"] == 28
    for stage in evidence["candidate_stages"].values():
        assert stage["chosen"]["missing_roles"] == []
        assert set(stage["chosen"]["roles"]) == set(REQUIRED_ROLES)


def test_complete_fixture_is_available() -> None:
    root = ROOT / f".pytest-tmp-llc-step1-{uuid4().hex}"
    try:
        result = freeze_baseline(_write_fixture(root / "complete"), ROOT)
        assert result["baseline_status"] == "available"
        assert result["diagnostics"]["missing_or_invalid"] == []
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_missing_external_pf_is_blocked_without_cross_role_fallback() -> None:
    root = ROOT / f".pytest-tmp-llc-step1-{uuid4().hex}"
    try:
        result = freeze_baseline(_write_fixture(root / "missing-pf", include_external_pf=False), ROOT)
        assert result["baseline_status"] == "blocked"
        assert "external_lr.pareto_png" in result["diagnostics"]["missing_or_invalid"]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_missing_representative_role_is_blocked() -> None:
    root = ROOT / f".pytest-tmp-llc-step1-{uuid4().hex}"
    try:
        result = freeze_baseline(_write_fixture(root / "missing-role", include_min_loss=False), ROOT)
        assert result["baseline_status"] == "blocked"
        assert "transformer.chosen.min-loss" in result["diagnostics"]["missing_or_invalid"]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_non_llc_display_baseline_has_no_llc_role_tabs() -> None:
    from scripts.freeze_llc_pf_representatives_step1_baseline import _display_baseline

    result = _display_baseline(ROOT, "buck_diode_rectified_unidirectional")
    assert result["is_llc"] is False
    assert result["observed_llc_geometry_roles"] == []
    assert result["llc_role_specific_tabs_present"] is False
