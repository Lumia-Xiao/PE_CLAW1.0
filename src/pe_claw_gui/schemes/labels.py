from __future__ import annotations

from ..models import Scheme


def build_scheme_label(scheme: Scheme) -> str:
    """Return a user-facing label for a scheme candidate."""
    return scheme.label
