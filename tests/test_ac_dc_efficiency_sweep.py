from __future__ import annotations

from dataclasses import dataclass, replace
from importlib import import_module
import importlib
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.app.result_views.efficiency_view import build_efficiency_summary_text
from pe_claw_gui.pipeline import run_efficiency_sweep, run_full_pipeline
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import efficiency_sweep_blocking_warning
from pe_claw_gui.topologies.base.registry import build_default_registry


EFFICIENCY_SWEEP_PIPELINE = importlib.import_module(
    "pe_claw_gui.pipeline.run_efficiency_sweep_pipeline"
)
BRIDGE_RECTIFIER_PIPELINE = importlib.import_module(
    "pe_claw_gui.pipeline.run_bridge_rectifier_pipeline"
)
CAPACITOR_PIPELINE = importlib.import_module("pe_claw_gui.pipeline.run_capacitor_pipeline")
DEVICE_PIPELINE = importlib.import_module("pe_claw_gui.pipeline.run_device_pipeline")
MAGNETIC_PIPELINE = importlib.import_module("pe_claw_gui.pipeline.run_magnetic_pipeline")


AC_DC_TOPOLOGY_IDS = (
    "single_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_diode_bridge_rectifier_dc_inductor_filter",
    "three_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_boost_pfc_diode_bridge",
    "single_phase_totem_pole_bridgeless_pfc",
)
AC_DC_BRIDGE_TOPOLOGY_IDS = {
    "single_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_diode_bridge_rectifier_dc_inductor_filter",
    "three_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_boost_pfc_diode_bridge",
}
AC_DC_PFC_TOPOLOGY_IDS = {
    "single_phase_boost_pfc_diode_bridge",
    "single_phase_totem_pole_bridgeless_pfc",
}
DC_REACTOR_TOPOLOGY_ID = "single_phase_diode_bridge_rectifier_dc_inductor_filter"
BOOST_PFC_TOPOLOGY_ID = "single_phase_boost_pfc_diode_bridge"
TOTEM_POLE_TOPOLOGY_ID = "single_phase_totem_pole_bridgeless_pfc"


@dataclass(frozen=True)
class FullAcDcCase:
    topology_id: str
    plugin: object
    report: object
    result: object
    output_dir: Path
    hardware_snapshot: dict[str, object]


@pytest.fixture(scope="module")
def full_ac_dc_cases(tmp_path_factory: pytest.TempPathFactory) -> dict[str, FullAcDcCase]:
    """Build each complete AC-DC design once for the regression module."""

    registry = build_default_registry()
    output_root = tmp_path_factory.mktemp("ac_dc_efficiency_full")
    cases: dict[str, FullAcDcCase] = {}
    options = PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=True)
    for topology_id in AC_DC_TOPOLOGY_IDS:
        plugin = registry.get_plugin(topology_id)
        topology_module = import_module(plugin.__module__)
        report = run_full_pipeline(
            plugin=plugin,
            raw_input=topology_module.build_default_inputs(),
            include_waveforms=True,
            pipeline_options=options,
        )
        hardware_snapshot = _hardware_snapshot(report)
        output_dir = output_root / topology_id
        result = run_efficiency_sweep(
            report,
            plugin=plugin,
            load_points=(0.5, 1.0),
            output_dir=output_dir,
        )
        cases[topology_id] = FullAcDcCase(
            topology_id=topology_id,
            plugin=plugin,
            report=report,
            result=result,
            output_dir=output_dir,
            hardware_snapshot=hardware_snapshot,
        )
    return cases


