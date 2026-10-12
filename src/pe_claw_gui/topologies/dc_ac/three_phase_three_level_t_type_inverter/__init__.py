"""Input-contract and plugin skeleton for the first-round T-type inverter.

Only ``build_spec`` is implemented in step 1. Calculation hooks raise an
explicit ``NotImplementedError`` until their implementation steps complete;
the plugin is deliberately not registered in the application yet.
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


@dataclass(frozen=True)
class ThreePhaseThreeLevelTTypeInverterPlugin(TopologyPlugin):
    """Unregistered T-type plugin skeleton with an explicit staged boundary."""

    topology_id: str = TOPOLOGY_ID
    display_name: str = DISPLAY_NAME
    legacy_key: str = LEGACY_KEY
    implemented: bool = False

    def build_spec(self, raw_input: Mapping[str, str]) -> TopologySpec:
        return build_spec(raw_input)

    def synthesize(self, spec: TopologySpec) -> TopologyCandidate:
        return synthesize(spec)

    def generate_waveforms(
        self,
        candidate: TopologyCandidate,
        operating_point: OperatingPoint | None = None,
    ) -> WaveformSet | None:
        raise NotImplementedError("T-type waveform generation is planned for implementation step 3.")

    def extract_stress(
        self,
        candidate: TopologyCandidate,
        waveform_set: WaveformSet | None = None,
    ) -> StressResult:
        raise NotImplementedError("T-type stress extraction is planned for implementation step 5.")

    def evaluate(
        self,
        candidate: TopologyCandidate,
        waveform_set: WaveformSet | None = None,
        stress_result: StressResult | None = None,
    ) -> TopologyResult:
        raise NotImplementedError("T-type evaluation is planned for implementation step 5.")

    def build_report(
        self,
        spec: TopologySpec,
        candidate: TopologyCandidate,
        operating_point: OperatingPoint | None = None,
        waveform_set: WaveformSet | None = None,
        stress_result: StressResult | None = None,
        topology_result: TopologyResult | None = None,
    ) -> DesignReport:
        raise NotImplementedError("T-type report assembly is planned for implementation step 5.")


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
    "synthesize",
]
