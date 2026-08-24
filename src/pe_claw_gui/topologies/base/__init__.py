"""Base topology abstractions."""

from .category import ConverterCategory
from .capabilities import TopologyCapability, get_topology_capability
from .candidate import TopologyCandidate
from .interface import TopologyPlugin
from .registry import TopologyDefinition, TopologyRegistry, build_default_registry
from .result import TopologyResult
from .spec import TopologySpec

__all__ = [
    "ConverterCategory",
    "TopologyCapability",
    "TopologyCandidate",
    "TopologyDefinition",
    "TopologyPlugin",
    "TopologyRegistry",
    "TopologyResult",
    "TopologySpec",
    "get_topology_capability",
    "build_default_registry",
]
