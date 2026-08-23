from __future__ import annotations

import sys
from pathlib import Path
import importlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.engines.capacitors.selection import evaluate_capacitor_bank
from pe_claw_gui.libraries.capacitors import (
    capacitor_library_coverage_counts,
    clear_registered_capacitor_cache,
    count_registered_capacitor_candidates,
    list_registered_capacitors,
)
from pe_claw_gui.models.capacitor import CapacitorSizingRequest


def test_registered_capacitors_include_all_series_without_duplicates() -> None:
    candidates = list_registered_capacitors()
    part_numbers = [candidate.part_number for candidate in candidates]

    assert len(candidates) == 32910
    assert len(part_numbers) == len(set(part_numbers))
    assert {
        "WIMA DC-LINK MKP 4",
        "WIMA DC-LINK MKP 6",
        "WIMA DC-LINK HC",
        "WIMA SMD-PET",
        "WIMA SMD-PPS",
        "WIMA MKP 10",
        "WIMA FKP 1",
        "MPB",
        "MPK",
        "MPN",
        "MPH",
        "PCK",
        "MPT",
        "MPY",
        "EZPE",
        "EZPV",
        "EZPV-D",
        "EZPR",
        "Type1",
        "CBB 131 DL",
        "CBB 131S DY",
        "CBB 132 DH",
        "CBB 136 DP",
        "CBB 138 DS",
    }.issubset({candidate.series for candidate in candidates})
    assert {
        "C44P-T",
        "C4AQ-P",
        "C4AK",
        "C4AU",
        "C4AQ-M",
        "C4AS",
        "C4AT",
        "MDC",
        "R76H",
        "R75H",
        "R71H",
        "F863H X2 310 125C",
        "R76",
        "R71",
        "R73",
        "SMR",
        "F862 X2 310",
        "R75",
        "R60",
        "F863 X2 310",
        "A50 AXIAL",
        "C44U-T",
        "C44U-M",
        "C44P-R",
        "C28",
        "R66",
        "RSB",
        "C4BT",
        "C4BS",
        "C44U",
        "C44A",
        "C4DE",
        "C4AQ",
        "B25654A*001 xEVCap Lead Wire",
        "B3267*D/G/J/T",
        "B3271*P",
        "B32714H ... B32718H",
        "B3272*A/G/T",
        "B3277*D/E/G/J/T",
        "B3277*H",
        "B3277*M",
        "B3277*P",
        "B3277*X/Y/Z",
        "B41456/B41458",
    }.issubset({candidate.series for candidate in candidates})
    assert {candidate.manufacturer for candidate in candidates} == {
        "KEMET / YAGEO",
        "TDK",
        "WIMA",
        "Rubycon",
        "Panasonic",
        "Jianghai",
        "Lelon",
        "Nippon Chemi-Con",
    }


def test_registered_capacitors_are_cached_with_stable_count() -> None:
    clear_registered_capacitor_cache()
    first = list_registered_capacitors()
    second = list_registered_capacitors()

    assert first is second
    assert len(first) == 32910
    assert len(second) == 32910
    assert count_registered_capacitor_candidates() == 32910


