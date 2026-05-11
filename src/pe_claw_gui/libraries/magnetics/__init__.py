"""Static magnetics library namespace."""

from .models import (
    LitzWireRecord,
    MagneticAllowProfileRecord,
    MagneticCoreRecord,
    MagneticGeometryTemplateRecord,
    MagneticMaterialRecord,
    MagneticSourceInfo,
    RoundWireRecord,
    SteinmetzRangeRecord,
)
from .registry import MagneticLibraryRegistry, build_empty_magnetic_registry

__all__ = [
    "LitzWireRecord",
    "MagneticAllowProfileRecord",
    "MagneticCoreRecord",
    "MagneticGeometryTemplateRecord",
    "MagneticLibraryRegistry",
    "MagneticMaterialRecord",
    "MagneticSourceInfo",
    "RoundWireRecord",
    "SteinmetzRangeRecord",
    "build_empty_magnetic_registry",
]
