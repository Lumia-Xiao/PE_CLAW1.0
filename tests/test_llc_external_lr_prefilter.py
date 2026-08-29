from __future__ import annotations

from pe_claw_gui.models.magnetic_result import LlcExternalResonantInductorTarget
from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier import transformer_design as td


def _request() -> LlcExternalResonantInductorTarget:
    return LlcExternalResonantInductorTarget(
        lr_target_h=1.2e-3,
        transformer_lk_h=0.1e-3,
        external_lr_target_h=1.1e-3,
        external_lr_target_uH=1100.0,
        lr_total_target_h=1.2e-3,
        lr_external_fraction=1.1 / 1.2,
        current_basis="fixture",
        frequency_basis="fixture",
        current_rms_a=3.0,
        current_peak_a=5.0,
        fs_basis_hz=100_000.0,
        fs_min_hz=80_000.0,
        fs_max_hz=120_000.0,
        transformer_design_id="fixture-transformer",
        transformer_leakage_method="fixture",
        transformer_leakage_status="acceptable",
    )


def _core(*, window_area_m2: float = 1.0e-3) -> td._NormalizedCoreRecord:
    return td._NormalizedCoreRecord(
        core_id="fixture-core",
        ae_m2=1.0e-3,
        ae_source_field="fixture",
        le_m=0.1,
        ve_m3=1.0e-5,
        window_area_m2=window_area_m2,
        outer_width_m=0.02,
        outer_height_m=0.02,
        mean_length_per_turn_m=0.04,
        gross_volume_m3=1.0e-5,
    )


def _wire(*, outer_diameter_m: float = 0.01) -> td._NormalizedWireRecord:
    return td._NormalizedWireRecord(
        wire_id="fixture-wire",
        strand_diameter_m=0.0001,
        strands_per_bundle=100,
        bundle_copper_area_m2=1.0e-5,
        outer_diameter_m=outer_diameter_m,
        equivalent_bundle_diameter_m=outer_diameter_m,
    )


def test_external_lr_prefilter_reports_gap_saturation_fill_and_current_limits() -> None:
    reasons = td._external_lr_prefilter_reasons(
        request=_request(),
        core=_core(window_area_m2=1.0e-6),
        wire=_wire(),
        turns=1,
        b_limit_t=0.01,
    )

    assert "invalid_gap" in reasons
    assert "saturation" in reasons
    assert "fill" in reasons
    assert "current_density" not in reasons


def test_external_lr_prefilter_preserves_candidate_count_and_skips_expensive_model(monkeypatch) -> None:
    request = _request()
    material = td._NormalizedMaterialRecord(
        material_id="fixture-material",
        b_sat_t=0.3,
        steinmetz_ranges=[],
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError("prefiltered candidate reached the core-loss model")

    monkeypatch.setattr(td, "evaluate_candidate_core_loss", fail_if_called)
    result = td.generate_llc_external_resonant_inductor_candidates(
        request,
        core_records=[_core(window_area_m2=1.0e-6)],
        material_records=[material],
        wire_records=[_wire()],
        search_bounds=td.LLCMagneticSearchBounds(
            mode="full",
            max_scale_factor=8,
            transformer_core_limit=None,
            transformer_material_limit=None,
            transformer_wire_limit=None,
            external_lr_core_limit=None,
            external_lr_material_limit=None,
            external_lr_wire_limit=None,
            external_lr_max_turns=180,
            design_basis={},
            selection_policy="fixture",
        ),
        write_csv=False,
    )

    counts = result.performance_counts
    assert counts["generated_candidate_count"] == counts["evaluated_candidate_count"]
    assert counts["generated_candidate_count"] == (
        counts["prefilter_rejected_candidate_count"]
        + counts["precise_evaluated_candidate_count"]
    )
    assert counts["generated_candidate_count"] == counts["prefilter_rejected_candidate_count"]
    assert counts["prefilter_pass_count"] == 0
    assert counts["precise_evaluated_candidate_count"] == 0
    assert counts["prefilter_rejected_by_fill_count"] > 0
    assert result.rejection_counts["prefilter_fill"] > 0
    assert all(candidate.rejection_reason.startswith("prefilter:") for candidate in result.candidates)
