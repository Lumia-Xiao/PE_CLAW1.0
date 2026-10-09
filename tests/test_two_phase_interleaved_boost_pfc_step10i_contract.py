from __future__ import annotations

import math

import pytest

from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.topologies.ac_dc.single_phase_interleaved_boost_pfc_diode_bridge import (
    build_spec,
    generate_waveforms,
    synthesize,
    validate_operating_point_contract,
)


@pytest.fixture()
def candidate():
    return synthesize(build_spec({}))


def test_operating_point_contract_uses_rms_ac_voltage_and_design_range(candidate) -> None:
    validate_operating_point_contract(candidate, OperatingPoint(vin_v=180.0, load_ratio=0.1))
    validate_operating_point_contract(candidate, OperatingPoint(vin_v=230.0, load_ratio=1.0))
    validate_operating_point_contract(candidate, OperatingPoint(vin_v=265.0, load_ratio=1.0))


@pytest.mark.parametrize("vin_v", [0.0, -1.0, math.nan, math.inf, 179.999, 265.001])
def test_operating_point_contract_rejects_invalid_or_out_of_range_vin(candidate, vin_v) -> None:
    with pytest.raises(ValueError, match="vin_v"):
        validate_operating_point_contract(candidate, OperatingPoint(vin_v=vin_v))


@pytest.mark.parametrize("load_ratio", [-0.01, math.nan, math.inf])
def test_operating_point_contract_rejects_invalid_load_ratio(candidate, load_ratio) -> None:
    with pytest.raises(ValueError, match="load_ratio"):
        validate_operating_point_contract(candidate, OperatingPoint(vin_v=230.0, load_ratio=load_ratio))


@pytest.mark.parametrize(
    "point",
    [
        OperatingPoint(vin_v=230.0, vout_v=0.0),
        OperatingPoint(vin_v=230.0, power_factor=0.0),
        OperatingPoint(vin_v=230.0, power_factor=1.1),
        OperatingPoint(vin_v=230.0, switching_frequency_hz=0.0),
    ],
)
def test_operating_point_contract_rejects_invalid_optional_overrides(candidate, point) -> None:
    with pytest.raises(ValueError):
        validate_operating_point_contract(candidate, point)


def test_operating_point_contract_is_topology_local(candidate) -> None:
    validate_operating_point_contract(
        candidate,
        OperatingPoint(vin_v=230.0, load_ratio=0.5, vout_v=400.0, power_factor=0.99),
    )


def test_waveform_entrypoint_enforces_the_two_phase_contract(candidate) -> None:
    with pytest.raises(ValueError, match="design RMS AC range"):
        generate_waveforms(candidate, operating_point=OperatingPoint(vin_v=266.0))
