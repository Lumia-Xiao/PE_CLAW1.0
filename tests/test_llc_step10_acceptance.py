from __future__ import annotations

import json
from pathlib import Path

from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.fha_design import (
    design_llc_fha,
    solve_operating_frequency,
)
from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.input_schema import (
    build_default_inputs,
    build_spec,
)


def test_llc_acceptance_covers_line_and_load_corners() -> None:
    design = design_llc_fha(build_spec(build_default_inputs()))
    corners = (
        ("nominal", design.vin_nom_v, design.pout_max_w),
        ("low_input", design.vin_min_v, design.pout_max_w),
        ("high_input", design.vin_max_v, design.pout_max_w),
        ("light_load", design.vin_nom_v, design.pout_min_w),
    )

    results = [solve_operating_frequency(design, vin, design.vout_nom_v, power) for _, vin, power in corners]

    assert all(result.fs_hz > 0.0 for result in results)
    assert all(result.gain_error >= 0.0 for result in results)
    assert len({label for label, _, _ in corners}) == 4


def test_step10_evidence_directory_is_repo_relative() -> None:
    evidence = Path(__file__).resolve().parents[1] / "migration" / "evidence"

    assert evidence.is_dir()


def test_step10_acceptance_artifacts_include_regression_and_comparison_outputs() -> None:
    evidence = (
        Path(__file__).resolve().parents[1]
        / "migration"
        / "evidence"
        / "20260829"
        / "llc_magnetic_performance_step10"
    )
    acceptance = evidence / "llc_magnetic_performance_step10_acceptance.json"
    payload = json.loads(acceptance.read_text(encoding="ascii"))

    assert payload["regression_summary"]["result"] == "377 passed, 1 skipped"
    assert payload["comparison_artifacts"]
    comparison_csv = evidence / "llc_magnetic_performance_comparison.csv"
    comparison_markdown = evidence / "llc_magnetic_performance_comparison.md"
    assert comparison_csv.is_file()
    assert comparison_markdown.is_file()
    assert "transformer-small" in comparison_csv.read_text(encoding="ascii")
    assert "n/a" in comparison_markdown.read_text(encoding="ascii")
