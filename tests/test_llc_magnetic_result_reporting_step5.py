from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from scripts.build_llc_magnetic_result_display_step1_baseline import (
    COMBINED_ID,
    EXTERNAL_LR_ID,
    TRANSFORMER_ID,
    build_baseline_report,
)
from pe_claw_gui.app.result_views.inductor_view import build_inductor_summary_text
from pe_claw_gui.engines.hardware_overview import _build_inductor_group
from pe_claw_gui.models.geometry_result import GeometryTarget
from pe_claw_gui.models.loss_result import LossResult
from pe_claw_gui.models.magnetic_result import LlcMagneticResultSummary, LlcMagneticStageSummary
from pe_claw_gui.models.thermal_result import ThermalResult
from pe_claw_gui.pipeline.run_loss_pipeline import _run_loss_pipeline_without_excitation_audit
from pe_claw_gui.pipeline.run_thermal_pipeline import run_thermal_pipeline
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.reports.structured_output import build_structured_report


def _summary() -> LlcMagneticResultSummary:
    return LlcMagneticResultSummary(
        transformer=LlcMagneticStageSummary(status="available", recommended_design_id=TRANSFORMER_ID),
        external_lr=LlcMagneticStageSummary(status="available", recommended_design_id=EXTERNAL_LR_ID),
        recommended_transformer_design_id=TRANSFORMER_ID,
        recommended_external_lr_design_id=EXTERNAL_LR_ID,
        recommended_combined_magnetic_design_id=COMBINED_ID,
    )


def _llc_report():
    report = build_baseline_report()
    transformer = report.magnetic.llc_transformer_result.recommended_preliminary_candidate
    external = report.magnetic.llc_external_resonant_inductor_search_result.recommended_candidate
    magnetic = replace(
        report.magnetic,
        llc_result_summary=_summary(),
        recommended_transformer_design_id=TRANSFORMER_ID,
        recommended_external_lr_design_id=EXTERNAL_LR_ID,
        recommended_combined_magnetic_design_id=COMBINED_ID,
    )
    return replace(report, magnetic=magnetic, candidate=SimpleNamespace(metadata={}, delta_vo=None))


def test_llc_loss_pipeline_preserves_role_loss_and_volume_conservation() -> None:
    report = _llc_report()
    report = _run_loss_pipeline_without_excitation_audit(
        report,
        pipeline_options=PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=False),
    )
    loss = report.loss
    assert loss is not None
    assert loss.recommended_design_id == COMBINED_ID
    assert loss.breakdown_w["llc_transformer_total_loss_w"] == pytest.approx(3.74375)
    assert loss.breakdown_w["llc_external_resonant_inductor_total_loss_w"] == pytest.approx(1.27589)
    assert loss.breakdown_w["llc_magnetic_total_loss_w"] == pytest.approx(5.01964)
    assert loss.breakdown_w["llc_magnetic_core_loss_w"] == pytest.approx(
        loss.breakdown_w["llc_transformer_core_loss_w"]
        + loss.breakdown_w["llc_external_resonant_inductor_core_loss_w"]
    )
    assert loss.breakdown_w["llc_magnetic_copper_loss_w"] == pytest.approx(
        loss.breakdown_w["llc_transformer_copper_loss_w"]
        + loss.breakdown_w["llc_external_resonant_inductor_copper_loss_w"]
    )
    assert loss.component_volumes_m3["combined_magnetic_volume_m3"] == pytest.approx(
        loss.component_volumes_m3["transformer_volume_m3"]
        + loss.component_volumes_m3["external_lr_volume_m3"]
    )


def test_llc_thermal_pipeline_reports_transformer_and_external_lr_hotspots() -> None:
    report = run_thermal_pipeline(
        _llc_report(),
        pipeline_options=PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=False),
    )
    thermal = report.thermal
    assert thermal is not None
    assert thermal.recommended_design_id == COMBINED_ID
    assert thermal.llc_component_thermal["transformer"]["design_id"] == TRANSFORMER_ID
    assert thermal.llc_component_thermal["transformer"]["hotspot_c"] == pytest.approx(76.2)
    assert thermal.llc_component_thermal["external_lr"]["design_id"] == EXTERNAL_LR_ID
    assert thermal.llc_component_thermal["external_lr"]["hotspot_c"] == pytest.approx(48.5)
    assert thermal.chosen_design_estimates[0].assembly_type == "transformer"
    assert thermal.chosen_design_estimates[0].estimate is not None
    assert thermal.chosen_design_estimates[0].estimate.total_loss_w == pytest.approx(3.74375)
    assert thermal.chosen_design_estimates[1].assembly_type == "external_lr"
    assert thermal.chosen_design_estimates[1].estimate is not None
    assert thermal.chosen_design_estimates[1].estimate.total_loss_w == pytest.approx(1.27589)
    assert thermal.llc_component_estimates["transformer"].design_id == TRANSFORMER_ID
    assert thermal.llc_component_estimates["external_lr"].design_id == EXTERNAL_LR_ID


