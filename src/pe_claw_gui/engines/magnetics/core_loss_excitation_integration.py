"""Shadow-only adapters from selected PE-Claw magnetics to core-loss excitation."""

from __future__ import annotations

from dataclasses import replace
import math
from typing import Any, Iterable

from ...models.design_report import DesignReport
from ...models.inductor import FixedInductorDesignCandidate
from ...models.magnetic_loss_contract import (
    CoreLossExcitationBuildRequest,
    CoreLossExcitationBuildResult,
)
from ...models.magnetic_result import MagneticResult
from ..thermal.thermal_estimator import resolve_ambient_temperature_c
from .core_loss_excitation_builder import build_core_loss_excitation


CORE_LOSS_EXCITATION_AUDIT_VERSION = "core-loss-excitation-build-v1"
_LONG_TIME_SCALE_TOPOLOGY_IDS = {
    "single_phase_boost_pfc_diode_bridge",
    "single_phase_totem_pole_bridgeless_pfc",
    "single_phase_full_bridge_inverter",
    "three_phase_two_level_voltage_source_inverter",
    "three_phase_three_level_npc_inverter",
}


def attach_core_loss_excitation_audit(
    report: DesignReport,
    *,
    include_design_reference: bool = True,
    include_operating_waveform: bool = True,
) -> DesignReport:
    """Attach selected-hardware excitation records without changing production loss."""

    if report.magnetic is None:
        return report
    existing = report.magnetic.core_loss_excitation_audit
    records = dict(existing.get("records", {})) if isinstance(existing, dict) else {}
    try:
        generated = _build_role_records(
            report,
            include_design_reference=include_design_reference,
            include_operating_waveform=include_operating_waveform,
        )
        records.update(generated)
    except Exception as exc:
        records["integration:error"] = {
            "status": "invalid_input",
            "excitation": None,
            "source_component_id": report.magnetic.selected_design_id or "unselected-magnetic-component",
            "reconstruction_method": "role_adapter_failure",
            "waveform_period_s": None,
            "waveform_sample_count": 0,
            "source_fields": [],
            "consistency_checks": {},
            "messages": [f"{type(exc).__name__}: {exc}"],
        }
    audit = {
        "contract_version": CORE_LOSS_EXCITATION_AUDIT_VERSION,
        "mode": "shadow_only",
        "records": dict(sorted(records.items())),
    }
    return replace(report, magnetic=replace(report.magnetic, core_loss_excitation_audit=audit))


def _build_role_records(
    report: DesignReport,
    *,
    include_design_reference: bool,
    include_operating_waveform: bool,
) -> dict[str, object]:
    result_type = report.magnetic.result_type
    if result_type == "flyback_coupled_inductor":
        return _flyback_records(report, include_design_reference, include_operating_waveform)
    if result_type == "separated_llc_transformer":
        return _llc_records(report, include_design_reference, include_operating_waveform)
    if result_type == "psfb_transformer_output_inductor":
        return _psfb_records(report, include_design_reference, include_operating_waveform)
    if result_type == "ac_dc_sendust_reactor":
        return _sendust_records(report, include_design_reference, include_operating_waveform)
    return _generic_inductor_records(report, include_design_reference, include_operating_waveform)


