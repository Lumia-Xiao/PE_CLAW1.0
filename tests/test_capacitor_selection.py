from __future__ import annotations

import math
import sys
import csv
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.engines.capacitors.selection import (
    NON_DC_LINK_FILTER_NOTE,
    evaluate_capacitor_bank,
    evaluate_capacitor_bank_from_stats,
    prepare_capacitor_waveform_stats,
    select_capacitor_bank,
)
from pe_claw_gui.engines.capacitors.artifacts import write_capacitor_pareto_artifacts
from pe_claw_gui.engines.capacitors.pareto import apply_representative_labels, extract_pareto_front
from pe_claw_gui.libraries.capacitors import (
    list_c44p_t_capacitors,
    list_c4ak_capacitors,
    list_c4as_capacitors,
    get_b25654a_001_capacitors,
    get_b3267_d_g_j_t_capacitors,
    get_b3271xp_capacitors,
    get_b32714h_718h_capacitors,
    get_b3272agt_capacitors,
    get_b3277_d_e_g_j_t_capacitors,
    get_b3277h_capacitors,
    get_b3277m_capacitors,
    get_b3277p_capacitors,
    get_b3277xyz_capacitors,
    list_jianghai_capacitors,
    list_registered_capacitors,
)
from pe_claw_gui.models.capacitor import CapacitorSizingRequest


KEMET_YAGEO_NON_DC_LINK_SERIES = {
    "MDC",
    "R76H",
    "R71H",
    "F863H X2 310 125C",
    "R76",
    "R71",
    "R73",
    "SMR",
    "F862 X2 310",
    "R60",
    "F863 X2 310",
    "A50 AXIAL",
    "C44P-R",
    "C28",
    "R66",
    "RSB",
    "C4BT",
    "C4BS",
    "C44A",
}


def _waveform(amplitude_a: float = 10.0, points: int = 401) -> tuple[list[float], list[float]]:
    period_s = 1.0 / 10_000.0
    time_s = [index * period_s / (points - 1) for index in range(points)]
    current_a = [amplitude_a * math.sin(2.0 * math.pi * 10_000.0 * time) for time in time_s]
    return time_s, current_a


def _request(
    *,
    dc_voltage_v: float = 600.0,
    ripple_ratio_percent: float = 5.0,
    amplitude_a: float = 10.0,
    max_parallel_count: int = 6,
) -> CapacitorSizingRequest:
    time_s, current_a = _waveform(amplitude_a=amplitude_a)
    return CapacitorSizingRequest(
        side="output",
        dc_voltage_v=dc_voltage_v,
        ripple_ratio_percent=ripple_ratio_percent,
        current_time_s=time_s,
        current_waveform_a=current_a,
        switching_frequency_hz=10_000.0,
        ambient_temp_c=25.0,
        max_parallel_count=max_parallel_count,
    )


def test_larger_capacitance_reduces_capacitive_ripple() -> None:
    request = _request()
    capacitors = list_c44p_t_capacitors()
    small = next(item for item in capacitors if item.part_number == "C44PRGR5220T64K")
    large = next(item for item in capacitors if item.part_number == "C44PRGR6100T99K")

    small_entry = evaluate_capacitor_bank(request, small, parallel_count=1)
    large_entry = evaluate_capacitor_bank(request, large, parallel_count=1)

    assert large.capacitance_f > small.capacitance_f
    assert large_entry.ripple_capacitive_pp_v < small_entry.ripple_capacitive_pp_v


def test_parallel_count_increases_ceq_and_reduces_rs_eq() -> None:
    request = _request()
    candidate = next(item for item in list_c44p_t_capacitors() if item.part_number == "C44PRGR6100T99K")

    single = evaluate_capacitor_bank(request, candidate, parallel_count=1)
    parallel = evaluate_capacitor_bank(request, candidate, parallel_count=4)

    assert parallel.equivalent_capacitance_f == pytest.approx(4.0 * single.equivalent_capacitance_f)
    assert parallel.equivalent_rs_ohm == pytest.approx(single.equivalent_rs_ohm / 4.0)


