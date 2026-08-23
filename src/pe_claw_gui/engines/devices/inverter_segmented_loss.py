"""Line-cycle segmented loss helpers for the single-phase full-bridge inverter."""

from __future__ import annotations

from dataclasses import dataclass, replace
import math

from ...libraries.semiconductors.power_device import PowerDevice
from ...models.design_report import DesignReport
from ...models.device_loss import DeviceLossResult, SwitchStress
from ...models.operating_point import OperatingPoint
from .loss_evaluator import evaluate_switch_loss


DEFAULT_LINE_CYCLE_SEGMENT_COUNT = 20
ZVS_CURRENT_THRESHOLD_A = 1e-6
TCM_LOW_SLOPE_FSW_TOLERANCE = 0.999


@dataclass(frozen=True)
class InverterLineCycleSegment:
    """One quasi-static line-cycle segment for inverter loss evaluation."""

    index: int
    theta_rad: float
    v_ac_v: float
    i_ac_a: float
    p_ac_w: float
    modulation: float
    voltage_sign: int
    current_sign: int
    zvs_turn_on: bool
    active_switch_pair: str
    commutation_note: str
    fsw_hz: float
    natural_fsw_hz: float
    i_peak_a: float
    i_rms_a: float
    mixed_mode_clamped: bool = False
    low_slope_fsw_violation: bool = False


@dataclass(frozen=True)
class InverterSegmentedLossResult:
    """Averaged per-switch loss and segment metadata."""

    per_switch_loss: DeviceLossResult
    segments: tuple[InverterLineCycleSegment, ...]
    segment_losses: tuple[DeviceLossResult, ...]
    zvs_segment_count: int
    segment_count: int
    notes: tuple[str, ...]


def build_inverter_line_cycle_segments(
    report: DesignReport,
    operating_point: OperatingPoint | None = None,
    *,
    segment_count: int = DEFAULT_LINE_CYCLE_SEGMENT_COUNT,
) -> tuple[InverterLineCycleSegment, ...]:
    """Build midpoint-sampled quasi-static inverter line-cycle segments."""

    candidate = report.candidate
    if candidate is None:
        raise ValueError("Inverter line-cycle segments require a synthesized candidate.")
    if segment_count <= 0:
        raise ValueError("Inverter line-cycle segment count must be positive.")

    metadata = candidate.metadata
    load_ratio = _load_ratio(operating_point)
    vdc_v = _positive_float(metadata.get("vdc_nom_v"), candidate.vin_nom)
    vac_rms_v = _positive_float(metadata.get("vac_rms_v"), candidate.vout_target)
    pout_w = _positive_float(metadata.get("pout_w"), candidate.pout_target)
    power_factor = _operating_power_factor(operating_point, metadata.get("power_factor"))
    power_factor_abs = _power_factor_abs_for_current(power_factor)
    active_power_sign = _active_power_sign(power_factor)
    vac_peak_v = math.sqrt(2.0) * vac_rms_v
    iac_rms_a = load_ratio * pout_w / max(vac_rms_v * power_factor_abs, 1e-12)
    iac_peak_a = math.sqrt(2.0) * iac_rms_a
    phi_rad = math.acos(power_factor_abs)
    is_tcm = str(candidate.mode_capable).startswith("tcm_")
    tcm_valley_a = float(metadata.get("tcm_valley_current_target_a", candidate.il_valley))
    tcm_irev_abs_a = abs(tcm_valley_a)
    tcm_vac_floor_v = float(metadata.get("tcm_vac_floor_v", 0.02 * vac_peak_v))
    tcm_fsw_min_hz = float(metadata.get("fsw_min_hz", 0.0) or 0.0)

    segments: list[InverterLineCycleSegment] = []
    for index in range(segment_count):
        theta_rad = 2.0 * math.pi * (index + 0.5) / segment_count
        v_ac_v = vac_peak_v * math.sin(theta_rad)
        i_ac_a = active_power_sign * iac_peak_a * math.sin(theta_rad - phi_rad)
        abs_current_a = abs(i_ac_a)
        if is_tcm:
            state = _tcm_cycle_state(
                avg_a=i_ac_a,
                vac_v=v_ac_v,
                vdc_v=vdc_v,
                inductance_h=candidate.inductance_h,
                irev_abs_a=tcm_irev_abs_a,
                vac_floor_v=tcm_vac_floor_v,
                fsw_min_hz=tcm_fsw_min_hz,
            )
            i_peak_a = max(abs(float(state["peak_signed_a"])), abs(float(state["valley_signed_a"])))
            i_rms_a = _triangular_rms(float(state["peak_signed_a"]), float(state["valley_signed_a"]))
            fsw_hz = float(state["fsw_hz"])
            natural_fsw_hz = float(state["natural_fsw_hz"])
            mixed_mode_clamped = bool(state["mixed_mode_clamped"])
            low_slope_fsw_violation = mixed_mode_clamped
        else:
            i_peak_a = abs_current_a
            i_rms_a = abs_current_a / math.sqrt(2.0)
            fsw_hz = candidate.fs_hz
            natural_fsw_hz = candidate.fs_hz
            mixed_mode_clamped = False
            low_slope_fsw_violation = False
        voltage_sign = _sign(v_ac_v)
        current_sign = _sign(i_ac_a)
        zvs_turn_on = (
            voltage_sign != 0
            and current_sign != 0
            and voltage_sign != current_sign
            and abs(i_ac_a) > ZVS_CURRENT_THRESHOLD_A
        )
        active_pair = "S1/S4" if voltage_sign >= 0 else "S2/S3"
        commutation_note = (
            "current opposes commanded bridge voltage; incoming switch turn-on is treated as diode-assisted ZVS"
            if zvs_turn_on
            else "current follows commanded bridge voltage; incoming switch turn-on is treated as hard-switched"
        )
        segments.append(
            InverterLineCycleSegment(
                index=index,
                theta_rad=theta_rad,
                v_ac_v=v_ac_v,
                i_ac_a=i_ac_a,
                p_ac_w=v_ac_v * i_ac_a,
                modulation=_clamp(v_ac_v / max(vdc_v, 1e-12), -1.0, 1.0),
                voltage_sign=voltage_sign,
                current_sign=current_sign,
                zvs_turn_on=zvs_turn_on,
                active_switch_pair=active_pair,
                commutation_note=commutation_note,
                fsw_hz=fsw_hz,
                natural_fsw_hz=natural_fsw_hz,
                i_peak_a=i_peak_a,
                i_rms_a=i_rms_a,
                mixed_mode_clamped=mixed_mode_clamped,
                low_slope_fsw_violation=low_slope_fsw_violation,
            )
        )
    return tuple(segments)