def _generic_inductor_records(
    report: DesignReport,
    include_design_reference: bool,
    include_operating_waveform: bool,
) -> dict[str, object]:
    design = _selected_fixed_design(report.magnetic)
    if design is None:
        return {}
    temperature_c = resolve_ambient_temperature_c(report)
    records: dict[str, object] = {}
    area_m2 = _positive_float(design.metadata.get("core_effective_area_m2"))
    volume_m3 = _positive_float(design.metadata.get("core_effective_volume_m3"))
    source_fields = _candidate_source_fields(design)
    requirements = report.magnetic.design_requirements
    frequency_hz = _positive_float(requirements.get("fs_hz")) or _waveform_frequency(report)

    tcm_segments = design.metadata.get("tcm_segments")
    if include_design_reference and isinstance(tcm_segments, (tuple, list)) and tcm_segments:
        records.update(_tcm_segment_records(report, design, tcm_segments, temperature_c, area_m2, volume_m3))
    elif include_design_reference and frequency_hz is not None:
        inverter_flux = _single_phase_inverter_pwm_flux_declarations(
            report,
            design,
            frequency_hz=frequency_hz,
            area_m2=area_m2,
        )
        if inverter_flux is not None:
            bpp_t, ac_peak_t, dc_offset_t, source_fields = inverter_flux
            inverter_result = _build_scalar(
                frequency_hz=frequency_hz,
                temperature_c=temperature_c,
                report=report,
                role="main_inductor",
                component_id=design.candidate_id,
                volume_m3=volume_m3,
                inductance_h=design.inductance_h,
                template="bipolar_triangular",
                ac_peak_t=ac_peak_t,
                peak_to_peak_t=bpp_t,
                dc_offset_t=dc_offset_t,
                absolute_peak_t=None,
                source_fields=source_fields,
            )
            records["design_reference:main_inductor"] = _with_saturation_screening_flux(
                inverter_result,
                design.b_peak_design_t,
            ).to_dict()
        else:
            current_min_a = _finite_float(requirements.get("i_valley_a"))
            current_max_a = _finite_float(requirements.get("i_peak_a"))
            if current_min_a is None or current_max_a is None:
                records["design_reference:main_inductor"] = _build_unavailable(
                    frequency_hz=frequency_hz,
                    temperature_c=temperature_c,
                    report=report,
                    role="main_inductor",
                    component_id=design.candidate_id,
                    source_fields=(*source_fields, "MagneticResult.design_requirements:i_peak/i_valley_missing"),
                ).to_dict()
            else:
                records["design_reference:main_inductor"] = _build_piecewise_current_scalar(
                    frequency_hz=frequency_hz,
                    temperature_c=temperature_c,
                    report=report,
                    role="main_inductor",
                    component_id=design.candidate_id,
                    area_m2=area_m2,
                    volume_m3=volume_m3,
                    turns=design.turns,
                    inductance_h=design.inductance_h,
                    current_min_a=current_min_a,
                    current_max_a=current_max_a,
                    current_rms_a=_positive_float(requirements.get("i_rms_a")),
                    declared_absolute_peak_t=design.b_peak_design_t,
                    source_fields=(*source_fields, "MagneticResult.design_requirements"),
                ).to_dict()

    if include_operating_waveform and report.waveform is not None:
        current_source = _generic_operating_current_source(report)
        if current_source is None:
            records["operating_waveform:main_inductor"] = _build_unavailable(
                frequency_hz=frequency_hz or (1.0 / report.waveform.switching_period_s),
                temperature_c=temperature_c,
                report=report,
                role="main_inductor",
                component_id=design.candidate_id,
                source_fields=(
                    *source_fields,
                    "WaveformSet.metadata.magnetic_local_switching_period:missing",
                ),
            ).to_dict()
            return records
        operating_frequency_hz, current_time_s, current_a, current_source_field = current_source
        records["operating_waveform:main_inductor"] = _build(
            frequency_hz=operating_frequency_hz,
            temperature_c=temperature_c,
            report=report,
            role="main_inductor",
            component_id=design.candidate_id,
            area_m2=area_m2,
            volume_m3=volume_m3,
            turns=design.turns,
            inductance_h=design.inductance_h,
            current_time_s=current_time_s,
            current_a=current_a,
            current_rms_a=_rms(current_a),
            declared_absolute_peak_t=design.b_peak_design_t,
            source_fields=(*source_fields, current_source_field),
        ).to_dict()
    return records


def _with_saturation_screening_flux(
    result: CoreLossExcitationBuildResult,
    absolute_peak_t: float | None,
) -> CoreLossExcitationBuildResult:
    """Attach absolute saturation-screening B without changing AC excitation."""

    if absolute_peak_t is None:
        return result
    checks = dict(result.consistency_checks)
    checks["saturation_screening"] = {
        "flux_absolute_peak_t": float(absolute_peak_t),
        "definition": "Babsolute=L*Ipeak/(N*Ae); screening value, not PWM AC loss flux",
    }
    return replace(result, consistency_checks=checks)


