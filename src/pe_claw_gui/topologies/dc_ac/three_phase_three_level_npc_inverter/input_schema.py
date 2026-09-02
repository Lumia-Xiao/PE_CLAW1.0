"""Input handling for the three-phase three-level NPC inverter."""

from __future__ import annotations

import math
from collections.abc import Mapping

from ....libraries.semiconductors.metadata import merge_semiconductor_filter_metadata
from ....utils.ambient_temperature import merge_ambient_metadata
from ...base.spec import TopologySpec

TOPOLOGY_ID = "three_phase_three_level_npc_inverter"
DISPLAY_NAME = "Three-Phase Three-Level NPC Inverter"
LEGACY_KEY = "ThreePhase_ThreeLevel_NPC_Inverter"

NPC_DESIGN_BASIS_DEFAULTS = {
    "vdc_min": "650",
    "vdc_nom": "700",
    "vdc_max": "750",
    "vac_ll_rms": "400",
    "f_output_hz": "50",
    "f_line_hz": "50",
    "fsw_hz": "20000",
    "pout_w": "10000",
    "power_factor": "1.0",
    "power_factor_min": "0.8",
    "power_factor_max": "1.0",
    "modulation_method": "phase_disposition_level_shifted_spwm",
    "modulation_index_limit": "1.0",
    "inductor_current_ripple_ratio": "0.2",
    "dc_link_voltage_ripple_ratio": "0.05",
    "neutral_point_voltage_deviation_ratio": "0.02",
    "neutral_point_voltage_stress_factor": "1.02",
    "switching_overvoltage_v": "50",
    "switching_overvoltage_source": "engineering_assumption_pending_double_pulse_test",
    "switching_overvoltage_validation_status": "unverified_assumption",
    "static_voltage_margin_ratio": "0.20",
    "efficiency_target": "0.98",
    "load_ratio_min": "0.05",
    "overload_ratio_max": "1.10",
    "ambient_temp_c": "25",
    "cooling_method": "forced_air",
    "altitude_m": "0",
    "target_junction_temp_c": "100",
    "application_notes": "Grid-connected three-phase inverter; CCM first-pass design basis.",
}


def build_default_inputs() -> dict[str, str]:
    """Return default raw inputs for first-pass three-phase NPC inverter design."""

    return dict(NPC_DESIGN_BASIS_DEFAULTS)


