"""Input handling for the single-phase full-bridge inverter topology."""

from __future__ import annotations

from collections.abc import Mapping

from ...base.spec import TopologySpec
from ....utils.ambient_temperature import merge_ambient_metadata

TOPOLOGY_ID = "single_phase_full_bridge_inverter"
DISPLAY_NAME = "Single-Phase Full-Bridge Inverter"
LEGACY_KEY = "SinglePhase_FullBridge_Inverter"


def build_default_inputs() -> dict[str, str]:
    """Return default raw inputs for the first-pass inverter design."""

    return {
        "conduction_mode": "CCM",
        "vdc_nom": "400",
        "vac_rms": "230",
        "f_line_hz": "50",
        "fsw_hz": "20000",
        "fsw_min_hz": "50000",
        "fsw_max_hz": "300000",
        "pout_w": "1000",
        "power_factor": "1.0",
        "inductor_current_ripple_ratio": "0.2",
        "tcm_valley_current_target_a": "-1",
        "dc_link_voltage_ripple_ratio": "0.05",
        "ambient_temp_c": "25",
        "target_junction_temp_c": "100",
    }


def build_spec(raw_input: Mapping[str, str]) -> TopologySpec:
    """Parse and validate raw GUI inputs into a full-bridge inverter spec."""

    conduction_mode = str(raw_input.get("conduction_mode", "CCM")).strip().lower()
    if conduction_mode not in {"ccm", "tcm"}:
        raise ValueError("Conduction mode must be CCM or TCM.")
    normalized_raw_input = dict(raw_input)
    normalized_raw_input["conduction_mode"] = conduction_mode

    try:
        vdc_nom_v = float(raw_input["vdc_nom"])
        vac_rms_v = float(raw_input["vac_rms"])
        f_line_hz = float(raw_input["f_line_hz"])
        fsw_hz = float(raw_input["fsw_hz"])
        if conduction_mode == "tcm":
            fsw_min_hz = float(raw_input.get("fsw_min_hz", "50000"))
            fsw_max_hz = float(raw_input.get("fsw_max_hz", "300000"))
        else:
            fsw_min_hz = _optional_float(raw_input.get("fsw_min_hz"), 50000.0)
            fsw_max_hz = _optional_float(raw_input.get("fsw_max_hz"), 300000.0)
        pout_w = float(raw_input["pout_w"])
        power_factor = float(raw_input["power_factor"])
        inductor_current_ripple_ratio = float(raw_input["inductor_current_ripple_ratio"])
        if conduction_mode == "tcm":
            tcm_valley_current_target_a = float(raw_input.get("tcm_valley_current_target_a", "-1"))
        else:
            tcm_valley_current_target_a = _optional_float(raw_input.get("tcm_valley_current_target_a"), -1.0)
        dc_link_voltage_ripple_ratio = float(raw_input["dc_link_voltage_ripple_ratio"])
        metadata = merge_ambient_metadata(
            {
                "legacy_key": LEGACY_KEY,
                "vdc_nom_v": vdc_nom_v,
                "vac_rms_v": vac_rms_v,
                "f_line_hz": f_line_hz,
                "fsw_hz": fsw_hz,
                "fsw_min_hz": fsw_min_hz,
                "fsw_max_hz": fsw_max_hz,
                "power_factor": power_factor,
                "conduction_mode": conduction_mode,
                "interleaved_cell_count": 1,
                "inductor_current_ripple_ratio": inductor_current_ripple_ratio,
                "tcm_valley_current_target_a": tcm_valley_current_target_a,
                "dc_link_voltage_ripple_ratio": dc_link_voltage_ripple_ratio,
                "modulation": "unipolar_spwm",
                "dc_link_capacitor_basis": "single-phase twice-line-frequency energy balance",
            },
            raw_input,
        )
    except KeyError as exc:
        raise ValueError(f"Missing input field: {exc.args[0]}") from exc
    except ValueError as exc:
        if "Ambient temperature" in str(exc) or "Target junction temperature" in str(exc):
            raise ValueError(str(exc)) from exc
        raise ValueError("All full-bridge inverter design inputs must be valid numbers.") from exc

    if vdc_nom_v <= 0.0:
        raise ValueError("Vdc nominal must be positive.")
    if vac_rms_v <= 0.0:
        raise ValueError("Vac rms must be positive.")
    if f_line_hz <= 0.0:
        raise ValueError("Line frequency must be positive.")
    if fsw_hz <= 0.0:
        raise ValueError("Switching frequency must be positive.")
    if conduction_mode == "tcm" and fsw_min_hz <= 0.0:
        raise ValueError("TCM minimum switching frequency must be positive.")
    if conduction_mode == "tcm" and fsw_max_hz <= fsw_min_hz:
        raise ValueError("TCM maximum switching frequency must be greater than TCM minimum switching frequency.")
    if pout_w <= 0.0:
        raise ValueError("Output power must be positive.")
    if power_factor <= 0.0 or power_factor > 1.0:
        raise ValueError("Power factor must be in the range (0, 1].")
    if inductor_current_ripple_ratio <= 0.0:
        raise ValueError("Inductor current ripple ratio must be positive.")
    if conduction_mode == "tcm" and tcm_valley_current_target_a >= 0.0:
        raise ValueError("TCM valley current target must be negative.")
    if dc_link_voltage_ripple_ratio <= 0.0:
        raise ValueError("DC-link voltage ripple ratio must be positive.")

    return TopologySpec(
        topology_id=TOPOLOGY_ID,
        display_name=DISPLAY_NAME,
        vin_min=vdc_nom_v,
        vin_max=vdc_nom_v,
        vout=vac_rms_v,
        pout=pout_w,
        fs_khz=fsw_hz / 1e3,
        ripple_current_ratio=inductor_current_ripple_ratio,
        ripple_voltage_ratio_percent=dc_link_voltage_ripple_ratio * 100.0,
        raw_input=normalized_raw_input,
        metadata=metadata,
    )


def _optional_float(value: object, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback
