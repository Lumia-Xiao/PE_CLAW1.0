"""CLLC topology placeholder plugin."""

from __future__ import annotations

from ..boost import BoostPlaceholderPlugin

PLUGIN = BoostPlaceholderPlugin(
    topology_id="cllc_placeholder",
    display_name="CLLC Placeholder",
    legacy_key="CLLC_Placeholder",
)