def normalize_design_basis(raw_input: Mapping[str, object]) -> dict[str, object]:
    """Normalize the authoritative NPC design basis and its derived current."""

    values = {**NPC_DESIGN_BASIS_DEFAULTS, **{str(key): value for key, value in raw_input.items()}}
    # Older API callers supplied only Vdc nominal; retain their fixed-bus behavior.
    if "vdc_min" not in raw_input:
        values["vdc_min"] = values["vdc_nom"]
    if "vdc_max" not in raw_input:
        values["vdc_max"] = values["vdc_nom"]

    def number(key: str) -> float:
        try:
            return float(values[key])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"NPC design-basis field {key!r} must be a valid number.") from exc

    vdc_min_v = number("vdc_min")
    vdc_nom_v = number("vdc_nom")
    vdc_max_v = number("vdc_max")
    vac_ll_rms_v = number("vac_ll_rms")
    output_frequency_hz = number("f_output_hz")
    line_frequency_hz = number("f_line_hz")
    switching_frequency_hz = number("fsw_hz")
    output_power_w = number("pout_w")
    power_factor = number("power_factor")
    power_factor_min = number("power_factor_min")
    power_factor_max = number("power_factor_max")
    modulation_index_limit = number("modulation_index_limit")
    current_ripple_ratio = number("inductor_current_ripple_ratio")
    voltage_ripple_ratio = number("dc_link_voltage_ripple_ratio")
    neutral_point_deviation_ratio = number("neutral_point_voltage_deviation_ratio")
    neutral_point_stress_factor = number("neutral_point_voltage_stress_factor")
    switching_overvoltage_v = number("switching_overvoltage_v")
    static_voltage_margin_ratio = number("static_voltage_margin_ratio")
    efficiency_target = number("efficiency_target")
    load_ratio_min = number("load_ratio_min")
    overload_ratio_max = number("overload_ratio_max")
    ambient_temp_c = number("ambient_temp_c")
    altitude_m = number("altitude_m")
    target_junction_temp_c = number("target_junction_temp_c")

    positive = {
        "vdc_min": vdc_min_v,
        "vdc_nom": vdc_nom_v,
        "vdc_max": vdc_max_v,
        "vac_ll_rms": vac_ll_rms_v,
        "f_output_hz": output_frequency_hz,
        "f_line_hz": line_frequency_hz,
        "fsw_hz": switching_frequency_hz,
        "pout_w": output_power_w,
        "modulation_index_limit": modulation_index_limit,
        "inductor_current_ripple_ratio": current_ripple_ratio,
        "dc_link_voltage_ripple_ratio": voltage_ripple_ratio,
        "neutral_point_voltage_deviation_ratio": neutral_point_deviation_ratio,
        "efficiency_target": efficiency_target,
        "load_ratio_min": load_ratio_min,
        "overload_ratio_max": overload_ratio_max,
    }
    for key, value in positive.items():
        if value <= 0.0:
            label = "Vdc nominal" if key == "vdc_nom" else key
            raise ValueError(f"{label} must be positive.")
    if not vdc_min_v <= vdc_nom_v <= vdc_max_v:
        raise ValueError("NPC DC-link voltage basis must satisfy Vdc_min <= Vdc_nom <= Vdc_max.")
    if neutral_point_stress_factor < 1.0:
        raise ValueError("Neutral-point voltage stress factor must be at least 1.")
    if switching_overvoltage_v < 0.0:
        raise ValueError("Switching overvoltage must not be negative.")
    if static_voltage_margin_ratio < 0.20:
        raise ValueError("Static voltage margin must be at least 20%.")
    if not 0.0 < abs(power_factor) <= 1.0:
        raise ValueError("Power factor magnitude must be in the range (0, 1].")
    if not 0.0 < power_factor_min <= power_factor_max <= 1.0:
        raise ValueError("Power factor range must satisfy 0 < PF_min <= PF_max <= 1.")
    if not power_factor_min <= abs(power_factor) <= power_factor_max:
        raise ValueError("Design-point power factor must be inside the requested PF range.")
    if not 0.0 < efficiency_target <= 1.0:
        raise ValueError("Efficiency target must be in the range (0, 1].")
    if load_ratio_min > 1.0:
        raise ValueError("Minimum load ratio must not exceed 1.")
    if overload_ratio_max < 1.0:
        raise ValueError("Maximum overload ratio must be at least 1.")
    if not str(values["modulation_method"]).strip():
        raise ValueError("Modulation method must not be empty.")
    if not str(values["cooling_method"]).strip():
        raise ValueError("Cooling method must not be empty.")

    vac_phase_peak_v = math.sqrt(2.0 / 3.0) * vac_ll_rms_v
    derived_phase_current_rms_a = output_power_w / (math.sqrt(3.0) * vac_ll_rms_v * abs(power_factor))
    design_modulation_index = 2.0 * vac_phase_peak_v / vdc_nom_v
    return {
        "schema_version": 1,
        "status": "normalized_design_basis",
        "topology_id": TOPOLOGY_ID,
        "dc_link_voltage_v": {"min": vdc_min_v, "nominal": vdc_nom_v, "max": vdc_max_v},
        "ac_output": {
            "line_line_rms_v": vac_ll_rms_v,
            "frequency_hz": output_frequency_hz,
            "line_frequency_hz": line_frequency_hz,
            "power_w": output_power_w,
            "phase_current_rms_a": derived_phase_current_rms_a,
            "phase_current_basis": "Pout / (sqrt(3) * Vac_ll_rms * abs(PF))",
        },
        "switching": {
            "frequency_hz": switching_frequency_hz,
            "modulation_method": str(values["modulation_method"]).strip(),
            "modulation_index_design": design_modulation_index,
            "modulation_index_limit": modulation_index_limit,
            "modulation_index_basis": "2 * Vac_phase_peak / Vdc_nom",
        },
        "power_factor": {"design": power_factor, "min": power_factor_min, "max": power_factor_max},
        "targets": {
            "inductor_current_ripple_ratio": current_ripple_ratio,
            "dc_link_voltage_ripple_ratio": voltage_ripple_ratio,
            "neutral_point_voltage_deviation_ratio": neutral_point_deviation_ratio,
            "neutral_point_voltage_stress_factor": neutral_point_stress_factor,
            "static_voltage_margin_ratio": static_voltage_margin_ratio,
            "efficiency": efficiency_target,
        },
        "voltage_stress": {
            "neutral_point_stress_factor": neutral_point_stress_factor,
            "switching_overvoltage_v": switching_overvoltage_v,
            "switching_overvoltage_source": str(values["switching_overvoltage_source"]).strip(),
            "switching_overvoltage_validation_status": str(values["switching_overvoltage_validation_status"]).strip(),
            "static_voltage_margin_ratio": static_voltage_margin_ratio,
        },
        "operating_range": {"load_ratio_min": load_ratio_min, "overload_ratio_max": overload_ratio_max},
        "thermal": {
            "ambient_temperature_c": ambient_temp_c,
            "cooling_method": str(values["cooling_method"]).strip(),
            "altitude_m": altitude_m,
            "target_junction_temperature_c": target_junction_temp_c,
        },
        "application_notes": str(values["application_notes"]).strip(),
        "assumptions": [
            "Vdc min/nominal/max are explicit design-basis operating points.",
            "Output and line frequency are independently recorded; this grid-connected basis uses the same default value.",
            "Output current is derived at the design power factor and is not an independently entered rating.",
            "Dynamic switching overvoltage is an explicit engineering assumption until double-pulse and busbar validation are available.",
        ],
        "source": {
            "type": "runtime_raw_input",
            "identity": "topology_form_or_api",
            "path": str(values.get("design_request_path", "runtime_raw_input")),
        },
    }


