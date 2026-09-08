"""Record the current three-phase NPC waveform contract baseline."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter.input_schema import (
    build_default_inputs,
)


TOPOLOGY_ID = "three_phase_three_level_npc_inverter"
REQUIRED_WAVEFORM_KEYS = (
    "time_s",
    "ia_a",
    "ib_a",
    "ic_a",
    "va_phase_neutral_pwm_v",
    "vb_phase_neutral_pwm_v",
    "vc_phase_neutral_pwm_v",
    "gate_a_s1",
    "gate_a_s2",
    "gate_a_s3",
    "gate_a_s4",
)


def _rms(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values) / len(values)) if values else 0.0


def _phase_metrics(values: list[float]) -> dict[str, float]:
    return {
        "min_a": min(values) if values else 0.0,
        "max_a": max(values) if values else 0.0,
        "mean_a": sum(values) / len(values) if values else 0.0,
        "rms_a": _rms(values),
        "start_a": values[0] if values else 0.0,
        "end_a": values[-1] if values else 0.0,
        "periodic_end_minus_start_a": (values[-1] - values[0]) if values else 0.0,
    }


def build_baseline() -> dict[str, Any]:
    """Build a JSON-serializable baseline without writing runtime artifacts."""

    raw_input = build_default_inputs()
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    spec = plugin.build_spec(raw_input)
    candidate = plugin.synthesize(spec)
    waveform = plugin.generate_waveforms(candidate)
    details = waveform.metadata.get("three_phase_npc_pd_spwm_waveforms", {})
    if not isinstance(details, dict):
        raise AssertionError("NPC waveform metadata is missing")

    phase_currents = {
        phase: [float(value) for value in details[key]]
        for phase, key in (("a", "ia_a"), ("b", "ib_a"), ("c", "ic_a"))
    }
    current_sum = [sum(values) for values in zip(*phase_currents.values(), strict=True)]
    events = waveform.metadata.get("three_phase_npc_switching_events", [])
    event_types = Counter(
        str(event.get("event_type"))
        for event in events
        if isinstance(event, dict)
    )

    return {
        "schema_version": "npc_step1_baseline_v1",
        "topology_id": TOPOLOGY_ID,
        "raw_input": raw_input,
        "data_flow": [
            "input_schema.build_spec",
            "topology_plugin.synthesize",
            "topology_plugin.generate_waveforms",
            "npc.waveform.generate_waveforms",
            "WaveformSet",
            "waveform.metadata.three_phase_npc_pd_spwm_waveforms",
            "WaveformView._render_three_phase_npc_waveforms",
            "NPC event loss evaluation consumes waveform.metadata.three_phase_npc_switching_events",
        ],
        "interface": {
            "waveform_set_fields": {
                "time_s": len(waveform.time_s),
                "inductor_current_a": len(waveform.inductor_current_a),
                "switch_node_voltage_v": len(waveform.switch_node_voltage_v),
                "gate_s1": len(waveform.gate_s1),
            },
            "required_npc_waveform_keys_present": {
                key: key in details for key in REQUIRED_WAVEFORM_KEYS
            },
            "npc_waveform_key_count": len(details),
        },
        "candidate": {
            "inductance_h": float(candidate.inductance_h),
            "switching_frequency_hz": float(candidate.fs_hz),
            "line_frequency_hz": float(spec.metadata["f_line_hz"]),
        },
        "waveform": {
            "sample_count": len(waveform.time_s),
            "time_span_s": float(waveform.time_span_s),
            "phase_current": {
                phase: _phase_metrics(values) for phase, values in phase_currents.items()
            },
            "three_phase_current_sum_max_abs_a": max((abs(value) for value in current_sum), default=0.0),
            "periodic_correction_a": [
                float(value)
                for value in waveform.metadata.get("phase_current_periodic_correction_a", [])
            ],
            "integration_method": waveform.metadata.get("phase_current_integration_method"),
            "periodic_correction_applied": waveform.metadata.get(
                "phase_current_periodic_correction_applied"
            ),
        },
        "switching_events": {
            "count": len(events) if isinstance(events, list) else 0,
            "event_type_counts": dict(sorted(event_types.items())),
        },
        "output_policy": {
            "design_results_root": "outputs",
            "test_temporary_root": "pytest_temp",
            "generated_baseline_path": "pytest_temp/npc_step1_baseline.json",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "pytest_temp" / "npc_step1_baseline.json",
        help="JSON output path; defaults to pytest_temp/npc_step1_baseline.json",
    )
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(build_baseline(), indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(json.dumps({"output": str(output.resolve()), "schema_version": "npc_step1_baseline_v1"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
