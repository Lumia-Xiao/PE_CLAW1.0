from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from pe_claw_gui.models.common_spec import CommonSpec
from pe_claw_gui.models.design_report import DesignReport
from pe_claw_gui.models.llc_run_context import LlcRunContext
from pe_claw_gui.models.magnetic_result import LlcMagneticCombinationContract
from pe_claw_gui.pipeline.run_magnetic_pipeline import (
    build_llc_magnetic_combination_contract,
    validate_llc_magnetic_combination_contract,
)


TOPOLOGY_ID = "llc_resonant_converter_diode_rectifier"


def _report() -> DesignReport:
    spec = CommonSpec(
        topology_id=TOPOLOGY_ID,
        display_name="LLC",
        vin_min=360.0,
        vin_max=420.0,
        vout=48.0,
        pout=4000.0,
        fs_khz=100.0,
        ripple_current_ratio=0.2,
        ripple_voltage_ratio_percent=5.0,
    )
    context = LlcRunContext.create(TOPOLOGY_ID, {"vin": "400", "pout": "4000"})
    return DesignReport(spec=spec, llc_run_context=context)


def _parts():
    transformer = SimpleNamespace(
        candidate_id="transformer-current",
        np=18,
        ns=18,
        lm_target_h=1.8e-3,
        lm_actual_h=1.82e-3,
        estimated_lk_h=0.12e-3,
        current_basis_label="FHA worst-case corner",
    )
    external_target = SimpleNamespace(
        external_lr_target_h=1.08e-3,
        lr_total_target_h=1.2e-3,
        fs_basis_hz=85000.0,
        current_basis="sinusoidal_peak",
        current_rms_a=4.0,
        current_peak_a=6.0,
    )
    external = SimpleNamespace(
        design_id="external-current",
        actual_l_h=1.1e-3,
        total_lr_actual_h=1.22e-3,
    )
    fha = SimpleNamespace(
        fr_hz=100000.0,
        vin_min_v=360.0,
        vin_nom_v=400.0,
        vin_max_v=420.0,
        vout_min_v=47.5,
        vout_nom_v=48.0,
        vout_max_v=48.5,
        worst_case_current_stress={"resonant_tank_peak_a": 6.0},
    )
    return transformer, external_target, external, fha


def test_llc_magnetic_contract_round_trips_and_closes_total_lr() -> None:
    report = _report()
    transformer, external_target, external, fha = _parts()
    contract = build_llc_magnetic_combination_contract(
        report=report,
        fha_design=fha,
        transformer_target={"lr_target_h": 1.2e-3},
        transformer=transformer,
        external_lr=external,
        external_lr_target=external_target,
        transformer_artifact_paths=["transformer.csv"],
        external_lr_artifact_paths=["external.csv"],
        external_lr_status="available",
    )

    assert contract.combined_magnetic_design_id == "transformer-current+external-current"
    assert contract.total_lr_target_h == pytest.approx(0.12e-3 + 1.08e-3)
    assert contract.total_lr_actual_h == pytest.approx(0.12e-3 + 1.1e-3)
    restored = LlcMagneticCombinationContract.from_dict(contract.to_dict())
    assert restored == contract
    assert validate_llc_magnetic_combination_contract(
        report=report,
        contract=contract,
        transformer_candidates=[transformer],
        external_lr_candidates=[external],
    ) == {"valid": True, "reason": ""}


def test_llc_magnetic_contract_rejects_stale_id_and_run_or_topology_mismatch() -> None:
    report = _report()
    transformer, external_target, external, fha = _parts()
    contract = build_llc_magnetic_combination_contract(
        report=report,
        fha_design=fha,
        transformer_target={"lr_target_h": 1.2e-3},
        transformer=transformer,
        external_lr=external,
        external_lr_target=external_target,
        transformer_artifact_paths=[],
        external_lr_artifact_paths=[],
        external_lr_status="available",
    )

    stale = validate_llc_magnetic_combination_contract(
        report=report,
        contract=contract,
        transformer_candidates=[SimpleNamespace(**{**vars(transformer), "candidate_id": "old-transformer"})],
        external_lr_candidates=[external],
    )
    assert stale["valid"] is False
    assert "unknown transformer design ID" in str(stale["reason"])

    wrong_run = replace(contract, run_id="old-run")
    run_result = validate_llc_magnetic_combination_contract(
        report=report,
        contract=wrong_run,
        transformer_candidates=[transformer],
        external_lr_candidates=[external],
    )
    assert run_result["valid"] is False
    assert "run mismatch" in str(run_result["reason"])

    wrong_topology = replace(contract, topology_id="not-llc")
    topology_result = validate_llc_magnetic_combination_contract(
        report=report,
        contract=wrong_topology,
        transformer_candidates=[transformer],
        external_lr_candidates=[external],
    )
    assert topology_result["valid"] is False
    assert "topology mismatch" in str(topology_result["reason"])


def test_llc_magnetic_contract_rejects_open_target_and_actual_lr_closure() -> None:
    report = _report()
    transformer, external_target, external, fha = _parts()
    contract = build_llc_magnetic_combination_contract(
        report=report,
        fha_design=fha,
        transformer_target={"lr_target_h": 1.2e-3},
        transformer=transformer,
        external_lr=external,
        external_lr_target=external_target,
        transformer_artifact_paths=[],
        external_lr_artifact_paths=[],
        external_lr_status="available",
    )

    target_result = validate_llc_magnetic_combination_contract(
        report=report,
        contract=replace(contract, total_lr_target_h=1.25e-3),
        transformer_candidates=[transformer],
        external_lr_candidates=[external],
    )
    assert target_result["valid"] is False
    assert "target is not closed" in str(target_result["reason"])

    actual_result = validate_llc_magnetic_combination_contract(
        report=report,
        contract=replace(contract, total_lr_actual_h=1.25e-3),
        transformer_candidates=[transformer],
        external_lr_candidates=[external],
    )
    assert actual_result["valid"] is False
    assert "actual is not closed" in str(actual_result["reason"])


def test_llc_magnetic_contract_allows_not_required_external_lr_without_combined_id() -> None:
    report = _report()
    transformer, external_target, _, fha = _parts()
    not_required_target = SimpleNamespace(
        external_lr_target_h=0.0,
        lr_total_target_h=0.12e-3,
        fs_basis_hz=100000.0,
        current_basis="not_required",
        current_rms_a=0.0,
        current_peak_a=0.0,
    )
    contract = build_llc_magnetic_combination_contract(
        report=report,
        fha_design=fha,
        transformer_target={"lr_target_h": 0.12e-3},
        transformer=transformer,
        external_lr=None,
        external_lr_target=not_required_target,
        transformer_artifact_paths=[],
        external_lr_artifact_paths=[],
        external_lr_status="not_required",
    )

    assert contract.external_lr_design_id is None
    assert contract.combined_magnetic_design_id is None
    assert validate_llc_magnetic_combination_contract(
        report=report,
        contract=contract,
        transformer_candidates=[transformer],
        external_lr_candidates=[],
    ) == {"valid": True, "reason": ""}