def build_spec(raw_input: Mapping[str, str]) -> TopologySpec:
    """Parse and validate raw GUI inputs into a first-pass NPC inverter spec."""

    try:
        basis = normalize_design_basis(raw_input)
        vdc_nom_v = float(basis["dc_link_voltage_v"]["nominal"])
        vdc_min_v = float(basis["dc_link_voltage_v"]["min"])
        vdc_max_v = float(basis["dc_link_voltage_v"]["max"])
        vac_ll_rms_v = float(basis["ac_output"]["line_line_rms_v"])
        f_line_hz = float(basis["ac_output"]["line_frequency_hz"])
        fsw_hz = float(basis["switching"]["frequency_hz"])
        pout_w = float(basis["ac_output"]["power_w"])
        power_factor = float(basis["power_factor"]["design"])
        inductor_current_ripple_ratio = float(basis["targets"]["inductor_current_ripple_ratio"])
        dc_link_voltage_ripple_ratio = float(basis["targets"]["dc_link_voltage_ripple_ratio"])
        metadata = merge_ambient_metadata(
            {
                "legacy_key": LEGACY_KEY,
                "vdc_min_v": vdc_min_v,
                "vdc_nom_v": vdc_nom_v,
                "vdc_max_v": vdc_max_v,
                "vac_ll_rms_v": vac_ll_rms_v,
                "f_line_hz": f_line_hz,
                "fsw_hz": fsw_hz,
                "pout_w": pout_w,
                "power_factor": power_factor,
                "conduction_mode": "ccm",
                "inductor_current_ripple_ratio": inductor_current_ripple_ratio,
                "dc_link_voltage_ripple_ratio": dc_link_voltage_ripple_ratio,
                "npc_neutral_point_stress_factor": float(basis["voltage_stress"]["neutral_point_stress_factor"]),
                "npc_switching_overvoltage_v": float(basis["voltage_stress"]["switching_overvoltage_v"]),
                "npc_switching_overvoltage_source": basis["voltage_stress"]["switching_overvoltage_source"],
                "npc_switching_overvoltage_validation_status": basis["voltage_stress"]["switching_overvoltage_validation_status"],
                "npc_static_voltage_margin_ratio": float(basis["voltage_stress"]["static_voltage_margin_ratio"]),
                "modulation_scheme": f"{basis['switching']['modulation_method']}_first_pass",
                "topology_level_count": 3,
                "phase_count": 3,
                "design_basis": basis,
            },
            raw_input,
        )
    except KeyError as exc:
        raise ValueError(f"Missing input field: {exc.args[0]}") from exc
    except ValueError as exc:
        if "Ambient temperature" in str(exc) or "Target junction temperature" in str(exc):
            raise ValueError(str(exc)) from exc
        raise ValueError("All three-phase NPC inverter design inputs must be valid numbers: " + str(exc)) from exc

    metadata = merge_semiconductor_filter_metadata(metadata, raw_input)

    return TopologySpec(
        topology_id=TOPOLOGY_ID,
        display_name=DISPLAY_NAME,
        vin_min=vdc_min_v,
        vin_max=vdc_max_v,
        vout=vac_ll_rms_v,
        pout=pout_w,
        fs_khz=fsw_hz / 1e3,
        ripple_current_ratio=inductor_current_ripple_ratio,
        ripple_voltage_ratio_percent=dc_link_voltage_ripple_ratio * 100.0,
        raw_input=dict(raw_input),
        metadata=metadata,
    )
