"""Controller for placeholder downstream stages."""

from __future__ import annotations

from ..shell.state_store import AppStateStore


class DeviceController:
    """Read device-stage status from the shared state."""

    def __init__(self, state_store: AppStateStore) -> None:
        self._state_store = state_store

    def get_status(self) -> str:
        """Return the current device-stage summary."""
        if self._state_store.design_report is None or self._state_store.design_report.device is None:
            return "Device selection has not run yet."
        device_result = self._state_store.design_report.device
        lines = []
        if device_result.selected_devices:
            lines.append("Selected devices")
            lines.extend(f"  {role}: {part_number}" for role, part_number in sorted(device_result.selected_devices.items()))
        if device_result.candidate_counts:
            lines.append("Candidate counts")
            lines.extend(f"  {role}: {count}" for role, count in sorted(device_result.candidate_counts.items()))
        if device_result.notes:
            lines.append("Notes")
            lines.extend(f"  {note}" for note in device_result.notes)
        return "\n".join(lines) if lines else "Device selection completed with no summary text."
