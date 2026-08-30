from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

from pe_claw_gui.app.result_views.llc_result_text import _llc_geometry_lines
from pe_claw_gui.models.geometry_result import GeometryResult, GeometryTarget
from pe_claw_gui.models.inductor import FixedInductorDesignCandidate
from pe_claw_gui.pipeline.run_geometry_pipeline import (
    _llc_external_lr_selection_by_role,
    _llc_unavailable_geometry_targets,
)
from pe_claw_gui.reports.structured_output import _geometry_payload


def _candidate(design_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        design_id=design_id,
        core_family="e",
        core_id="E 55/28/25",
        material_name="SMP97",
        turns=11,
        gap_m=1e-3,
        actual_l_h=1.1e-3,
        target_l_h=1.1e-3,
        estimated_volume_m3=41.8581e-6,
        total_loss_w=1.27589,
        core_effective_area_m2=1e-4,
        core_window_area_m2=1e-4,
        core_width_m=55e-3,
        core_height_m=28e-3,
        core_depth_m=25e-3,
        core_volume_m3=20e-6,
        winding_volume_m3=5e-6,
        gross_volume_m3=41.8581e-6,
        wire_name="SMP97",
        wire_parallel_count=4,
        b_peak_t=0.1,
        copper_loss_w=0.5,
        core_loss_w=0.77589,
        fill_factor=0.2,
        lr_closure_status="closed",
    )


def test_llc_representative_resolution_prefers_named_chosen_selections() -> None:
    recommended = _candidate("recommended-id")
    min_volume = _candidate("min-volume-id")
    result = SimpleNamespace(
        chosen_candidates=[
            SimpleNamespace(role="recommended", candidate=recommended),
            SimpleNamespace(role="min-volume", candidate=min_volume),
        ],
        recommended_candidate=_candidate("stale-fallback-id"),
        min_volume_candidate=None,
        min_loss_candidate=None,
        compromise_candidate=_candidate("compromise-id"),
    )

    resolved = _llc_external_lr_selection_by_role(result)

    assert resolved["recommended"].candidate.design_id == "recommended-id"
    assert resolved["min-volume"].candidate.design_id == "min-volume-id"
    assert resolved["compromise"].candidate.design_id == "compromise-id"
    assert "min-loss" not in resolved


def test_llc_unavailable_geometry_targets_keep_component_role_and_reason() -> None:
    targets = _llc_unavailable_geometry_targets("No representative was produced.")

    assert [target.role for target in targets] == ["min_volume", "min_loss", "recommended"]
    assert all(target.component_role == "external_resonant_inductor" for target in targets)
    assert all(target.design_id is None for target in targets)
    assert all(target.error_message == "No representative was produced." for target in targets)


def test_llc_geometry_payload_preserves_role_and_representative_source() -> None:
    geometry = GeometryResult(
        component_type="external_resonant_inductor",
        targets=[
            GeometryTarget(
                role="recommended",
                label="Recommended",
                component_role="external_resonant_inductor",
                representative_role="compromise",
                design_id="lr-compromise",
                volume_m3=41.8581e-6,
                loss_w=1.27589,
            ),
            GeometryTarget(
                role="min_loss",
                label="Min-loss",
                component_role="external_resonant_inductor",
                error_message="No min-loss external Lr representative was produced.",
            ),
        ],
    )
    payload = _geometry_payload(SimpleNamespace(geometry=geometry))

    assert payload["metadata"]["component_type"] == "external_resonant_inductor"
    assert payload["metadata"]["component_roles"] == ["external_resonant_inductor"]
    assert payload["targets"][0]["component_role"] == "external_resonant_inductor"
    assert payload["targets"][0]["representative_role"] == "compromise"
    assert payload["targets"][1]["error"] == "No min-loss external Lr representative was produced."


def test_llc_geometry_text_does_not_present_external_lr_as_transformer() -> None:
    geometry = GeometryResult(
        component_type="external_resonant_inductor",
        summary="External resonant inductor geometry prepared.",
        targets=[
            GeometryTarget(
                role="recommended",
                label="Recommended",
                component_role="external_resonant_inductor",
                design_id="lr-recommended",
                volume_m3=41.8581e-6,
                loss_w=1.27589,
            )
        ],
    )
    report = SimpleNamespace(geometry=geometry)

    text = "\n".join(_llc_geometry_lines(report))

    assert "component: external_resonant_inductor" in text
    assert "component_role=external_resonant_inductor" in text
    assert "transformer geometry" not in text.casefold()
