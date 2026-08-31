from __future__ import annotations

from dataclasses import replace

from pe_claw_gui.app.result_views.thermal_view import ThermalView
from pe_claw_gui.models.thermal_result import ThermalResult
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_thermal_pipeline import run_thermal_pipeline

from scripts.build_llc_magnetic_result_display_step1_baseline import build_baseline_report
from tests.test_llc_magnetic_result_reporting_step5 import _llc_report


def _render(report) -> str:
    captured: dict[str, str] = {}

    class CaptureView:
        def _set_text(self, value: str) -> None:
            captured["text"] = value

    ThermalView.render(CaptureView(), report)
    return captured["text"]


def test_llc_thermal_view_renders_separate_component_hotspots() -> None:
    report = run_thermal_pipeline(
        _llc_report(),
        pipeline_options=PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=False),
    )
    text = _render(report)

    assert "Recommended combined design:" in text
    assert "hotspot proxy: 76.2 C" in text
    assert "hotspot proxy: 48.5 C" in text
    assert "Component hotspots are estimated separately; no combined thermal network is modeled." in text
    assert "Recommended hotspot proxy: - C" not in text
    assert "Best Design By Stack Count" not in text
    assert "No thermal estimate is available" not in text


def test_llc_thermal_view_keeps_unavailable_component_explicit() -> None:
    report = _llc_report()
    report = replace(
        report,
        magnetic=replace(
            report.magnetic,
            llc_external_resonant_inductor_search_result=None,
            llc_external_resonant_inductor_target=None,
        ),
    )
    report = run_thermal_pipeline(
        report,
        pipeline_options=PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=False),
    )
    text = _render(report)

    assert "Transformer" in text
    assert "External Lr" in text
    assert "hotspot proxy: N/A (not_evaluated)" in text
    assert "Best Design By Stack Count" not in text


def test_non_llc_thermal_view_keeps_stack_count_contract() -> None:
    report = build_baseline_report()
    thermal = ThermalResult(
        summary="fixed-inductor thermal fixture",
        recommended_design_id="fixed-current",
        chosen_design_estimates=[],
        best_by_stack_count={},
    )
    report = replace(report, spec=replace(report.spec, topology_id="buck_diode_rectified_unidirectional"), thermal=thermal)
    text = _render(report)

    assert "Recommended hotspot proxy: - C" in text
    assert "Best Design By Stack Count" in text
