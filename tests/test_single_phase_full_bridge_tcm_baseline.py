from __future__ import annotations

import math
import sys
from pathlib import Path

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
