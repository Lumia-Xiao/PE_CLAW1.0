"""Legacy compatibility dataclasses backed by the new runtime models."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common_spec import CommonSpec
from .design_report import DesignReport
from .stress_result import StressMetric, StressResult
from .waveform import WaveformSet


@dataclass(frozen=True)
class DesignSpec(CommonSpec):
    """Legacy alias for a normalized runtime spec."""

    @property
    def archetype_key(self) -> str:
        return self.metadata.get("legacy_key", self.topology_id)


@dataclass(frozen=True)
class Archetype:
    """Legacy archetype metadata for compatibility imports."""

    key: str
    display_name: str
    converter_family: str
    conduction_mode: str
    rectification: str
    power_flow: str
    description: str = ""


@dataclass(frozen=True)
class CoreDesign:
    """Legacy Buck design shape produced from the new topology candidate."""

    archetype: Archetype
    vin_min: float
    vin_max: float
    vin_nom: float
    vout_target: float
    pout_target: float
    duty_nom: float
    iout: float
    fs_hz: float
    inductance_h: float
    capacitance_f: float
    delta_il: float
    delta_vo: float
    il_peak: float
    il_valley: float
    ccm_valid: bool

    @classmethod
    def from_report(cls, report: DesignReport) -> "CoreDesign":
        if report.candidate is None:
            raise ValueError("Design report does not contain a topology candidate.")
        legacy_key = report.spec.metadata.get("legacy_key", report.spec.topology_id)
        archetype = Archetype(
            key=legacy_key,
            display_name=report.spec.display_name,
            converter_family="Buck",
            conduction_mode="CCM/DCM",
            rectification="Diode",
            power_flow="Unidirectional",
            description="Compatibility archetype generated from the new runtime registry.",
        )
        candidate = report.candidate
        return cls(
            archetype=archetype,
            vin_min=candidate.vin_min,
            vin_max=candidate.vin_max,
            vin_nom=candidate.vin_nom,
            vout_target=candidate.vout_target,
            pout_target=candidate.pout_target,
            duty_nom=candidate.duty_nom,
            iout=candidate.iout,
            fs_hz=candidate.fs_hz,
            inductance_h=candidate.inductance_h,
            capacitance_f=candidate.capacitance_f,
            delta_il=candidate.delta_il,
            delta_vo=candidate.delta_vo,
            il_peak=candidate.il_peak,
            il_valley=candidate.il_valley,
            ccm_valid=candidate.ccm_valid,
        )


StressReport = StressResult


@dataclass(frozen=True)
class DeviceCandidateSet:
    """Legacy placeholder container for future filtered device candidates."""

    mosfets: list[dict] = field(default_factory=list)
    diodes: list[dict] = field(default_factory=list)
    inductors: list[dict] = field(default_factory=list)
    capacitors: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Scheme:
    """One evaluated converter implementation scheme."""

    identifier: str
    label: str
    summary: str
    score: float | None = None
    total_loss_w: float | None = None
    device_selection: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DesignPipelineResult:
    """Legacy pipeline result after the design stage."""

    spec: DesignSpec
    archetype: Archetype
    core_design: CoreDesign
    stress_report: StressReport

    @classmethod
    def from_report(cls, report: DesignReport) -> "DesignPipelineResult":
        spec = DesignSpec(
            topology_id=report.spec.topology_id,
            display_name=report.spec.display_name,
            vin_min=report.spec.vin_min,
            vin_max=report.spec.vin_max,
            vout=report.spec.vout,
            pout=report.spec.pout,
            fs_khz=report.spec.fs_khz,
            ripple_current_ratio=report.spec.ripple_current_ratio,
            ripple_voltage_ratio_percent=report.spec.ripple_voltage_ratio_percent,
            raw_input=report.spec.raw_input,
            metadata=report.spec.metadata,
        )
        core_design = CoreDesign.from_report(report)
        return cls(spec=spec, archetype=core_design.archetype, core_design=core_design, stress_report=report.stress or StressReport(
            switch=StressMetric(0.0, 0.0),
            rectifier=StressMetric(0.0, 0.0),
        ))


@dataclass(frozen=True)
class WaveformPipelineResult:
    """Legacy pipeline result after waveform generation."""

    core_design: CoreDesign
    waveform_set: WaveformSet
    stress_report: StressReport

    @classmethod
    def from_report(cls, report: DesignReport) -> "WaveformPipelineResult":
        if report.waveform is None:
            raise ValueError("Design report does not contain waveform data.")
        return cls(
            core_design=CoreDesign.from_report(report),
            waveform_set=report.waveform,
            stress_report=report.stress or StressReport(
                switch=StressMetric(0.0, 0.0),
                rectifier=StressMetric(0.0, 0.0),
            ),
        )


@dataclass(frozen=True)
class SchemePipelineResult:
    """Legacy placeholder result for the deprecated scheme stage."""

    core_design: CoreDesign
    waveform_set: WaveformSet
    stress_report: StressReport
    device_candidates: DeviceCandidateSet
    ranked_schemes: list[Scheme]
    notes: list[str] = field(default_factory=list)