def test_capacitor_library_coverage_counts_are_deterministic() -> None:
    coverage = capacitor_library_coverage_counts()

    assert coverage["total"] == 32910
    assert coverage["by_manufacturer"] == {
        "Jianghai": 555,
        "KEMET / YAGEO": 5690,
        "Lelon": 2986,
        "Nippon Chemi-Con": 10105,
        "Panasonic": 423,
        "Rubycon": 6975,
        "TDK": 3307,
        "WIMA": 2869,
    }
    assert coverage["by_series"]["WIMA DC-LINK MKP 4"] == 316
    assert coverage["by_series"]["WIMA DC-LINK MKP 6"] == 90
    assert coverage["by_series"]["WIMA DC-LINK HC"] == 18
    assert coverage["by_application_category"]["dc_link"] == 5099
    assert coverage["by_application_category"]["dc_link_candidate"] == 247
    assert coverage["by_application_category"]["dc_link_legacy"] == 1
    assert coverage["by_application_category"]["high_ripple_film"] == 67
    assert coverage["by_application_category"]["smd_general"] == 254
    assert coverage["by_package_shape"]["rectangular_box"] == 10278
    assert coverage["by_application_category"]["industrial_smps_dc_link"] == 18692
    assert coverage["by_application_category"]["board_level_electrolytic"] == 2892
    assert coverage["by_package_shape"]["cylindrical_can"] == 22502
    assert coverage["by_package_shape"]["cylindrical_plastic_case"] == 31
    assert coverage["by_terminal_count"]["2-pin"] == 30572
    assert coverage["by_terminal_count"]["4-pin"] == 2114
    assert coverage["by_terminal_type"]["tinned_wire"] == 2548
    assert coverage["by_terminal_type"]["tinned_plates"] == 519
    assert coverage["by_terminal_type"]["snap_in_pin"] == 10357
    assert coverage["by_terminal_type"]["radial_leads"] == 5419
    assert coverage["by_terminal_type"]["smd_can_terminal"] == 1302
    assert coverage["by_mounting_style"]["smd"] == 254
    assert coverage["by_mounting_style"]["snap_in_pcb"] == 6570
    assert coverage["by_mounting_style"]["snap_in_can"] == 3787
    assert coverage["by_mounting_style"]["radial_leaded_can"] == 5419
    assert coverage["by_mounting_style"]["smd_can"] == 1302
    assert coverage["by_dielectric"]["PP"] == 2174
    assert coverage["by_dielectric"]["polypropylene"] == 1274
    assert coverage["by_dielectric"]["aluminum_oxide"] == 21584
    assert all(candidate.application_category for candidate in list_registered_capacitors())
    assert not [candidate for candidate in list_registered_capacitors() if candidate.application_category == "unspecified"]


def test_capacitor_application_categories_are_explicit_and_series_appropriate() -> None:
    candidates = list_registered_capacitors()
    by_series = {
        series: {candidate.application_category for candidate in candidates if candidate.series == series}
        for series in {candidate.series for candidate in candidates}
    }
    by_manufacturer_series = {
        (candidate.manufacturer, candidate.series): {
            item.application_category
            for item in candidates
            if item.manufacturer == candidate.manufacturer and item.series == candidate.series
        }
        for candidate in candidates
    }

    assert by_series["C44P-T"] == {"dc_link"}
    assert by_series["C4AQ-P"] == {"dc_link"}
    assert by_series["C4AK"] == {"dc_link"}
    assert by_series["C4AS"] == {"snubber_pulse"}
    assert by_series["C4AT"] == {"switching"}
    assert by_series["F862 X2 310"] == {"emi_x2"}
    assert by_series["F863 X2 310"] == {"emi_x2"}
    assert by_series["F863H X2 310 125C"] == {"emi_x2"}
    assert by_series["R71"] == {"ac_filter"}
    assert by_series["R75"] == {"dc_link"}
    assert by_series["R76"] == {"snubber_pulse"}
    assert by_series["R73"] == {"snubber_pulse"}
    assert by_series["R60"] == {"general_film"}
    assert by_manufacturer_series[("KEMET / YAGEO", "SMR")] == {"general_film"}
    assert "industrial_smps_dc_link" in by_manufacturer_series[("Nippon Chemi-Con", "SMR")]
    assert by_series["MDC"] == {"general_film"}
    assert by_series["A50 AXIAL"] == {"axial_film"}
    assert by_series["C44U"] == {"dc_link"}
    assert by_series["C44U-M"] == {"dc_link"}
    assert by_series["C44U-T"] == {"dc_link"}
    assert by_series["C44P-R"] == {"ac_filter"}
    assert by_series["C28"] == {"motor_run"}
    assert by_series["R66"] == {"general_film"}
    assert by_series["RSB"] == {"general_film"}
    assert by_series["C4BT"] == {"switching"}
    assert by_series["C4BS"] == {"snubber_pulse"}
    assert by_series["C44A"] == {"snubber_pulse"}
    assert by_series["C4DE"] == {"dc_link"}
    assert by_series["C4AQ"] == {"dc_link"}
    assert by_series["B25654A*001 xEVCap Lead Wire"] == {"dc_link"}
    assert by_series["B3267*D/G/J/T"] == {"dc_link"}
    assert by_series["B3271*P"] == {"dc_link"}
    assert by_series["B32714H ... B32718H"] == {"dc_link"}
    assert by_series["B3272*A/G/T"] == {"dc_link"}
    assert by_series["B3277*D/E/G/J/T"] == {"dc_link"}
    assert by_series["B3277*H"] == {"dc_link"}
    assert by_series["B3277*M"] == {"dc_link"}
    assert by_series["B3277*P"] == {"dc_link"}
    assert by_series["B3277*X/Y/Z"] == {"dc_link"}
    assert by_series["B41456/B41458"] == {"industrial_smps_dc_link"}
    assert by_series["EZPE"] == {"dc_link"}
    assert by_series["EZPV"] == {"dc_link"}
    assert by_series["EZPV-D"] == {"dc_link"}
    assert by_series["EZPR"] == {"dc_link_candidate"}
    assert by_series["Type1"] == {"dc_link_legacy"}
    assert by_series["CBB 131 DL"] == {"dc_link"}
    assert by_series["CBB 131S DY"] == {"dc_link"}
    assert by_series["CBB 132 DH"] == {"dc_link"}
    assert by_series["CBB 136 DP"] == {"dc_link"}
    assert by_series["CBB 138 DS"] == {"dc_link"}


