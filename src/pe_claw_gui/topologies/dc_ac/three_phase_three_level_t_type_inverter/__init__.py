"""Input-contract and plugin skeleton for the first-round T-type inverter.

All six first-pass hooks and the topology-only registry/GUI path are implemented.
Component selection and loss/efficiency stages remain unavailable.
"""

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
from .input_schema import build_default_inputs, build_spec
from .synthesizer import calculate_three_phase_three_level_t_type_inverter, synthesize
from .topology_contract import DISPLAY_NAME, LEGACY_KEY, TOPOLOGY_ID
from .waveform import generate_waveforms
from .stress import extract_stress
from .evaluator import evaluate, build_report


@dataclass(frozen=True)
class ThreePhaseThreeLevelTTypeInverterPlugin(TopologyPlugin):
    """Unregistered T-type plugin skeleton with an explicit staged boundary."""

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
        return extract_stress(candidate, waveform_set)

    def evaluate(
        self,
        candidate: TopologyCandidate,
        waveform_set: WaveformSet | None = None,
        stress_result: StressResult | None = None,
    ) -> TopologyResult:
        return evaluate(candidate, waveform_set, stress_result)

    def build_report(
        self,
        spec: TopologySpec,
        candidate: TopologyCandidate,
        operating_point: OperatingPoint | None = None,
        waveform_set: WaveformSet | None = None,
        stress_result: StressResult | None = None,
        topology_result: TopologyResult | None = None,
    ) -> DesignReport:
        return build_report(spec, candidate, operating_point, waveform_set, stress_result, topology_result)


PLUGIN = ThreePhaseThreeLevelTTypeInverterPlugin()

__all__ = [
    "DISPLAY_NAME",
    "LEGACY_KEY",
    "PLUGIN",
    "TOPOLOGY_ID",
    "ThreePhaseThreeLevelTTypeInverterPlugin",
    "build_default_inputs",
    "build_spec",
    "calculate_three_phase_three_level_t_type_inverter",
    "generate_waveforms",
    "synthesize",
]