def test_series_parallel_bank_equivalent_values_are_reported() -> None:
    request = _request(dc_voltage_v=700.0, ripple_ratio_percent=10.0)
    candidate = next(item for item in list_c44p_t_capacitors() if item.part_number == "C44PRGR6100T99K")

    entry = evaluate_capacitor_bank(request, candidate, parallel_count=3, series_count=2)

    assert entry.series_count == 2
    assert entry.parallel_count == 3
    assert entry.total_capacitor_count == 6
    assert entry.bank_voltage_rating_dc_v == pytest.approx(2.0 * candidate.voltage_rating_dc_v)
    assert entry.equivalent_capacitance_f == pytest.approx(candidate.capacitance_f * 3.0 / 2.0)
    assert entry.equivalent_rs_ohm == pytest.approx(candidate.rs_ohm * 2.0 / 3.0)
    assert entry.equivalent_esl_h == pytest.approx(candidate.esl_h * 2.0 / 3.0)
    assert entry.capacitor_current_rms_per_cap_a == pytest.approx(entry.capacitor_current_rms_total_a / 3.0)
    assert entry.p_total_per_cap_w == pytest.approx(entry.p_total_w / 6.0)


def test_excessive_dc_voltage_rejects_candidate() -> None:
    request = _request(dc_voltage_v=1500.0)
    candidate = next(item for item in list_c44p_t_capacitors() if item.part_number == "C44PRGR6100T99K")

    entry = evaluate_capacitor_bank(request, candidate, parallel_count=1)

    assert not entry.feasible
    assert any("DC voltage rating" in reason for reason in entry.rejection_reasons)


def test_excessive_irms_rejects_candidate() -> None:
    request = _request(amplitude_a=500.0, ripple_ratio_percent=100.0, max_parallel_count=1)
    candidate = next(item for item in list_c44p_t_capacitors() if item.part_number == "C44PRGR6100T99K")

    entry = evaluate_capacitor_bank(request, candidate, parallel_count=1)

    assert not entry.feasible
    assert any("RMS current" in reason for reason in entry.rejection_reasons)


def test_excessive_ripple_rejects_candidate() -> None:
    request = _request(ripple_ratio_percent=0.0001)
    candidate = next(item for item in list_c44p_t_capacitors() if item.part_number == "C44PRGR6100T99K")

    entry = evaluate_capacitor_bank(request, candidate, parallel_count=1)

    assert not entry.feasible
    assert any("Ripple" in reason for reason in entry.rejection_reasons)


def test_feasible_candidate_is_selected_for_synthetic_waveform() -> None:
    request = _request(dc_voltage_v=400.0, ripple_ratio_percent=20.0, amplitude_a=5.0, max_parallel_count=8)

    result = select_capacitor_bank(request, list_c44p_t_capacitors())

    assert result.recommended is not None
    assert result.recommended.feasible
    assert result.recommended_policy_name == "minimum-parallel margin-aware recommendation"
    assert result.minimum_feasible_parallel_count is not None
    assert result.recommended_parallel_count == result.recommended.parallel_count
    assert result.recommended_ripple_utilization is not None
    assert "minimum-parallel margin-aware recommendation" in result.recommended_selection_reason
    assert result.min_volume is not None
    assert result.min_loss is not None
    assert result.pareto_front
    assert result.feasible_candidates
    assert all(entry.parallel_count <= 5 for entry in result.feasible_candidates)
    assert result.top_candidates


def test_registered_selection_evaluates_c4ak_with_other_series() -> None:
    request = _request(dc_voltage_v=400.0, ripple_ratio_percent=50.0, amplitude_a=3.0)

    result = select_capacitor_bank(request, list_registered_capacitors())

    assert result.diagnostics["registered_candidates"] == 32910
    assert result.diagnostics["after_application_filter"] == 23791
    assert any(entry.candidate.series == "C4AK" for entry in result.feasible_candidates)
    assert any(entry.candidate.series == "C4AU" for entry in result.feasible_candidates)
    assert any(entry.candidate.series == "B3267*D/G/J/T" for entry in result.feasible_candidates)
    assert any(entry.candidate.series == "B3271*P" for entry in result.feasible_candidates)
    assert any(entry.candidate.series == "B32714H ... B32718H" for entry in result.feasible_candidates)
    assert any(entry.candidate.series == "B3272*A/G/T" for entry in result.feasible_candidates)
    assert any(entry.candidate.series == "B3277*D/E/G/J/T" for entry in result.feasible_candidates)
    assert any(entry.candidate.series == "B3277*H" for entry in result.feasible_candidates)
    assert any(entry.candidate.series == "B3277*M" for entry in result.feasible_candidates)
    assert any(entry.candidate.series == "B3277*P" for entry in result.feasible_candidates)
    assert any(entry.candidate.series == "B3277*X/Y/Z" for entry in result.feasible_candidates)
    assert any(entry.candidate.series.startswith("CBB 13") for entry in result.feasible_candidates)
    assert all(
        entry.candidate.application_category in {"dc_link", "industrial_smps_dc_link"}
        for entry in result.feasible_candidates
    )
    assert any(NON_DC_LINK_FILTER_NOTE in note for note in result.notes)


