from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import _sweep_operating_point
from pe_claw_gui.models.design_report import DesignReport
from pe_claw_gui.topologies.dc_ac.single_phase_full_bridge_inverter.input_schema import build_default_inputs


def test_tcm_baseline_covers_one_line_period_and_reports_variable_frequency() -> None:
    raw = build_default_inputs()
    raw.update(
        {
            "conduction_mode": "TCM",
            "fsw_min_hz": "5000",
            "fsw_max_hz": "100000",
            "tcm_valley_current_target_a": "-1",
        }
    )
    plugin = build_default_registry().get_plugin("single_phase_full_bridge_inverter")
    candidate = plugin.synthesize(plugin.build_spec(raw))
    waveform = plugin.generate_waveforms(candidate)
    envelope = waveform.metadata["single_phase_inverter_tcm_envelope"]
    detail_time = [float(value) for value in envelope["detail_time_s"]]
    detail_fsw = [float(value) for value in envelope["detail_fsw_hz"]]

    assert math.isclose(waveform.time_span_s, 1.0 / 50.0, abs_tol=1e-12)
    assert detail_time[0] == 0.0
    assert detail_time[-1] == waveform.time_span_s
    assert len(detail_time) == envelope["detail_sample_count"]
    assert min(detail_fsw) < max(detail_fsw)
    assert all(math.isfinite(value) for value in detail_time + detail_fsw)


def test_tcm_operating_point_refresh_changes_current_and_frequency_with_load() -> None:
    raw = build_default_inputs()
    raw.update(
        {
            "conduction_mode": "TCM",
            "fsw_min_hz": "5000",
            "fsw_max_hz": "100000",
            "tcm_valley_current_target_a": "-1",
        }
    )
    plugin = build_default_registry().get_plugin("single_phase_full_bridge_inverter")
    candidate = plugin.synthesize(plugin.build_spec(raw))
    snapshots = {}
    for load_ratio in (0.05, 0.5, 1.0):
        waveform = plugin.generate_waveforms(
            candidate,
            operating_point=OperatingPoint(vin_v=400.0, load_ratio=load_ratio, power_factor=1.0),
        )
        envelope = waveform.metadata["single_phase_inverter_tcm_envelope"]
        snapshots[load_ratio] = {
            "waveform_load_ratio": waveform.load_ratio,
            "iavg_peak_a": max(abs(float(value)) for value in envelope["detail_iavg_a"]),
            "detail_fsw_mean_hz": sum(float(value) for value in envelope["detail_fsw_hz"]) / len(envelope["detail_fsw_hz"]),
            "detail_fsw_min_hz": min(float(value) for value in envelope["detail_fsw_hz"]),
            "detail_fsw_max_hz": max(float(value) for value in envelope["detail_fsw_hz"]),
        }

    assert [snapshots[load]["waveform_load_ratio"] for load in (0.05, 0.5, 1.0)] == [0.05, 0.5, 1.0]
    assert snapshots[0.05]["iavg_peak_a"] < snapshots[0.5]["iavg_peak_a"] < snapshots[1.0]["iavg_peak_a"]
    assert snapshots[0.05]["detail_fsw_mean_hz"] != snapshots[1.0]["detail_fsw_mean_hz"]
    assert snapshots[0.05]["detail_fsw_min_hz"] != snapshots[1.0]["detail_fsw_min_hz"]


def test_efficiency_sweep_operating_point_preserves_each_tcm_load_ratio() -> None:
    raw = build_default_inputs()
    raw["conduction_mode"] = "TCM"
    plugin = build_default_registry().get_plugin("single_phase_full_bridge_inverter")
    spec = plugin.build_spec(raw)
    candidate = plugin.synthesize(spec)
    report = DesignReport(spec=spec, candidate=candidate, operating_point=OperatingPoint(vin_v=400.0, load_ratio=1.0, power_factor=1.0))
    for load_ratio in (0.05, 0.5, 1.0):
        operating_point = _sweep_operating_point(report, load_ratio)
        assert operating_point.load_ratio == load_ratio
        assert operating_point.power_factor == 1.0


