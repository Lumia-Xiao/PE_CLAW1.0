"""LLC synchronous-rectifier waveform entry point."""

from __future__ import annotations

from dataclasses import replace

from ....models.operating_point import OperatingPoint
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from ..llc_resonant_converter_diode_rectifier.waveform import generate_waveforms as _generate_diode_llc_waveforms


def generate_waveforms(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
) -> WaveformSet | None:
    """Generate first-pass FHA waveform readback for LLC SR visualization."""

    waveform = _generate_diode_llc_waveforms(candidate, operating_point=operating_point)
    llc_waveforms = waveform.metadata.get("llc_fha_waveforms", {})
    if isinstance(llc_waveforms, dict):
        secondary_states = llc_waveforms.get("secondary_diode_states", {})
        if isinstance(secondary_states, dict):
            llc_waveforms = dict(llc_waveforms)
            llc_waveforms["secondary_rectifier_type"] = "full_bridge_synchronous_rectifier"
            llc_waveforms["secondary_sync_switch_states"] = {
                key.replace("D", "SR", 1): list(value)
                for key, value in secondary_states.items()
            }
            notes = list(llc_waveforms.get("notes", []))
            notes.append(
                "Secondary diode conduction states are reused as first-pass secondary_sync_switch gate/conduction states for LLC SR."
            )
            llc_waveforms["notes"] = notes
            metadata = dict(waveform.metadata)
            metadata["llc_fha_waveforms"] = llc_waveforms
            return replace(waveform, notes=[*waveform.notes, notes[-1]], metadata=metadata)
    return waveform
