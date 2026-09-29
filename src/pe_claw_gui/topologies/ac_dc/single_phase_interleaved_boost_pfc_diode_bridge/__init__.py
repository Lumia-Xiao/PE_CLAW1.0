"""Independent first-pass two-phase interleaved Boost PFC electrical core.

This package is intentionally not registered with the runtime topology registry.
It provides the step-2 input and synthesis boundary for later integration.
"""

from .input_schema import DISPLAY_NAME, LEGACY_KEY, TOPOLOGY_ID, build_default_inputs, build_spec
from .evaluator import evaluate
from .synthesizer import synthesize
from .stress import InterleavedPFCStress, PhaseStress, extract_phase_stress, extract_stress
from .waveform import generate_waveforms

__all__ = [
    "DISPLAY_NAME",
    "InterleavedPFCStress",
    "LEGACY_KEY",
    "PhaseStress",
    "TOPOLOGY_ID",
    "build_default_inputs",
    "build_spec",
    "evaluate",
    "extract_phase_stress",
    "extract_stress",
    "generate_waveforms",
    "synthesize",
]