def evaluate_inverter_segmented_switch_loss(
    device: PowerDevice,
    report: DesignReport,
    base_stress: SwitchStress,
    *,
    operating_point: OperatingPoint | None = None,
    segment_count: int = DEFAULT_LINE_CYCLE_SEGMENT_COUNT,
    method: str = "accurate",
) -> InverterSegmentedLossResult:
    """Evaluate averaged per-switch inverter loss over one line cycle."""

    segments = build_inverter_line_cycle_segments(report, operating_point, segment_count=segment_count)
    segment_losses: list[DeviceLossResult] = []
    for segment in segments:
        segment_stress = _segment_switch_stress(base_stress, segment)
        loss = evaluate_switch_loss(device, segment_stress, method=method)
        segment_losses.append(loss)

    averaged = _average_loss_result(
        device=device,
        base_loss=evaluate_switch_loss(device, base_stress, method=method),
        losses=segment_losses,
        zvs_segment_count=sum(1 for segment in segments if segment.zvs_turn_on),
        low_slope_segment_count=sum(1 for segment in segments if segment.low_slope_fsw_violation),
        segment_count=len(segments),
    )
    notes = (
        f"Single-phase inverter semiconductor loss uses {len(segments)} midpoint line-cycle segments.",
        "Per segment, the selected switch loss is evaluated with the existing device loss evaluator.",
        "ZVS direction classification is diagnostic only; turn-on loss is not suppressed in this conservative model.",
        *(
            ("TCM low-slope segments use first-pass mixed-mode fallback: fsw is clamped to fsw_min and fixed valley current is relaxed.",)
            if any(segment.low_slope_fsw_violation for segment in segments)
            else ()
        ),
    )
    return InverterSegmentedLossResult(
        per_switch_loss=averaged,
        segments=segments,
        segment_losses=tuple(segment_losses),
        zvs_segment_count=sum(1 for segment in segments if segment.zvs_turn_on),
        segment_count=len(segments),
        notes=notes,
    )


def _segment_switch_stress(base_stress: SwitchStress, segment: InverterLineCycleSegment) -> SwitchStress:
    abs_current_a = abs(segment.i_peak_a)
    fsw_hz = max(float(segment.fsw_hz), 1e-12)
    return replace(
        base_stress,
        mode="full_bridge_tcm_line_segment" if "tcm" in base_stress.mode.lower() else "full_bridge_unipolar_spwm_line_segment",
        i_rms_A=segment.i_rms_a,
        i_avg_A=0.5 * abs_current_a,
        i_turn_on_A=abs_current_a,
        i_turn_off_A=abs_current_a,
        fsw_Hz=fsw_hz,
        duty=0.5,
        conduction_time_s=0.5 / fsw_hz,
    )


