"""Input handling for the three-level TZCM fixed-frequency topology."""

from __future__ import annotations

from collections.abc import Mapping

from ....libraries.semiconductors.metadata import merge_semiconductor_filter_metadata, with_default_semiconductor_filter_input
from ...base.spec import TopologySpec
from ....utils.ambient_temperature import merge_ambient_metadata, with_default_ambient_input

TOPOLOGY_ID = "three_level_tzcm_fixed_frequency"
DISPLAY_NAME = "Three-Level DC-DC TZCM Fixed Frequency"
LEGACY_KEY = "ThreeLevelTZCM_FixedFrequency"

DEFAULT_FSW_HZ = 40e3
DEADTIME_S = 0.5e-6
D1_MIN = 0.06
D4_MAX = 0.94
COSS_EQ_F = 178e-12


def _parse_ripple_voltage_ratio(raw_input: Mapping[str, str]) -> tuple[float, float]:
    if "ripple_voltage_ratio_percent" in raw_input:
        ripple_percent = float(raw_input["ripple_voltage_ratio_percent"])
        return ripple_percent / 100.0, ripple_percent
    ripple_ratio = float(raw_input["vout_ripple_ratio"])
    return ripple_ratio, ripple_ratio * 100.0


def build_default_inputs() -> dict[str, str]:
    """Return default raw inputs for the three-level TZCM topology."""
    return with_default_semiconductor_filter_input(with_default_ambient_input({
        "vin_nom": "400",
        "vout_nom": "200",
        "pout_nom": "2000",
        "fsw_khz": "40",
        "izvs": "2",
        "ripple_voltage_ratio_percent": "1.0",
    }))


def build_spec(raw_input: Mapping[str, str]) -> TopologySpec:
    """Parse and validate raw GUI inputs into a TZCM topology spec."""
    try:
        vin = float(raw_input["vin_nom"])
        vin_min = float(raw_input.get("vin_min", vin))
        vin_max = float(raw_input.get("vin_max", vin))
        vout = float(raw_input["vout_nom"])
        pout = float(raw_input["pout_nom"])
        fsw_khz = float(raw_input.get("fsw_khz", DEFAULT_FSW_HZ / 1e3))
        izvs = float(raw_input["izvs"])
        vout_ripple_ratio, ripple_voltage_ratio_percent = _parse_ripple_voltage_ratio(raw_input)
    except KeyError as exc:
        raise ValueError(f"Missing input field: {exc.args[0]}") from exc
    except ValueError as exc:
        if "Ambient temperature" in str(exc) or "Target junction temperature" in str(exc) or "Semiconductor " in str(exc):
            raise ValueError(str(exc)) from exc
        raise ValueError("All TZCM design inputs must be valid numbers.") from exc

    if vin <= 0.0 or vin_min <= 0.0 or vin_max <= 0.0 or vout <= 0.0:
        raise ValueError("Vin nominal and Vout nominal must be positive.")
    if vin_min > vin_max:
        raise ValueError("Vin minimum must be less than or equal to Vin maximum.")
    if not (vin_min <= vin <= vin_max):
        raise ValueError("Vin nominal must fall within the Vin minimum/maximum range.")
    if pout <= 0.0:
        raise ValueError("Pout nominal must be positive.")
    fsw_hz = fsw_khz * 1e3
    if fsw_hz <= 0.0:
        raise ValueError("Switching frequency must be positive.")
    if izvs < 0.0:
        raise ValueError("Izvs must be non-negative.")
    if vout_ripple_ratio <= 0.0:
        raise ValueError("Vout ripple ratio must be positive.")

    return TopologySpec(
        topology_id=TOPOLOGY_ID,
        display_name=DISPLAY_NAME,
        vin_min=vin_min,
        vin_max=vin_max,
        vout=vout,
        pout=pout,
        fs_khz=fsw_hz / 1e3,
        ripple_current_ratio=0.0,
        ripple_voltage_ratio_percent=ripple_voltage_ratio_percent,
        raw_input=dict(raw_input),
        metadata=merge_semiconductor_filter_metadata(
            merge_ambient_metadata(
                {
                    "legacy_key": LEGACY_KEY,
                    "vin_nom": vin,
                    "izvs": izvs,
                    "vout_ripple_ratio": vout_ripple_ratio,
                    "fsw_hz": fsw_hz,
                    "fsw_khz": fsw_khz,
                    "deadtime_s": DEADTIME_S,
                    "d1_min": D1_MIN,
                    "d4_max": D4_MAX,
                    "coss_eq_f": COSS_EQ_F,
                },
                raw_input,
            ),
            raw_input,
        ),
    )