def _single_phase_inverter_pwm_flux_declarations(
    report: DesignReport,
    design: FixedInductorDesignCandidate,
    *,
    frequency_hz: float,
    area_m2: float | None,
) -> tuple[float, float, float, tuple[str, ...]] | None:
    """Return PWM AC flux declarations for the inverter output inductor.

    The inverter's design-point current contains the 60-Hz fundamental.  It is
    therefore not a valid one-switching-period excitation for core-loss audit.
    Use the explicit PWM volt-second proxy from the normalized inductor
    request, while retaining candidate ``b_peak_design_t`` separately as the
    absolute saturation-screening value.
    """

    if report.spec.topology_id != "single_phase_full_bridge_inverter":
        return None
    if area_m2 is None or area_m2 <= 0.0 or design.turns <= 0 or frequency_hz <= 0.0:
        return None
    requirements = report.magnetic.design_requirements if report.magnetic is not None else {}
    candidate = report.candidate
    v_l_on_v = _finite_float(requirements.get("v_l_on_v"))
    voltage_source = "MagneticResult.design_requirements:v_l_on_v"
    duty = _finite_float(requirements.get("duty_nom"))
    if v_l_on_v is None and candidate is not None:
        v_l_on_v = 0.5 * abs(float(candidate.vin_nom))
        voltage_source = "DesignReport.candidate:0.5*vin_nom_fallback"
    if duty is None:
        duty = 0.5
    if v_l_on_v is None or duty is None or duty <= 0.0:
        return None
    bpp_t = abs(v_l_on_v) * duty / (frequency_hz * design.turns * area_m2)
    if not math.isfinite(bpp_t) or bpp_t < 0.0:
        return None
    return (
        bpp_t,
        0.5 * bpp_t,
        0.0,
        (
            voltage_source,
            "MagneticResult.design_requirements:duty_nom",
            "PWM AC flux definition:DeltaBpp=|Vl|*D/(fs*N*Ae)",
            "Babsolute retained separately from FixedInductorDesignCandidate.b_peak_design_t",
        ),
    )


def _flyback_records(
    report: DesignReport,
    include_design_reference: bool,
    include_operating_waveform: bool,
) -> dict[str, object]:
    design = _selected_fixed_design(report.magnetic)
    if design is None:
        return {}
    metadata = design.metadata
    temperature_c = resolve_ambient_temperature_c(report)
    frequency_hz = _candidate_frequency(report)
    area_m2 = _positive_float(metadata.get("core_effective_area_m2"))
    records: dict[str, object] = {}
    source_fields = _candidate_source_fields(design)
    if include_design_reference:
        peak_a = _float(metadata.get("primary_peak_current_a"), 0.0)
        valley_a = _float(report.magnetic.design_requirements.get("primary_valley_current_a"), 0.0)
        current_time_s, current_a = _triangular_current_source(frequency_hz, 0.5 * (peak_a + valley_a), peak_a, valley_a)
        records["design_reference:flyback_coupled_inductor_core"] = _build(
            frequency_hz=frequency_hz,
            temperature_c=temperature_c,
            report=report,
            role="flyback_coupled_inductor_core",
            component_id=design.candidate_id,
            area_m2=area_m2,
            volume_m3=design.core_volume_m3,
            turns=int(metadata.get("primary_turns", design.turns)),
            inductance_h=design.inductance_h,
            current_time_s=current_time_s,
            current_a=current_a,
            current_rms_a=_positive_float(metadata.get("primary_rms_current_a")),
            declared_absolute_peak_t=design.b_peak_design_t,
            source_fields=(*source_fields, "Flyback selected primary current metrics"),
        ).to_dict()
    if include_operating_waveform and report.waveform is not None:
        records["operating_waveform:flyback_coupled_inductor_core"] = _build(
            frequency_hz=frequency_hz,
            temperature_c=temperature_c,
            report=report,
            role="flyback_coupled_inductor_core",
            component_id=design.candidate_id,
            area_m2=area_m2,
            volume_m3=design.core_volume_m3,
            turns=int(metadata.get("primary_turns", design.turns)),
            inductance_h=design.inductance_h,
            current_time_s=tuple(report.waveform.time_s),
            current_a=tuple(report.waveform.inductor_current_a),
            current_rms_a=_rms(report.waveform.inductor_current_a),
            declared_absolute_peak_t=design.b_peak_design_t,
            source_fields=(*source_fields, "WaveformSet.inductor_current_a:flyback_magnetizing_current"),
        ).to_dict()
    return records