def test_default_dc_link_selection_can_see_tdk_b3271xp_candidates() -> None:
    request = _request(dc_voltage_v=400.0, ripple_ratio_percent=100.0, amplitude_a=1.0, max_parallel_count=8)

    result = select_capacitor_bank(request, get_b3271xp_capacitors())

    assert result.recommended is not None
    assert result.feasible_candidates
    assert result.diagnostics["after_application_filter"] == 218
    assert {entry.candidate.manufacturer for entry in result.feasible_candidates} == {"TDK"}
    assert {entry.candidate.series for entry in result.feasible_candidates} == {"B3271*P"}
    assert all(entry.candidate.application_category == "dc_link" for entry in result.feasible_candidates)
    assert all(entry.candidate.package_shape == "rectangular_box" for entry in result.feasible_candidates)


def test_default_dc_link_selection_can_see_tdk_b3272agt_candidates() -> None:
    request = _request(dc_voltage_v=400.0, ripple_ratio_percent=100.0, amplitude_a=1.0, max_parallel_count=8)

    result = select_capacitor_bank(request, get_b3272agt_capacitors())

    assert result.recommended is not None
    assert result.feasible_candidates
    assert result.diagnostics["after_application_filter"] == 90
    assert {entry.candidate.manufacturer for entry in result.feasible_candidates} == {"TDK"}
    assert {entry.candidate.series for entry in result.feasible_candidates} == {"B3272*A/G/T"}
    assert all(entry.candidate.application_category == "dc_link" for entry in result.feasible_candidates)
    assert all(entry.candidate.package_shape == "rectangular_box" for entry in result.feasible_candidates)


def test_default_dc_link_selection_can_see_tdk_b3277p_candidates() -> None:
    request = _request(dc_voltage_v=400.0, ripple_ratio_percent=100.0, amplitude_a=1.0, max_parallel_count=8)

    result = select_capacitor_bank(request, get_b3277p_capacitors())

    assert result.recommended is not None
    assert result.feasible_candidates
    assert result.diagnostics["after_application_filter"] == 44
    assert {entry.candidate.manufacturer for entry in result.feasible_candidates} == {"TDK"}
    assert {entry.candidate.series for entry in result.feasible_candidates} == {"B3277*P"}
    assert all(entry.candidate.application_category == "dc_link" for entry in result.feasible_candidates)
    assert all(entry.candidate.package_shape == "rectangular_box" for entry in result.feasible_candidates)


@pytest.mark.parametrize(
    ("library", "expected_count", "series"),
    [
        (get_b3267_d_g_j_t_capacitors, 115, "B3267*D/G/J/T"),
        (get_b32714h_718h_capacitors, 236, "B32714H ... B32718H"),
        (get_b25654a_001_capacitors, 11, "B25654A*001 xEVCap Lead Wire"),
        (get_b3277m_capacitors, 218, "B3277*M"),
        (get_b3277xyz_capacitors, 206, "B3277*X/Y/Z"),
        (get_b3277_d_e_g_j_t_capacitors, 137, "B3277*D/E/G/J/T"),
        (get_b3277h_capacitors, 218, "B3277*H"),
    ],
)
def test_default_dc_link_selection_can_see_new_tdk_candidates(library, expected_count: int, series: str) -> None:
    request = _request(dc_voltage_v=300.0, ripple_ratio_percent=100.0, amplitude_a=1.0, max_parallel_count=8)

    result = select_capacitor_bank(request, library())

    assert result.diagnostics["after_application_filter"] == expected_count
    if series == "B25654A*001 xEVCap Lead Wire":
        assert result.diagnostics["registered_candidates"] == expected_count
        assert result.diagnostics["after_rough_prefilter"] == 0
        assert result.feasible_candidates == []
        assert any("No feasible output capacitor candidate" in warning for warning in result.warnings)
    else:
        assert result.recommended is not None
        assert result.feasible_candidates
        assert {entry.candidate.manufacturer for entry in result.feasible_candidates} == {"TDK"}
        assert {entry.candidate.series for entry in result.feasible_candidates} == {series}
        assert all(entry.candidate.application_category == "dc_link" for entry in result.feasible_candidates)
        assert all(entry.candidate.package_shape == "rectangular_box" for entry in result.feasible_candidates)


