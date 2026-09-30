"""Independent first-pass electrical synthesis for two-phase interleaved PFC."""

from __future__ import annotations

from math import pi, sqrt

from ...base.candidate import TopologyCandidate
from ...base.spec import TopologySpec
from .input_schema import PHASE_COUNT, PHASE_SHIFT_DEG
from .interleaving import calculate_interleaved_ripple
from .line_cycle import (
    InterleavedBoostPFCLineCycle,
    sample_interleaved_boost_pfc_line_cycle,
)

_DEFAULT_VDC_MARGIN_RATIO = 1.02
_DEFAULT_BRIDGE_VOLTAGE_MARGIN = 2.0


def synthesize(spec: TopologySpec) -> TopologyCandidate:
    """Build a deterministic CCM two-phase electrical candidate."""

    metadata = spec.metadata
    vac_rms_v = float(metadata["vac_rms_v"])
    vac_rms_min_v = float(metadata["vac_rms_min_v"])
    vac_rms_max_v = float(metadata["vac_rms_max_v"])
    f_line_hz = float(metadata["f_line_hz"])
    vdc_target_v = float(metadata["vdc_target_v"])
    fsw_hz = float(metadata["fsw_hz"])
    ripple_ratio = float(metadata["inductor_current_ripple_ratio"])
    dc_bus_ripple_percent = float(metadata["dc_bus_ripple_percent"])
    power_factor_target = float(metadata["power_factor_target"])
    input_inductance_h = float(metadata["input_inductance_h"])

    vac_peak_nom_v = sqrt(2.0) * vac_rms_v
    vac_peak_max_v = sqrt(2.0) * vac_rms_max_v
    required_min_vdc_v = _DEFAULT_VDC_MARGIN_RATIO * vac_peak_max_v
    delta_vdc_pp_v = vdc_target_v * dc_bus_ripple_percent / 100.0
    idc_a = spec.pout / vdc_target_v

    def input_current_rms(vac_rms: float) -> float:
        return spec.pout / max(vac_rms * power_factor_target, 1e-12)

    nominal_input_rms_a = input_current_rms(vac_rms_v)
    low_line_input_rms_a = input_current_rms(vac_rms_min_v)
    high_line_input_rms_a = input_current_rms(vac_rms_max_v)
    nominal_line_cycle = sample_interleaved_boost_pfc_line_cycle(
        vac_rms_v=vac_rms_v,
        vdc_target_v=vdc_target_v,
        input_current_rms_a=nominal_input_rms_a,
        ripple_current_ratio=ripple_ratio,
    )
    low_line_cycle = sample_interleaved_boost_pfc_line_cycle(
        vac_rms_v=vac_rms_min_v,
        vdc_target_v=vdc_target_v,
        input_current_rms_a=low_line_input_rms_a,
        ripple_current_ratio=ripple_ratio,
    )
    high_line_cycle = sample_interleaved_boost_pfc_line_cycle(
        vac_rms_v=vac_rms_max_v,
        vdc_target_v=vdc_target_v,
        input_current_rms_a=high_line_input_rms_a,
        ripple_current_ratio=ripple_ratio,
    )

    # Low line carries the highest current and is the conservative first-pass
    # design envelope for each phase's series inductance.
    inductor_requirements_h = [
        v_rectified * duty / max(delta_i * fsw_hz, 1e-12)
        for v_rectified, duty, delta_i in zip(
            low_line_cycle.v_rectified_v,
            low_line_cycle.duty,
            low_line_cycle.delta_i_allowed_a,
            strict=True,
        )
    ]
    total_series_inductance_required_h = max(inductor_requirements_h)
    worst_index = inductor_requirements_h.index(total_series_inductance_required_h)
    phase_boost_inductance_h = max(total_series_inductance_required_h - input_inductance_h, 0.0)
    phase_total_series_inductance_h = phase_boost_inductance_h + input_inductance_h

    duty_nom = min(max(1.0 - vac_peak_nom_v / max(vdc_target_v, 1e-12), 0.0), 1.0)
    delta_il_pp_nom_a = vac_peak_nom_v * duty_nom / max(phase_total_series_inductance_h * fsw_hz, 1e-12)
    phase_peak_nom_a = sqrt(2.0) * nominal_input_rms_a / PHASE_COUNT
    phase_il_peak_a = phase_peak_nom_a + 0.5 * delta_il_pp_nom_a
    phase_il_valley_a = max(phase_peak_nom_a - 0.5 * delta_il_pp_nom_a, 0.0)
    cdc_required_f = spec.pout / (
        2.0 * pi * f_line_hz * max(vdc_target_v, 1e-12) * max(delta_vdc_pp_v, 1e-12)
    )
    feasible = vdc_target_v >= required_min_vdc_v

    achieved_ripple_values_a = [
        v_rectified * duty / max(phase_total_series_inductance_h * fsw_hz, 1e-12)
        for v_rectified, duty in zip(
            low_line_cycle.v_rectified_v,
            low_line_cycle.duty,
            strict=True,
        )
    ]
    achieved_worst_index = achieved_ripple_values_a.index(max(achieved_ripple_values_a))
    nominal_interleaved_ripple = calculate_interleaved_ripple(
        duty=nominal_line_cycle.duty,
        phase_ripple_pp_a=[
            vac * duty / max(phase_total_series_inductance_h * fsw_hz, 1e-12)
            for vac, duty in zip(nominal_line_cycle.v_rectified_v, nominal_line_cycle.duty, strict=True)
        ],
    )
    nominal_ripple_index = nominal_interleaved_ripple.aggregate_ripple_pp_a.index(
        max(nominal_interleaved_ripple.aggregate_ripple_pp_a)
    )
    line_condition_metrics = {
        "nominal": _line_condition_metrics(
            nominal_line_cycle,
            vac_rms_v=vac_rms_v,
            input_current_rms_a=nominal_input_rms_a,
            total_series_inductance_h=phase_total_series_inductance_h,
            fsw_hz=fsw_hz,
        ),
        "low_line": _line_condition_metrics(
            low_line_cycle,
            vac_rms_v=vac_rms_min_v,
            input_current_rms_a=low_line_input_rms_a,
            total_series_inductance_h=phase_total_series_inductance_h,
            fsw_hz=fsw_hz,
        ),
        "high_line": _line_condition_metrics(
            high_line_cycle,
            vac_rms_v=vac_rms_max_v,
            input_current_rms_a=high_line_input_rms_a,
            total_series_inductance_h=phase_total_series_inductance_h,
            fsw_hz=fsw_hz,
        ),
    }
    phase_line_cycle = {
        "phase_1": _phase_line_cycle_metadata(nominal_line_cycle),
        "phase_2": _phase_line_cycle_metadata(nominal_line_cycle),
    }
    failure_reason = None if feasible else "interleaved_boost_pfc_dc_bus_below_high_line_peak"
    notes = [
        "First-pass CCM two-phase interleaved Boost PFC synthesis using a sinusoidal input-current target.",
        "Input power is ideal Pout; the requested power factor sets the required RMS line current.",
        "Low line is the conservative inductor-sizing envelope; high line sets the DC-bus peak feasibility boundary.",
        "The two phases are fixed at ideal 50/50 current sharing and 180-degree interleaving.",
        "DCM, CrM, zero-crossing control dynamics, THD, EMI, and detailed parasitics remain outside this step.",
    ]
    if not feasible:
        notes.append("Vdc target must exceed high-line rectified peak with margin before synthesis is accepted.")

    candidate_metadata = {
        **metadata,
        "implemented_stage": "step_2_independent_electrical_synthesis",
        "phase_count": PHASE_COUNT,
        "phase_shift_deg": PHASE_SHIFT_DEG,
        "phase_current_fraction": {"phase_1": 0.5, "phase_2": 0.5},
        "electrical_current_basis": "Pout/(Vac_rms*power_factor_target); ideal conversion with requested PF",
        "electrical_input_power_w": spec.pout,
        "power_factor_target": power_factor_target,
        "electrical_input_current_rms_a": nominal_input_rms_a,
        "electrical_input_current_peak_a": sqrt(2.0) * nominal_input_rms_a,
        "phase_current_rms_a": {"phase_1": nominal_input_rms_a / 2.0, "phase_2": nominal_input_rms_a / 2.0},
        "phase_current_peak_a": {"phase_1": phase_peak_nom_a, "phase_2": phase_peak_nom_a},
        "vac_peak_nom_v": vac_peak_nom_v,
        "vac_peak_min_v": sqrt(2.0) * vac_rms_min_v,
        "vac_peak_max_v": vac_peak_max_v,
        "required_min_vdc_v": required_min_vdc_v,
        "vdc_feasibility_passed": feasible,
        "inductor_design_line": "low_line",
        "line_cycle_point_count": nominal_line_cycle.point_count,
        "line_cycle": nominal_line_cycle.as_metadata(),
        "low_line_line_cycle": low_line_cycle.as_metadata(),
        "high_line_line_cycle": high_line_cycle.as_metadata(),
        "phase_line_cycle": phase_line_cycle,
        "line_condition_metrics": line_condition_metrics,
        "design_boundary_basis": {
            "inductor": {
                "current_design_basis": "low_line_phase_current_envelope_and_allowed_ripple",
                "voltage_design_basis": "low_line_rectified_line_cycle_volt_second",
                "line_condition": "low_line",
            },
            "power_devices": {
                "current_design_basis": "low_line_phase_current_envelope; phase positions use ideal 50/50 sharing",
                "voltage_design_basis": "high_line_rectified_peak_and_target_dc_bus",
                "current_line_condition": "low_line",
                "voltage_line_condition": "high_line",
            },
            "input_bridge": {
                "current_design_basis": "low_line_aggregate_rectified_input_current_envelope",
                "voltage_design_basis": "high_line_rectified_peak_reverse_stress",
                "current_line_condition": "low_line",
                "voltage_line_condition": "high_line",
            },
        },
        "input_inductance_h": input_inductance_h,
        "input_inductance_role": "per_phase_series_input_inductance",
        "phase_boost_inductance_h": {"phase_1": phase_boost_inductance_h, "phase_2": phase_boost_inductance_h},
        "phase_total_series_inductance_h": {
            "phase_1": phase_total_series_inductance_h,
            "phase_2": phase_total_series_inductance_h,
        },
        "boost_inductor_required_h": phase_boost_inductance_h,
        "total_series_inductance_required_h": total_series_inductance_required_h,
        "boost_inductor_requirement_basis": "max[Vrect*D/(DeltaI_phase_allowed*fsw)] at low line minus per-phase input inductance",
        "boost_inductor_worst_theta_deg": low_line_cycle.theta_deg[worst_index],
        "boost_inductor_worst_vrectified_v": low_line_cycle.v_rectified_v[worst_index],
        "boost_inductor_worst_duty": low_line_cycle.duty[worst_index],
        "boost_inductor_worst_delta_i_allowed_a": low_line_cycle.delta_i_allowed_a[worst_index],
        "inductor_ripple_reference": "per_phase_peak_current_at_each_line_condition",
        "inductor_ripple_equation": "Vrect*D/((Linput_phase+Lboost_phase)*fsw)",
        "delta_il_pp_target_a": ripple_ratio * phase_peak_nom_a,
        "delta_il_pp_nom_a": delta_il_pp_nom_a,
        "delta_il_pp_nom_basis": "per-phase Vrect_peak*D_nom/((Linput_phase+Lboost_phase)*fsw)",
        "inductor_ripple_target_ratio": ripple_ratio,
        "inductor_ripple_worst_case_a": achieved_ripple_values_a[achieved_worst_index],
        "inductor_ripple_worst_theta_deg": low_line_cycle.theta_deg[achieved_worst_index],
        "interleaved_ripple": {
            **nominal_interleaved_ripple.as_metadata(),
            "phase_shift_deg": PHASE_SHIFT_DEG,
            "aggregate_ripple_basis": "DeltaI_phase*abs(1-2D) for identical 180-degree-shifted phases",
            "worst_theta_deg": nominal_line_cycle.theta_deg[nominal_ripple_index],
            "worst_aggregate_ripple_pp_a": nominal_interleaved_ripple.aggregate_ripple_pp_a[nominal_ripple_index],
        },
        "dc_link_capacitance_required_f": cdc_required_f,
        "dc_link_capacitance_requirement_basis": "Pout/(2*pi*f_line*Vdc*DeltaVdc_pp)",
        "dc_link_ripple_limit_vpp": delta_vdc_pp_v,
        "dc_link_ripple_predicted_vpp": delta_vdc_pp_v,
        "dc_bus_ripple_vpp_v": delta_vdc_pp_v,
        "minimum_required_capacitance_f": cdc_required_f,
        "selected_capacitance_f": cdc_required_f,
        "idc_a": idc_a,
        "bridge_current_basis": "aggregate absolute rectified input current",
        "bridge_current_rms_a": nominal_input_rms_a,
        "bridge_current_peak_a": sqrt(2.0) * nominal_input_rms_a,
        "bridge_reverse_stress_v": vac_peak_max_v,
        "recommended_diode_vrrm_v": _DEFAULT_BRIDGE_VOLTAGE_MARGIN * vac_peak_max_v,
        "formula_basis": {
            "input_current": {"equation": "Iline_rms=Pout/(Vac_rms*PF_target)", "unit": "A"},
            "phase_sharing": {"equation": "Iphase=Iline/2", "unit": "A"},
            "boost_duty": {"equation": "D=1-Vrect/Vdc", "unit": "ratio", "boundary": "[0,1]"},
            "phase_inductance": {"equation": "Ltotal=Vrect*D/(DeltaIphase*fsw)", "unit": "H"},
            "interleaved_ripple": {"equation": "DeltaIaggregate=DeltaIphase*abs(1-2D)", "unit": "A"},
            "dc_link_capacitance": {"equation": "C=Pout/(2*pi*fline*Vdc*DeltaVpp)", "unit": "F"},
        },
    }

    return TopologyCandidate(
        topology_id=spec.topology_id,
        display_name=spec.display_name,
        vin_min=spec.vin_min,
        vin_max=spec.vin_max,
        vin_nom=vac_rms_v,
        vout_target=vdc_target_v,
        pout_target=spec.pout,
        duty_nom=duty_nom,
        iout=idc_a,
        fs_hz=fsw_hz,
        inductance_h=phase_total_series_inductance_h,
        capacitance_f=cdc_required_f,
        delta_il=delta_il_pp_nom_a,
        delta_vo=delta_vdc_pp_v,
        il_peak=phase_il_peak_a,
        il_valley=phase_il_valley_a,
        ccm_valid=feasible,
        mode_capable="ccm_first_pass_interleaved_boost_pfc",
        output_ripple_vpp_v=delta_vdc_pp_v,
        feasible=feasible,
        failure_reason=failure_reason,
        r_load_nom_ohm=vdc_target_v * vdc_target_v / spec.pout,
        notes=notes,
        metadata=candidate_metadata,
    )


