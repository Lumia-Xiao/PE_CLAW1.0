"""Plugin contract for runtime topology adapters."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from ...models.design_report import DesignReport
from ...models.operating_point import OperatingPoint
from ...models.stress_result import StressResult
from ...models.waveform import WaveformSet
from .candidate import TopologyCandidate
from .result import TopologyResult
from .spec import TopologySpec


@runtime_checkable
class TopologyPlugin(Protocol):
    """Minimal plugin contract for runtime topology integration."""

    topology_id: str
    display_name: str
    legacy_key: str
    implemented: bool

    def build_spec(self, raw_input: Mapping[str, str]) -> TopologySpec:
        """Normalize raw GUI values into a topology spec."""

    def synthesize(self, spec: TopologySpec) -> TopologyCandidate:
        """Create a topology candidate from a normalized spec."""

    def generate_waveforms(
        self,
        candidate: TopologyCandidate,
        operating_point: OperatingPoint | None = None,
    ) -> WaveformSet | None:
        """Generate waveforms for a synthesized candidate."""

    def extract_stress(
        self,
        candidate: TopologyCandidate,
        waveform_set: WaveformSet | None = None,
    ) -> StressResult:
        """Extract electrical stress from a candidate and optional waveforms."""

    def evaluate(
        self,
        candidate: TopologyCandidate,
        waveform_set: WaveformSet | None = None,
        stress_result: StressResult | None = None,
    ) -> TopologyResult:
        """Build a topology-level evaluation summary."""

    def build_report(
        self,
        spec: TopologySpec,
        candidate: TopologyCandidate,
        operating_point: OperatingPoint | None = None,
        waveform_set: WaveformSet | None = None,
        stress_result: StressResult | None = None,
        topology_result: TopologyResult | None = None,
    ) -> DesignReport:
        """Assemble a design report for the runtime pipeline."""
