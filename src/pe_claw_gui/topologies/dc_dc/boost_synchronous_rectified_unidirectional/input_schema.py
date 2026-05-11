"""Input handling for the synchronous Boost topology."""

from __future__ import annotations

from collections.abc import Mapping

from ....libraries.semiconductors.metadata import merge_semiconductor_filter_metadata, with_default_semiconductor_filter_input
from ...base.spec import TopologySpec
from ....utils.ambient_temperature import merge_ambient_metadata, with_default_ambient_input

BOOST_TOPOLOGY_ID = "boost_synchronous_rectified_unidirectional"
BOOST_DISPLAY_NAME = "Boost Synchronous Rectified Unidirectional"
BOOST_LEGACY_KEY = "Boost_SynchronousRectified_Unidirectional"


def build_default_inputs() -> dict[str, str]:
    """Return default raw inputs for the synchronous Boost topology."""
    return with_default_semiconductor_filter_input(with_default_ambient_input({
        "vin_min": "18",
        "vin_max": "36",
        "vout": "48",
        "pout": "120",
        "fs_khz": "100",
        "ripple_current_ratio": "0.30",
        "ripple_voltage_ratio_percent": "1.0",
    }))


def build_spec(raw_input: Mapping[str, str]) -> TopologySpec:
    """Parse and validate raw GUI inputs into a synchronous Boost topology spec."""
    try:
        spec = TopologySpec(
            topology_id=BOOST_TOPOLOGY_ID,
            display_name=BOOST_DISPLAY_NAME,
            vin_min=float(raw_input["vin_min"]),
            vin_max=float(raw_input["vin_max"]),
            vout=float(raw_input["vout"]),
            pout=float(raw_input["pout"]),
            fs_khz=float(raw_input["fs_khz"]),
            ripple_current_ratio=float(raw_input["ripple_current_ratio"]),
            ripple_voltage_ratio_percent=float(raw_input["ripple_voltage_ratio_percent"]),
            raw_input=dict(raw_input),
            metadata=merge_semiconductor_filter_metadata(
                merge_ambient_metadata({"legacy_key": BOOST_LEGACY_KEY}, raw_input),
                raw_input,
            ),
        )
    except KeyError as exc:
        raise ValueError(f"Missing input field: {exc.args[0]}") from exc
    except ValueError as exc:
        if "Ambient temperature" in str(exc) or "Target junction temperature" in str(exc) or "Semiconductor " in str(exc):
            raise ValueError(str(exc)) from exc
        raise ValueError("All synchronous Boost design inputs must be valid numbers.") from exc

    if spec.vin_min <= 0.0 or spec.vin_max <= 0.0:
        raise ValueError("Input voltage limits must be positive.")
    if spec.vin_max < spec.vin_min:
        raise ValueError("Vin max must be greater than or equal to Vin min.")
    if spec.vout <= 0.0 or spec.pout <= 0.0:
        raise ValueError("Output voltage and output power must be positive.")
    if spec.vout <= spec.vin_max:
        raise ValueError("Boost output voltage must exceed the maximum input voltage.")
    if spec.fs_khz <= 0.0:
        raise ValueError("Switching frequency must be positive.")
    if spec.ripple_current_ratio <= 0.0:
        raise ValueError("Inductor ripple ratio must be positive.")
    if spec.ripple_voltage_ratio_percent <= 0.0:
        raise ValueError("Voltage ripple ratio must be positive.")

    return spec
