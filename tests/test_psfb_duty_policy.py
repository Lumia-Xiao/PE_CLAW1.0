from __future__ import annotations

import math

import pytest

from pe_claw_gui.topologies.dc_dc.phase_shifted_full_bridge_diode_rectifier_isolated.duty_policy import (
    assess_psfb_duty,
    calculate_psfb_duty,
)


COMMON = {
    "vout_v": 400.0,
    "diode_drop_total_v": 2.0,
    "turns_ratio_np_ns": 1.2599403578528827,
    "leakage_h": 2.2e-6,
    "iout_a": 5.0,
    "fs_hz": 100_000.0,
    "max_effective_duty": 0.78,
    "max_command_duty": 0.90,
}


def test_nominal_low_high_line_have_ordered_duty_and_auditable_scope() -> None:
    nominal = calculate_psfb_duty(vin_v=750.0, scope="design_point", **COMMON)
    low_line = calculate_psfb_duty(vin_v=650.0, scope="operating_point", **COMMON)
    high_line = calculate_psfb_duty(vin_v=850.0, scope="operating_point", **COMMON)

    assert nominal.scope == "design_point"
    assert low_line.scope == high_line.scope == "operating_point"
    for result in (nominal, low_line, high_line):
        assert 0.0 <= result.effective_duty <= result.command_duty <= 1.0
        assert math.isclose(
            result.duty_loss,
            result.command_duty - result.effective_duty,
            rel_tol=1e-12,
            abs_tol=1e-12,
        )
        assert result.within_physical_range
        assert result.duty_loss_consistent
        assert result.within_configured_limits
        assert result.status == "pass"
        assert result.failure_reason is None


def test_light_and_very_light_load_reduce_duty_loss() -> None:
    light = calculate_psfb_duty(
        vin_v=750.0,
        scope="operating_point",
        **{**COMMON, "iout_a": 1.0},
    )
    very_light = calculate_psfb_duty(
        vin_v=750.0,
        scope="operating_point",
        **{**COMMON, "iout_a": 0.5},
    )

    assert light.duty_loss < calculate_psfb_duty(vin_v=750.0, scope="operating_point", **COMMON).duty_loss
    assert very_light.duty_loss < light.duty_loss


def test_configured_limit_failure_is_explicit_and_not_clamped() -> None:
    result = calculate_psfb_duty(
        vin_v=600.0,
        scope="operating_point",
        **{**COMMON, "max_effective_duty": 0.70, "max_command_duty": 0.75},
    )

    assert result.effective_duty > result.max_effective_duty
    assert result.command_duty > result.max_command_duty
    assert result.status == "configured_boundary_failure"
    assert result.failure_reason == "configured_duty_limit_exceeded"
    assert not result.feasible


def test_illegal_duty_order_is_explicitly_rejected() -> None:
    result = assess_psfb_duty(
        effective_duty=0.80,
        duty_loss=0.05,
        command_duty=0.70,
        max_effective_duty=0.90,
        max_command_duty=0.95,
        scope="operating_point",
    )

    assert not result.within_physical_range
    assert result.status == "physical_boundary_failure"
    assert "duty_order_or_physical_range_violation" in (result.failure_reason or "")
    assert not result.feasible


def test_invalid_calculation_input_is_rejected() -> None:
    with pytest.raises(ValueError, match="vin_v must be finite and positive"):
        calculate_psfb_duty(vin_v=0.0, scope="operating_point", **COMMON)