def test_llc_inductor_summary_reports_loss_thermal_and_external_lr_geometry_roles() -> None:
    report = _llc_report()
    loss = LossResult(
        total_loss_w=5.01964,
        recommended_design_id=COMBINED_ID,
        recommended_design_total_volume_m3=150.75e-6,
        component_volumes_m3={
            "transformer_volume_m3": 108.8919e-6,
            "external_lr_volume_m3": 41.8581e-6,
            "combined_magnetic_volume_m3": 150.75e-6,
        },
        breakdown_w={
            "llc_transformer_core_loss_w": 2.1,
            "llc_transformer_copper_loss_w": 1.64375,
            "llc_transformer_total_loss_w": 3.74375,
            "llc_external_resonant_inductor_core_loss_w": 0.7,
            "llc_external_resonant_inductor_copper_loss_w": 0.57589,
            "llc_external_resonant_inductor_total_loss_w": 1.27589,
            "llc_magnetic_core_loss_w": 2.8,
            "llc_magnetic_copper_loss_w": 2.21964,
            "llc_magnetic_total_loss_w": 5.01964,
        },
    )
    thermal = ThermalResult(
        recommended_design_id=COMBINED_ID,
        llc_component_thermal={
            "transformer": {"status": "available", "design_id": TRANSFORMER_ID, "hotspot_c": 76.2, "source": "magnetic"},
            "external_lr": {"status": "available", "design_id": EXTERNAL_LR_ID, "hotspot_c": 48.5, "source": "magnetic"},
        },
    )
    geometry = replace(report.geometry, component_type="external_resonant_inductor")
    report = replace(report, loss=loss, thermal=thermal, geometry=geometry)
    text = build_inductor_summary_text(report)
    assert "transformer design: " in text
    assert "core loss: 2.1 W" in text
    assert "combined volume: 150.75 cm^3" in text
    assert "Transformer: available" in text
    assert "hotspot: 76.2 C" in text
    assert "component: external_resonant_inductor" in text
    assert "these artifacts are for external Lr" in text


def test_llc_structured_output_contains_role_specific_reporting() -> None:
    report = _llc_report()
    report = _run_loss_pipeline_without_excitation_audit(
        report,
        pipeline_options=PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=False),
    )
    report = run_thermal_pipeline(
        report,
        pipeline_options=PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=False),
    )
    report = replace(report, geometry=replace(report.geometry, component_type="external_resonant_inductor"))
    payload = build_structured_report(report)
    assert payload["loss"]["llc"]["combined"]["design_id"] == COMBINED_ID
    assert payload["loss"]["llc"]["transformer"]["volume"]["value"] == pytest.approx(108.8919e-6)
    assert payload["thermal"]["llc_components"]["external_lr"]["design_id"] == EXTERNAL_LR_ID
    assert payload["thermal"]["llc_components"]["transformer"]["hotspot_temperature"]["value"] == pytest.approx(76.2)
    assert payload["thermal"]["llc_components"]["transformer"]["core_loss"]["value"] == pytest.approx(2.1)
    assert payload["thermal"]["llc_components"]["external_lr"]["total_loss"]["value"] == pytest.approx(1.27589)
    assert payload["thermal"]["llc_components"]["external_lr"]["estimate_available"] is True
    assert payload["geometry"]["metadata"]["component_type"] == "external_resonant_inductor"
    assert payload["hardware"]["magnetic"]["selection_status"] == "pass"


def test_llc_hardware_overview_labels_external_lr_as_separate_component() -> None:
    report = _llc_report()
    layout = SimpleNamespace(
        design_id=EXTERNAL_LR_ID,
        core_family="E",
        core_name="E 55/28/25",
        base_core_name="E 55/28/25",
        wire_name="SMP97",
        turns=11,
        parallels=4,
        stack_count=1,
        overall_width_mm=55.0,
        overall_height_mm=28.0,
        overall_depth_mm=25.0,
    )
    target = GeometryTarget(
        role="recommended",
        label="Recommended",
        design_id=EXTERNAL_LR_ID,
        layout=layout,
        volume_m3=41.8581e-6,
        loss_w=1.27589,
        artifact_paths=[],
    )
    report = replace(
        report,
        geometry=replace(
            report.geometry,
            selected_design_id=EXTERNAL_LR_ID,
            selected_layout=layout,
            targets=[target],
        ),
    )
    group = _build_inductor_group(report)
    assert group.display_name == "External Resonant Inductor"
    assert group.recommended_name == EXTERNAL_LR_ID
    assert group.metadata["component_role"] == "external_resonant_inductor"
    assert group.metadata["recommended_transformer_design_id"] == TRANSFORMER_ID
    assert group.metadata["recommended_combined_magnetic_design_id"] == COMBINED_ID