def _phase_line_cycle_metadata(line_cycle: InterleavedBoostPFCLineCycle) -> dict[str, list[float]]:
    return {
        "theta_deg": list(line_cycle.theta_deg),
        "v_rectified_v": list(line_cycle.v_rectified_v),
        "phase_current_a": list(line_cycle.phase_current_a),
        "duty": list(line_cycle.duty),
        "delta_i_allowed_a": list(line_cycle.delta_i_allowed_a),
    }


def _line_condition_metrics(
    line_cycle: InterleavedBoostPFCLineCycle,
    *,
    vac_rms_v: float,
    input_current_rms_a: float,
    total_series_inductance_h: float,
    fsw_hz: float,
) -> dict[str, object]:
    """Return auditable current and ripple metrics for one line-voltage condition."""

    phase_current = [float(value) for value in line_cycle.phase_current_a]
    total_current = [float(value) for value in line_cycle.total_input_current_a]
    actual_ripple = [
        v_rectified * duty / max(total_series_inductance_h * fsw_hz, 1e-12)
        for v_rectified, duty in zip(
            line_cycle.v_rectified_v,
            line_cycle.duty,
            strict=True,
        )
    ]
    worst_index = actual_ripple.index(max(actual_ripple))
    phase_current_average_a = _mean(phase_current)
    phase_current_envelope_rms_sampled_a = _rms(phase_current)
    phase_current_rms_a = float(input_current_rms_a) / PHASE_COUNT
    phase_current_rms_with_ripple_a = sqrt(
        sum(
            current * current + ripple * ripple / 12.0
            for current, ripple in zip(phase_current, actual_ripple, strict=True)
        )
        / max(len(phase_current), 1)
    )
    return {
        "vac_rms_v": float(vac_rms_v),
        "vac_peak_v": sqrt(2.0) * float(vac_rms_v),
        "input_current_rms_a": float(input_current_rms_a),
        "input_current_peak_a": max(total_current, default=0.0),
        "input_current_average_rectified_a": _mean(total_current),
        "phase_current_average_a": phase_current_average_a,
        "phase_current_rms_a": phase_current_rms_a,
        "phase_current_envelope_rms_sampled_a": phase_current_envelope_rms_sampled_a,
        "phase_current_rms_with_switching_ripple_a": phase_current_rms_with_ripple_a,
        "phase_current_peak_a": max(phase_current, default=0.0),
        "phase_current_share": 1.0 / PHASE_COUNT,
        "phase_ripple_allowed_pp_a": max(line_cycle.delta_i_allowed_a, default=0.0),
        "phase_ripple_actual_pp_max_a": max(actual_ripple, default=0.0),
        "phase_ripple_actual_worst_theta_deg": line_cycle.theta_deg[worst_index],
        "phase_ripple_actual_worst_vrectified_v": line_cycle.v_rectified_v[worst_index],
        "phase_ripple_actual_worst_duty": line_cycle.duty[worst_index],
        "current_basis": "sinusoidal_rectified_line_current_with_ideal_equal_phase_sharing",
        "rms_basis": "sampled_phase_current_envelope_plus_triangular_switching_ripple_rms",
        "ripple_equation": "DeltaI_phase=Vrect*D/(Ltotal*fsw)",
        "line_cycle_point_count": line_cycle.point_count,
    }


def _mean(values: list[float]) -> float:
    return sum(values) / max(len(values), 1)


def _rms(values: list[float]) -> float:
    return sqrt(sum(value * value for value in values) / max(len(values), 1))
