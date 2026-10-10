from __future__ import annotations

import pytest

from pe_claw_gui.app.result_views.inductor_view import build_inductor_summary_text
from pe_claw_gui.app.result_views.loss_view import build_system_loss_summary
from pe_claw_gui.models.common_spec import CommonSpec
from pe_claw_gui.models.design_report import DesignReport
from pe_claw_gui.models.efficiency_sweep import EfficiencySweepPoint, EfficiencySweepResult
from pe_claw_gui.models.loss_result import LossResult
from pe_claw_gui.models.magnetic_result import MagneticResult
from pe_claw_gui.topologies.ac_dc.single_phase_interleaved_boost_pfc_diode_bridge.loss_readback import (
    resolve_interleaved_boost_pfc_loss_snapshot,
)


TOPOLOGY_ID = "single_phase_interleaved_boost_pfc_diode_bridge"


def _report(*, sweep: EfficiencySweepResult | None = None) -> DesignReport:
    spec = CommonSpec(
        topology_id=TOPOLOGY_ID,
        display_name="Two-phase interleaved Boost PFC",
        vin_min=180.0,
        vin_max=265.0,
        vout=400.0,
        pout=1000.0,
        fs_khz=100.0,
        ripple_current_ratio=0.4,
        ripple_voltage_ratio_percent=2.0,
    )
    loss = LossResult(
        total_loss_w=30.0,
        breakdown_w={
            "bridge_rectifier_loss_w": 8.0,
            "semiconductor_loss_w": 18.0,
            "inductor_total_loss_w": 0.7,
            "phase_1_inductor_total_loss_w": 0.35,
            "phase_2_inductor_total_loss_w": 0.35,
            "dc_link_capacitor_loss_w": 1.3,
            "other_loss_w": 2.0,
        },
    )
    return DesignReport(
        spec=spec,
        loss=loss,
        magnetic=MagneticResult(
            design_requirements={
                "phase_1_design_id": "phase-1",
                "phase_2_design_id": "phase-2",
            }
        ),
        efficiency_sweep=sweep,
    )


def _full_load_sweep() -> EfficiencySweepResult:
    point = EfficiencySweepPoint(
        load_pu=1.0,
        output_power_w=1000.0,
        total_loss_w=24.5262044235051,
        efficiency=0.976060930098605,
        semiconductor_loss_w=14.70342736831,
        magnetic_loss_w=0.478754624314492,
        capacitor_loss_w=1.45821150422788,
        other_loss_w=0.0,
        bridge_rectifier_loss_w=7.88581092665278,
        loss_breakdown_w={"phase_1_inductor": 0.239377312157246, "phase_2_inductor": 0.239377312157246},
    )
    return EfficiencySweepResult(points=(point,), load_grid=(1.0,), status="available")


def test_full_load_snapshot_sums_the_five_efficiency_components() -> None:
    snapshot = resolve_interleaved_boost_pfc_loss_snapshot(_report(sweep=_full_load_sweep()))

    assert snapshot.source == "full_load_efficiency_sweep"
    assert snapshot.total_loss_w == pytest.approx(24.5262044235051)
    assert snapshot.efficiency == pytest.approx(1000.0 / (1000.0 + 24.5262044235051))


def test_loss_and_inductor_views_use_the_same_full_load_snapshot() -> None:
    report = _report(sweep=_full_load_sweep())
    loss_text = "\n".join(build_system_loss_summary(report))
    inductor_text = build_inductor_summary_text(report)

    for text in (loss_text, inductor_text):
        assert "24.5262 W" in text
    assert "14.7034 W" in loss_text
    assert "7.88581 W" in loss_text
    assert "0.478755 W" in loss_text
    assert "0.239377 W" in loss_text
    assert "1.45821 W" in loss_text
    assert "97.6061 %" in loss_text
    assert "Full-load efficiency sweep (1.0 p.u.)" in loss_text
    assert "Full-load efficiency sweep (1.0 p.u.)" in inductor_text


def test_design_point_is_used_only_when_no_sweep_exists() -> None:
    snapshot = resolve_interleaved_boost_pfc_loss_snapshot(_report())
    text = "\n".join(build_system_loss_summary(_report()))

    assert snapshot.source == "design_point"
    assert snapshot.total_loss_w == 30.0
    assert "Design-point estimated efficiency" in text
    assert "30 W" in text


def test_blocked_sweep_does_not_fall_back_to_partial_design_or_sweep_values() -> None:
    blocked = EfficiencySweepResult(status="blocked", blocked_reason="missing phase-2 magnetic loss")
    report = _report(sweep=blocked)
    snapshot = resolve_interleaved_boost_pfc_loss_snapshot(report)
    text = "\n".join(build_system_loss_summary(report))

    assert snapshot.source == "unavailable"
    assert snapshot.total_loss_w is None
    assert "Total estimated loss: - W" in text
    assert "missing phase-2 magnetic loss" in text
    assert "30 W" not in text