def _llc_records(
    report: DesignReport,
    include_design_reference: bool,
    include_operating_waveform: bool,
) -> dict[str, object]:
    temperature_c = resolve_ambient_temperature_c(report)
    pareto = report.magnetic.transformer_pareto_result
    transformer = getattr(pareto, "recommended_candidate", None)
    external_search = report.magnetic.llc_external_resonant_inductor_search_result
    external = getattr(external_search, "recommended_candidate", None)
    waveform_metadata = _nested_metadata(report, "llc_fha_waveforms")
    fs_op_hz = _positive_float(waveform_metadata.get("fs_op_hz")) or _candidate_frequency(report)
    records: dict[str, object] = {}

    if transformer is not None and include_design_reference:
        records["design_reference:llc_transformer_core"] = _build_scalar(
            frequency_hz=_positive_float(transformer.frequency_basis_hz) or fs_op_hz,
            temperature_c=temperature_c,
            report=report,
            role="llc_transformer_core",
            component_id=transformer.candidate_id,
            volume_m3=transformer.ve_m3,
            inductance_h=transformer.lm_actual_h,
            template="bipolar_triangular",
            ac_peak_t=transformer.max_b_peak_t,
            peak_to_peak_t=transformer.max_delta_b_t,
            dc_offset_t=0.0,
            absolute_peak_t=transformer.max_b_peak_t,
            source_fields=("LLCTransformerScreeningCandidate.max_delta_b_t", "LLC transformer symmetric bipolar declaration"),
        ).to_dict()
    if transformer is not None and include_operating_waveform and waveform_metadata:
        records["operating_waveform:llc_transformer_core"] = _build_voltage(
            frequency_hz=fs_op_hz,
            temperature_c=temperature_c,
            report=report,
            role="llc_transformer_core",
            component_id=transformer.candidate_id,
            area_m2=transformer.ae_m2,
            volume_m3=transformer.ve_m3,
            turns=transformer.np,
            inductance_h=transformer.lm_actual_h,
            voltage_time_s=tuple(_list(waveform_metadata.get("time_s"))),
            voltage_v=tuple(_list(waveform_metadata.get("v_lm_square_v"))),
            declared_peak_to_peak_t=transformer.max_delta_b_t,
            declared_absolute_peak_t=transformer.max_b_peak_t,
            source_fields=("WaveformSet.metadata.llc_fha_waveforms.v_lm_square_v", "LLCTransformerScreeningCandidate.np/ae_m2"),
        ).to_dict()

    if external is not None and include_design_reference:
        records["design_reference:llc_external_resonant_inductor_core"] = _build_scalar(
            frequency_hz=external.fs_basis_hz,
            temperature_c=temperature_c,
            report=report,
            role="llc_external_resonant_inductor_core",
            component_id=external.design_id,
            volume_m3=external.core_volume_m3 or None,
            inductance_h=external.actual_l_h,
            template="sinusoidal_zero_mean",
            ac_peak_t=external.b_peak_t,
            peak_to_peak_t=2.0 * external.b_peak_t,
            dc_offset_t=0.0,
            absolute_peak_t=external.b_peak_t,
            source_fields=("LlcExternalResonantInductorCandidate.b_peak_t", "sinusoidal_peak current convention"),
        ).to_dict()
    if external is not None and include_operating_waveform and waveform_metadata:
        records["operating_waveform:llc_external_resonant_inductor_core"] = _build(
            frequency_hz=fs_op_hz,
            temperature_c=temperature_c,
            report=report,
            role="llc_external_resonant_inductor_core",
            component_id=external.design_id,
            area_m2=external.core_effective_area_m2,
            volume_m3=external.core_volume_m3 or None,
            turns=external.turns,
            inductance_h=external.actual_l_h,
            current_time_s=tuple(_list(waveform_metadata.get("time_s"))),
            current_a=tuple(_list(waveform_metadata.get("i_lr_a"))),
            current_rms_a=external.current_rms_a,
            declared_absolute_peak_t=external.b_peak_t,
            source_fields=("WaveformSet.metadata.llc_fha_waveforms.i_lr_a", "external Lr actual_l_h/turns/Ae"),
        ).to_dict()
    return records


