from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from scripts.build_llc_magnetic_result_display_step1_baseline import build_baseline_report
from pe_claw_gui.app.result_views.capacitor_pf_view import build_capacitor_pf_side_summary
from pe_claw_gui.app.result_views.capacitor_view import build_capacitor_summary_text
from pe_claw_gui.engines.capacitors.llc_resonant import search_llc_resonant_capacitor_banks
from pe_claw_gui.libraries.capacitors import list_c44p_t_capacitors
from pe_claw_gui.models.capacitor import CapacitorResult, LlcResonantCapacitorDesignRequest
from pe_claw_gui.reports.structured_output import build_structured_report


def _request() -> LlcResonantCapacitorDesignRequest:
    target = 74.37482607930382e-9
    return LlcResonantCapacitorDesignRequest(
        cr_target_f=target,
        cr_target_nF=target * 1e9,
        lr_target_h=10e-6,
        lr_total_actual_h=10e-6,
        transformer_lk_h=1e-6,
        external_lr_actual_h=9e-6,
        current_rms_a=10.0,
        current_peak_a=15.0,
        current_basis="test",
        voltage_rms_v=100.0,
        voltage_peak_v=150.0,
        voltage_basis="test",
        voltage_rating_basis="test",
        voltage_margin_factor=1.2,
        required_voltage_rating_v=180.0,
        fs_basis_hz=100_000.0,
        fs_min_hz=80_000.0,
        fs_max_hz=120_000.0,
        frequency_basis="test",
        is_design_required=True,
    )


def _candidate(capacitance_f: float, part_number: str):
    base = next(item for item in list_c44p_t_capacitors() if item.part_number == "C44PRGR6100T99K")
    return replace(
        base,
        part_number=part_number,
        capacitance_f=capacitance_f,
        application_category="resonant",
        voltage_rating_dc_v=1_000.0,
        irms_rating_a=100.0,
        rs_ohm=0.01,
        esr_mohm=None,
        rth_hotspot_to_ambient_c_per_w=0.1,
        hotspot_temp_max_c=150.0,
        self_heating_limit_c=100.0,
        total_volume_cm3=1.0,
    )


def _report(tmp_path: Path, capacitance_f: float, part_number: str):
    search = search_llc_resonant_capacitor_banks(
        _request(),
        (_candidate(capacitance_f, part_number),),
        output_dir=tmp_path,
    )
    baseline = build_baseline_report()
    capacitor = CapacitorResult(
        llc_resonant_capacitor_request=search.request,
        llc_resonant_capacitor_search_result=search,
    )
    return replace(baseline, capacitor=capacitor), search


def test_llc_cr_recommendation_is_consistent_in_structured_report_and_gui(tmp_path: Path) -> None:
    report, search = _report(tmp_path, 75e-9, "TEST_75_NF")
    recommended = search.recommended_candidate
    assert recommended is not None

    payload = build_structured_report(report)["capacitor"]["llc_resonant"]
    summary = build_capacitor_summary_text(report)
    pf_summary = build_capacitor_pf_side_summary(report, "llc_resonant", Path(search.pareto_png_path))

    assert payload["status"] == "pass"
    assert payload["constraint"]["capacitance_error_limit"]["value"] == pytest.approx(10.0)
    assert payload["recommended"]["design_id"] == recommended.design_id
    assert payload["recommended"]["capacitance_error"]["value"] == pytest.approx(
        recommended.capacitance_error_percent
    )
    assert recommended.design_id in summary
    assert recommended.design_id in pf_summary
    assert "constraint status: pass" in summary


def test_llc_cr_no_recommendation_is_explicit_in_structured_report_and_gui(tmp_path: Path) -> None:
    report, search = _report(tmp_path, 90e-9, "TEST_OVER_LIMIT")
    assert search.recommended_candidate is None

    payload = build_structured_report(report)["capacitor"]["llc_resonant"]
    summary = build_capacitor_summary_text(report)
    pf_summary = build_capacitor_pf_side_summary(report, "llc_resonant")

    assert payload["status"] == "fail"
    assert payload["recommended"]["design_id"] is None
    assert payload["rejection_counts"]["capacitance_error"] > 0
    assert payload["near_miss"]["closest_absolute_error"]["rejection_reason"] == "capacitance_error"
    assert "recommended: none" in summary
    assert "No recommendation:" in pf_summary
    assert "within +/-10% Cr target" in summary
