from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.topologies.ac_dc.single_phase_boost_pfc_diode_bridge import (
    PLUGIN as SINGLE_PHASE_PLUGIN,
    build_default_inputs as build_single_phase_default_inputs,
)
from pe_claw_gui.topologies.ac_dc.single_phase_interleaved_boost_pfc_diode_bridge import (
    build_default_inputs,
    build_spec,
    evaluate,
    extract_phase_stress,
    generate_waveforms,
    synthesize,
)

BASELINE = Path(__file__).resolve().parent / "fixtures" / "single_phase_boost_pfc_step0_baseline.json"


def _interleaved_candidate(raw: dict[str, str] | None = None):
    inputs = build_default_inputs()
    if raw:
        inputs.update(raw)
    spec = build_spec(inputs)
    return spec, synthesize(spec)


def test_step3_waveform_phase_currents_sum_to_total_and_store_180_degree_offsets() -> None:
    from math import sqrt

    _, candidate = _interleaved_candidate({"vdc_target_v": str(2.0 * 230.0 * sqrt(2.0))})
    waveform = generate_waveforms(candidate)
    metadata = waveform.metadata
    phase_waveforms = metadata["phase_waveforms"]

    phase_1_current = phase_waveforms["phase_1"]["inductor_current_avg_a"]
    phase_2_current = phase_waveforms["phase_2"]["inductor_current_avg_a"]
    aggregate_current = metadata["phase_currents_a"]["aggregate"]
    assert len(phase_1_current) == len(phase_2_current) == len(aggregate_current) == len(waveform.time_s)
    assert all(
        a + b == pytest.approx(total)
        for a, b, total in zip(phase_1_current, phase_2_current, aggregate_current, strict=True)
    )
    assert phase_waveforms["phase_1"]["switching_phase_deg"] == 0.0
    assert phase_waveforms["phase_2"]["switching_phase_deg"] == 180.0
    assert metadata["phase_shift_deg"] == 180.0
    assert waveform.inductor_current_a == aggregate_current
    assert metadata["interleaved_ripple_pp_a"]["aggregate_ripple_pp_a"][90] == pytest.approx(0.0, abs=1e-12)
    assert metadata["aggregate_waveform_basis"]["inductor_voltage_v"].startswith("representative per-phase")


def test_step3_waveform_uses_fixed_hardware_ripple_at_reduced_load() -> None:
    _, candidate = _interleaved_candidate()
    rated = generate_waveforms(candidate)
    half_load = generate_waveforms(candidate, OperatingPoint(vin_v=230.0, load_ratio=0.5))

    rated_ripple = rated.metadata["phase_ripple_pp_a"]["phase_1"]
    half_load_ripple = half_load.metadata["phase_ripple_pp_a"]["phase_1"]
    assert half_load.metadata["phase_currents_a"]["phase_1"][90] == pytest.approx(
        rated.metadata["phase_currents_a"]["phase_1"][90] * 0.5
    )
    assert half_load_ripple == pytest.approx(rated_ripple)


def test_step3_phase_stress_adapter_reports_both_phases_and_shared_bridge() -> None:
    _, candidate = _interleaved_candidate()
    waveform = generate_waveforms(candidate)
    adapter = extract_phase_stress(candidate, waveform)

    phase_1 = adapter.phase_stress["phase_1"]
    phase_2 = adapter.phase_stress["phase_2"]
    assert phase_1.main_switch == phase_2.main_switch
    assert phase_1.boost_diode == phase_2.boost_diode
    assert phase_1.main_switch.voltage_max_v == pytest.approx(candidate.vout_target)
    assert phase_1.boost_diode.voltage_max_v == pytest.approx(candidate.vout_target)
    assert adapter.input_bridge_rectifier.voltage_max_v == pytest.approx(candidate.metadata["bridge_reverse_stress_v"])
    assert adapter.input_bridge_rectifier.current_rms_a == pytest.approx(
        candidate.metadata["electrical_input_current_rms_a"], rel=0.005
    )
    assert adapter.shared_result.switch == phase_1.main_switch
    assert adapter.shared_result.rectifier == phase_1.boost_diode


def test_step3_evaluator_exposes_phase_and_aggregate_relationships() -> None:
    _, candidate = _interleaved_candidate()
    waveform = generate_waveforms(candidate)
    stress = extract_phase_stress(candidate, waveform)
    result = evaluate(candidate, waveform, stress.shared_result)

    assert result.feasible is candidate.feasible
    assert result.topology_id == candidate.topology_id
    assert any("Phase 2 switch RMS current" in line for line in result.summary_lines)
    assert any("Input bridge RMS current" in line for line in result.summary_lines)
    assert any("root-sum-square" in note for note in result.notes)


def _stable_snapshot(topology: str) -> tuple[Any, ...]:
    if topology == "single_phase":
        plugin = SINGLE_PHASE_PLUGIN
        spec = plugin.build_spec(build_single_phase_default_inputs())
        candidate = plugin.synthesize(spec)
        waveform = plugin.generate_waveforms(candidate)
        stress = plugin.extract_stress(candidate, waveform)
        result = plugin.evaluate(candidate, waveform, stress)
        return (
            candidate.inductance_h,
            candidate.capacitance_f,
            candidate.delta_il,
            waveform.metadata["boost_switch_current_rms_a"],
            stress.switch.current_peak_a,
            tuple(result.summary_lines),
        )

    _, candidate = _interleaved_candidate()
    waveform = generate_waveforms(candidate)
    stress = extract_phase_stress(candidate, waveform)
    result = evaluate(candidate, waveform, stress.shared_result)
    return (
        candidate.inductance_h,
        candidate.capacitance_f,
        waveform.metadata["aggregate_inductor_current_rms_a"],
        stress.phase_stress["phase_2"].main_switch.current_rms_a,
        tuple(result.summary_lines),
    )


def test_step3_old_and_new_topologies_are_order_independent_and_repeatable() -> None:
    baseline = json.loads(BASELINE.read_text(encoding="ascii"))
    expected_old = baseline["cases"][0]["candidate"]

    def run_order(order: tuple[str, str]) -> dict[str, tuple[Any, ...]]:
        return {topology: _stable_snapshot(topology) for topology in order}

    old_first = run_order(("single_phase", "interleaved"))
    new_first = run_order(("interleaved", "single_phase"))
    repeated_old_first = run_order(("single_phase", "interleaved"))

    assert old_first["single_phase"] == new_first["single_phase"] == repeated_old_first["single_phase"]
    assert old_first["interleaved"] == new_first["interleaved"] == repeated_old_first["interleaved"]
    assert old_first["single_phase"][0] == pytest.approx(expected_old["inductance_h"], rel=1e-9)
    assert old_first["single_phase"][1] == pytest.approx(expected_old["capacitance_f"], rel=1e-9)