def _average_loss_result(
    *,
    device: PowerDevice,
    base_loss: DeviceLossResult,
    losses: list[DeviceLossResult],
    zvs_segment_count: int,
    low_slope_segment_count: int,
    segment_count: int,
) -> DeviceLossResult:
    if not losses:
        return base_loss

    p_cond_w = _mean([loss.p_cond_W for loss in losses])
    p_sw_on_w = _mean([loss.p_sw_on_W for loss in losses])
    p_sw_off_w = _mean([loss.p_sw_off_W for loss in losses])
    p_rr_w = _mean([loss.p_rr_W for loss in losses])
    p_eoss_w = _mean([loss.p_eoss_W for loss in losses])
    p_gate_w = _mean([loss.p_gate_W for loss in losses])
    p_total_w = p_cond_w + p_sw_on_w + p_sw_off_w + p_rr_w + p_eoss_w + p_gate_w
    averaged_mode = (
        "full_bridge_tcm_line_cycle_average"
        if any("tcm" in loss.mode.lower() for loss in losses)
        else "full_bridge_unipolar_spwm_line_cycle_average"
    )
    warnings = [
        *base_loss.warnings,
        (
            f"Line-cycle segmented inverter loss: {zvs_segment_count} / {segment_count} "
            "segments flagged by the ZVS direction diagnostic."
        ),
        "Segmented inverter loss is a first-pass quasi-static average; ZVS diagnostics do not reduce turn-on loss until dead-time and Coss trajectory are modeled.",
        *(
            [
                (
                    f"TCM low-slope guard: {low_slope_segment_count} / {segment_count} "
                    "segments use mixed-mode fallback; fsw is clamped to fsw_min and fixed valley current is relaxed for loss stress."
                )
            ]
            if low_slope_segment_count
            else []
        ),
    ]
    return replace(
        base_loss,
        part_number=device.part_number,
        role="main_switch",
        mode=averaged_mode,
        p_cond_W=p_cond_w,
        p_sw_on_W=p_sw_on_w,
        p_sw_off_W=p_sw_off_w,
        p_rr_W=p_rr_w,
        p_eoss_W=p_eoss_w,
        p_gate_W=p_gate_w,
        p_total_W=p_total_w,
        method="segmented_line_cycle_conservative_zvs_diagnostic",
        warnings=_dedupe(warnings),
    )


def _load_ratio(operating_point: OperatingPoint | None) -> float:
    if operating_point is None:
        return 1.0
    try:
        return max(float(operating_point.load_ratio), 0.0)
    except (TypeError, ValueError):
        return 1.0


def _operating_power_factor(operating_point: OperatingPoint | None, design_power_factor) -> float:
    value = design_power_factor
    if operating_point is not None and operating_point.power_factor is not None:
        value = operating_point.power_factor
    try:
        return _clamp(float(value), -1.0, 1.0)
    except (TypeError, ValueError):
        return _clamp(float(design_power_factor), -1.0, 1.0)


def _power_factor_abs_for_current(power_factor: float) -> float:
    return max(abs(float(power_factor)), 1e-6)


def _active_power_sign(power_factor: float) -> float:
    return -1.0 if float(power_factor) < 0.0 else 1.0


def _bounded_power_factor(value) -> float:
    try:
        return _clamp(float(value), 1e-6, 1.0)
    except (TypeError, ValueError):
        return 1.0


def _positive_float(value, fallback: float) -> float:
    try:
        parsed = float(value)
        return parsed if parsed > 0.0 else fallback
    except (TypeError, ValueError):
        return fallback


def _sign(value: float) -> int:
    if value > 1e-12:
        return 1
    if value < -1e-12:
        return -1
    return 0


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _triangular_rms(ipeak_a: float, ivalley_a: float) -> float:
    return math.sqrt((ipeak_a * ipeak_a + ipeak_a * ivalley_a + ivalley_a * ivalley_a) / 3.0)


def _tcm_cycle_state(
    *,
    avg_a: float,
    vac_v: float,
    vdc_v: float,
    inductance_h: float,
    irev_abs_a: float,
    vac_floor_v: float,
    fsw_min_hz: float,
) -> dict[str, float | bool]:
    direction = _sign(avg_a) or _sign(vac_v) or 1
    avg_abs = abs(avg_a)
    natural_peak_abs = 2.0 * avg_abs + irev_abs_a
    natural_delta = natural_peak_abs + irev_abs_a
    vac_eff_v = min(max(abs(vac_v), vac_floor_v), 0.98 * vdc_v)
    a_factor = 1.0 / max(vdc_v - vac_eff_v, 1e-12) + 1.0 / max(vac_eff_v, 1e-12)
    natural_period_s = inductance_h * natural_delta * a_factor
    natural_fsw_hz = 1.0 / max(natural_period_s, 1e-12)
    mixed_mode_clamped = fsw_min_hz > 0.0 and natural_fsw_hz < fsw_min_hz * TCM_LOW_SLOPE_FSW_TOLERANCE
    if mixed_mode_clamped:
        switching_period_s = 1.0 / fsw_min_hz
        delta = switching_period_s / max(inductance_h * a_factor, 1e-12)
        peak_signed = avg_a + 0.5 * direction * delta
        valley_signed = avg_a - 0.5 * direction * delta
        fsw_hz = fsw_min_hz
    else:
        peak_signed = direction * natural_peak_abs
        valley_signed = -direction * irev_abs_a
        fsw_hz = natural_fsw_hz
    return {
        "peak_signed_a": peak_signed,
        "valley_signed_a": valley_signed,
        "fsw_hz": fsw_hz,
        "natural_fsw_hz": natural_fsw_hz,
        "mixed_mode_clamped": mixed_mode_clamped,
    }


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        deduped.append(value)
        seen.add(value)
    return deduped