def _psfb_records(
    report: DesignReport,
    include_design_reference: bool,
    include_operating_waveform: bool,
) -> dict[str, object]:
    design = _selected_fixed_design(report.magnetic)
    if design is None:
        return {}
    metadata = design.metadata
    temperature_c = resolve_ambient_temperature_c(report)
    frequency_hz = _candidate_frequency(report)
    records: dict[str, object] = {}
    if include_design_reference:
        records["design_reference:psfb_transformer_core"] = _build_scalar(
            frequency_hz=frequency_hz,
            temperature_c=temperature_c,
            report=report,
            role="psfb_transformer_core",
            component_id=design.candidate_id,
            volume_m3=design.core_volume_m3,
            inductance_h=design.inductance_h,
            template="bipolar_triangular",
            ac_peak_t=design.b_peak_design_t,
            peak_to_peak_t=None if design.b_peak_design_t is None else 2.0 * design.b_peak_design_t,
            dc_offset_t=0.0,
            absolute_peak_t=design.b_peak_design_t,
            source_fields=("PSFB transformer symmetric bipolar b_peak_design_t",),
        ).to_dict()
    if include_operating_waveform and report.waveform is not None:
        records["operating_waveform:psfb_transformer_core"] = _build_voltage(
            frequency_hz=frequency_hz,
            temperature_c=temperature_c,
            report=report,
            role="psfb_transformer_core",
            component_id=design.candidate_id,
            area_m2=_positive_float(metadata.get("core_effective_area_m2")),
            volume_m3=design.core_volume_m3,
            turns=int(metadata.get("primary_turns", design.turns)),
            inductance_h=design.inductance_h,
            voltage_time_s=tuple(report.waveform.time_s),
            voltage_v=tuple(report.waveform.switch_node_voltage_v),
            declared_peak_to_peak_t=None if design.b_peak_design_t is None else 2.0 * design.b_peak_design_t,
            declared_absolute_peak_t=design.b_peak_design_t,
            source_fields=("WaveformSet.switch_node_voltage_v:PSFB_primary_bridge", "selected transformer Np/Ae"),
        ).to_dict()
        output_area_m2 = _positive_float(metadata.get("output_inductor_core_effective_area_m2"))
        output_turns = _positive_int(metadata.get("output_inductor_turns"))
        output_l_h = _positive_float(metadata.get("output_inductor_inductance_h"))
        if output_area_m2 and output_turns and output_l_h:
            records["operating_waveform:psfb_output_inductor_core"] = _build(
                frequency_hz=frequency_hz,
                temperature_c=temperature_c,
                report=report,
                role="psfb_output_inductor_core",
                component_id=str(metadata.get("output_inductor_selected_design_id", "psfb-output-inductor")),
                area_m2=output_area_m2,
                volume_m3=_positive_float(metadata.get("output_inductor_core_effective_volume_m3")),
                turns=output_turns,
                inductance_h=output_l_h,
                current_time_s=tuple(report.waveform.time_s),
                current_a=tuple(report.waveform.inductor_current_a),
                current_rms_a=_rms(report.waveform.inductor_current_a),
                declared_absolute_peak_t=_positive_float(metadata.get("output_inductor_b_peak_t")),
                source_fields=("WaveformSet.inductor_current_a:PSFB_output_inductor", "paired output inductor L/N/Ae"),
            ).to_dict()
    return records


