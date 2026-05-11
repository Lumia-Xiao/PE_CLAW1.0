"""Aggregate design-report model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .capacitor import CapacitorResult
from .common_spec import CommonSpec
from .device_result import DeviceSelectionResult
from .efficiency_sweep import EfficiencySweepResult
from .geometry_result import GeometryResult
from .loss_result import LossResult
from .magnetic_result import MagneticResult
from .operating_point import OperatingPoint
from .semiconductor_geometry_result import SemiconductorGeometryResult
from .stress_result import StressResult
from .thermal_result import ThermalResult
from .waveform import WaveformSet

if TYPE_CHECKING:
    from ..topologies.base.candidate import TopologyCandidate
    from ..topologies.base.result import TopologyResult


@dataclass(frozen=True)
class DesignReport:
    """End-to-end handoff object used by the new PE-Claw runtime."""

    spec: CommonSpec
    candidate: "TopologyCandidate | None" = None
    operating_point: OperatingPoint | None = None
    waveform: WaveformSet | None = None
    stress: StressResult | None = None
    device: DeviceSelectionResult | None = None
    semiconductor_geometry: SemiconductorGeometryResult | None = None
    loss: LossResult | None = None
    magnetic: MagneticResult | None = None
    thermal: ThermalResult | None = None
    geometry: GeometryResult | None = None
    capacitor: CapacitorResult | None = None
    efficiency_sweep: EfficiencySweepResult | None = None
    run_design_started_at: str | None = None
    run_design_finished_at: str | None = None
    run_design_runtime_seconds: float | None = None
    run_magnetics_started_at: str | None = None
    run_magnetics_finished_at: str | None = None
    run_magnetics_runtime_seconds: float | None = None
    topology_result: "TopologyResult | None" = None
    notes: list[str] = field(default_factory=list)
