from __future__ import annotations

import json
import importlib
from pathlib import Path

from pe_claw_gui.app.result_views.thermal_view import ThermalView
from pe_claw_gui.reports.structured_output import canonical_json
from pe_claw_gui.pipeline.options import PipelineOptions

from tests.test_llc_magnetic_result_reporting_step5 import _llc_report


thermal_pipeline = importlib.import_module("pe_claw_gui.pipeline.run_thermal_pipeline")


WINDOWS_THERMAL_ARTIFACT = (
    r"C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0\outputs\thermal summary"
    r"\thermal_summary.csv"
)


def _render(report) -> str:
    captured: dict[str, str] = {}

    class CaptureView:
        def _set_text(self, value: str) -> None:
            captured["text"] = value

    ThermalView.render(CaptureView(), report)
    return captured["text"]


def test_llc_thermal_artifact_note_is_one_complete_string(monkeypatch) -> None:
    monkeypatch.setattr(
        thermal_pipeline,
        "export_thermal_summary",
        lambda entries, output_dir=None: [WINDOWS_THERMAL_ARTIFACT],
    )

    report = thermal_pipeline.run_thermal_pipeline(
        _llc_report(),
        pipeline_options=PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=False),
    )

    expected = f"Thermal summary artifact saved to {WINDOWS_THERMAL_ARTIFACT}."
    assert report.thermal is not None
    assert report.thermal.notes[-1] == expected
    assert len(report.thermal.notes) == 4
    assert report.thermal.notes[-1] not in list(expected)


def test_llc_thermal_view_preserves_windows_path_and_does_not_split_note(monkeypatch) -> None:
    monkeypatch.setattr(
        thermal_pipeline,
        "export_thermal_summary",
        lambda entries, output_dir=None: [WINDOWS_THERMAL_ARTIFACT],
    )
    report = thermal_pipeline.run_thermal_pipeline(
        _llc_report(),
        pipeline_options=PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=False),
    )

    text = _render(report)
    expected = f"  Thermal summary artifact saved to {WINDOWS_THERMAL_ARTIFACT}."
    assert expected in text
    assert "\n  T\n  h\n  e\n" not in text
    assert WINDOWS_THERMAL_ARTIFACT in text


def test_canonical_json_round_trip_preserves_windows_path_escaping() -> None:
    payload = {
        "thermal": {
            "artifact_paths": [WINDOWS_THERMAL_ARTIFACT],
            "note": f"Thermal summary artifact saved to {WINDOWS_THERMAL_ARTIFACT}.",
        }
    }

    encoded = canonical_json(payload)
    decoded = json.loads(encoded)
    assert decoded == payload
    assert "thermal_summary" in encoded
    assert "\\\\Users\\\\Lumia" in encoded
    assert "\\u005f" not in encoded
