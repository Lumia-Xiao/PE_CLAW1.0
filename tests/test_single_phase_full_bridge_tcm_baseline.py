from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.topologies.base.registry import build_default_registry
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