def _sendust_records(
    report: DesignReport,
    include_design_reference: bool,
    include_operating_waveform: bool,
) -> dict[str, object]:
    selection = report.magnetic.ac_dc_reactor_result
    selected = selection.selected_candidate if selection is not None else None
    if selected is None:
        return {}
    temperature_c = resolve_ambient_temperature_c(report)
    frequency_hz = selection.request.ripple_frequency_hz
    area_m2 = selected.ae_cm2 * 1.0e-4
    volume_m3 = selected.ve_cm3 * 1.0e-6
    records: dict[str, object] = {}
    if include_design_reference:
        records["design_reference:ac_dc_sendust_reactor_core"] = _build_scalar(
            frequency_hz=frequency_hz,
            temperature_c=temperature_c,
            report=report,
            role="ac_dc_sendust_reactor_core",
            component_id=selected.candidate_id,
            volume_m3=volume_m3,
            inductance_h=selected.per_core_effective_inductance_h,
            template="dc_biased_triangular",
            ac_peak_t=None if selected.delta_b_t is None else 0.5 * selected.delta_b_t,
            peak_to_peak_t=selected.delta_b_t,
            dc_offset_t=selected.b_dc_t,
            absolute_peak_t=selected.b_peak_t,
            source_fields=("AcDcReactorCandidate.b_dc_t", "AcDcReactorCandidate.delta_b_t:T_delta_b"),
        ).to_dict()
    if include_operating_waveform and report.waveform is not None:
        parallel = max(selected.parallel_core_count, 1)
        records["operating_waveform:ac_dc_sendust_reactor_core"] = _build(
            frequency_hz=frequency_hz,
            temperature_c=temperature_c,
            report=report,
            role="ac_dc_sendust_reactor_core",
            component_id=selected.candidate_id,
            area_m2=area_m2,
            volume_m3=volume_m3,
            turns=selected.per_core_turns,
            inductance_h=selected.per_core_effective_inductance_h,
            current_time_s=tuple(report.waveform.time_s),
            current_a=tuple(value / parallel for value in report.waveform.inductor_current_a),
            current_rms_a=_rms(report.waveform.inductor_current_a) / parallel,
            declared_peak_to_peak_t=selected.delta_b_t,
            declared_dc_offset_t=selected.b_dc_t,
            declared_absolute_peak_t=selected.b_peak_t,
            source_fields=("WaveformSet.inductor_current_a/parallel_core_count", "per-core L/N/Ae"),
        ).to_dict()
    return records


def _tcm_segment_records(
    report: DesignReport,
    design: FixedInductorDesignCandidate,
    segments: Iterable[object],
    temperature_c: float,
    area_m2: float | None,
    volume_m3: float | None,
) -> dict[str, object]:
    records: dict[str, object] = {}
    for sequence, raw in enumerate(segments):
        if not isinstance(raw, dict):
            continue
        frequency_hz = _positive_float(raw.get("fsw_hz"))
        if frequency_hz is None:
            continue
        sign = -1.0 if _float(raw.get("iavg_a"), 0.0) < 0.0 else 1.0
        peak_a = sign * _float(raw.get("ipeak_a"), 0.0)
        valley_a = sign * _float(raw.get("ivalley_a"), 0.0)
        period_s = 1.0 / frequency_hz
        duty = min(max(_float(raw.get("duty"), 0.5), 0.0), 1.0)
        current_time_s = (0.0, duty * period_s, period_s)
        current_a = (valley_a, peak_a, valley_a)
        result = _build(
            frequency_hz=frequency_hz,
            temperature_c=temperature_c,
            report=report,
            role="main_inductor_tcm_segment",
            component_id=design.candidate_id,
            area_m2=area_m2,
            volume_m3=volume_m3,
            turns=design.turns,
            inductance_h=design.inductance_h,
            current_time_s=current_time_s,
            current_a=current_a,
            current_rms_a=_positive_float(raw.get("irms_a")),
            source_fields=("FixedInductorDesignCandidate.metadata.tcm_segments", f"segment_index:{sequence}"),
        )
        segment_checks = dict(result.consistency_checks)
        segment_checks["tcm_segment"] = {
            "segment_index": sequence,
            "segment_duration_s": _positive_float(raw.get("duration_s")),
            "time_weight": _positive_float(raw.get("time_weight")),
        }
        result = replace(result, consistency_checks=segment_checks)
        records[f"design_reference:main_inductor:tcm_segment_{sequence:02d}"] = result.to_dict()
    return records


def _build(
    *,
    frequency_hz: float,
    temperature_c: float,
    report: DesignReport,
    role: str,
    component_id: str,
    area_m2: float | None,
    volume_m3: float | None,
    turns: int,
    inductance_h: float,
    current_time_s: tuple[float, ...],
    current_a: tuple[float, ...],
    current_rms_a: float | None,
    declared_peak_to_peak_t: float | None = None,
    declared_dc_offset_t: float | None = None,
    declared_absolute_peak_t: float | None = None,
    source_fields: tuple[str, ...] = (),
) -> CoreLossExcitationBuildResult:
    return build_core_loss_excitation(
        CoreLossExcitationBuildRequest(
            frequency_hz=frequency_hz,
            temperature_c=temperature_c,
            source_topology=report.spec.topology_id,
            source_role=role,
            source_component_id=component_id,
            effective_area_m2=area_m2,
            effective_volume_m3=volume_m3,
            core_mass_kg=None,
            turns=turns,
            inductance_h=inductance_h,
            magnetizing_current_rms_a=current_rms_a,
            current_time_s=current_time_s,
            current_a=current_a,
            declared_flux_peak_to_peak_t=declared_peak_to_peak_t,
            declared_flux_dc_offset_t=declared_dc_offset_t,
            declared_flux_absolute_peak_t=declared_absolute_peak_t,
            source_fields=source_fields,
        )
    )


