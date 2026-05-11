"""Deprecated compatibility package for legacy scheme imports."""

from .evaluator import evaluate_scheme
from .labels import build_scheme_label
from .ranking import rank_schemes

__all__ = [
    "build_scheme_label",
    "evaluate_scheme",
    "rank_schemes",
]