def test_new_tdk_csv_metadata_preserves_terminal_and_special_flags(tmp_path: Path) -> None:
    request = _request(dc_voltage_v=300.0, ripple_ratio_percent=1_000.0, amplitude_a=0.1, max_parallel_count=1)

    result = select_capacitor_bank(request, get_b3267_d_g_j_t_capacitors())
    result = write_capacitor_pareto_artifacts(result, tmp_path)
    rows = list(csv.DictReader((tmp_path / "output_capacitor_feasible_candidates.csv").open(newline="", encoding="utf-8")))

    assert rows
    assert any(row["part_number"] == "B32678J4606K000" and row["terminal_count"] == "12" for row in rows)
    assert any(row["part_number"] == "B32678T8705K000" and row["dual_use_restricted"] == "True" for row in rows)
    assert all(row["terminal_type"] == "radial_tinned_wire" for row in rows if row["series"] == "B3267*D/G/J/T")
    assert all(row["application_category"] == "dc_link" for row in rows if row["series"] == "B3267*D/G/J/T")


def test_new_non_dc_link_series_are_registered_but_excluded_by_default() -> None:
    request = _request(dc_voltage_v=300.0, ripple_ratio_percent=100.0, amplitude_a=1.0)
    candidates = tuple(
        candidate
        for candidate in list_registered_capacitors()
        if candidate.manufacturer == "KEMET / YAGEO" and candidate.series in KEMET_YAGEO_NON_DC_LINK_SERIES
    )

    result = select_capacitor_bank(request, candidates)

    assert {candidate.series for candidate in candidates} == KEMET_YAGEO_NON_DC_LINK_SERIES
    assert result.diagnostics["after_application_filter"] == 0
    assert result.diagnostics["detailed_bank_evaluations"] == 0
    assert any(NON_DC_LINK_FILTER_NOTE in note for note in result.notes)


def test_include_non_dc_link_capacitors_includes_new_categories() -> None:
    request = replace(_request(dc_voltage_v=300.0, ripple_ratio_percent=100.0, amplitude_a=1.0), include_non_dc_link_capacitors=True)
    candidates = tuple(
        candidate
        for candidate in list_registered_capacitors()
        if candidate.manufacturer == "KEMET / YAGEO" and candidate.series in KEMET_YAGEO_NON_DC_LINK_SERIES
    )

    result = select_capacitor_bank(request, candidates)

    assert result.diagnostics["after_application_filter"] == len(candidates)


def test_c4ak_selection_entry_preserves_library_metadata() -> None:
    request = _request(dc_voltage_v=400.0, ripple_ratio_percent=50.0, amplitude_a=3.0)
    candidate = next(item for item in list_c4ak_capacitors() if item.part_number == "C4AKGLU4400A31J")

    entry = evaluate_capacitor_bank(request, candidate, parallel_count=2)

    assert entry.candidate.manufacturer == "KEMET / YAGEO"
    assert entry.candidate.series == "C4AK"
    assert entry.candidate.package_shape == "rectangular_box"
    assert entry.candidate.terminal_count == 2
    assert entry.candidate.low_profile is True


def test_non_dc_link_recommendation_emits_application_warning() -> None:
    request = replace(_request(dc_voltage_v=300.0, ripple_ratio_percent=100.0, amplitude_a=1.0), include_non_dc_link_capacitors=True)

    result = select_capacitor_bank(request, tuple(list_c4as_capacitors()[:4]))

    assert result.recommended is not None
    assert result.recommended.candidate.application_category == "snubber_pulse"
    assert any("application_category=snubber_pulse" in warning for warning in result.warnings)


def test_default_selection_excludes_non_dc_link_categories_from_detailed_evaluation() -> None:
    request = _request(dc_voltage_v=300.0, ripple_ratio_percent=100.0, amplitude_a=1.0)

    result = select_capacitor_bank(request, tuple(list_c4as_capacitors()[:4]))

    assert result.recommended is None
    assert result.diagnostics["after_application_filter"] == 0
    assert result.diagnostics["detailed_bank_evaluations"] == 0
    assert any(NON_DC_LINK_FILTER_NOTE in note for note in result.notes)