def _build_unavailable(
    *,
    frequency_hz: float,
    temperature_c: float,
    report: DesignReport,
    role: str,
    component_id: str,
    source_fields: tuple[str, ...],
) -> CoreLossExcitationBuildResult:
    return build_core_loss_excitation(
        CoreLossExcitationBuildRequest(
            frequency_hz=frequency_hz,
            temperature_c=temperature_c,
            source_topology=report.spec.topology_id,
            source_role=role,
            source_component_id=component_id,
            source_fields=source_fields,
        )
    )


def _build_voltage(
    *,
    frequency_hz: float,
    temperature_c: float,
    report: DesignReport,
    role: str,
    component_id: str,
    area_m2: float | None,
    volume_m3: float | None,
    turns: int,
    inductance_h: float | None,
    voltage_time_s: tuple[float, ...],
    voltage_v: tuple[float, ...],
    declared_peak_to_peak_t: float | None,
    declared_absolute_peak_t: float | None,
    source_fields: tuple[str, ...],
) -> CoreLossExcitationBuildResult:
    return build_core_loss_excitation(
        CoreLossExcitationBuildRequest(
            frequency_hz=frequency_hz,
            temperature_c=temperature_c,
            source_topology=report.spec.topology_id,
            source_role=role,
            source_component_id=component_id,
            effective_area_m2=area_m2,
            effective_volume_m3=volume_m3,
            turns=turns,
            inductance_h=inductance_h,
            voltage_time_s=voltage_time_s,
            voltage_v=voltage_v,
            declared_flux_peak_to_peak_t=declared_peak_to_peak_t,
            declared_flux_dc_offset_t=0.0,
            declared_flux_absolute_peak_t=declared_absolute_peak_t,
            dc_offset_policy="zero_cycle_average",
            source_fields=source_fields,
        )
    )


def _build_piecewise_current_scalar(
    *,
    frequency_hz: float,
    temperature_c: float,
    report: DesignReport,
    role: str,
    component_id: str,
    area_m2: float | None,
    volume_m3: float | None,
    turns: int,
    inductance_h: float,
    current_min_a: float,
    current_max_a: float,
    current_rms_a: float | None,
    declared_absolute_peak_t: float | None,
    source_fields: tuple[str, ...],
) -> CoreLossExcitationBuildResult:
    return build_core_loss_excitation(
        CoreLossExcitationBuildRequest(
            frequency_hz=frequency_hz,
            temperature_c=temperature_c,
            source_topology=report.spec.topology_id,
            source_role=role,
            source_component_id=component_id,
            effective_area_m2=area_m2,
            effective_volume_m3=volume_m3,
            turns=turns,
            inductance_h=inductance_h,
            magnetizing_current_rms_a=current_rms_a,
            current_a=(current_min_a, current_max_a),
            declared_flux_absolute_peak_t=declared_absolute_peak_t,
            scalar_waveform_template="piecewise_linear_current",
            source_fields=source_fields,
        )
    )


def _build_scalar(
    *,
    frequency_hz: float,
    temperature_c: float,
    report: DesignReport,
    role: str,
    component_id: str,
    volume_m3: float | None,
    inductance_h: float | None,
    template: str,
    ac_peak_t: float | None,
    peak_to_peak_t: float | None,
    dc_offset_t: float | None,
    absolute_peak_t: float | None,
    source_fields: tuple[str, ...],
) -> CoreLossExcitationBuildResult:
    return build_core_loss_excitation(
        CoreLossExcitationBuildRequest(
            frequency_hz=frequency_hz,
            temperature_c=temperature_c,
            source_topology=report.spec.topology_id,
            source_role=role,
            source_component_id=component_id,
            effective_volume_m3=volume_m3,
            inductance_h=inductance_h,
            declared_flux_ac_peak_t=ac_peak_t,
            declared_flux_peak_to_peak_t=peak_to_peak_t,
            declared_flux_dc_offset_t=dc_offset_t,
            declared_flux_absolute_peak_t=absolute_peak_t,
            scalar_waveform_template=template,
            source_fields=source_fields,
        )
    )


