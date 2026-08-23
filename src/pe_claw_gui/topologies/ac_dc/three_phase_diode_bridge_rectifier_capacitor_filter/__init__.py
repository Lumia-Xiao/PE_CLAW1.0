"""Three-phase diode bridge rectifier with DC-link capacitor filter."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ....models.design_report import DesignReport
from ....models.operating_point import OperatingPoint
from ....models.stress_result import StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from ...base.interface import TopologyPlugin
from ...base.result import TopologyResult
from ...base.spec import TopologySpec
from .evaluator import build_report, evaluate
from .input_schema import DISPLAY_NAME, LEGACY_KEY, TOPOLOGY_ID, build_default_inputs, build_spec
from .stress import extract_stress
from .synthesizer import calculate_three_phase_diode_bridge_capacitor_filter_phase1, synthesize
from .waveform import (
    build_three_phase_diode_bridge_waveform_preview,
    generate_waveforms,
    refresh_selected_capacitor_candidate,
    simulate_three_phase_rectifier_for_load,
)
from .simulation import power_factor_requirement_status, simulate_three_phase_capacitor_rectifier


@dataclass(frozen=True)
class ThreePhaseDiodeBridgeRectifierCapacitorFilterPlugin(TopologyPlugin):
    """Runtime plugin for Phase 1 three-phase AC-DC diode bridge estimates."""

    topology_id: str = TOPOLOGY_ID
    display_name: str = DISPLAY_NAME
    legacy_key: str = LEGACY_KEY
    implemented: bool = True

    def build_spec(self, raw_input: Mapping[str, str]) -> TopologySpec:
        return build_spec(raw_input)

    def synthesize(self, spec: TopologySpec) -> TopologyCandidate:
        return synthesize(spec)

    def generate_waveforms(
        self,
        candidate: TopologyCandidate,
        operating_point: OperatingPoint | None = None,
    ) -> WaveformSet | None:
        return generate_waveforms(candidate, operating_point=operating_point)

    def extract_stress(
        self,
        candidate: TopologyCandidate,
        waveform_set: WaveformSet | None = None,
    ) -> StressResult:
        return extract_stress(candidate, waveform_set=waveform_set)

    def evaluate(
        self,
        candidate: TopologyCandidate,
        waveform_set: WaveformSet | None = None,
        stress_result: StressResult | None = None,
    ) -> TopologyResult:
        return evaluate(candidate, waveform_set=waveform_set, stress_result=stress_result)

    def build_report(
        self,
        spec: TopologySpec,
        candidate: TopologyCandidate,
        operating_point: OperatingPoint | None = None,
        waveform_set: WaveformSet | None = None,
        stress_result: StressResult | None = None,
        topology_result: TopologyResult | None = None,
    ) -> DesignReport:
        return build_report(
            spec=spec,
            candidate=candidate,
            operating_point=operating_point,
            waveform_set=waveform_set,
            stress_result=stress_result,
            topology_result=topology_result,
        )


PLUGIN = ThreePhaseDiodeBridgeRectifierCapacitorFilterPlugin()

__all__ = [
    "DISPLAY_NAME",
    "LEGACY_KEY",
    "PLUGIN",
    "TOPOLOGY_ID",
    "ThreePhaseDiodeBridgeRectifierCapacitorFilterPlugin",
    "build_default_inputs",
    "build_spec",
    "build_three_phase_diode_bridge_waveform_preview",
    "calculate_three_phase_diode_bridge_capacitor_filter_phase1",
    "evaluate",
    "extract_stress",
    "generate_waveforms",
    "refresh_selected_capacitor_candidate",
    "simulate_three_phase_capacitor_rectifier",
    "simulate_three_phase_rectifier_for_load",
    "power_factor_requirement_status",
    "synthesize",
]
