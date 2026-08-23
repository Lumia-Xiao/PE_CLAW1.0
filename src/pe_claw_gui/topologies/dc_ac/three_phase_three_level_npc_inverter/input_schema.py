"""Input handling for the three-phase three-level NPC inverter."""

from __future__ import annotations

from collections.abc import Mapping

from ....libraries.semiconductors.metadata import merge_semiconductor_filter_metadata
from ....utils.ambient_temperature import merge_ambient_metadata
from ...base.spec import TopologySpec

TOPOLOGY_ID = "three_phase_three_level_npc_inverter"
DISPLAY_NAME = "Three-Phase Three-Level NPC Inverter"
LEGACY_KEY = "ThreePhase_ThreeLevel_NPC_Inverter"


def build_default_inputs() -> dict[str, str]:
    """Return default raw inputs for first-pass three-phase NPC inverter design."""

    return {
        "vdc_nom": "700",
        "vac_ll_rms": "400",
        "f_line_hz": "50",
        "fsw_hz": "20000",
        "pout_w": "10000",
        "power_factor": "1.0",
        "inductor_current_ripple_ratio": "0.2",
        "dc_link_voltage_ripple_ratio": "0.05",
        "ambient_temp_c": "25",
        "target_junction_temp_c": "100",
    }


def build_spec(raw_input: Mapping[str, str]) -> TopologySpec:
    """Parse and validate raw GUI inputs into a first-pass NPC inverter spec."""

    try:
        vdc_nom_v = float(raw_input["vdc_nom"])
        vac_ll_rms_v = float(raw_input["vac_ll_rms"])
        f_line_hz = float(raw_input["f_line_hz"])
        fsw_hz = float(raw_input["fsw_hz"])
        pout_w = float(raw_input["pout_w"])
        power_factor = float(raw_input["power_factor"])
        inductor_current_ripple_ratio = float(raw_input["inductor_current_ripple_ratio"])
        dc_link_voltage_ripple_ratio = float(raw_input["dc_link_voltage_ripple_ratio"])
        metadata = merge_ambient_metadata(
            {
                "legacy_key": LEGACY_KEY,
                "vdc_nom_v": vdc_nom_v,
                "vac_ll_rms_v": vac_ll_rms_v,
                "f_line_hz": f_line_hz,
                "fsw_hz": fsw_hz,
                "pout_w": pout_w,
                "power_factor": power_factor,
                "conduction_mode": "ccm",
                "inductor_current_ripple_ratio": inductor_current_ripple_ratio,
                "dc_link_voltage_ripple_ratio": dc_link_voltage_ripple_ratio,
                "modulation_scheme": "phase_disposition_level_shifted_spwm_first_pass",
                "topology_level_count": 3,
                "phase_count": 3,
            },
            raw_input,
        )
    except KeyError as exc:
        raise ValueError(f"Missing input field: {exc.args[0]}") from exc
    except ValueError as exc:
        if "Ambient temperature" in str(exc) or "Target junction temperature" in str(exc):
            raise ValueError(str(exc)) from exc
        raise ValueError("All three-phase NPC inverter design inputs must be valid numbers.") from exc

    metadata = merge_semiconductor_filter_metadata(metadata, raw_input)

    if vdc_nom_v <= 0.0:
        raise ValueError("Vdc nominal must be positive.")
    if vac_ll_rms_v <= 0.0:
        raise ValueError("Vac line-line rms must be positive.")
    if f_line_hz <= 0.0:
        raise ValueError("Line frequency must be positive.")
    if fsw_hz <= 0.0:
        raise ValueError("Switching frequency must be positive.")
    if pout_w <= 0.0:
        raise ValueError("Output power must be positive.")
    if abs(power_factor) <= 0.0 or abs(power_factor) > 1.0:
        raise ValueError("Power factor magnitude must be in the range (0, 1].")
    if inductor_current_ripple_ratio <= 0.0:
        raise ValueError("Inductor current ripple ratio must be positive.")
    if dc_link_voltage_ripple_ratio <= 0.0:
        raise ValueError("DC-link voltage ripple ratio must be positive.")

    return TopologySpec(
        topology_id=TOPOLOGY_ID,
        display_name=DISPLAY_NAME,
        vin_min=vdc_nom_v,
        vin_max=vdc_nom_v,
        vout=vac_ll_rms_v,
        pout=pout_w,
        fs_khz=fsw_hz / 1e3,
        ripple_current_ratio=inductor_current_ripple_ratio,
        ripple_voltage_ratio_percent=dc_link_voltage_ripple_ratio * 100.0,
        raw_input=dict(raw_input),
        metadata=metadata,
    )
