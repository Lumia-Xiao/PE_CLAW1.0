"""DAB topology placeholder plugin."""

from __future__ import annotations

from ..boost import BoostPlaceholderPlugin

PLUGIN = BoostPlaceholderPlugin(
    topology_id="dab_placeholder",
    display_name="DAB Placeholder",
    legacy_key="DAB_Placeholder",
)
