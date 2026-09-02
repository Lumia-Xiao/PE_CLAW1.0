from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.pipeline import run_capacitor_pipeline, run_full_pipeline
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter import build_default_inputs


def _report(tmp_path: Path):
    plugin = build_default_registry().get_plugin("three_phase_three_level_npc_inverter")
    return run_full_pipeline(
        plugin=plugin,
        raw_input=build_default_inputs() | {"include_epcos_screw_terminal_electrolytics": "true"},
        include_waveforms=True,
        pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
        output_root=tmp_path / "npc-run",
    )


def test_npc_capacitor_audit_has_split_banks_and_run_scoped_artifacts(tmp_path: Path) -> None:
    report = _report(tmp_path)
    report = run_capacitor_pipeline(report, build_default_registry().get_plugin(report.spec.topology_id))
    assert report.capacitor is not None
    design = report.capacitor.npc_design
    assert design is not None
    assert design.baseline_part_number == "B43705A9568M600"
    assert design.baseline_series_count == 2
    assert design.upper_bank is not None and design.lower_bank is not None
    assert design.upper_bank.series_count == 2
    assert design.lower_bank.series_count == 2
    assert design.upper_bank.conservative_esr_basis != "datasheet ESRmax"
    assert design.upper_bank.equalizer_resistance_ohm == 100_000.0
    assert design.upper_bank.film_capacitance_per_leg_f > 0.0
    assert design.upper_bank.precharge_resistance_ohm == 10_000.0
    assert {item.scenario_id for item in design.scenarios} == {
        "rated", "load_variation", "pf_variation", "modulation_variation",
        "capacitor_mismatch", "three_phase_imbalance",
    }
    assert all(Path(path).is_file() for path in design.artifact_paths)
    assert all(Path(path).parent.name == "capacitor_design" for path in design.artifact_paths)
    payload = json.loads(Path(design.artifact_paths[0]).read_text(encoding="ascii"))
    assert payload["upper_bank"]["checks"]
    assert payload["scenarios"]


def test_npc_capacitor_audit_reports_required_checks_and_structured_payload(tmp_path: Path) -> None:
    report = _report(tmp_path)
    report = run_capacitor_pipeline(report, build_default_registry().get_plugin(report.spec.topology_id))
    design = report.capacitor.npc_design
    assert design is not None
    for bank in (design.upper_bank, design.lower_bank):
        assert bank is not None
        assert bank.expected_life_hours > 0.0
        assert bank.ripple_current_rating_a > 0.0
        assert bank.surge_current_rating_a > 0.0
        assert bank.precharge_energy_j > 0.0
        assert {"hotspot", "life", "ripple_current", "surge_current"}.issubset(bank.checks)
    assert design.worst_midpoint_deviation_ratio >= 0.0
    assert design.total_design_volume_l > 0.0