def test_include_non_dc_link_capacitors_enables_non_dc_link_evaluation() -> None:
    request = replace(_request(dc_voltage_v=300.0, ripple_ratio_percent=100.0, amplitude_a=1.0), include_non_dc_link_capacitors=True)

    result = select_capacitor_bank(request, tuple(list_c4as_capacitors()[:4]))

    assert result.recommended is not None
    assert result.diagnostics["after_application_filter"] == 4
    assert result.diagnostics["detailed_bank_evaluations"] > 0
    assert not any(NON_DC_LINK_FILTER_NOTE in note for note in result.notes)


def test_evaluate_from_prepared_stats_matches_public_wrapper() -> None:
    request = _request(dc_voltage_v=400.0, ripple_ratio_percent=50.0, amplitude_a=3.0)
    candidate = next(item for item in list_c4ak_capacitors() if item.part_number == "C4AKGLU4400A31J")
    stats = prepare_capacitor_waveform_stats(request)

    wrapped = evaluate_capacitor_bank(request, candidate, parallel_count=2)
    from_stats = evaluate_capacitor_bank_from_stats(request, stats, candidate, parallel_count=2)

    assert from_stats == wrapped


def test_allowed_capacitor_technology_filters_candidates() -> None:
    request = replace(_request(dc_voltage_v=300.0, ripple_ratio_percent=100.0, amplitude_a=1.0), allowed_capacitor_technologies=("film",))
    film = replace(list_c44p_t_capacitors()[0], part_number="FILM", capacitor_technology="film")
    electrolytic = replace(list_c44p_t_capacitors()[1], part_number="ELECTRO", capacitor_technology="aluminum_electrolytic")

    result = select_capacitor_bank(request, (film, electrolytic))

    assert result.diagnostics["after_application_filter"] == 2
    assert result.diagnostics["after_technology_filter"] == 1
    assert all(entry.candidate.part_number == "FILM" for entry in result.feasible_candidates)
    assert any("after technology filter=1" in note for note in result.notes)


def test_capacitance_min_rejects_under_sized_bank() -> None:
    candidate = replace(
        list_c44p_t_capacitors()[0],
        capacitance_f=100e-6,
        voltage_rating_dc_v=1000.0,
        irms_rating_a=100.0,
        pmax_w=100.0,
        rs_ohm=1e-6,
        dvdt_v_per_us=1000.0,
    )
    request = replace(_request(dc_voltage_v=300.0, ripple_ratio_percent=1000.0, amplitude_a=0.1), capacitance_min_f=250e-6)

    single = evaluate_capacitor_bank(request, candidate, parallel_count=1)
    triple = evaluate_capacitor_bank(request, candidate, parallel_count=3)

    assert not single.feasible
    assert any("Equivalent capacitance" in reason for reason in single.rejection_reasons)
    assert triple.feasible


def test_request_max_parallel_count_limits_evaluated_entries() -> None:
    request = _request(dc_voltage_v=400.0, ripple_ratio_percent=100.0, amplitude_a=1.0, max_parallel_count=3)

    result = select_capacitor_bank(request, tuple(list_c4ak_capacitors()[:8]))

    assert result.diagnostics["max_parallel_count"] == 3
    assert all(entry.parallel_count <= 3 for entry in result.feasible_candidates)


def test_default_max_parallel_count_remains_five() -> None:
    request = _request(dc_voltage_v=400.0, ripple_ratio_percent=100.0, amplitude_a=1.0)

    result = select_capacitor_bank(request, tuple(list_c4ak_capacitors()[:8]))

    assert result.diagnostics["max_parallel_count"] == 5
    assert all(entry.parallel_count <= 5 for entry in result.feasible_candidates)


def test_optimized_selection_matches_brute_force_representatives_on_small_fixture() -> None:
    request = _request(dc_voltage_v=300.0, ripple_ratio_percent=100.0, amplitude_a=1.0, max_parallel_count=5)
    candidates = tuple(list_c44p_t_capacitors()[:10])

    optimized = select_capacitor_bank(request, candidates)
    brute_entries = [
        evaluate_capacitor_bank(request, candidate, parallel_count)
        for candidate in candidates
        for parallel_count in range(1, 6)
    ]
    brute_feasible = [entry for entry in brute_entries if entry.feasible]
    _, _, brute_min_volume, brute_min_loss, brute_compromise, _ = apply_representative_labels(
        brute_feasible,
        extract_pareto_front(brute_feasible),
    )

    assert {(entry.candidate.part_number, entry.series_count, entry.parallel_count) for entry in optimized.feasible_candidates} == {
        (entry.candidate.part_number, entry.series_count, entry.parallel_count) for entry in brute_feasible
    }
    assert (optimized.min_volume.candidate.part_number, optimized.min_volume.parallel_count) == (
        brute_min_volume.candidate.part_number,
        brute_min_volume.parallel_count,
    )
    assert (optimized.min_loss.candidate.part_number, optimized.min_loss.parallel_count) == (
        brute_min_loss.candidate.part_number,
        brute_min_loss.parallel_count,
    )
    assert (optimized.compromise.candidate.part_number, optimized.compromise.parallel_count) == (
        brute_compromise.candidate.part_number,
        brute_compromise.parallel_count,
    )


