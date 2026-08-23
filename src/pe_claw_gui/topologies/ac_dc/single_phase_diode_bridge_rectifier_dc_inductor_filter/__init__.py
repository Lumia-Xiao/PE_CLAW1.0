"""Single-phase diode bridge rectifier with DC-side smoothing inductor."""

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
from .synthesizer import calculate_choke_input_estimates, calculate_small_dc_reactor_estimates, synthesize
from .waveform import generate_waveforms, refresh_selected_hardware_candidate
from .simulation import simulate_ac_dc_diode_bridge_dc_inductor_filter, solve_rload_for_target_power_dc_inductor


@dataclass(frozen=True)
class SinglePhaseDiodeBridgeRectifierDCInductorFilterPlugin(TopologyPlugin):
    """Runtime plugin for the Phase 1 AC-DC DC-side inductor rectifier."""

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


PLUGIN = SinglePhaseDiodeBridgeRectifierDCInductorFilterPlugin()

__all__ = [
    "DISPLAY_NAME",
    "LEGACY_KEY",
    "PLUGIN",
    "TOPOLOGY_ID",
    "SinglePhaseDiodeBridgeRectifierDCInductorFilterPlugin",
    "build_default_inputs",
    "build_spec",
    "calculate_choke_input_estimates",
    "calculate_small_dc_reactor_estimates",
    "evaluate",
    "extract_stress",
    "generate_waveforms",
    "refresh_selected_hardware_candidate",
    "simulate_ac_dc_diode_bridge_dc_inductor_filter",
    "solve_rload_for_target_power_dc_inductor",
    "synthesize",
]
