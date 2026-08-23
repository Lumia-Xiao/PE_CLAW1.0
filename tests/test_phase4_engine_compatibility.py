from __future__ import annotations

from pe_claw_gui.engines.magnetics.inductor_design import _candidate_frame


def test_empty_magnetic_candidate_frame_preserves_export_columns() -> None:
    frame = _candidate_frame([])

    assert frame.empty
    assert {"total_volume_m3", "reference_total_loss_w"} <= set(frame.columns)
