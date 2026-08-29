from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

from scripts.build_llc_magnetic_result_display_step1_baseline import build_baseline_report
from pe_claw_gui.app.result_views.inductor_view import build_inductor_summary_text
from pe_claw_gui.models.magnetic_result import LlcMagneticResultSummary, LlcMagneticStageSummary
from pe_claw_gui.pipeline.run_magnetic_pipeline import _llc_transformer_design_requirements


def _requirements():
    fha = SimpleNamespace(
        topology_id="llc_resonant_converter_diode_rectifier",
        vin_min_v=360.0,
        vin_nom_v=400.0,
        vin_max_v=420.0,
        vout_min_v=47.5,
        vout_nom_v=48.0,
        vout_max_v=48.5,
        pout_min_w=400.0,
        pout_max_w=4000.0,
        fs_min_hz=85000.0,
        fr_hz=100000.0,
        fs_max_hz=145000.0,
    )
    transformer_target = {
        "base_np": 18,
        "base_ns": 18,
        "lm_target_h": 1.8e-3,
        "lr_target_h": 1.2e-3,
        "b_limit_t": 0.18,
        "primary_bridge_type": "full_bridge",
        "secondary_rectifier_type": "full_bridge_rectifier",
        "boundary_saturation_case_names": ["Vin_min/Vout_min/Pmax", "Vin_max/Vout_max/Pmax"],
        "primary_current_basis": "FHA worst-case corner",
        "primary_current_rms_a": 9.0,
        "primary_current_peak_a": 15.0,
        "secondary_current_basis": "reflected-load current",
        "secondary_current_rms_a": 8.0,
        "secondary_current_peak_a": 12.0,
    }
    recommended = SimpleNamespace(
        np=18,
        ns=18,
        estimated_lk_h=0.12e-3,
        leakage_method="first_pass_geometry_estimate",
        leakage_status="acceptable",
    )
    external_target = SimpleNamespace(
        is_design_required=True,
        external_lr_target_h=1.08e-3,
        external_lr_target_uH=1080.0,
        lr_total_target_h=1.2e-3,
        transformer_lk_h=0.12e-3,
        current_basis="sinusoidal_peak",
        frequency_basis="lowest-frequency FHA corner",
        current_rms_a=4.0,
        current_peak_a=6.0,
        fs_basis_hz=85000.0,
        fs_min_hz=85000.0,
        fs_max_hz=145000.0,
        warning="",
    )
    search_result = SimpleNamespace(evaluated_candidate_count=100, feasible_candidate_count=20)
    search_bounds = SimpleNamespace(
        mode="fast",
        selection_policy="deterministic bounded search",
        to_dict=lambda: {
            "transformer": {"core_limit": 48, "material_limit": 16, "wire_limit": 16},
            "external_lr": {"core_limit": 24, "material_limit": 12, "wire_limit": 12, "max_turns": 180},
        },
    )
    return _llc_transformer_design_requirements(
        transformer_target,
        search_result,
        fha_design=fha,
        display_name="LLC Resonant Converter Diode Rectifier",
        recommended_candidate=recommended,
        external_lr_target=external_target,
        search_bounds=search_bounds,
    )


def test_llc_requirements_include_fha_transformer_and_external_lr_sources() -> None:
    requirements = _requirements()

    assert requirements["display_name"] == "LLC Resonant Converter Diode Rectifier"
    assert requirements["vin_min_v"] == 360.0
    assert requirements["vin_nom_v"] == 400.0
    assert requirements["vin_max_v"] == 420.0
    assert requirements["pout_min_w"] == 400.0
    assert requirements["pout_max_w"] == 4000.0
    assert requirements["fs_min_hz"] == 85000.0
    assert requirements["fs_nom_hz"] == 100000.0
    assert requirements["fs_max_hz"] == 145000.0
    assert requirements["base_np"] == 18
    assert requirements["recommended_np"] == 18
    assert requirements["transformer_estimated_lk_h"] == 0.12e-3
    assert requirements["external_lr_target_h"] == 1.08e-3
    assert requirements["external_lr_current_rms_a"] == 4.0
    assert requirements["external_lr_fs_basis_hz"] == 85000.0
    assert requirements["magnetic_search_mode"] == "fast"
    assert requirements["magnetic_search_bounds"]["external_lr"]["max_turns"] == 180
    assert requirements["field_status"]["external_lr"] == "available"


def test_llc_requirements_formatter_uses_llc_labels_and_units() -> None:
    report = build_baseline_report()
    magnetic = report.magnetic
    summary = LlcMagneticResultSummary(
        transformer=LlcMagneticStageSummary(status="available", recommended_design_id="transformer"),
        external_lr=LlcMagneticStageSummary(status="available", recommended_design_id="external"),
        recommended_transformer_design_id="transformer",
        recommended_external_lr_design_id="external",
        recommended_combined_magnetic_design_id="transformer+external",
    )
    report = replace(
        report,
        magnetic=replace(
            magnetic,
            llc_result_summary=summary,
            design_requirements=_requirements(),
        ),
    )

    text = build_inductor_summary_text(report)
    assert "Vin min/nom/max: 360 V / 400 V / 420 V" in text
    assert "Pout min/max: 400 W / 4000 W" in text
    assert "fs min/nom/max: 85000 Hz / 100000 Hz / 145000 Hz" in text
    assert "Base transformer Np:Ns: 18:18" in text
    assert "Recommended transformer Np:Ns: 18:18" in text
    assert "Lm target: 1800 uH" in text
    assert "Total Lr target: 1200 uH" in text
    assert "Transformer estimated Llk: 120 uH" in text
    assert "External Lr target: 1080 uH (available)" in text
    assert "External Lr Irms/Ipeak: 4 A / 6 A" in text
    assert "B limit: 0.18 T" in text
    assert "Magnetic search mode: fast" in text
    assert "L target:" not in text
    assert "Iavg:" not in text
    assert "Delta iL:" not in text
    assert "Mode:" not in text


def test_llc_requirements_distinguish_external_lr_not_evaluated() -> None:
    requirements = _llc_transformer_design_requirements(
        {"base_np": 1, "base_ns": 1},
        SimpleNamespace(evaluated_candidate_count=0, feasible_candidate_count=0),
    )
    assert requirements["external_lr_status"] == "not_evaluated"
    assert requirements["external_lr_target_h"] is None
