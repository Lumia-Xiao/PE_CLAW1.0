from __future__ import annotations

from pathlib import Path

from scripts.build_llc_magnetic_result_display_step6_acceptance import (
    REQUIRED_GEOMETRY_ROLES,
    REQUIRED_REPRESENTATIVE_ROLES,
    build_acceptance_payload,
)
from scripts.validate_llc_step8_e2e import build_acceptance_inputs


def test_acceptance_inputs_can_freeze_400_to_400_without_mutating_defaults() -> None:
    raw_input = build_acceptance_inputs(vin_v=400, vout_v=400)

    assert [raw_input[key] for key in ("vin_min", "vin_nom", "vin_max")] == ["400"] * 3
    assert [raw_input[key] for key in ("vout_min", "vout_nom", "vout_max")] == ["400"] * 3


def test_acceptance_rejects_wrong_voltage_and_stale_artifacts(tmp_path: Path) -> None:
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"image")
    evidence = {
        "run_id": "current",
        "output_root": str(tmp_path / "run"),
        "manifest_path": str(tmp_path / "missing.json"),
        "input_snapshot": {
            "vin_min": "400", "vin_nom": "400", "vin_max": "400",
            "vout_min": "48", "vout_nom": "48", "vout_max": "48",
        },
        "stage_status": {},
        "ui_acceptance": {
            "run_id": "old", "output_root": str(tmp_path / "old"), "failures": [],
            "pf_artifacts": {
                role: {
                    "status": "available", "run_id": "old",
                    "files": {"pareto_png_path": {
                        "path": str(outside), "exists": True, "non_empty": True,
                    }},
                }
                for role in ("transformer", "external_lr")
            },
            "representatives": {}, "geometry": {"targets": []},
            "transformer_geometry": {"status": "unavailable", "diagnostics": []},
        },
    }

    payload = build_acceptance_payload(evidence)

    assert payload["valid"] is False
    assert any("not 400 V" in item for item in payload["failures"])
    assert any("stale" in item for item in payload["failures"])
    assert any("outside the current run" in item for item in payload["failures"])
    assert any("without a diagnostic" in item for item in payload["failures"])


def test_acceptance_role_sets_match_the_ui_contract() -> None:
    assert REQUIRED_REPRESENTATIVE_ROLES == ("recommended", "min-volume", "min-loss")
    assert REQUIRED_GEOMETRY_ROLES == ("min_volume", "min_loss", "recommended")


def test_acceptance_reports_missing_pf_representative_and_blocked_magnetics(tmp_path: Path) -> None:
    evidence = {
        "run_id": "run-current",
        "output_root": str(tmp_path / "run-current"),
        "manifest_path": str(tmp_path / "missing-manifest.json"),
        "input_snapshot": {
            key: "400" for key in (
                "vin_min", "vin_nom", "vin_max", "vout_min", "vout_nom", "vout_max",
            )
        },
        "stage_status": {"magnetics": "blocked"},
        "ui_acceptance": {},
    }

    payload = build_acceptance_payload(evidence)

    assert payload["valid"] is False
    assert any("stage magnetics is blocked" in item for item in payload["failures"])
    assert any("transformer PF artifact contract is unavailable" in item for item in payload["failures"])
    assert any("external_lr representative is unavailable" in item for item in payload["failures"])
    assert any("external Lr geometry target is unavailable" in item for item in payload["failures"])
