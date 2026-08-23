"""First-pass implementation boundary for LLC synchronous rectification.

This module documents the executable full-bridge SR first-pass boundary. The
topology reuses the diode LLC FHA/transformer/capacitor path and replaces the
secondary diode semantics with synchronous-rectifier switch readback.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LLCSynchronousRectifierFirstPassScope:
    """Small structured record for the LLC SR first-pass implementation scope."""

    target_topology_id: str
    source_topology_id: str
    first_pass_rectifier_structure: str
    reused_diode_llc_modules: tuple[str, ...]
    sr_specific_work_items: tuple[str, ...]
    replaced_diode_llc_semantics: tuple[str, ...]
    blocked_until_work_items: tuple[str, ...]
    executable_after_step: bool


def build_llc_sr_first_pass_scope() -> LLCSynchronousRectifierFirstPassScope:
    """Return the locked scope for the first-pass full-bridge LLC SR path."""

    return LLCSynchronousRectifierFirstPassScope(
        target_topology_id="llc_resonant_converter_synchronous_rectifier",
        source_topology_id="llc_resonant_converter_diode_rectifier",
        first_pass_rectifier_structure="full_bridge_synchronous_rectifier",
        reused_diode_llc_modules=(
            "fha_design",
            "transformer_design",
            "resonant_capacitor_pipeline",
            "waveform_frequency_solution",
            "session_report_artifact_pipeline",
        ),
        sr_specific_work_items=(
            "secondary_sync_switch_role",
            "sr_stress_adapter",
            "sr_loss_model",
            "sr_deadtime_body_diode_readback",
            "sr_report_audit",
        ),
        replaced_diode_llc_semantics=(
            "rectifier_diode_role",
            "diode_forward_drop_loss_model",
            "secondary_diode_waveform_states",
            "diode_reverse_recovery_follow_up",
        ),
        blocked_until_work_items=(
            "input_schema_and_md_first_mapping",
            "secondary_sync_switch_device_role",
            "sr_stress_and_loss_readback",
            "report_audit_review_acceptance",
        ),
        executable_after_step=True,
    )


__all__ = [
    "LLCSynchronousRectifierFirstPassScope",
    "build_llc_sr_first_pass_scope",
]
