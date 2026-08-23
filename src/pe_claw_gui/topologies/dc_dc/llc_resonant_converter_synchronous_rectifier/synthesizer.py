"""LLC synchronous-rectifier synthesis entry point."""

from __future__ import annotations

from dataclasses import asdict, replace

from ...base.candidate import TopologyCandidate
from ...base.spec import TopologySpec
from ..llc_resonant_converter_diode_rectifier.fha_design import design_llc_fha
from ..llc_resonant_converter_diode_rectifier.transformer_design import (
    build_transformer_design_target_metadata,
)
from .input_schema import (
    LLC_DISPLAY_NAME,
    LLC_LEGACY_KEY,
    LLC_TOPOLOGY_ID,
    SYNCHRONOUS_RECTIFIER_TIMING_MODE_INPUT_KEY,
)
from .stress_readback import build_llc_sr_stress_readback
from .timing_readback import build_llc_sr_timing_readback


def synthesize(spec: TopologySpec) -> TopologyCandidate:
    """Synthesize a first-pass full-bridge SR LLC candidate from diode LLC FHA."""

    fha_spec = _diode_fha_compatible_spec(spec)
    design = design_llc_fha(fha_spec)
    iout = design.pout_max_w / design.vout_nom_v
    timing_mode = str(
        spec.metadata.get(
            SYNCHRONOUS_RECTIFIER_TIMING_MODE_INPUT_KEY,
            "ideal_complementary_first_pass",
        )
    )
    llc_fha_metadata = asdict(design)
    llc_fha_metadata.update(
        {
            "topology_id": LLC_TOPOLOGY_ID,
            "secondary_rectifier_type": "full_bridge_synchronous_rectifier",
            "secondary_rectifier_note": (
                "For full_bridge_synchronous_rectifier, Ns is the full secondary winding; "
                "secondary rectification uses four synchronous switches in this first-pass SR MVP."
            ),
            "semiconductor_topology_counts": _sr_topology_counts(design.primary_bridge_type),
            "transformer_design_target": build_transformer_design_target_metadata(design),
        }
    )
    stress_readback = build_llc_sr_stress_readback(llc_fha_metadata, timing_mode=timing_mode)
    timing_readback = build_llc_sr_timing_readback(
        stress_readback,
        timing_mode=timing_mode,
        fsw_hz=design.fr_hz,
    )
    notes = [
        "First-pass LLC SR FHA electrical design; magnetic design and time-domain SR timing are not final signoff.",
        "Candidate inductance is the resonant inductance Lr and candidate capacitance is the resonant capacitance Cr.",
        "Secondary full-bridge rectification is modeled with secondary_sync_switch roles, not rectifier_diode roles.",
        "Separated LLC transformer target metadata is generated; Run Magnetics screens transformer candidates.",
    ]
    if not design.overall_feasible:
        notes.append("LLC FHA coverage did not pass all checked corners; see candidate metadata for diagnostics.")
    notes.extend(design.warnings)

    return TopologyCandidate(
        topology_id=LLC_TOPOLOGY_ID,
        display_name=LLC_DISPLAY_NAME,
        vin_min=design.vin_min_v,
        vin_max=design.vin_max_v,
        vin_nom=design.vin_nom_v,
        vout_target=design.vout_nom_v,
        pout_target=design.pout_max_w,
        duty_nom=0.5,
        iout=iout,
        fs_hz=design.fr_hz,
        inductance_h=design.lr_h,
        capacitance_f=design.cr_f,
        delta_il=0.0,
        delta_vo=0.0,
        il_peak=iout,
        il_valley=0.0,
        ccm_valid=design.overall_feasible,
        mode_capable="fha",
        feasible=design.overall_feasible,
        failure_reason=None if design.overall_feasible else "LLC FHA coverage failed one or more checked corners.",
        r_load_nom_ohm=design.rout_nom_ohm,
        notes=notes,
        metadata={
            "legacy_key": spec.metadata.get("legacy_key", LLC_LEGACY_KEY),
            "llc_fha": llc_fha_metadata,
            "llc_sr": {
                "stress_readback": stress_readback,
                "timing_readback": timing_readback,
                "first_pass_limitations": (
                    "LLC SR synthesis reuses diode LLC FHA electrical metadata.",
                    "SR timing, reverse conduction, Coss/Eoss, current sharing, and layout parasitics need follow-up.",
                ),
            },
        },
    )


def _diode_fha_compatible_spec(spec: TopologySpec) -> TopologySpec:
    raw_input = dict(spec.raw_input)
    metadata = dict(spec.metadata)
    raw_input["secondary_rectifier_type"] = "full_bridge_rectifier"
    metadata["secondary_rectifier_type"] = "full_bridge_rectifier"
    return replace(spec, raw_input=raw_input, metadata=metadata)


def _sr_topology_counts(primary_bridge_type: str) -> dict[str, object]:
    if primary_bridge_type == "half_bridge":
        main_switch = {
            "role_kind": "active_switch",
            "topology_position_count": 2,
            "position_labels": ["S_H", "S_L"],
        }
    else:
        main_switch = {
            "role_kind": "active_switch",
            "topology_position_count": 4,
            "position_labels": ["S1", "S2", "S3", "S4"],
        }
    return {
        "main_switch": main_switch,
        "secondary_sync_switch": {
            "role_kind": "synchronous_rectifier_switch",
            "topology_position_count": 4,
            "position_labels": ["SR1", "SR2", "SR3", "SR4"],
        },
    }