def test_yageo_canonical_imports_work() -> None:
    c44p_t = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.c44p_t")
    c4aq_p = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.c4aq_p")
    c4ak = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.c4ak")
    c4au = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.c4au")
    c4aq_m = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.c4aq_m")
    c4as = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.c4as")
    c4at = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.c4at")
    mdc = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.mdc")
    r76h = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.r76h")
    r75h = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.r75h")
    r71h = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.r71h")
    f863h = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.f863h_x2_310_125c")
    r76 = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.r76")
    r71 = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.r71")
    r73 = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.r73")
    smr = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.smr")
    r862 = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.r862_x2_310")
    r75 = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.r75")
    r60 = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.r60")
    r863 = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.r863_x2_310")
    a50_axial = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.a50_axial")
    c44u_t = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.c44u_t")
    c44u_m = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.c44u_m")
    c44p_r = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.c44p_r")
    c28 = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.c28")
    r66 = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.r66")
    rsb = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.rsb")
    c4bt = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.c4bt")
    c4bs = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.c4bs")
    c44u = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.c44u")
    c44a = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.c44a")
    c4de = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.c4de")
    c4aq = importlib.import_module("pe_claw_gui.libraries.capacitors.yageo.c4aq")
    from pe_claw_gui.libraries.capacitors.yageo import (
        list_a50_axial_capacitors,
        list_c28_capacitors,
        list_c44a_capacitors,
        list_c44p_r_capacitors,
        list_c44p_t_capacitors,
        list_c44u_capacitors,
        list_c44u_m_capacitors,
        list_c44u_t_capacitors,
        list_c4ak_capacitors,
        list_c4aq_capacitors,
        list_c4aq_m_capacitors,
        list_c4aq_p_capacitors,
        list_c4as_capacitors,
        list_c4at_capacitors,
        list_c4au_capacitors,
        list_c4bs_capacitors,
        list_c4bt_capacitors,
        list_c4de_capacitors,
        list_f863h_x2_310_125c_capacitors,
        list_mdc_capacitors,
        list_r60_capacitors,
        list_r66_capacitors,
        list_r71_capacitors,
        list_r71h_capacitors,
        list_r73_capacitors,
        list_r75_capacitors,
        list_r75h_capacitors,
        list_r76_capacitors,
        list_r76h_capacitors,
        list_r862_x2_310_capacitors,
        list_r863_x2_310_capacitors,
        list_rsb_capacitors,
        list_smr_capacitors,
        list_yageo_capacitors,
    )

    assert c44p_t.list_c44p_t_capacitors() == list_c44p_t_capacitors()
    assert c4aq_p.list_c4aq_p_capacitors() == list_c4aq_p_capacitors()
    assert c4ak.list_c4ak_capacitors() == list_c4ak_capacitors()
    assert c4au.list_c4au_capacitors() == list_c4au_capacitors()
    assert c4aq_m.list_c4aq_m_capacitors() == list_c4aq_m_capacitors()
    assert c4as.list_c4as_capacitors() == list_c4as_capacitors()
    assert c4at.list_c4at_capacitors() == list_c4at_capacitors()
    assert mdc.list_mdc_capacitors() == list_mdc_capacitors()
    assert r76h.list_r76h_capacitors() == list_r76h_capacitors()
    assert r75h.list_r75h_capacitors() == list_r75h_capacitors()
    assert r71h.list_r71h_capacitors() == list_r71h_capacitors()
    assert f863h.list_f863h_x2_310_125c_capacitors() == list_f863h_x2_310_125c_capacitors()
    assert r76.list_r76_capacitors() == list_r76_capacitors()
    assert r71.list_r71_capacitors() == list_r71_capacitors()
    assert r73.list_r73_capacitors() == list_r73_capacitors()
    assert smr.list_smr_capacitors() == list_smr_capacitors()
    assert r862.list_r862_x2_310_capacitors() == list_r862_x2_310_capacitors()
    assert r75.list_r75_capacitors() == list_r75_capacitors()
    assert r60.list_r60_capacitors() == list_r60_capacitors()
    assert r863.list_r863_x2_310_capacitors() == list_r863_x2_310_capacitors()
    assert a50_axial.list_a50_axial_capacitors() == list_a50_axial_capacitors()
    assert c44u_t.list_c44u_t_capacitors() == list_c44u_t_capacitors()
    assert c44u_m.list_c44u_m_capacitors() == list_c44u_m_capacitors()
    assert c44p_r.list_c44p_r_capacitors() == list_c44p_r_capacitors()
    assert c28.list_c28_capacitors() == list_c28_capacitors()
    assert r66.list_r66_capacitors() == list_r66_capacitors()
    assert rsb.list_rsb_capacitors() == list_rsb_capacitors()
    assert c4bt.list_c4bt_capacitors() == list_c4bt_capacitors()
    assert c4bs.list_c4bs_capacitors() == list_c4bs_capacitors()
    assert c44u.list_c44u_capacitors() == list_c44u_capacitors()
    assert c44a.list_c44a_capacitors() == list_c44a_capacitors()
    assert c4de.list_c4de_capacitors() == list_c4de_capacitors()
    assert c4aq.list_c4aq_capacitors() == list_c4aq_capacitors()
    assert len(list_yageo_capacitors()) == 5690


