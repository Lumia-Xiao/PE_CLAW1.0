from __future__ import annotations

from pe_claw_gui.engines.devices.stress_adapter import build_design_point_switch_stress_cases
from pe_claw_gui.models.design_report import DesignReport
from pe_claw_gui.topologies.ac_dc.single_phase_interleaved_boost_pfc_diode_bridge import (
    PLUGIN,
    build_default_inputs,
    build_spec,
    extract_design_phase_stress,
    extract_phase_stress,
    generate_waveforms,
    synthesize,
)


def _report() -> tuple[DesignReport, object]:
    spec = build_spec(build_default_inputs())
    candidate = synthesize(spec)
    waveform = generate_waveforms(candidate)
    stress = extract_phase_stress(candidate, waveform).shared_result
    return DesignReport(spec=spec, candidate=candidate, waveform=waveform, stress=stress), candidate


def test_step10c_combines_low_line_current_with_high_line_voltage() -> None:
    report, candidate = _report()
    nominal = extract_phase_stress(candidate, report.waveform)
    design = extract_design_phase_stress(candidate, report.waveform)
    high_line_peak_v = candidate.metadata["line_condition_metrics"]["high_line"]["vac_peak_v"]

    assert design.phase_stress["phase_1"] == design.phase_stress["phase_2"]
    assert design.phase_stress["phase_1"].main_switch.current_rms_a > nominal.phase_stress["phase_1"].main_switch.current_rms_a
    assert design.phase_stress["phase_1"].boost_diode.current_rms_a > nominal.phase_stress["phase_1"].boost_diode.current_rms_a
    assert design.phase_stress["phase_1"].main_switch.voltage_max_v == max(candidate.vout_target, high_line_peak_v)
    assert design.input_bridge_rectifier.current_rms_a > nominal.input_bridge_rectifier.current_rms_a
    assert design.input_bridge_rectifier.voltage_max_v == candidate.metadata["bridge_reverse_stress_v"]
    assert any("low-line current envelope" in note for note in design.shared_result.notes)
    assert any("not a single-line operating waveform" in note for note in design.shared_result.notes)


def test_step10c_design_point_adapter_uses_boundary_stress_without_changing_nominal_waveform() -> None:
    report, candidate = _report()
    cases = build_design_point_switch_stress_cases(report, plugin=PLUGIN)
    assert len(cases) == 1
    stresses = {item.role: item for item in cases[0].stresses}
    design = extract_design_phase_stress(candidate, report.waveform)

    assert stresses["phase_1_main_switch"].i_rms_A == design.phase_stress["phase_1"].main_switch.current_rms_a
    assert stresses["phase_2_main_switch"].i_rms_A == design.phase_stress["phase_2"].main_switch.current_rms_a
    assert stresses["phase_1_boost_diode"].v_block_V == design.phase_stress["phase_1"].boost_diode.voltage_max_v
    assert stresses["phase_2_boost_diode"].v_block_V == design.phase_stress["phase_2"].boost_diode.voltage_max_v
    assert report.waveform.metadata["load_ratio"] == 1.0
    assert report.waveform.metadata["phase_device_metrics"]["phase_1"]["switch_current_rms_a"] < design.phase_stress["phase_1"].main_switch.current_rms_a
