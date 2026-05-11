"""PSFB topology placeholder plugin."""

from __future__ import annotations

from ..boost import BoostPlaceholderPlugin

PLUGIN = BoostPlaceholderPlugin(
    topology_id="psfb_placeholder",
    display_name="PSFB Placeholder",
    legacy_key="PSFB_Placeholder",
)
