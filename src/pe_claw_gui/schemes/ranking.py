from __future__ import annotations

from ..models import Scheme


def rank_schemes(schemes: list[Scheme], strategy: str = "default") -> list[Scheme]:
    """Rank evaluated schemes.

    TODO: support strategy-specific ranking once real scoring exists.
    """
    if strategy == "default":
        return sorted(schemes, key=lambda scheme: (scheme.score is None, -(scheme.score or 0.0)))
    return schemes[:]
