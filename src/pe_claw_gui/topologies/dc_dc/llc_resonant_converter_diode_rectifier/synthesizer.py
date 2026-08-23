"""LLC diode-rectifier synthesis entry point."""

from __future__ import annotations

from dataclasses import asdict

from ...base.candidate import TopologyCandidate
from ...base.spec import TopologySpec
from .fha_design import design_llc_fha
from .transformer_design import build_transformer_design_target_metadata


def synthesize(spec: TopologySpec) -> TopologyCandidate:
    """Synthesize a first-pass FHA electrical design for the diode LLC topology."""

    design = design_llc_fha(spec)
    iout = design.pout_max_w / design.vout_nom_v
    notes = [
        "First-pass LLC FHA electrical design; magnetic design and time-domain waveforms are not included.",
        "Candidate inductance is the resonant inductance Lr and candidate capacitance is the resonant capacitance Cr.",
    ]
    if not design.overall_feasible:
        notes.append("LLC FHA coverage did not pass all checked corners; see candidate metadata for diagnostics.")
    notes.append(
        "Separated LLC transformer target metadata is generated; Run Magnetics screens transformer candidates."
    )
    notes.extend(design.warnings)
    llc_fha_metadata = asdict(design)
    llc_fha_metadata.update(
        {
            "hardware_reuse_mode": spec.metadata.get("hardware_reuse_mode", "new_design"),
            "hardware_design_case_id": spec.metadata.get("hardware_design_case_id", ""),
            "load_ratio": float(spec.metadata.get("load_ratio", 1.0)),
            "load_ratio_source": spec.metadata.get(
                "load_ratio_source", "unspecified_input"
            ),
            "commanded_switching_frequency_hz": float(
                spec.metadata.get("commanded_switching_frequency_hz", design.fr_hz)
            ),
        }
    )
    fixed_hardware = spec.metadata.get("fixed_hardware", {})
    if isinstance(fixed_hardware, dict) and fixed_hardware:
        llc_fha_metadata.update(
            {
                "selected_output_capacitance_f": float(fixed_hardware["output_capacitance_f"]),
                "selected_output_capacitor_esr_ohm": float(fixed_hardware["output_capacitor_esr_ohm"]),
                "fixed_hardware_snapshot": dict(fixed_hardware),
            }
        )
    llc_fha_metadata["transformer_design_target"] = build_transformer_design_target_metadata(design)

    return TopologyCandidate(
        topology_id=spec.topology_id,
        display_name=spec.display_name,
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
            "legacy_key": spec.metadata.get("legacy_key"),
            "hardware_reuse_mode": spec.metadata.get("hardware_reuse_mode", "new_design"),
            "hardware_design_case_id": spec.metadata.get("hardware_design_case_id", ""),
            "load_ratio": float(spec.metadata.get("load_ratio", 1.0)),
            "load_ratio_source": spec.metadata.get(
                "load_ratio_source", "unspecified_input"
            ),
            "llc_fha": llc_fha_metadata,
        },
    )
