"""Independent first-pass two-phase interleaved Boost PFC electrical core.

This package is intentionally not registered with the runtime topology registry.
It provides the step-2 input and synthesis boundary for later integration.
"""

from .input_schema import DISPLAY_NAME, LEGACY_KEY, TOPOLOGY_ID, build_default_inputs, build_spec
from .synthesizer import synthesize

__all__ = [
    "DISPLAY_NAME",
    "LEGACY_KEY",
    "TOPOLOGY_ID",
    "build_default_inputs",
    "build_spec",
    "synthesize",
]
