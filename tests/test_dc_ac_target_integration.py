from __future__ import annotations

import json
import sys
from importlib import import_module
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.app.controllers.run_design_controller import RunDesignController
from pe_claw_gui.app.controllers.waveform_controller import WaveformController
from pe_claw_gui.app.result_views.stress_view import build_stress_summary_lines
from pe_claw_gui.app.result_views.summary_view import _build_electrical_parameter_lines
from pe_claw_gui.app.shell.state_store import AppStateStore
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "migration" / "evidence" / "20260827" / "step9_dc_ac" / "dc_ac_target_fixtures.json"
FIXTURES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
TOPOLOGY_IDS = tuple(case["topology_id"] for case in FIXTURES["cases"])
NO_DOWNSTREAM = PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False)
FORBIDDEN_TOKENS = (
    "pe_claw_gui.agentic",
    "pe_claw_gui.agents",
    "ai_design",
    "run_ai_design",
    "design_intent",
    "topology_recommender",
)


def _case(topology_id: str) -> dict[str, object]:
    return next(case for case in FIXTURES["cases"] if case["topology_id"] == topology_id)


def _default_report(topology_id: str):
    registry = build_default_registry()
    plugin = registry.get_plugin(topology_id)
    module = import_module(plugin.__module__)
    return run_full_pipeline(
        plugin=plugin,
        raw_input=module.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=NO_DOWNSTREAM,
    )


def test_target_registry_exposes_exactly_the_three_implemented_dc_ac_topologies() -> None:
    registry = build_default_registry()
    definitions = registry.list_topologies("dc_ac")

    assert tuple(definition.topology_id for definition in definitions) == TOPOLOGY_IDS
    assert all(definition.implemented for definition in definitions)
    assert all(registry.get_plugin(topology_id).implemented for topology_id in TOPOLOGY_IDS)
    assert all(registry.get_form_class(topology_id).implemented for topology_id in TOPOLOGY_IDS)


@pytest.mark.parametrize("topology_id", TOPOLOGY_IDS)
def test_target_fixture_matches_deterministic_design_waveform_and_stress(topology_id: str) -> None:
    case = _case(topology_id)
    report = _default_report(topology_id)
    candidate = report.candidate
    waveform = report.waveform
    stress = report.stress

    assert candidate is not None
    assert waveform is not None
    assert stress is not None
    for key, expected in case["candidate"].items():
        if key in {"phase_count", "switch_position_count", "clamp_diode_count", "dc_link_split_capacitor_count"}:
            assert candidate.metadata.get(key) == expected
        else:
            assert getattr(candidate, key) == pytest.approx(expected)
    assert waveform.mode == case["waveform"]["mode"]
    assert len(waveform.time_s) == case["waveform"]["sample_count"]
    assert stress.switch.voltage_max_v == pytest.approx(case["stress"]["switch_voltage_max_v"])
    assert stress.switch.current_peak_a == pytest.approx(case["stress"]["switch_current_peak_a"])
    assert stress.rectifier.voltage_max_v == pytest.approx(case["stress"]["rectifier_voltage_max_v"])
    assert stress.rectifier.current_peak_a == pytest.approx(case["stress"]["rectifier_current_peak_a"])


@pytest.mark.parametrize("topology_id", TOPOLOGY_IDS)
def test_controller_design_to_waveform_chain_reuses_candidate_and_selected_hardware(topology_id: str) -> None:
    registry = build_default_registry()
    plugin = registry.get_plugin(topology_id)
    module = import_module(plugin.__module__)
    raw_input = module.build_default_inputs()
    store = AppStateStore(registry=registry)
    store.set_selected_topology(topology_id, plugin)
    design_controller = RunDesignController(store)
    waveform_controller = WaveformController(store)

    designed = design_controller.run_active_topology(raw_input)
    assert designed.candidate is not None
    selected_devices = dict(designed.device.selected_devices) if designed.device is not None else {}
    refreshed = waveform_controller.generate_waveforms(
        OperatingPoint(vin_v=float(designed.candidate.vin_nom), load_ratio=0.5, power_factor=0.8),
    )

    assert refreshed.candidate is designed.candidate
    assert refreshed.waveform is not None
    assert refreshed.waveform.load_ratio == pytest.approx(0.5)
    assert refreshed.waveform.metadata["operating_power_factor"] == pytest.approx(0.8)
    assert refreshed.device is not None
    assert refreshed.device.selected_devices == selected_devices
    assert store.design_report is refreshed


@pytest.mark.parametrize("topology_id", TOPOLOGY_IDS)
def test_result_summaries_keep_topology_specific_units_and_roles(topology_id: str) -> None:
    report = _default_report(topology_id)
    rendered = "\n".join(
        [
            *_build_electrical_parameter_lines(report),
            *build_stress_summary_lines(report),
        ]
    )

    assert "Vin_nom" not in rendered
    assert "Duty_nom" not in rendered
    assert "Iout" not in rendered
    assert "Operating PF" in rendered
    if topology_id == "single_phase_full_bridge_inverter":
        assert "Vac_rms" in rendered
        assert "Full-bridge switch stress" in rendered
    elif topology_id == "three_phase_two_level_voltage_source_inverter":
        assert "Vac line-line rms" in rendered
        assert "Six-switch bridge switch stress" in rendered
    else:
        assert "NPC active switch stress" in rendered
        assert "NPC clamp diode stress" in rendered


def test_dc_ac_runtime_sources_have_no_excluded_ai_or_agentic_dependencies() -> None:
    runtime_root = ROOT / "src" / "pe_claw_gui"
    violations: list[str] = []
    for path in runtime_root.rglob("*.py"):
        if "topologies" not in path.parts and "app" not in path.parts and "pipeline" not in path.parts:
            continue
        source = path.read_text(encoding="utf-8").lower()
        for token in FORBIDDEN_TOKENS:
            if token in source:
                violations.append(f"{path.relative_to(ROOT)}: {token}")
    assert violations == []


def test_fixture_records_source_and_target_roots_and_all_three_cases() -> None:
    assert FIXTURES["contract"] == "dc_ac_target_fixture_v1"
    assert FIXTURES["source_root"].endswith("PE_Claw260517_1_extracted\\PE_Claw")
    assert FIXTURES["target_root"].endswith("PE-Claw1.0")
    assert len(FIXTURES["cases"]) == 3
