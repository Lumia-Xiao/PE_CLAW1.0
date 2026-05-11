"""LLC topology placeholder plugin."""

from __future__ import annotations

from ..boost import BoostPlaceholderPlugin

PLUGIN = BoostPlaceholderPlugin(
    topology_id="llc_placeholder",
    display_name="LLC Placeholder",
    legacy_key="LLC_Placeholder",
)
