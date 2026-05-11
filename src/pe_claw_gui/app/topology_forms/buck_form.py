"""Deprecated compatibility wrapper for the Buck form module."""

from .buck_diode_rectified_unidirectional_form import BuckDiodeRectifiedUnidirectionalForm


BuckTopologyForm = BuckDiodeRectifiedUnidirectionalForm

__all__ = [
    "BuckDiodeRectifiedUnidirectionalForm",
    "BuckTopologyForm",
]
