"""Result view widgets for the target multi-topology GUI structure."""

from .ai_design_view import AIDesignView
from .capacitor_view import CapacitorView
from .capacitor_pf_view import CapacitorPFView
from .device_view import DeviceView
from .efficiency_view import EfficiencyView
from .geometry_view import GeometryView
from .hardware_overview_view import HardwareOverviewView
from .inductor_pf_view import InductorPFView
from .inductor_view import InductorView
from .loss_view import LossView
from .magnetic_view import MagneticView
from .stress_view import StressView
from .summary_view import SummaryView
from .thermal_view import ThermalView
from .waveform_view import WaveformView

__all__ = [
    "AIDesignView",
    "CapacitorView",
    "CapacitorPFView",
    "DeviceView",
    "EfficiencyView",
    "GeometryView",
    "HardwareOverviewView",
    "InductorPFView",
    "InductorView",
    "LossView",
    "MagneticView",
    "StressView",
    "SummaryView",
    "ThermalView",
    "WaveformView",
]
