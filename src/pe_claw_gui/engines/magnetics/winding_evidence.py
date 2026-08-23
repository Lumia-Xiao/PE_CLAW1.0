"""Shared construction helpers for Step 19B winding evidence."""

from __future__ import annotations

from typing import Any, Mapping

from ...models.magnetic_winding_contract import WindingElectricalEvidence


COPPER_RESISTIVITY_25C_OHM_M = 1.724e-8


def build_winding_electrical_evidence(
    *,
    wire_id: str,
    wire_name: str,
    source_wire_record: Mapping[str, Any],
    conducting_area_m2: float,
    area_basis: str,
    strand_diameter_m: float,
    strand_count: int,
    parallel_winding_count: int,
    turns: int,
    mean_length_per_turn_m: float,
    resistance_temperature_c: float,
    resistance_temperature_factor: float,
    rac_multiplier: float,
    rms_current_a: float,
    fill_area_m2: float,
    resistance_ohm_per_m_25c: float | None = None,
) -> WindingElectricalEvidence:
    """Build one evidence record with conductor and correction factors once."""

    total_conductor_length_m = mean_length_per_turn_m * turns
    resistance_per_m = (
        COPPER_RESISTIVITY_25C_OHM_M / conducting_area_m2
        if resistance_ohm_per_m_25c is None
        else resistance_ohm_per_m_25c
    )
    rdc_25c_ohm = resistance_per_m * total_conductor_length_m / parallel_winding_count
    dc_copper_loss_w = rms_current_a**2 * rdc_25c_ohm * resistance_temperature_factor
    total_copper_loss_w = dc_copper_loss_w * rac_multiplier
    return WindingElectricalEvidence(
        wire_id=wire_id,
        wire_name=wire_name,
        source_wire_record=source_wire_record,
        conducting_area_m2=conducting_area_m2,
        area_basis=area_basis,
        strand_diameter_m=strand_diameter_m,
        strand_count=strand_count,
        parallel_winding_count=parallel_winding_count,
        turns=turns,
        mean_length_per_turn_m=mean_length_per_turn_m,
        total_conductor_length_m=total_conductor_length_m,
        rdc_25c_ohm=rdc_25c_ohm,
        resistance_temperature_c=resistance_temperature_c,
        resistance_temperature_factor=resistance_temperature_factor,
        rac_multiplier=rac_multiplier,
        rms_current_a=rms_current_a,
        dc_copper_loss_w=dc_copper_loss_w,
        ac_copper_loss_w=total_copper_loss_w - dc_copper_loss_w,
        total_copper_loss_w=total_copper_loss_w,
        fill_area_m2=fill_area_m2,
    )
