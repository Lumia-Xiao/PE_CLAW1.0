"""Active Boost diode-rectified topology plugin."""

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
from .input_schema import BOOST_DISPLAY_NAME, BOOST_LEGACY_KEY, BOOST_TOPOLOGY_ID, build_default_inputs, build_spec
from .stress import extract_stress
from .synthesizer import synthesize
from .waveform import generate_waveforms


@dataclass(frozen=True)
class BoostPlugin(TopologyPlugin):
    """Runtime plugin for Boost_DiodeRectified_Unidirectional."""

    topology_id: str = BOOST_TOPOLOGY_ID
    display_name: str = BOOST_DISPLAY_NAME
    legacy_key: str = BOOST_LEGACY_KEY
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


PLUGIN = BoostPlugin()
