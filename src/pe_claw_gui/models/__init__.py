from .bridge_rectifier import (
    BridgeRectifierCandidate,
    BridgeRectifierCandidateEvaluation,
    BridgeRectifierLossEstimate,
    BridgeRectifierRankingBreakdown,
    BridgeRectifierSelectionRequest,
    BridgeRectifierSelectionResult,
    BridgeRectifierThermalEstimate,
)
from .common_spec import CommonSpec
from .design_assessment import AssessmentDimension, DesignAssessment
from .design_report import DesignReport
from .device_loss import DeviceLossResult, SwitchStress
from .device_result import DeviceSelectionResult
from .efficiency_sweep import EfficiencySweepPoint, EfficiencySweepResult
from .device_thermal import ReferenceJunctionTemperatureEstimate, SinkThermalRequirement
from .geometry_result import GeometryResult, InductorGeometryLayout
from .inductor import (
    FixedInductorDesignCandidate,
    InductorDesignRequest,
    InductorOperatingEvaluation,
    InductorOperatingPointRequest,
)
from .loss_result import LossResult
from .llc_run_context import LlcRunContext
from .magnetic_loss_contract import (
    CoreLossExcitation,
    CoreLossExcitationBuildRequest,
    CoreLossExcitationBuildResult,
    CoreLossExcitationBuildStatus,
    CoreLossEvaluationContext,
    CoreLossResult,
    CoreLossValidityStatus,
    MaterialLossModel,
    MeasuredLossDataset,
    MeasuredLossPoint,
    NormalizedMagneticMaterialV2,
    SourceProvenance,
    TabulatedModelPoint,
)
from .magnetic_result import (
    LlcMagneticResultSummary,
    LlcMagneticStageSummary,
    MagneticResult,
)
from .magnetic_winding_contract import WindingElectricalEvidence
from .openmagnetics_component_contract import (
    CatalogDistributorEntry,
    CatalogGapEntry,
    ComponentNormalizationBatch,
    ComponentNormalizationIssue,
    CoreShapeMetrics,
    DimensionRange,
    NormalizedCatalogCoreV2,
    NormalizedCoreShapeV2,
    NormalizedWireV2,
    ReferenceResolution,
)
from .operating_point import OperatingPoint
from .semiconductor_geometry_result import SemiconductorGeometryLayout, SemiconductorGeometryResult
from .pipeline import (
    Archetype,
    CoreDesign,
    DesignPipelineResult,
    DesignSpec,
    DeviceCandidateSet,
    Scheme,
    SchemePipelineResult,
    StressMetric,
    StressReport,
    WaveformPipelineResult,
)
from .stress_result import StressResult
from .thermal_result import ThermalComparisonEntry, ThermalEstimate, ThermalResult
from .topology_comparison import TopologyComparison, TopologyComparisonEntry
from .waveform import WaveformSet

DeviceResult = DeviceSelectionResult

__all__ = [
    "Archetype",
    "BridgeRectifierCandidate",
    "BridgeRectifierCandidateEvaluation",
    "BridgeRectifierLossEstimate",
    "BridgeRectifierRankingBreakdown",
    "BridgeRectifierSelectionRequest",
    "BridgeRectifierSelectionResult",
    "BridgeRectifierThermalEstimate",
    "CommonSpec",
    "CoreDesign",
    "AssessmentDimension",
    "DesignAssessment",
    "DesignReport",
    "DesignPipelineResult",
    "DesignSpec",
    "DeviceLossResult",
    "DeviceResult",
    "DeviceSelectionResult",
    "EfficiencySweepPoint",
    "EfficiencySweepResult",
    "DeviceCandidateSet",
    "DimensionRange",
    "FixedInductorDesignCandidate",
    "GeometryResult",
    "InductorGeometryLayout",
    "InductorDesignRequest",
    "InductorOperatingEvaluation",
    "InductorOperatingPointRequest",
    "LossResult",
    "LlcRunContext",
    "CoreLossExcitation",
    "CoreLossExcitationBuildRequest",
    "CoreLossExcitationBuildResult",
    "CoreLossExcitationBuildStatus",
    "CoreLossEvaluationContext",
    "CoreLossResult",
    "CoreLossValidityStatus",
    "CoreShapeMetrics",
    "CatalogDistributorEntry",
    "CatalogGapEntry",
    "ComponentNormalizationBatch",
    "ComponentNormalizationIssue",
    "MagneticResult",
    "LlcMagneticResultSummary",
    "LlcMagneticStageSummary",
    "WindingElectricalEvidence",
    "MaterialLossModel",
    "MeasuredLossDataset",
    "MeasuredLossPoint",
    "NormalizedMagneticMaterialV2",
    "NormalizedCatalogCoreV2",
    "NormalizedCoreShapeV2",
    "NormalizedWireV2",
    "OperatingPoint",
    "ReferenceJunctionTemperatureEstimate",
    "ReferenceResolution",
    "SemiconductorGeometryLayout",
    "SemiconductorGeometryResult",
    "Scheme",
    "SchemePipelineResult",
    "SinkThermalRequirement",
    "StressMetric",
    "StressResult",
    "StressReport",
    "SwitchStress",
    "SourceProvenance",
    "TabulatedModelPoint",
    "ThermalComparisonEntry",
    "ThermalEstimate",
    "ThermalResult",
    "TopologyComparison",
    "TopologyComparisonEntry",
    "WaveformPipelineResult",
    "WaveformSet",
]
