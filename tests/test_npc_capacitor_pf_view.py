from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.app.result_views.capacitor_pf_view import (
    build_capacitor_pf_side_summary,
    resolve_capacitor_pf_plot_paths,
)
from pe_claw_gui.app.result_views import capacitor_pf_view


def _report(tmp_path: Path):
    upper_png = tmp_path / "upper_capacitor_pareto_front.png"
    lower_png = tmp_path / "lower_capacitor_pareto_front.png"
    upper_csv = tmp_path / "upper_capacitor_pareto_front.csv"
    lower_csv = tmp_path / "lower_capacitor_pareto_front.csv"
    for path in (upper_png, lower_png, upper_csv, lower_csv):
        path.write_bytes(b"artifact")

    upper = SimpleNamespace(
        request=SimpleNamespace(
            side="upper",
            dc_voltage_v=425.0,
            ripple_ratio_percent=5.0,
        ),
        artifact_paths=[str(tmp_path / "upper_capacitor_feasible_candidates.csv"), str(upper_csv), str(upper_png)],
        warnings=[],
        notes=[],
        evaluated_count=1,
        feasible_count=1,
        pareto_front=[],
        recommended_policy_name="",
        minimum_feasible_parallel_count=None,
        recommended_parallel_count=None,
        recommended_ripple_utilization=None,
        recommended_selection_reason="",
        recommended=None,
        min_volume=None,
        min_loss=None,
        compromise=None,
    )
    lower = SimpleNamespace(**{**upper.__dict__, "request": SimpleNamespace(side="lower", dc_voltage_v=425.0, ripple_ratio_percent=5.0), "artifact_paths": [str(lower_csv), str(lower_png)]})
    return SimpleNamespace(
        spec=SimpleNamespace(topology_id="three_phase_three_level_npc_inverter"),
        capacitor=SimpleNamespace(
            input_selection=upper,
            output_selection=lower,
            artifact_paths=[str(upper_png), str(lower_png)],
            llc_resonant_capacitor_search_result=None,
        ),
    )


def test_npc_pf_view_maps_input_output_to_upper_lower_artifacts(tmp_path: Path) -> None:
    report = _report(tmp_path)

    paths = resolve_capacitor_pf_plot_paths(report)

    assert paths == {
        "input": tmp_path / "upper_capacitor_pareto_front.png",
        "output": tmp_path / "lower_capacitor_pareto_front.png",
    }
    assert "Upper DC-link capacitor Pareto front" in build_capacitor_pf_side_summary(report, "input", paths["input"])
    assert "upper_capacitor_pareto_front.csv" in build_capacitor_pf_side_summary(report, "input", paths["input"])
    assert "Lower DC-link capacitor Pareto front" in build_capacitor_pf_side_summary(report, "output", paths["output"])
    assert "lower_capacitor_pareto_front.csv" in build_capacitor_pf_side_summary(report, "output", paths["output"])
    assert capacitor_pf_view._side_label(report, "input") == "Upper DC-link capacitor"
    assert capacitor_pf_view._side_label(report, "output") == "Lower DC-link capacitor"


def test_non_npc_pf_view_keeps_input_output_artifact_names(tmp_path: Path) -> None:
    report = _report(tmp_path)
    report.spec.topology_id = "single_phase_full_bridge_inverter"
    input_png = tmp_path / "input_capacitor_pareto_front.png"
    output_png = tmp_path / "output_capacitor_pareto_front.png"
    input_png.write_bytes(b"artifact")
    output_png.write_bytes(b"artifact")
    report.capacitor.input_selection.artifact_paths = [str(input_png)]
    report.capacitor.output_selection.artifact_paths = [str(output_png)]

    paths = resolve_capacitor_pf_plot_paths(report)

    assert paths == {"input": input_png, "output": output_png}
