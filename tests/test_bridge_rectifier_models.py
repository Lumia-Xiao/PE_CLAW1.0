from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from pe_claw_gui.models import (
    BridgeRectifierCandidate,
    BridgeRectifierCandidateEvaluation,
    BridgeRectifierLossEstimate,
    BridgeRectifierRankingBreakdown,
    BridgeRectifierSelectionRequest,
    BridgeRectifierSelectionResult,
    BridgeRectifierThermalEstimate,
)


def _request() -> BridgeRectifierSelectionRequest:
    return BridgeRectifierSelectionRequest(
        topology_id="single_phase_diode_bridge_rectifier_capacitor_filter",
        ac_input_rms_v=230.0,
        dc_bus_voltage_v=325.0,
        output_power_w=1000.0,
        dc_output_current_a=3.08,
        bridge_current_avg_a=3.08,
        bridge_current_rms_a=5.0,
        required_reverse_voltage_v=650.0,
        line_frequency_hz=50.0,
        ambient_temp_c=40.0,
        target_junction_temp_c=125.0,
    )


def _candidate() -> BridgeRectifierCandidate:
    return BridgeRectifierCandidate(
        candidate_id="Good-Ark::GBU1008::4786-GBU1008-ND",
        part_number="GBU1008",
        manufacturer="Good-Ark Semiconductor",
        digikey_part_number="4786-GBU1008-ND",
        package_family="GBU",
        package_case="4-SIP, GBU",
        mounting_type="Through Hole",
        v_rrm_v=800.0,
        io_avg_rectified_a=10.0,
        vf_max_v=1.1,
        vf_test_current_a=5.0,
        tj_min_c=-55.0,
        tj_max_c=150.0,
        body_length_mm=22.0,
        body_width_mm=3.5,
        body_height_mm=18.5,
        unit_price_usd=1.28,
        stock_qty=428.0,
        rth_jc_k_per_w=2.2,
        rth_ja_k_per_w=22.0,
        thermal_condition="rough package-family estimate",
        package_dimension_status="rough_package_family_estimate",
        thermal_status="rough_datasheet_family_estimate",
        datasheet_url="https://goodarksemi.com/docs/datasheets/general_purpose_bridge_rectifiers/GBU10xx.pdf",
        digikey_url="https://www.digikey.sg/en/products/detail/good-ark-semiconductor/GBU1008/26524076",
    )


def test_bridge_rectifier_request_preserves_selection_requirements() -> None:
    request = _request()

    assert request.topology_id == "single_phase_diode_bridge_rectifier_capacitor_filter"
    assert request.required_reverse_voltage_v == 650.0
    assert request.voltage_margin == 1.20
    assert request.current_margin == 1.10
    assert request.thermal_mode == "rough_rth_ja"
    assert request.bridge_current_waveform_a == ()


def test_bridge_rectifier_candidate_tracks_package_cost_and_thermal_data() -> None:
    candidate = _candidate()

    assert candidate.package_family == "GBU"
    assert candidate.vf_max_v == 1.1
    assert candidate.unit_price_usd == 1.28
    assert candidate.rth_jc_k_per_w == 2.2
    assert candidate.rth_ja_k_per_w == 22.0
    assert candidate.body_volume_mm3 == 22.0 * 3.5 * 18.5


def test_bridge_rectifier_candidate_evaluation_hard_filter_property() -> None:
    candidate = _candidate()
    loss = BridgeRectifierLossEstimate(
        conduction_loss_w=6.776,
        total_loss_w=6.776,
        vf_used_v=1.1,
        current_basis_a=3.08,
        current_basis_label="bridge_current_avg_a",
    )
    thermal = BridgeRectifierThermalEstimate(
        rth_used_k_per_w=22.0,
        rth_basis="rth_ja",
        ambient_temp_c=40.0,
        target_junction_temp_c=125.0,
        tj_est_c=189.1,
        junction_margin_c=-64.1,
        feasible=False,
    )
    failed = BridgeRectifierCandidateEvaluation(
        candidate=candidate,
        passed_voltage=True,
        passed_current=True,
        passed_price=True,
        passed_package_data=True,
        passed_vf_data=True,
        passed_thermal_data=True,
        passed_thermal=False,
        loss_estimate=loss,
        thermal_estimate=thermal,
        rejection_reasons=("thermal estimate exceeds target junction temperature",),
    )
    passed = BridgeRectifierCandidateEvaluation(
        candidate=candidate,
        passed_voltage=True,
        passed_current=True,
        passed_price=True,
        passed_package_data=True,
        passed_vf_data=True,
        passed_thermal_data=True,
        passed_thermal=True,
        loss_estimate=loss,
    )

    assert failed.passed_hard_filters is False
    assert passed.passed_hard_filters is True


def test_bridge_rectifier_ranking_breakdown_tracks_score_components() -> None:
    breakdown = BridgeRectifierRankingBreakdown(
        loss_w=4.0,
        tj_est_c=100.0,
        unit_price_usd=2.0,
        body_volume_cm3=1.5,
        thermal_over_target_c=0.0,
        normalized_loss=0.2,
        normalized_tj=0.3,
        normalized_price=0.4,
        normalized_volume=0.5,
        loss_score_component=0.12,
        tj_score_component=0.075,
        price_score_component=0.04,
        volume_score_component=0.025,
        thermal_penalty_component=0.0,
        total_score=0.26,
    )

    assert breakdown.method == "normalized_loss_tj_price_volume"
    assert breakdown.total_score == 0.26
    assert breakdown.data_confidence_penalty_component == 0.0
    assert breakdown.data_confidence_policy == "allow_rough_estimates"
    assert breakdown.loss_weight == 0.60
    assert breakdown.tj_weight == 0.25
    assert breakdown.loss_score_component + breakdown.tj_score_component + breakdown.price_score_component + breakdown.volume_score_component == 0.26


def test_bridge_rectifier_selection_result_contains_auditable_evaluations() -> None:
    candidate = _candidate()
    evaluation = BridgeRectifierCandidateEvaluation(
        candidate=candidate,
        passed_voltage=True,
        passed_current=True,
        passed_price=True,
        passed_package_data=True,
        passed_vf_data=True,
        passed_thermal_data=True,
    )
    result = BridgeRectifierSelectionResult(
        request=_request(),
        candidate_count=1,
        passed_candidate_count=1,
        selected_candidate=candidate,
        evaluations=(evaluation,),
        rejection_summary={"voltage filter failed": 2},
        notes=["Bridge selector model contract only; selection algorithm is not implemented here."],
    )

    assert result.selected_candidate is candidate
    assert result.evaluations == (evaluation,)
    assert result.rejection_summary["voltage filter failed"] == 2
    assert result.notes[0].startswith("Bridge selector model contract")
