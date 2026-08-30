from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path

import pytest

from pe_claw_gui.engines.capacitors.llc_resonant import (
    CAPACITANCE_ERROR_LIMIT_PERCENT,
    CAPACITANCE_WARNING_PERCENT,
    search_llc_resonant_capacitor_banks,
)
from pe_claw_gui.libraries.capacitors import list_c44p_t_capacitors
from pe_claw_gui.models.capacitor import CapacitorCandidate, LlcResonantCapacitorDesignRequest


TARGET_F = 74.37482607930382


def _request(target_f: float = TARGET_F) -> LlcResonantCapacitorDesignRequest:
    return LlcResonantCapacitorDesignRequest(
        cr_target_f=target_f,
        cr_target_nF=target_f * 1e9,
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


def _candidate(capacitance_f: float, *, name: str = "TEST") -> CapacitorCandidate:
    base = next(item for item in list_c44p_t_capacitors() if item.part_number == "C44PRGR6100T99K")
    return replace(
        base,
        part_number=name,
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


def _search(tmp_path: Path, *candidates: CapacitorCandidate, request=None):
    return search_llc_resonant_capacitor_banks(
        request or _request(),
        tuple(candidates),
        output_dir=tmp_path,
    )


def test_llc_cr_error_boundary_uses_ten_percent_hard_limit(tmp_path: Path) -> None:
    assert CAPACITANCE_ERROR_LIMIT_PERCENT == pytest.approx(10.0)
    assert CAPACITANCE_WARNING_PERCENT == pytest.approx(10.0)

    for error_percent, should_pass in ((9.99, True), (10.0, True), (10.01, False)):
        target = 100.0
        capacitance = 110.0 if error_percent == 10.0 else target * (1.0 + error_percent / 100.0)
        candidate = _candidate(capacitance, name=f"TEST_{error_percent}")
        result = _search(tmp_path / str(error_percent), candidate, request=_request(target))
        selected = [entry for entry in result.candidates if entry.parallel_count == 1][0]
        assert (selected.rejection_reason == "") is should_pass
        feasible_ids = {entry.design_id for entry in result.feasible_candidates}
        assert (selected.design_id in feasible_ids) is should_pass


def test_llc_cr_75_nf_is_preferred_over_80_nf_for_74_3748_nf_target(tmp_path: Path) -> None:
    result = _search(
        tmp_path,
        _candidate(75.0, name="TEST_75_NF"),
        _candidate(80.0, name="TEST_80_NF"),
    )

    by_part = {entry.part_number: entry for entry in result.candidates if entry.parallel_count == 1}
    assert by_part["TEST_75_NF"].capacitance_error_percent == pytest.approx(0.84093, abs=1e-3)
    assert by_part["TEST_80_NF"].capacitance_error_percent == pytest.approx(7.56328, abs=1e-3)
    assert result.recommended_candidate is not None
    assert result.recommended_candidate.part_number == "TEST_75_NF"
    assert abs(result.recommended_candidate.capacitance_error_percent) <= 10.0


def test_llc_cr_only_over_limit_candidates_have_no_recommendation(tmp_path: Path) -> None:
    result = _search(tmp_path, _candidate(90.0, name="TEST_OVER_LIMIT"))

    assert result.recommended_candidate is None
    assert result.chosen_candidates == []
    assert result.feasible_candidates == []
    assert result.nearest_upper_bank is not None
    assert result.nearest_upper_bank.rejection_reason == "capacitance_error"
    assert result.near_miss_csv_path


def test_llc_cr_csvs_expose_constraint_and_recommendation_state(tmp_path: Path) -> None:
    result = _search(
        tmp_path,
        _candidate(75.0, name="TEST_75_NF"),
        _candidate(90.0, name="TEST_OVER_LIMIT"),
    )

    with Path(result.feasible_csv_path).open(newline="", encoding="utf-8") as handle:
        feasible_rows = list(csv.DictReader(handle))
    with Path(result.near_miss_csv_path).open(newline="", encoding="utf-8") as handle:
        near_miss_rows = list(csv.DictReader(handle))

    assert feasible_rows
    assert all(abs(float(row["capacitance_error_percent"])) <= 10.0 for row in feasible_rows)
    assert any(row["recommended_flag"] == "True" for row in feasible_rows)
    assert any(
        row["part_number"] == "TEST_OVER_LIMIT"
        and row["rejection_reason"] == "capacitance_error"
        for row in near_miss_rows
    )
    assert result.coverage_summary["capacitance_error_limit_percent"] == pytest.approx(10.0)
    assert result.coverage_summary["within_error_limit_count"] == len(
        [entry for entry in result.candidates if abs(entry.capacitance_error_percent) <= 10.0]
    )