def _selected_fixed_design(magnetic: MagneticResult) -> FixedInductorDesignCandidate | None:
    if magnetic.selected_design_id:
        for design in magnetic.chosen_designs:
            if design.candidate_id == magnetic.selected_design_id:
                return design
    return magnetic.chosen_designs[len(magnetic.chosen_designs) // 2] if magnetic.chosen_designs else None


def _candidate_source_fields(design: FixedInductorDesignCandidate) -> tuple[str, ...]:
    return (
        "FixedInductorDesignCandidate.inductance_h",
        "FixedInductorDesignCandidate.turns",
        "FixedInductorDesignCandidate.metadata.core_effective_area_m2",
        f"assembly_type:{design.assembly_type}",
        f"stack_count:{design.stack_count}",
    )


def _triangular_current_source(
    frequency_hz: float,
    average_a: float,
    peak_a: float,
    valley_a: float,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    period_s = 1.0 / frequency_hz
    midpoint_a = average_a if math.isfinite(average_a) else 0.5 * (peak_a + valley_a)
    return (
        (0.0, 0.25 * period_s, 0.75 * period_s, period_s),
        (midpoint_a, peak_a, valley_a, midpoint_a),
    )


def _nested_metadata(report: DesignReport, key: str) -> dict[str, object]:
    if report.waveform is None or not isinstance(report.waveform.metadata, dict):
        return {}
    value = report.waveform.metadata.get(key)
    return value if isinstance(value, dict) else {}


def _generic_operating_current_source(
    report: DesignReport,
) -> tuple[float, tuple[float, ...], tuple[float, ...], str] | None:
    if report.waveform is None:
        return None
    if report.spec.topology_id not in _LONG_TIME_SCALE_TOPOLOGY_IDS:
        return (
            1.0 / report.waveform.switching_period_s,
            tuple(report.waveform.time_s),
            tuple(report.waveform.inductor_current_a),
            "WaveformSet.inductor_current_a",
        )
    local = report.waveform.metadata.get("magnetic_local_switching_period")
    if not isinstance(local, dict):
        return None
    frequency_hz = _positive_float(local.get("frequency_hz"))
    time_s = tuple(_list(local.get("time_s")))
    current_a = tuple(_list(local.get("current_a")))
    if frequency_hz is None or len(time_s) < 2 or len(time_s) != len(current_a):
        return None
    return frequency_hz, time_s, current_a, "WaveformSet.metadata.magnetic_local_switching_period.current_a"


def _candidate_frequency(report: DesignReport) -> float:
    if report.waveform is not None and report.waveform.switching_period_s > 0.0:
        return 1.0 / report.waveform.switching_period_s
    if report.candidate is None or report.candidate.fs_hz <= 0.0:
        raise ValueError("Selected magnetic role has no positive operating frequency.")
    return report.candidate.fs_hz


def _waveform_frequency(report: DesignReport) -> float | None:
    if report.waveform is not None and report.waveform.switching_period_s > 0.0:
        return 1.0 / report.waveform.switching_period_s
    return None


def _rms(values: Iterable[float]) -> float | None:
    values = tuple(float(value) for value in values)
    return math.sqrt(sum(value * value for value in values) / len(values)) if values else None


def _positive_float(value: object) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) and result > 0.0 else None


def _positive_int(value: object) -> int | None:
    try:
        result = int(value)
    except (TypeError, ValueError):
        return None
    return result if result > 0 else None


def _float(value: object, fallback: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return fallback
    return result if math.isfinite(result) else fallback


def _finite_float(value: object) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _list(value: object) -> list[float]:
    if not isinstance(value, (tuple, list)):
        return []
    return [float(item) for item in value]


__all__ = ["CORE_LOSS_EXCITATION_AUDIT_VERSION", "attach_core_loss_excitation_audit"]
