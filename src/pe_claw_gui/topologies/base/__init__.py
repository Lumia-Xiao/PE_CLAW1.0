"""Base topology abstractions."""

from .category import ConverterCategory
from .candidate import TopologyCandidate
from .interface import TopologyPlugin
from .registry import TopologyDefinition, TopologyRegistry, build_default_registry
from .result import TopologyResult
from .spec import TopologySpec

__all__ = [
    "ConverterCategory",
    "TopologyCandidate",
    "TopologyDefinition",
    "TopologyPlugin",
    "TopologyRegistry",
    "TopologyResult",
    "TopologySpec",
    "build_default_registry",
]
