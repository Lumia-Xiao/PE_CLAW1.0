from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.engines.devices.thermal_backsolve import required_sink_thermal_resistance


def test_required_sink_rth_backsolve_nominal_math() -> None:
    result = required_sink_thermal_resistance(
        p_total_w=2.2,
        ambient_temp_c=25.0,
        target_junction_temp_c=100.0,
        rth_jc_k_per_w=5.04,
        rth_cs_k_per_w=1.0,
    )

    assert result.required_total_rth_k_per_w == pytest.approx((100.0 - 25.0) / 2.2)
    assert result.required_sink_rth_k_per_w == pytest.approx(((100.0 - 25.0) / 2.2) - 5.04 - 1.0)
    assert result.feasible is True


def test_required_sink_rth_backsolve_rejects_invalid_low_target() -> None:
    result = required_sink_thermal_resistance(
        p_total_w=2.2,
        ambient_temp_c=25.0,
        target_junction_temp_c=20.0,
        rth_jc_k_per_w=5.04,
        rth_cs_k_per_w=1.0,
    )

    assert result.feasible is False
    assert result.required_sink_rth_k_per_w is None
    assert any("above ambient" in warning for warning in result.warnings)


def test_required_sink_rth_backsolve_handles_nonpositive_loss() -> None:
    result = required_sink_thermal_resistance(
        p_total_w=0.0,
        ambient_temp_c=25.0,
        target_junction_temp_c=100.0,
        rth_jc_k_per_w=5.04,
        rth_cs_k_per_w=1.0,
    )

    assert result.feasible is True
    assert result.required_sink_rth_k_per_w == pytest.approx(0.0)
    assert result.estimated_sink_volume_cm3 == pytest.approx(0.0)


def test_required_sink_rth_backsolve_reports_nonfeasible_sink_requirement() -> None:
    result = required_sink_thermal_resistance(
        p_total_w=40.0,
        ambient_temp_c=25.0,
        target_junction_temp_c=80.0,
        rth_jc_k_per_w=5.04,
        rth_cs_k_per_w=1.0,
    )

    assert result.feasible is False
    assert result.required_sink_rth_k_per_w is not None
    assert result.required_sink_rth_k_per_w <= 0.0
