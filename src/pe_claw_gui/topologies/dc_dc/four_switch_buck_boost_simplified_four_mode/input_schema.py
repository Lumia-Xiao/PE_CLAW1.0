"""Input handling for the simplified four-mode four-switch Buck-Boost topology."""

from __future__ import annotations

from collections.abc import Mapping

from ....libraries.semiconductors.metadata import merge_semiconductor_filter_metadata, with_default_semiconductor_filter_input
from ...base.spec import TopologySpec
from ....utils.ambient_temperature import merge_ambient_metadata, with_default_ambient_input

TOPOLOGY_ID = "four_switch_buck_boost_simplified_four_mode"
DISPLAY_NAME = "Four-Switch Buck-Boost Simplified Four-Mode"
LEGACY_KEY = "FourSwitchBuckBoost_SimplifiedFourMode"


def build_default_inputs() -> dict[str, str]:
    """Return default raw inputs for the four-switch Buck-Boost topology."""
    return with_default_semiconductor_filter_input(with_default_ambient_input({
        "vin_min": "18",
        "vin_max": "36",
        "vout": "24",
        "pout": "120",
        "fs_khz": "100",
        "ripple_current_ratio": "0.30",
        "ripple_voltage_ratio_percent": "1.0",
        "duty_clamp": "0.10",
        "transition_band_ratio": "0.10",
    }))


def build_spec(raw_input: Mapping[str, str]) -> TopologySpec:
    """Parse and validate raw GUI inputs into a four-switch Buck-Boost spec."""
    try:
        duty_clamp = float(raw_input["duty_clamp"])
        transition_band_ratio = float(raw_input["transition_band_ratio"])
        spec = TopologySpec(
            topology_id=TOPOLOGY_ID,
            display_name=DISPLAY_NAME,
            vin_min=float(raw_input["vin_min"]),
            vin_max=float(raw_input["vin_max"]),
            vout=float(raw_input["vout"]),
            pout=float(raw_input["pout"]),
            fs_khz=float(raw_input["fs_khz"]),
            ripple_current_ratio=float(raw_input["ripple_current_ratio"]),
            ripple_voltage_ratio_percent=float(raw_input["ripple_voltage_ratio_percent"]),
            raw_input=dict(raw_input),
            metadata=merge_semiconductor_filter_metadata(
                merge_ambient_metadata(
                    {
                        "legacy_key": LEGACY_KEY,
                        "duty_clamp": duty_clamp,
                        "transition_band_ratio": transition_band_ratio,
                    },
                    raw_input,
                ),
                raw_input,
            ),
        )
    except KeyError as exc:
        raise ValueError(f"Missing input field: {exc.args[0]}") from exc
    except ValueError as exc:
        if "Ambient temperature" in str(exc) or "Target junction temperature" in str(exc) or "Semiconductor " in str(exc):
            raise ValueError(str(exc)) from exc
        raise ValueError("All four-switch Buck-Boost design inputs must be valid numbers.") from exc

    if spec.vin_min <= 0.0 or spec.vin_max <= 0.0:
        raise ValueError("Input voltage limits must be positive.")
    if spec.vin_max < spec.vin_min:
        raise ValueError("Vin max must be greater than or equal to Vin min.")
    if spec.vout <= 0.0 or spec.pout <= 0.0:
        raise ValueError("Output voltage and output power must be positive.")
    if spec.fs_khz <= 0.0:
        raise ValueError("Switching frequency must be positive.")
    if spec.ripple_current_ratio <= 0.0:
        raise ValueError("Inductor ripple ratio must be positive.")
    if spec.ripple_voltage_ratio_percent <= 0.0:
        raise ValueError("Voltage ripple ratio must be positive.")
    if not 0.0 < duty_clamp < 0.5:
        raise ValueError("Duty clamp must be between 0 and 0.5.")
    if not 0.0 < transition_band_ratio < 0.5:
        raise ValueError("Transition band ratio must be between 0 and 0.5.")

    return spec
