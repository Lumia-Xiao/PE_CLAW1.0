"""Controller for waveform execution."""

from __future__ import annotations

from dataclasses import replace

from ...models.operating_point import OperatingPoint
from ...pipeline import run_operating_point_refresh
from ...pipeline.options import PipelineOptions
from ...utils.ambient_temperature import (
    AMBIENT_TEMP_INPUT_KEY,
    TARGET_JUNCTION_TEMP_INPUT_KEY,
    parse_ambient_temperature_c,
    parse_target_junction_temperature_c,
)
from ..shell.state_store import AppStateStore


class WaveformController:
    """Generate waveforms for the currently selected topology."""

    def __init__(self, state_store: AppStateStore) -> None:
        self._state_store = state_store

    def generate_waveforms(self, operating_point: OperatingPoint, runtime_overrides: dict[str, str] | None = None):
        """Refresh only operating-point-dependent outputs for the active design."""
        if self._state_store.design_report is None or self._state_store.design_report.candidate is None:
            raise RuntimeError("Run the topology design before generating waveforms.")
        if self._state_store.selected_topology_id is None:
            raise RuntimeError("Select a topology before generating waveforms.")
        plugin = self._state_store.active_plugin or self._state_store.registry.get_plugin(self._state_store.selected_topology_id)
        report = _apply_runtime_overrides(self._state_store.design_report, runtime_overrides)
        report = run_operating_point_refresh(
            report=report,
            plugin=plugin,
            operating_point=operating_point,
            pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
        )
        self._state_store.active_plugin = plugin
        self._state_store.design_report = report
        if runtime_overrides:
            updated_raw_input = dict(self._state_store.last_raw_input or {})
            updated_raw_input.update(runtime_overrides)
            self._state_store.last_raw_input = updated_raw_input
        return report


def _apply_runtime_overrides(report, runtime_overrides: dict[str, str] | None):
    if not runtime_overrides:
        return report

    raw_input = dict(report.spec.raw_input)
    metadata = dict(report.spec.metadata)
    ambient_raw_value = runtime_overrides.get(AMBIENT_TEMP_INPUT_KEY)
    if ambient_raw_value is not None:
        ambient_temp_c = parse_ambient_temperature_c(ambient_raw_value)
        raw_input[AMBIENT_TEMP_INPUT_KEY] = ambient_raw_value
        metadata[AMBIENT_TEMP_INPUT_KEY] = ambient_temp_c

    target_junction_raw_value = runtime_overrides.get(TARGET_JUNCTION_TEMP_INPUT_KEY)
    if target_junction_raw_value is not None:
        target_junction_temp_c = parse_target_junction_temperature_c(target_junction_raw_value)
        raw_input[TARGET_JUNCTION_TEMP_INPUT_KEY] = target_junction_raw_value
        metadata[TARGET_JUNCTION_TEMP_INPUT_KEY] = target_junction_temp_c

    if ambient_raw_value is None and target_junction_raw_value is None:
        return report
    return replace(report, spec=replace(report.spec, raw_input=raw_input, metadata=metadata))