def test_tdk_canonical_imports_work() -> None:
    b41456 = importlib.import_module("pe_claw_gui.libraries.capacitors.tdk.b41456_b41458")
    b3271xp = importlib.import_module("pe_claw_gui.libraries.capacitors.tdk.b3271xp")
    b3267 = importlib.import_module("pe_claw_gui.libraries.capacitors.tdk.b3267_d_g_j_t")
    b327h = importlib.import_module("pe_claw_gui.libraries.capacitors.tdk.b32714h_718h")
    b3272agt = importlib.import_module("pe_claw_gui.libraries.capacitors.tdk.b3272agt")
    b3277p = importlib.import_module("pe_claw_gui.libraries.capacitors.tdk.b3277p")
    b256 = importlib.import_module("pe_claw_gui.libraries.capacitors.tdk.b25654a_001")
    b3277m = importlib.import_module("pe_claw_gui.libraries.capacitors.tdk.b3277m")
    b3277xyz = importlib.import_module("pe_claw_gui.libraries.capacitors.tdk.b3277xyz")
    b3277_degjt = importlib.import_module("pe_claw_gui.libraries.capacitors.tdk.b3277_d_e_g_j_t")
    b3277h = importlib.import_module("pe_claw_gui.libraries.capacitors.tdk.b3277h")
    from pe_claw_gui.libraries.capacitors.tdk import (
        get_b41456_b41458_capacitors,
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
        list_epcos_screw_terminal_capacitors,
        list_tdk_capacitors,
    )

    assert b41456.get_b41456_b41458_capacitors() == get_b41456_b41458_capacitors()
    assert b256.get_b25654a_001_capacitors() == get_b25654a_001_capacitors()
    assert b3267.get_b3267_d_g_j_t_capacitors() == get_b3267_d_g_j_t_capacitors()
    assert b3271xp.get_b3271xp_capacitors() == get_b3271xp_capacitors()
    assert b327h.get_b32714h_718h_capacitors() == get_b32714h_718h_capacitors()
    assert b3272agt.get_b3272agt_capacitors() == get_b3272agt_capacitors()
    assert b3277p.get_b3277p_capacitors() == get_b3277p_capacitors()
    assert b3277m.get_b3277m_capacitors() == get_b3277m_capacitors()
    assert b3277xyz.get_b3277xyz_capacitors() == get_b3277xyz_capacitors()
    assert b3277_degjt.get_b3277_d_e_g_j_t_capacitors() == get_b3277_d_e_g_j_t_capacitors()
    assert b3277h.get_b3277h_capacitors() == get_b3277h_capacitors()
    assert list_tdk_capacitors() == (
        *list_epcos_screw_terminal_capacitors(),
        *get_b3271xp_capacitors(),
        *get_b3272agt_capacitors(),
        *get_b3277p_capacitors(),
        *get_b3267_d_g_j_t_capacitors(),
        *get_b32714h_718h_capacitors(),
        *get_b25654a_001_capacitors(),
        *get_b3277m_capacitors(),
        *get_b3277xyz_capacitors(),
        *get_b3277_d_e_g_j_t_capacitors(),
        *get_b3277h_capacitors(),
    )
    assert len(get_b41456_b41458_capacitors()) == 6
    assert len(get_b25654a_001_capacitors()) == 11
    assert len(get_b3267_d_g_j_t_capacitors()) == 115
    assert len(get_b3271xp_capacitors()) == 218
    assert len(get_b32714h_718h_capacitors()) == 236
    assert len(get_b3272agt_capacitors()) == 90
    assert len(get_b3277p_capacitors()) == 44
    assert len(get_b3277m_capacitors()) == 218
    assert len(get_b3277xyz_capacitors()) == 206
    assert len(get_b3277_d_e_g_j_t_capacitors()) == 137
    assert len(get_b3277h_capacitors()) == 218
    assert len(list_epcos_screw_terminal_capacitors()) == 1814
    assert len(list_tdk_capacitors()) == 3307


def test_legacy_kemet_wrapper_modules_are_removed() -> None:
    import pytest

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("pe_claw_gui.libraries.capacitors.kemet_c44p_t")
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("pe_claw_gui.libraries.capacitors.kemet_c4aq_p")


def test_capacitor_selection_does_not_mutate_cached_candidate_objects() -> None:
    candidates = list_registered_capacitors()
    candidate = candidates[0]
    before = candidate
    request = CapacitorSizingRequest(
        side="output",
        dc_voltage_v=400.0,
        ripple_ratio_percent=50.0,
        current_time_s=[0.0, 0.5e-4, 1.0e-4],
        current_waveform_a=[0.0, 1.0, 0.0],
        switching_frequency_hz=10_000.0,
        ambient_temp_c=25.0,
    )

    evaluate_capacitor_bank(request, candidate, parallel_count=1)

    assert candidates[0] is before
    assert candidates[0] == before