def test_capacitor_pareto_csv_includes_series_and_package_metadata(tmp_path: Path) -> None:
    request = _request(dc_voltage_v=300.0, ripple_ratio_percent=50.0, amplitude_a=3.0)
    result = select_capacitor_bank(request, tuple(list_c4ak_capacitors()[:3]))

    result = write_capacitor_pareto_artifacts(result, tmp_path)

    feasible_csv = tmp_path / "output_capacitor_feasible_candidates.csv"
    rows = list(csv.DictReader(feasible_csv.open(newline="", encoding="utf-8")))
    assert rows
    assert {
        "manufacturer",
        "series",
        "application_category",
        "capacitor_technology",
        "loss_model_type",
        "capacitor_type",
        "package_shape",
        "mounting_style",
        "construction",
        "dielectric",
        "terminal_count",
        "terminal_type",
        "low_profile",
        "available_upon_request",
        "dual_use_restricted",
        "safety_class",
        "esr_basis",
        "loss_basis",
        "thermal_basis",
        "irms_rating_basis",
        "not_recommended_for_new_design",
        "order_code_template",
        "is_order_code_template",
        "order_code_note",
        "order_code_placeholders",
        "availability_status",
        "rs_ohm",
        "esr_value_type",
        "esr_temperature_c",
        "irms_frequency_hz",
        "tan_delta",
        "tan_delta_source",
        "series_count",
        "parallel_count",
        "total_capacitor_count",
        "bank_voltage_rating_dc_v",
        "series_parallel_label",
    }.issubset(rows[0].keys())
    assert any(
        row["manufacturer"] == "KEMET / YAGEO"
        and row["series"] == "C4AK"
        and row["application_category"] == "dc_link"
        and row["package_shape"] == "rectangular_box"
        for row in rows
    )
    recommended_rows = [row for row in rows if row["recommended_flag"] == "True"]
    assert result.diagnostics["artifact_feasible_row_count"] == len(rows)
    assert result.diagnostics["artifact_row_count"] == result.diagnostics["artifact_feasible_row_count"] + result.diagnostics["artifact_pareto_row_count"]
    assert recommended_rows
    assert any(
        row["part_number"] == result.recommended.candidate.part_number
        and int(row["series_count"]) == result.recommended.series_count
        and int(row["parallel_count"]) == result.recommended.parallel_count
        and int(row["total_capacitor_count"]) == result.recommended.total_capacitor_count
        for row in recommended_rows
    )


def test_jianghai_template_metadata_is_written_to_capacitor_csv(tmp_path: Path) -> None:
    base = next(candidate for candidate in list_jianghai_capacitors() if len(candidate.order_code_placeholders) >= 3)
    template_candidate = replace(
        base,
        capacitance_f=500e-6,
        rs_ohm=0.001,
        irms_rating_a=100.0,
        pmax_w=100.0,
        dvdt_v_per_us=1000.0,
    )
    request = _request(dc_voltage_v=300.0, ripple_ratio_percent=50.0, amplitude_a=1.0)
    result = select_capacitor_bank(request, (replace(template_candidate, capacitance_f=500e-6, rs_ohm=0.001),))

    result = write_capacitor_pareto_artifacts(result, tmp_path)

    rows = list(csv.DictReader((tmp_path / "output_capacitor_feasible_candidates.csv").open(newline="", encoding="utf-8")))
    assert rows
    row = rows[0]
    assert row["part_number"] == template_candidate.part_number
    assert row["order_code_template"] == template_candidate.part_number
    assert row["is_order_code_template"] == "True"
    assert row["order_code_placeholders"] == "◊ | ∆ | ##"
    assert "Jianghai order code contains configurable placeholders" in row["order_code_note"]