@pytest.mark.parametrize("topology_id", sorted(AC_DC_BRIDGE_TOPOLOGY_IDS))
def test_bridge_selection_precedes_dependent_full_pipeline_stages(
    topology_id: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bridge hardware must exist before dependent design stages run."""

    registry = build_default_registry()
    plugin = registry.get_plugin(topology_id)
    topology_module = import_module(plugin.__module__)
    pipeline_module = importlib.import_module("pe_claw_gui.pipeline.run_full_pipeline")
    events: list[str] = []

    original_bridge = pipeline_module.run_bridge_rectifier_pipeline

    def record_bridge(report, *args, **kwargs):
        events.append("bridge")
        return original_bridge(report, *args, **kwargs)

    def record_stage(name: str):
        def stage(report, *args, **kwargs):
            events.append(name)
            return report

        return stage

    monkeypatch.setattr(pipeline_module, "run_bridge_rectifier_pipeline", record_bridge)
    monkeypatch.setattr(pipeline_module, "run_magnetic_pipeline", record_stage("magnetic"))
    monkeypatch.setattr(pipeline_module, "run_loss_pipeline", record_stage("loss"))
    monkeypatch.setattr(pipeline_module, "run_thermal_pipeline", record_stage("thermal"))
    monkeypatch.setattr(pipeline_module, "run_geometry_pipeline", record_stage("geometry"))

    report = run_full_pipeline(
        plugin=plugin,
        raw_input=topology_module.build_default_inputs(),
        include_waveforms=False,
        pipeline_options=PipelineOptions(
            enable_magnetic_design=True,
            enable_capacitor_design=False,
            enable_bridge_rectifier_selection=True,
        ),
    )

    assert report.bridge_rectifier is not None
    assert report.bridge_rectifier.selected_candidate is not None
    assert report.bridge_rectifier.passed_candidate_count > 0
    assert events.index("bridge") < events.index("magnetic")
    assert events.index("bridge") < events.index("loss")
    assert events.index("bridge") < events.index("thermal")
    assert events.index("bridge") < events.index("geometry")


@pytest.mark.parametrize("topology_id", AC_DC_TOPOLOGY_IDS)
def test_ac_dc_complete_design_and_efficiency_sweep(
    full_ac_dc_cases: dict[str, FullAcDcCase],
    topology_id: str,
) -> None:
    case = full_ac_dc_cases[topology_id]
    report = case.report
    result = case.result

    assert report.candidate is not None
    assert report.waveform is not None
    assert report.stress is not None
    assert report.topology_result is not None
    assert report.capacitor is not None
    assert report.capacitor.output_selection is not None
    assert report.capacitor.output_selection.recommended is not None
    assert result.load_grid == (0.5, 1.0)
    assert len(result.points) == 2
    assert any(point.efficiency is not None for point in result.points)
    assert all(
        point.efficiency is None or 0.0 < point.efficiency <= 1.0
        for point in result.points
    )
    assert result.warnings == ()
    assert result.signature
    assert set(result.artifact_paths) == {"csv", "efficiency_curve", "loss_breakdown_stacked"}
    assert all(
        Path(path).exists() and Path(path).stat().st_size > 0
        for path in result.artifact_paths.values()
    )
    assert _hardware_snapshot(report) == case.hardware_snapshot
    assert all(point.capacitor_loss_w is not None for point in result.points)

    if topology_id in AC_DC_BRIDGE_TOPOLOGY_IDS:
        assert report.bridge_rectifier is not None
        assert report.bridge_rectifier.selected_candidate is not None
        assert report.bridge_rectifier.passed_candidate_count > 0
        assert all(point.bridge_rectifier_loss_w is not None for point in result.points)
    else:
        assert report.bridge_rectifier is None
        assert all(point.bridge_rectifier_loss_w is None for point in result.points)

    if topology_id == DC_REACTOR_TOPOLOGY_ID:
        reactor_result = report.magnetic.ac_dc_reactor_result
        assert reactor_result is not None
        assert reactor_result.selected_candidate is not None
        assert all(point.magnetic_loss_w is not None for point in result.points)
    elif topology_id in AC_DC_PFC_TOPOLOGY_IDS:
        assert report.magnetic is not None
        assert report.magnetic.selected_design_id
        assert all(point.magnetic_loss_w is not None for point in result.points)

    if topology_id == BOOST_PFC_TOPOLOGY_ID:
        assert report.device is not None
        assert {"main_switch", "rectifier_diode"}.issubset(report.device.selected_devices)
        assert all(point.semiconductor_loss_w is not None for point in result.points)
    elif topology_id == TOTEM_POLE_TOPOLOGY_ID:
        assert report.device is not None
        assert {"totem_pole_hf_switch", "totem_pole_lf_switch"}.issubset(
            report.device.selected_devices
        )
        assert all(point.semiconductor_loss_w is not None for point in result.points)
    else:
        assert report.device is None
        assert all(point.semiconductor_loss_w is None for point in result.points)


def test_ac_dc_efficiency_sweep_prerequisite_warnings(
    full_ac_dc_cases: dict[str, FullAcDcCase],
) -> None:
    bridge_report = full_ac_dc_cases[
        "single_phase_diode_bridge_rectifier_capacitor_filter"
    ].report
    reactor_report = full_ac_dc_cases[DC_REACTOR_TOPOLOGY_ID].report
    boost_report = full_ac_dc_cases[BOOST_PFC_TOPOLOGY_ID].report
    totem_report = full_ac_dc_cases[TOTEM_POLE_TOPOLOGY_ID].report

    assert efficiency_sweep_blocking_warning(replace(bridge_report, bridge_rectifier=None)) == (
        "Efficiency sweep requires selected AC-DC bridge rectifier hardware from Run Design."
    )
    assert efficiency_sweep_blocking_warning(replace(reactor_report, magnetic=None)) == (
        "Efficiency sweep requires selected AC-DC reactor hardware from Run Magnetics."
    )
    assert efficiency_sweep_blocking_warning(replace(boost_report, capacitor=None)) == (
        "Boost PFC efficiency sweep requires selected DC-link capacitor hardware from Run Capacitor."
    )
    assert efficiency_sweep_blocking_warning(replace(boost_report, magnetic=None)) == (
        "Boost PFC efficiency sweep requires selected boost-inductor hardware from Run Magnetics."
    )
    incomplete_boost_device = replace(
        boost_report.device,
        selected_devices={"main_switch": boost_report.device.selected_devices["main_switch"]},
    )
    assert efficiency_sweep_blocking_warning(replace(boost_report, device=incomplete_boost_device)) == (
        "Boost PFC efficiency sweep requires selected boost switch and independent boost diode hardware."
    )
    incomplete_totem_device = replace(
        totem_report.device,
        selected_devices={
            "totem_pole_hf_switch": totem_report.device.selected_devices["totem_pole_hf_switch"]
        },
    )
    assert efficiency_sweep_blocking_warning(replace(totem_report, device=incomplete_totem_device)) == (
        "Totem-Pole PFC efficiency sweep requires selected HF and LF switch hardware."
    )


def test_ac_dc_efficiency_sweep_does_not_reselect_fixed_hardware(
    full_ac_dc_cases: dict[str, FullAcDcCase],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fail_reselection(*args, **kwargs):
        raise AssertionError("Efficiency sweep attempted to reselect fixed hardware.")

    monkeypatch.setattr(BRIDGE_RECTIFIER_PIPELINE, "select_bridge_rectifier", fail_reselection)
    monkeypatch.setattr(CAPACITOR_PIPELINE, "select_capacitor_bank", fail_reselection)
    monkeypatch.setattr(DEVICE_PIPELINE, "run_device_pipeline", fail_reselection)
    monkeypatch.setattr(MAGNETIC_PIPELINE, "select_ac_dc_sendust_reactor", fail_reselection)
    monkeypatch.setattr(
        MAGNETIC_PIPELINE,
        "synthesize_fixed_inductor_candidates_with_backend",
        fail_reselection,
    )

    for topology_id, case in full_ac_dc_cases.items():
        result = run_efficiency_sweep(
            case.report,
            plugin=case.plugin,
            load_points=(0.75,),
            output_dir=tmp_path / topology_id,
        )
        assert len(result.points) == 1
        assert result.points[0].efficiency is not None
        assert _hardware_snapshot(case.report) == case.hardware_snapshot


def test_efficiency_sweep_handles_empty_ac_dc_waveform(
    full_ac_dc_cases: dict[str, FullAcDcCase],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    case = full_ac_dc_cases["single_phase_diode_bridge_rectifier_capacitor_filter"]

    def return_no_waveform(self, candidate, operating_point=None):
        return None

    monkeypatch.setattr(type(case.plugin), "generate_waveforms", return_no_waveform)
    result = run_efficiency_sweep(
        case.report,
        plugin=case.plugin,
        load_points=(0.33,),
        output_dir=tmp_path,
    )

    assert len(result.points) == 1
    assert result.points[0].efficiency is None
    assert "waveform generation returned no data" in result.points[0].warnings[0]


def test_efficiency_sweep_isolates_a_failed_ac_dc_load_point(
    full_ac_dc_cases: dict[str, FullAcDcCase],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    case = full_ac_dc_cases["single_phase_diode_bridge_rectifier_capacitor_filter"]
    original_evaluator = EFFICIENCY_SWEEP_PIPELINE._evaluate_ac_dc_load_point

    def fail_half_load(base_report, active_plugin, load_pu):
        if load_pu == 0.5:
            raise RuntimeError("synthetic waveform failure")
        return original_evaluator(base_report, active_plugin, load_pu)

    monkeypatch.setattr(EFFICIENCY_SWEEP_PIPELINE, "_evaluate_ac_dc_load_point", fail_half_load)
    result = run_efficiency_sweep(
        case.report,
        plugin=case.plugin,
        load_points=(0.5, 1.0),
        output_dir=tmp_path,
    )

    assert len(result.points) == 2
    assert result.points[0].efficiency is None
    assert "synthetic waveform failure" in result.points[0].warnings[0]
    assert result.points[1].efficiency is not None


def test_ac_dc_result_names_bridge_loss_and_writes_artifacts(
    full_ac_dc_cases: dict[str, FullAcDcCase],
    tmp_path: Path,
) -> None:
    case = full_ac_dc_cases["single_phase_diode_bridge_rectifier_capacitor_filter"]
    result = run_efficiency_sweep(
        case.report,
        plugin=case.plugin,
        load_points=(0.1, 1.0),
        output_dir=tmp_path,
    )

    assert all(point.bridge_rectifier_loss_w is not None for point in result.points)
    assert all(point.semiconductor_loss_w is None for point in result.points)
    assert all(point.loss_breakdown_w.get("bridge_rectifier") is not None for point in result.points)
    assert result.peak_efficiency == max(
        point.efficiency for point in result.points if point.efficiency is not None
    )
    assert result.full_load_efficiency == result.points[1].efficiency
    assert result.light_load_efficiency == result.points[0].efficiency
    assert "bridge rectifier" in result.sweep_basis["included_losses"]
    assert set(result.artifact_paths) == {"csv", "efficiency_curve", "loss_breakdown_stacked"}
    assert all(Path(path).exists() for path in result.artifact_paths.values())
    assert "bridge rectifier:" in build_efficiency_summary_text(result)


def test_efficiency_sweep_reuses_matching_cached_result(
    full_ac_dc_cases: dict[str, FullAcDcCase],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = full_ac_dc_cases["single_phase_diode_bridge_rectifier_capacitor_filter"]
    cached_report = replace(case.report, efficiency_sweep=case.result)

    def fail_evaluation(*args, **kwargs):
        raise AssertionError("Matching efficiency sweep cache was not reused.")

    monkeypatch.setattr(EFFICIENCY_SWEEP_PIPELINE, "_evaluate_sweep_load_point", fail_evaluation)
    reused = run_efficiency_sweep(
        cached_report,
        plugin=case.plugin,
        load_points=(0.5, 1.0),
        output_dir=case.output_dir,
    )

    assert reused is case.result


def test_efficiency_sweep_signature_invalidates_for_changed_hardware(
    full_ac_dc_cases: dict[str, FullAcDcCase],
    tmp_path: Path,
) -> None:
    load_grid = (0.5, 1.0)

    bridge_report = full_ac_dc_cases[
        "single_phase_diode_bridge_rectifier_capacitor_filter"
    ].report
    bridge = bridge_report.bridge_rectifier
    changed_bridge = replace(
        bridge,
        selected_candidate=replace(
            bridge.selected_candidate,
            vf_max_v=bridge.selected_candidate.vf_max_v + 0.01,
        ),
    )
    changed_bridge_report = replace(
        bridge_report,
        bridge_rectifier=changed_bridge,
        efficiency_sweep=full_ac_dc_cases[
            "single_phase_diode_bridge_rectifier_capacitor_filter"
        ].result,
    )
    _assert_signature_changes(bridge_report, changed_bridge_report, load_grid)
    changed_bridge_result = run_efficiency_sweep(
        changed_bridge_report,
        plugin=full_ac_dc_cases[
            "single_phase_diode_bridge_rectifier_capacitor_filter"
        ].plugin,
        load_points=load_grid,
        output_dir=tmp_path / "changed_bridge",
    )
    assert changed_bridge_result is not changed_bridge_report.efficiency_sweep
    assert changed_bridge_result.signature != changed_bridge_report.efficiency_sweep.signature

    reactor_report = full_ac_dc_cases[DC_REACTOR_TOPOLOGY_ID].report
    reactor_result = reactor_report.magnetic.ac_dc_reactor_result
    changed_reactor_result = replace(
        reactor_result,
        selected_candidate=replace(
            reactor_result.selected_candidate,
            candidate_id=f"{reactor_result.selected_candidate.candidate_id}-alternate",
        ),
    )
    changed_reactor_report = replace(
        reactor_report,
        magnetic=replace(reactor_report.magnetic, ac_dc_reactor_result=changed_reactor_result),
    )
    _assert_signature_changes(reactor_report, changed_reactor_report, load_grid)

    boost_report = full_ac_dc_cases[BOOST_PFC_TOPOLOGY_ID].report
    changed_devices = dict(boost_report.device.selected_devices)
    changed_devices["main_switch"] = f"{changed_devices['main_switch']}-alternate"
    changed_device_report = replace(
        boost_report,
        device=replace(boost_report.device, selected_devices=changed_devices),
    )
    _assert_signature_changes(boost_report, changed_device_report, load_grid)

    capacitor_report = full_ac_dc_cases[TOTEM_POLE_TOPOLOGY_ID].report
    output_selection = capacitor_report.capacitor.output_selection
    changed_output_selection = replace(
        output_selection,
        recommended=replace(
            output_selection.recommended,
            parallel_count=output_selection.recommended.parallel_count + 1,
        ),
    )
    changed_capacitor_report = replace(
        capacitor_report,
        capacitor=replace(capacitor_report.capacitor, output_selection=changed_output_selection),
    )
    _assert_signature_changes(capacitor_report, changed_capacitor_report, load_grid)


def test_efficiency_sweep_regenerates_missing_artifacts(
    full_ac_dc_cases: dict[str, FullAcDcCase],
    tmp_path: Path,
) -> None:
    case = full_ac_dc_cases["single_phase_diode_bridge_rectifier_capacitor_filter"]
    first = run_efficiency_sweep(
        case.report,
        plugin=case.plugin,
        load_points=(0.5, 1.0),
        output_dir=tmp_path,
    )
    curve_path = Path(first.artifact_paths["efficiency_curve"])
    curve_path.unlink()

    second = run_efficiency_sweep(
        replace(case.report, efficiency_sweep=first),
        plugin=case.plugin,
        load_points=(0.5, 1.0),
        output_dir=tmp_path,
    )

    assert second.signature == first.signature
    assert curve_path.exists()


def _assert_signature_changes(base_report, changed_report, load_grid: tuple[float, ...]) -> None:
    base_signature = EFFICIENCY_SWEEP_PIPELINE._build_signature(base_report, load_grid)
    changed_signature = EFFICIENCY_SWEEP_PIPELINE._build_signature(changed_report, load_grid)
    assert changed_signature != base_signature


def _hardware_snapshot(report) -> dict[str, object]:
    bridge_id = None
    if report.bridge_rectifier is not None and report.bridge_rectifier.selected_candidate is not None:
        bridge_id = report.bridge_rectifier.selected_candidate.candidate_id

    capacitor_bank = None
    if (
        report.capacitor is not None
        and report.capacitor.output_selection is not None
        and report.capacitor.output_selection.recommended is not None
    ):
        recommended = report.capacitor.output_selection.recommended
        capacitor_bank = (
            recommended.candidate.part_number,
            recommended.series_count,
            recommended.parallel_count,
        )

    magnetic_id = None
    if report.magnetic is not None:
        reactor_result = report.magnetic.ac_dc_reactor_result
        if reactor_result is not None and reactor_result.selected_candidate is not None:
            magnetic_id = reactor_result.selected_candidate.candidate_id
        else:
            magnetic_id = report.magnetic.selected_design_id

    return {
        "bridge_rectifier": bridge_id,
        "selected_devices": tuple(
            sorted((report.device.selected_devices if report.device is not None else {}).items())
        ),
        "capacitor_bank": capacitor_bank,
        "magnetic_design": magnetic_id,
    }