def test_tcm_event_audit_exposes_missing_event_level_switching_source() -> None:
    raw = build_default_inputs()
    raw.update(
        {
            "conduction_mode": "TCM",
            "fsw_min_hz": "5000",
            "fsw_max_hz": "100000",
            "tcm_valley_current_target_a": "-1",
        }
    )
    plugin = build_default_registry().get_plugin("single_phase_full_bridge_inverter")
    candidate = plugin.synthesize(plugin.build_spec(raw))
    waveform = plugin.generate_waveforms(candidate)
    metadata = waveform.metadata
    tcm = metadata["single_phase_inverter_tcm_envelope"]

    assert "single_phase_inverter_refined_waveforms" not in metadata
    assert len(tcm["switching_events"]) == 4 * tcm["detail_cycle_count"]
    audit = tcm["switching_event_audit"]
    assert audit["event_count"] == len(tcm["switching_events"])
    assert audit["turn_on_count"] == 2 * tcm["detail_cycle_count"]
    assert audit["turn_off_count"] == 2 * tcm["detail_cycle_count"]
    assert audit["soft_turn_on_count"] > 0
    assert audit["hard_turn_on_count"] > 0
    assert tcm["detail_cycle_count"] > 0
    assert len(tcm["detail_cycle_fsw_hz"]) == tcm["detail_cycle_count"]
    assert min(tcm["detail_cycle_fsw_hz"]) < max(tcm["detail_cycle_fsw_hz"])


def test_tcm_magnetic_and_capacitor_inputs_use_complete_detail_period() -> None:
    from pe_claw_gui.engines.magnetics.inductor_adapter import build_inductor_design_request
    from pe_claw_gui.pipeline.run_capacitor_pipeline import _resolve_output_capacitor_waveform
    from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
    from pe_claw_gui.pipeline.options import PipelineOptions

    raw = build_default_inputs()
    raw.update({"conduction_mode": "TCM", "fsw_min_hz": "5000", "fsw_max_hz": "100000", "tcm_valley_current_target_a": "-1"})
    plugin = build_default_registry().get_plugin("single_phase_full_bridge_inverter")
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=raw,
        include_waveforms=True,
        pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
    )
    tcm = report.waveform.metadata["single_phase_inverter_tcm_envelope"]
    detail_time = tcm["detail_time_s"]
    detail_current = tcm["detail_inductor_current_a"]
    assert detail_time[0] == 0.0
    assert detail_time[-1] == pytest.approx(1.0 / 50.0)
    assert len(detail_time) == len(detail_current)

    request = build_inductor_design_request(report)
    assert request.metadata["tcm_current_stats_basis"] == "detailed_tcm_current_one_line_period"
    assert request.i_rms_a > 0.0
    assert request.i_peak_a >= request.i_rms_a

    capacitor_time, capacitor_current, _ = _resolve_output_capacitor_waveform(report)
    assert capacitor_time == detail_time
    assert len(capacitor_time) == len(capacitor_current)
    assert capacitor_time[-1] == pytest.approx(1.0 / 50.0)


def test_tcm_selection_only_pipeline_closes_non_applicable_run_stages(tmp_path: Path) -> None:
    import json

    from pe_claw_gui.pipeline.options import PipelineOptions
    from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline

    raw = build_default_inputs()
    raw.update({"conduction_mode": "TCM", "fsw_min_hz": "5000", "fsw_max_hz": "100000", "tcm_valley_current_target_a": "-1"})
    plugin = build_default_registry().get_plugin("single_phase_full_bridge_inverter")
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=raw,
        include_waveforms=True,
        pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
        output_root=tmp_path / "tcm-run",
    )

    assert report.run_context is not None
    statuses = report.run_context.stage_status
    assert statuses["design"] == "succeeded"
    assert statuses["semiconductor_design"] == "succeeded"
    assert statuses["validation"] == "not_applicable"
    assert report.run_context.output_root.endswith("tcm-run")
    manifest = json.loads(Path(report.run_context.manifest_path).read_text(encoding="utf-8"))
    assert manifest["status"] == "succeeded"
    assert manifest["stage_status"] == statuses
    diagnostic_path = Path(report.run_context.output_root) / "validation" / "tcm_diagnostic.json"
    diagnostic = json.loads(diagnostic_path.read_text(encoding="utf-8"))
    assert diagnostic["topology_id"] == "single_phase_full_bridge_inverter"
    assert diagnostic["line_cycle"]["detail_time_start_s"] == 0.0
    assert diagnostic["line_cycle"]["detail_time_end_s"] == pytest.approx(1.0 / 50.0)
    assert diagnostic["switching_events"]["event_count"] > 0
    assert diagnostic["losses"]["other_loss_w"] == 0.0
    assert diagnostic["failure"]["stage"] is None
