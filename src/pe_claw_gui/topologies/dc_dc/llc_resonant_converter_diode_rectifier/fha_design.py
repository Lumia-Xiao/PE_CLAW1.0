"""First-pass FHA electrical design for the diode-rectified LLC topology."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from math import atan2, pi, sqrt

from ...base.spec import TopologySpec


@dataclass(frozen=True)
class LLCOperatingPointResult:
    """One FHA frequency-search result for an LLC operating corner."""

    label: str
    vin_v: float
    vout_v: float
    pout_w: float
    feasible: bool
    fs_hz: float
    fn: float
    q_op: float
    rac_ohm: float
    m_req: float
    m_actual: float
    gain_error: float


@dataclass(frozen=True)
class LLCAchievedOperatingPoint:
    """Fixed-hardware FHA result at one commanded switching frequency."""

    vin_v: float
    vout_achieved_v: float
    iout_achieved_a: float
    pout_achieved_w: float
    rload_ohm: float
    fr_hz: float
    fs_op_hz: float
    fn_op: float
    gain: float
    q_op: float
    rac_ohm: float
    operating_point_feasible: bool
    accuracy_scope: str = "first_harmonic_fixed_frequency_estimate"
    off_resonance_accuracy_limited: bool = False


@dataclass(frozen=True)
class LLCInputImpedanceAssessment:
    """FHA tank input impedance and ZVS classification for one LLC operating point."""

    zin_ohm: complex
    angle_rad: float
    angle_deg: float
    tank_characteristic: str
    zvs_assumed: bool


@dataclass(frozen=True)
class LLCFHADesign:
    """Structured diode LLC FHA electrical-design result."""

    topology_id: str
    vin_min_v: float
    vin_nom_v: float
    vin_max_v: float
    vout_min_v: float
    vout_nom_v: float
    vout_max_v: float
    pout_max_w: float
    min_load_ratio: float
    pout_min_w: float
    fs_min_hz: float
    fs_max_hz: float
    fr_hz: float
    primary_bridge_type: str
    secondary_rectifier_type: str
    primary_bridge_gain_factor: float
    secondary_rectifier_note: str
    np_turns: int
    ns_turns: int
    turns_ratio: float
    ideal_turns_ratio: float
    turns_ratio_error: float
    rout_nom_ohm: float
    rac_nom_ohm: float
    ln: float
    q_nom: float
    zr_ohm: float
    lr_h: float
    cr_f: float
    lm_h: float
    turns_ratio_tolerance_percent: float = 5.0
    turns_ratio_within_tolerance: bool = True
    coverage_results: list[LLCOperatingPointResult] = field(default_factory=list)
    current_estimates_nominal_full_load: dict[str, object] = field(default_factory=dict)
    current_estimates_by_corner: list[dict[str, object]] = field(default_factory=list)
    worst_case_current_stress: dict[str, object] = field(default_factory=dict)
    semiconductor_topology_counts: dict[str, object] = field(default_factory=dict)
    zvs_assessment: str | None = None
    zvs_data_status: str = "not_evaluated"
    zvs_all_checked_corners: bool | None = None
    zvs_assessment_by_corner: list[dict[str, object]] = field(default_factory=list)
    zvs_worst_angle_deg: float | None = None
    zvs_worst_corner: str | None = None
    zvs_assessment_basis: str | None = None
    overall_feasible: bool = False
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class _LLCInputSpec:
    topology_id: str
    vin_min_v: float
    vin_nom_v: float
    vin_max_v: float
    vout_min_v: float
    vout_nom_v: float
    vout_max_v: float
    pout_max_w: float
    min_load_ratio: float
    fs_min_hz: float
    fs_max_hz: float
    turns_ratio_tolerance_percent: float
    primary_bridge_type: str
    secondary_rectifier_type: str


def primary_bridge_gain_factor(primary_bridge_type: str) -> float:
    """Return the first-pass FHA drive gain factor for the selected primary bridge."""

    if primary_bridge_type == "full_bridge":
        return 1.0
    if primary_bridge_type == "half_bridge":
        return 0.5
    raise ValueError("Primary bridge type must be full_bridge or half_bridge.")


def secondary_rectifier_note(secondary_rectifier_type: str) -> str:
    """Return the first-pass secondary winding interpretation note."""

    if secondary_rectifier_type == "full_bridge_rectifier":
        return "For full_bridge_rectifier, Ns is the full secondary winding in this first-pass FHA model."
    if secondary_rectifier_type == "full_wave_center_tapped_rectifier":
        return (
            "For full_wave_center_tapped_rectifier, Ns is treated as one half-secondary winding "
            "in this first-pass FHA model."
        )
    raise ValueError(
        "Secondary rectifier type must be full_bridge_rectifier or full_wave_center_tapped_rectifier."
    )


def semiconductor_topology_counts(primary_bridge_type: str, secondary_rectifier_type: str) -> dict[str, object]:
    """Return physical semiconductor position counts for the selected diode LLC structure."""

    if primary_bridge_type == "full_bridge":
        main_switch = {
            "topology_position_count": 4,
            "position_labels": ["S1", "S2", "S3", "S4"],
        }
    elif primary_bridge_type == "half_bridge":
        main_switch = {
            "topology_position_count": 2,
            "position_labels": ["S_H", "S_L"],
        }
    else:
        raise ValueError("Primary bridge type must be full_bridge or half_bridge.")

    if secondary_rectifier_type == "full_bridge_rectifier":
        rectifier_diode = {
            "topology_position_count": 4,
            "position_labels": ["D1", "D2", "D3", "D4"],
        }
    elif secondary_rectifier_type == "full_wave_center_tapped_rectifier":
        rectifier_diode = {
            "topology_position_count": 2,
            "position_labels": ["D1", "D2"],
        }
    else:
        raise ValueError(
            "Secondary rectifier type must be full_bridge_rectifier or full_wave_center_tapped_rectifier."
        )

    return {
        "main_switch": main_switch,
        "rectifier_diode": rectifier_diode,
    }


def llc_fha_gain(fn: float, ln: float, q: float) -> float:
    """Return normalized FHA voltage-gain magnitude."""

    if fn <= 0.0 or ln <= 0.0 or q <= 0.0:
        raise ValueError("fn, ln, and q must be positive.")
    numerator = ln * fn**2
    denominator = ((ln + 1.0) * fn**2 - 1.0) + 1j * q * ln * fn * (fn**2 - 1.0)
    if abs(denominator) <= 1e-18:
        raise ValueError("LLC FHA gain denominator is singular for the supplied values.")
    return abs(numerator / denominator)


def estimate_integer_turns_ratio(
    vin_nom_v: float,
    vout_nom_v: float,
    primary_bridge_gain_factor: float = 1.0,
    turns_ratio_tolerance_percent: float = 5.0,
) -> tuple[int, int, float, float, float]:
    """Select a low-turn integer Np:Ns inside the allowed ideal-ratio error."""

    if vin_nom_v <= 0.0 or vout_nom_v <= 0.0 or primary_bridge_gain_factor <= 0.0:
        raise ValueError("Nominal input/output voltages and primary bridge gain factor must be positive.")
    if not 0.0 <= turns_ratio_tolerance_percent <= 100.0:
        raise ValueError("Turns-ratio tolerance percent must be between 0 and 100.")
    n_ideal = primary_bridge_gain_factor * vin_nom_v / vout_nom_v
    tolerance = turns_ratio_tolerance_percent / 100.0
    candidates: list[tuple[int, int, float, float, float]] = []
    for ns_turns in range(1, 31):
        np_min = max(int(n_ideal * ns_turns * (1.0 - tolerance)), 1)
        np_max = max(int(n_ideal * ns_turns * (1.0 + tolerance)) + 1, 1)
        for np_turns in range(np_min, np_max + 1):
            n = np_turns / ns_turns
            ratio_error = abs(n - n_ideal) / n_ideal
            if ratio_error <= tolerance + 1e-12:
                candidates.append((np_turns, ns_turns, n, n_ideal, ratio_error))
    if not candidates:
        raise ValueError(
            "No integer turns-ratio candidate satisfies the configured turns-ratio tolerance."
        )
    return min(candidates, key=lambda row: (row[0], row[4], row[1]))


def compute_equivalent_loads(spec: TopologySpec, n: float) -> tuple[float, float, float]:
    """Compute nominal DC and FHA AC equivalent loads."""

    inputs = _extract_llc_inputs(spec)
    if n <= 0.0:
        raise ValueError("Turns ratio must be positive.")
    rout_nom_ohm = inputs.vout_nom_v**2 / inputs.pout_max_w
    rac_nom_ohm = (8.0 / pi**2) * n**2 * rout_nom_ohm
    pout_min_w = inputs.min_load_ratio * inputs.pout_max_w
    return rout_nom_ohm, rac_nom_ohm, pout_min_w


def compute_llc_components(fr_hz: float, ln: float, q: float, rac_nom_ohm: float) -> tuple[float, float, float, float]:
    """Compute resonant tank impedance and component values."""

    if fr_hz <= 0.0 or ln <= 0.0 or q <= 0.0 or rac_nom_ohm <= 0.0:
        raise ValueError("fr_hz, ln, q, and rac_nom_ohm must be positive.")
    zr_ohm = q * rac_nom_ohm
    lr_h = zr_ohm / (2.0 * pi * fr_hz)
    cr_f = 1.0 / (2.0 * pi * fr_hz * zr_ohm)
    lm_h = ln * lr_h
    return zr_ohm, lr_h, cr_f, lm_h


def assess_llc_fha_input_impedance(
    *,
    fs_hz: float,
    lr_h: float,
    cr_f: float,
    lm_h: float,
    turns_ratio: float,
    vout_v: float,
    pout_w: float,
    boundary_imag_tolerance_ohm: float = 1e-9,
) -> LLCInputImpedanceAssessment:
    """Return the FHA input impedance and inductive/capacitive ZVS assessment."""

    if fs_hz <= 0.0 or lr_h <= 0.0 or cr_f <= 0.0 or lm_h <= 0.0:
        raise ValueError("LLC FHA input impedance requires positive fs, Lr, Cr, and Lm.")
    if turns_ratio <= 0.0 or vout_v <= 0.0 or pout_w <= 0.0:
        raise ValueError("LLC FHA input impedance requires positive turns ratio, Vout, and Pout.")

    omega_rad_s = 2.0 * pi * fs_hz
    zr_ohm = 1j * omega_rad_s * lr_h + 1.0 / (1j * omega_rad_s * cr_f)
    zm_ohm = 1j * omega_rad_s * lm_h
    ro_ohm = vout_v**2 / pout_w
    rac_ohm = (8.0 / pi**2) * turns_ratio**2 * ro_ohm
    zp_ohm = (zm_ohm * rac_ohm) / (zm_ohm + rac_ohm)
    zin_ohm = zr_ohm + zp_ohm
    angle_rad = atan2(zin_ohm.imag, zin_ohm.real)
    angle_deg = angle_rad * 180.0 / pi

    if zin_ohm.imag > boundary_imag_tolerance_ohm:
        tank_characteristic = "inductive"
    elif zin_ohm.imag < -boundary_imag_tolerance_ohm:
        tank_characteristic = "capacitive"
    else:
        tank_characteristic = "boundary"
    return LLCInputImpedanceAssessment(
        zin_ohm=zin_ohm,
        angle_rad=angle_rad,
        angle_deg=angle_deg,
        tank_characteristic=tank_characteristic,
        zvs_assumed=tank_characteristic == "inductive",
    )


def estimate_llc_fha_currents(
    design: LLCFHADesign,
    vin_v: float,
    vout_v: float,
    pout_w: float,
    fs_hz: float,
) -> dict[str, object]:
    """Estimate first-pass sinusoidal FHA current stresses for one operating point."""

    _validate_current_inputs(design, vin_v, vout_v, pout_w, fs_hz)
    omega_rad_s = 2.0 * pi * fs_hz
    rout_ohm = vout_v**2 / pout_w
    rac_ohm = (8.0 / pi**2) * design.turns_ratio**2 * rout_ohm
    vac1_rms_v = (2.0 * sqrt(2.0) / pi) * design.primary_bridge_gain_factor * vin_v
    z_r_ohm = 1j * omega_rad_s * design.lr_h + 1.0 / (1j * omega_rad_s * design.cr_f)
    z_m_ohm = 1j * omega_rad_s * design.lm_h
    z_p_ohm = (z_m_ohm * rac_ohm) / (z_m_ohm + rac_ohm)
    z_total_ohm = z_r_ohm + z_p_ohm
    if abs(z_total_ohm) <= 1e-18 or abs(z_m_ohm) <= 1e-18 or rac_ohm <= 0.0:
        raise ValueError("LLC FHA current estimate encountered a singular impedance.")

    ir_complex_a = vac1_rms_v / z_total_ohm
    ir_rms_a = abs(ir_complex_a)
    vp_v = ir_complex_a * z_p_ohm
    im_rms_a = abs(vp_v / z_m_ohm)
    reflected_load_current_rms_a = abs(vp_v / rac_ohm)
    ir_peak_a = sqrt(2.0) * ir_rms_a
    output_current_a = pout_w / vout_v
    rectifier_reverse_voltage_stress_v = (
        design.vout_max_v
        if design.secondary_rectifier_type == "full_bridge_rectifier"
        else 2.0 * design.vout_max_v
    )
    notes = [
        "First-pass FHA sinusoidal current stress estimates are used for diode LLC semiconductor screening.",
        "Worst-case current stress is selected from feasible FHA coverage corners.",
        "Primary switch RMS assumes each primary switch conducts for approximately half a switching period.",
        "Rectifier diode average/RMS currents are output-side first-pass estimates, not conduction-angle-integrated waveform results.",
        "Rectifier peak current is estimated from the reflected FHA tank-current peak.",
        "Detailed LLC time-domain waveforms, dead-time commutation, ZVS current, harmonics, diode conduction angle, and device-level current sharing are not implemented yet.",
    ]
    return {
        "vin_v": vin_v,
        "vout_v": vout_v,
        "pout_w": pout_w,
        "fs_hz": fs_hz,
        "rout_ohm": rout_ohm,
        "rac_ohm": rac_ohm,
        "vac1_rms_v": vac1_rms_v,
        "ir_rms_a": ir_rms_a,
        "ir_peak_a": ir_peak_a,
        "im_rms_a": im_rms_a,
        "reflected_load_current_rms_a": reflected_load_current_rms_a,
        "primary_switch_rms_a": ir_rms_a / sqrt(2.0),
        "primary_switch_peak_a": ir_peak_a,
        "output_current_a": output_current_a,
        "rectifier_diode_avg_a": output_current_a / 2.0,
        "rectifier_diode_rms_a": output_current_a / sqrt(2.0),
        "rectifier_diode_peak_a": design.turns_ratio * ir_peak_a,
        "primary_switch_voltage_stress_v": design.vin_max_v,
        "rectifier_reverse_voltage_stress_v": rectifier_reverse_voltage_stress_v,
        "current_estimation_method": "first_pass_fha_sinusoidal_nominal_full_load",
        "current_estimation_notes": notes,
    }


def solve_operating_frequency(
    design: LLCFHADesign,
    vin_v: float,
    vout_v: float,
    pout_w: float,
) -> LLCOperatingPointResult:
    """Find the switching frequency whose FHA gain best matches one corner."""

    if vin_v <= 0.0 or vout_v <= 0.0 or pout_w <= 0.0:
        raise ValueError("Operating-point voltage and power values must be positive.")

    rout_ohm = vout_v**2 / pout_w
    rac_ohm = (8.0 / pi**2) * design.turns_ratio**2 * rout_ohm
    q_op = design.zr_ohm / rac_ohm
    m_req = design.turns_ratio * vout_v / (design.primary_bridge_gain_factor * vin_v)

    points = 1501
    best_fs_hz = design.fs_min_hz
    best_gain = llc_fha_gain(best_fs_hz / design.fr_hz, design.ln, q_op)
    best_error = abs(best_gain - m_req)
    for index in range(1, points):
        alpha = index / (points - 1)
        fs_hz = design.fs_min_hz + alpha * (design.fs_max_hz - design.fs_min_hz)
        gain = llc_fha_gain(fs_hz / design.fr_hz, design.ln, q_op)
        gain_error = abs(gain - m_req)
        if gain_error < best_error:
            best_fs_hz = fs_hz
            best_gain = gain
            best_error = gain_error

    relative_error = best_error / max(abs(m_req), 1e-12)
    return LLCOperatingPointResult(
        label="",
        vin_v=vin_v,
        vout_v=vout_v,
        pout_w=pout_w,
        feasible=relative_error <= 0.02 and design.fs_min_hz <= best_fs_hz <= design.fs_max_hz,
        fs_hz=best_fs_hz,
        fn=best_fs_hz / design.fr_hz,
        q_op=q_op,
        rac_ohm=rac_ohm,
        m_req=m_req,
        m_actual=best_gain,
        gain_error=relative_error,
    )


def solve_fixed_frequency_operating_point(
    design: LLCFHADesign,
    *,
    vin_v: float,
    rload_ohm: float,
    fs_op_hz: float,
) -> LLCAchievedOperatingPoint:
    """Evaluate achieved output for fixed hardware, load, and commanded frequency."""

    if min(vin_v, rload_ohm, fs_op_hz, design.fr_hz, design.turns_ratio) <= 0.0:
        raise ValueError("Fixed-frequency LLC operating-point inputs must be positive.")
    rac_ohm = (8.0 / pi**2) * design.turns_ratio**2 * rload_ohm
    q_op = design.zr_ohm / rac_ohm
    fn_op = fs_op_hz / design.fr_hz
    gain = llc_fha_gain(fn_op, design.ln, q_op)
    vout_achieved_v = gain * design.primary_bridge_gain_factor * vin_v / design.turns_ratio
    iout_achieved_a = vout_achieved_v / rload_ohm
    pout_achieved_w = vout_achieved_v * iout_achieved_a
    return LLCAchievedOperatingPoint(
        vin_v=vin_v,
        vout_achieved_v=vout_achieved_v,
        iout_achieved_a=iout_achieved_a,
        pout_achieved_w=pout_achieved_w,
        rload_ohm=rload_ohm,
        fr_hz=design.fr_hz,
        fs_op_hz=fs_op_hz,
        fn_op=fn_op,
        gain=gain,
        q_op=q_op,
        rac_ohm=rac_ohm,
        operating_point_feasible=design.fs_min_hz <= fs_op_hz <= design.fs_max_hz,
        off_resonance_accuracy_limited=abs(fn_op - 1.0) > 0.2,
    )


def check_llc_design_coverage(design: LLCFHADesign) -> tuple[list[LLCOperatingPointResult], bool]:
    """Check the LLC FHA candidate at required line/load corners."""

    results = [
        replace(solve_operating_frequency(design, vin_v, vout_v, pout_w), label=label)
        for label, vin_v, vout_v, pout_w in _coverage_corner_specs(design)
    ]
    return results, all(result.feasible for result in results)


def design_llc_fha(spec: TopologySpec) -> LLCFHADesign:
    """Synthesize a first-pass diode LLC FHA electrical design."""

    inputs = _extract_llc_inputs(spec)
    fixed_hardware = spec.metadata.get("fixed_hardware", {})
    if isinstance(fixed_hardware, dict) and fixed_hardware:
        return _design_from_fixed_hardware(spec, inputs, fixed_hardware)
    fr_hz = sqrt(inputs.fs_min_hz * inputs.fs_max_hz)
    kpri = primary_bridge_gain_factor(inputs.primary_bridge_type)
    np_turns, ns_turns, n, n_ideal, ratio_error = estimate_integer_turns_ratio(
        inputs.vin_nom_v,
        inputs.vout_nom_v,
        kpri,
        inputs.turns_ratio_tolerance_percent,
    )
    rout_nom_ohm, rac_nom_ohm, pout_min_w = compute_equivalent_loads(spec, n)
    rectifier_note = secondary_rectifier_note(inputs.secondary_rectifier_type)

    best_feasible: tuple[float, LLCFHADesign] | None = None
    best_diagnostic: tuple[float, LLCFHADesign] | None = None
    for ln_index in range(15):
        ln = 3.0 + 0.5 * ln_index
        for q_index in range(21):
            q_nom = 0.2 + 0.05 * q_index
            zr_ohm, lr_h, cr_f, lm_h = compute_llc_components(fr_hz, ln, q_nom, rac_nom_ohm)
            design = LLCFHADesign(
                topology_id=inputs.topology_id,
                vin_min_v=inputs.vin_min_v,
                vin_nom_v=inputs.vin_nom_v,
                vin_max_v=inputs.vin_max_v,
                vout_min_v=inputs.vout_min_v,
                vout_nom_v=inputs.vout_nom_v,
                vout_max_v=inputs.vout_max_v,
                pout_max_w=inputs.pout_max_w,
                min_load_ratio=inputs.min_load_ratio,
                pout_min_w=pout_min_w,
                fs_min_hz=inputs.fs_min_hz,
                fs_max_hz=inputs.fs_max_hz,
                fr_hz=fr_hz,
                primary_bridge_type=inputs.primary_bridge_type,
                secondary_rectifier_type=inputs.secondary_rectifier_type,
                primary_bridge_gain_factor=kpri,
                secondary_rectifier_note=rectifier_note,
                np_turns=np_turns,
                ns_turns=ns_turns,
                turns_ratio=n,
                ideal_turns_ratio=n_ideal,
                turns_ratio_error=ratio_error,
                rout_nom_ohm=rout_nom_ohm,
                rac_nom_ohm=rac_nom_ohm,
                ln=ln,
                q_nom=q_nom,
                zr_ohm=zr_ohm,
                lr_h=lr_h,
                cr_f=cr_f,
                lm_h=lm_h,
                turns_ratio_tolerance_percent=inputs.turns_ratio_tolerance_percent,
                turns_ratio_within_tolerance=(
                    ratio_error * 100.0 <= inputs.turns_ratio_tolerance_percent + 1e-12
                ),
            )
            coverage_results, overall_feasible = check_llc_design_coverage(design)
            design = _replace_coverage(design, coverage_results, overall_feasible)
            score = _rank_score(design)
            row = (score, design)
            if overall_feasible and (best_feasible is None or score < best_feasible[0]):
                best_feasible = row
            if best_diagnostic is None or score < best_diagnostic[0]:
                best_diagnostic = row

    if best_feasible is not None:
        return _with_nominal_current_estimate(best_feasible[1])
    if best_diagnostic is None:
        raise ValueError("No LLC FHA diagnostic candidate was generated.")
    warnings = [
        "No scanned Ln/Q candidate met all FHA coverage corners within the 2% gain-error tolerance.",
        "Returned candidate is the best diagnostic result from the configured scan.",
    ]
    return _with_nominal_current_estimate(_replace_coverage(
        best_diagnostic[1],
        best_diagnostic[1].coverage_results,
        False,
        warnings=warnings,
    ))


def _validate_current_inputs(
    design: LLCFHADesign,
    vin_v: float,
    vout_v: float,
    pout_w: float,
    fs_hz: float,
) -> None:
    if vin_v <= 0.0 or vout_v <= 0.0 or pout_w <= 0.0 or fs_hz <= 0.0:
        raise ValueError("LLC FHA current estimate operating values must be positive.")
    if design.lr_h <= 0.0 or design.cr_f <= 0.0 or design.lm_h <= 0.0:
        raise ValueError("LLC FHA current estimate requires positive Lr, Cr, and Lm.")
    if design.turns_ratio <= 0.0 or design.primary_bridge_gain_factor <= 0.0:
        raise ValueError("LLC FHA current estimate requires positive turns ratio and primary bridge gain factor.")


def _design_from_fixed_hardware(
    spec: TopologySpec,
    inputs: _LLCInputSpec,
    hardware: dict[str, object],
) -> LLCFHADesign:
    lr_h = float(hardware["resonant_inductance_h"])
    lm_h = float(hardware["magnetizing_inductance_h"])
    cr_f = float(hardware["resonant_capacitance_f"])
    np_turns = int(round(float(hardware["transformer_primary_turns"])))
    ns_turns = int(round(float(hardware["transformer_secondary_turns"])))
    rout_nom_ohm = float(hardware["load_resistance_ohm"])
    if min(lr_h, lm_h, cr_f, np_turns, ns_turns, rout_nom_ohm) <= 0.0:
        raise ValueError("Fixed LLC hardware snapshot values must be positive.")
    turns_ratio = np_turns / ns_turns
    fr_hz = 1.0 / (2.0 * pi * sqrt(lr_h * cr_f))
    ln = lm_h / lr_h
    zr_ohm = sqrt(lr_h / cr_f)
    rac_nom_ohm = (8.0 / pi**2) * turns_ratio**2 * rout_nom_ohm
    q_nom = zr_ohm / rac_nom_ohm
    kpri = primary_bridge_gain_factor(inputs.primary_bridge_type)
    ideal_turns_ratio = kpri * inputs.vin_nom_v / inputs.vout_nom_v
    design = LLCFHADesign(
        topology_id=inputs.topology_id,
        vin_min_v=inputs.vin_min_v,
        vin_nom_v=inputs.vin_nom_v,
        vin_max_v=inputs.vin_max_v,
        vout_min_v=inputs.vout_min_v,
        vout_nom_v=inputs.vout_nom_v,
        vout_max_v=inputs.vout_max_v,
        pout_max_w=inputs.pout_max_w,
        min_load_ratio=inputs.min_load_ratio,
        pout_min_w=inputs.min_load_ratio * inputs.pout_max_w,
        fs_min_hz=inputs.fs_min_hz,
        fs_max_hz=inputs.fs_max_hz,
        fr_hz=fr_hz,
        primary_bridge_type=inputs.primary_bridge_type,
        secondary_rectifier_type=inputs.secondary_rectifier_type,
        primary_bridge_gain_factor=kpri,
        secondary_rectifier_note=secondary_rectifier_note(inputs.secondary_rectifier_type),
        np_turns=np_turns,
        ns_turns=ns_turns,
        turns_ratio=turns_ratio,
        ideal_turns_ratio=ideal_turns_ratio,
        turns_ratio_error=abs(turns_ratio - ideal_turns_ratio) / ideal_turns_ratio,
        rout_nom_ohm=rout_nom_ohm,
        rac_nom_ohm=rac_nom_ohm,
        ln=ln,
        q_nom=q_nom,
        zr_ohm=zr_ohm,
        lr_h=lr_h,
        cr_f=cr_f,
        lm_h=lm_h,
        turns_ratio_tolerance_percent=inputs.turns_ratio_tolerance_percent,
        turns_ratio_within_tolerance=(
            abs(turns_ratio - ideal_turns_ratio) / ideal_turns_ratio * 100.0
            <= inputs.turns_ratio_tolerance_percent + 1e-12
        ),
        warnings=["LLC tank and transformer ratio were loaded from a complete fixed-hardware snapshot."],
    )
    coverage_results, overall_feasible = check_llc_design_coverage(design)
    return _with_nominal_current_estimate(
        _replace_coverage(design, coverage_results, overall_feasible, warnings=design.warnings)
    )


def _with_nominal_current_estimate(design: LLCFHADesign) -> LLCFHADesign:
    nominal = next(
        (result for result in design.coverage_results if result.label == "Vin_nom, Vout_nom, Pout_max"),
        None,
    )
    fs_hz = nominal.fs_hz if nominal is not None else design.fr_hz
    try:
        current_estimate = estimate_llc_fha_currents(
            design,
            vin_v=design.vin_nom_v,
            vout_v=design.vout_nom_v,
            pout_w=design.pout_max_w,
            fs_hz=fs_hz,
        )
        warnings = list(design.warnings)
    except ValueError as exc:
        current_estimate = {
            "current_estimation_method": "first_pass_fha_sinusoidal_nominal_full_load",
            "current_estimation_notes": [f"Current estimation failed: {exc}"],
            "error": str(exc),
        }
        warnings = [*design.warnings, f"LLC FHA current estimation failed: {exc}"]
    corner_estimates = _estimate_currents_by_corner(design)
    worst_case_current_stress = _select_worst_case_current_stress(design, corner_estimates)
    return _replace_coverage(
        design,
        design.coverage_results,
        design.overall_feasible,
        current_estimates_nominal_full_load=current_estimate,
        current_estimates_by_corner=corner_estimates,
                worst_case_current_stress=worst_case_current_stress,
                semiconductor_topology_counts=semiconductor_topology_counts(
                    design.primary_bridge_type,
                    design.secondary_rectifier_type,
                ),
                warnings=warnings,
            )


def _coverage_corner_specs(design: LLCFHADesign) -> tuple[tuple[str, float, float, float], ...]:
    return (
        ("Vin_min, Vout_max, Pout_max", design.vin_min_v, design.vout_max_v, design.pout_max_w),
        ("Vin_nom, Vout_nom, Pout_max", design.vin_nom_v, design.vout_nom_v, design.pout_max_w),
        ("Vin_max, Vout_min, Pout_max", design.vin_max_v, design.vout_min_v, design.pout_max_w),
        ("Vin_min, Vout_max, Pout_min", design.vin_min_v, design.vout_max_v, design.pout_min_w),
        ("Vin_max, Vout_min, Pout_min", design.vin_max_v, design.vout_min_v, design.pout_min_w),
    )


def _estimate_currents_by_corner(design: LLCFHADesign) -> list[dict[str, object]]:
    coverage_by_label = {result.label: result for result in design.coverage_results}
    estimates: list[dict[str, object]] = []
    for corner_name, vin_v, vout_v, pout_w in _coverage_corner_specs(design):
        solved = coverage_by_label.get(corner_name)
        if solved is None:
            solved = replace(solve_operating_frequency(design, vin_v, vout_v, pout_w), label=corner_name)
        warnings: list[str] = []
        if not solved.feasible:
            warnings.append("FHA gain coverage check failed at this corner; current estimate is diagnostic only.")
        try:
            estimate = estimate_llc_fha_currents(
                design,
                vin_v=vin_v,
                vout_v=vout_v,
                pout_w=pout_w,
                fs_hz=solved.fs_hz,
            )
            estimate.update({
                "corner_name": corner_name,
                "fn": solved.fn,
                "m_req": solved.m_req,
                "m_actual": solved.m_actual,
                "gain_error": solved.gain_error,
                "q_op": solved.q_op,
                "rac_ohm": solved.rac_ohm,
                "feasible": solved.feasible,
                "warnings": warnings,
                "current_estimation_method": "first_pass_fha_sinusoidal_corner_sweep",
            })
        except ValueError as exc:
            estimate = {
                "corner_name": corner_name,
                "vin_v": vin_v,
                "vout_v": vout_v,
                "pout_w": pout_w,
                "fs_hz": solved.fs_hz,
                "fn": solved.fn,
                "m_req": solved.m_req,
                "m_actual": solved.m_actual,
                "gain_error": solved.gain_error,
                "q_op": solved.q_op,
                "rac_ohm": solved.rac_ohm,
                "feasible": False,
                "warnings": [*warnings, f"Current estimation failed: {exc}"],
                "error": str(exc),
                "current_estimation_method": "first_pass_fha_sinusoidal_corner_sweep",
            }
        estimates.append(estimate)
    return estimates


def _select_worst_case_current_stress(
    design: LLCFHADesign,
    corner_estimates: list[dict[str, object]],
) -> dict[str, object]:
    usable = [
        estimate
        for estimate in corner_estimates
        if bool(estimate.get("feasible")) and _has_numeric_current_estimates(estimate)
    ]
    source_warning = ""
    if not usable:
        usable = [estimate for estimate in corner_estimates if _has_numeric_current_estimates(estimate)]
        if usable:
            source_warning = "No feasible FHA current corner existed; diagnostic current estimates were used."
    if not usable:
        return {
            "source": "worst_feasible_coverage_corner_fha_estimate",
            "warnings": ["No numeric FHA current corner estimates were available."],
        }

    warnings = [source_warning] if source_warning else []
    primary_rms, primary_rms_corner = _max_value_and_corner(usable, "primary_switch_rms_a")
    primary_peak, primary_peak_corner = _max_value_and_corner(usable, "primary_switch_peak_a")
    rectifier_avg, rectifier_avg_corner = _max_value_and_corner(usable, "rectifier_diode_avg_a")
    rectifier_rms, rectifier_rms_corner = _max_value_and_corner(usable, "rectifier_diode_rms_a")
    rectifier_peak, rectifier_peak_corner = _max_value_and_corner(usable, "rectifier_diode_peak_a")
    resonant_rms, _ = _max_value_and_corner(usable, "ir_rms_a")
    resonant_peak, _ = _max_value_and_corner(usable, "ir_peak_a")
    output_current_max, _ = _max_value_and_corner(usable, "output_current_a")
    rectifier_reverse_voltage_stress_v = (
        design.vout_max_v
        if design.secondary_rectifier_type == "full_bridge_rectifier"
        else 2.0 * design.vout_max_v
    )
    return {
        "primary_switch_rms_a": primary_rms,
        "primary_switch_rms_corner": primary_rms_corner,
        "primary_switch_peak_a": primary_peak,
        "primary_switch_peak_corner": primary_peak_corner,
        "rectifier_diode_avg_a": rectifier_avg,
        "rectifier_diode_avg_corner": rectifier_avg_corner,
        "rectifier_diode_rms_a": rectifier_rms,
        "rectifier_diode_rms_corner": rectifier_rms_corner,
        "rectifier_diode_peak_a": rectifier_peak,
        "rectifier_diode_peak_corner": rectifier_peak_corner,
        "resonant_tank_rms_a": resonant_rms,
        "resonant_tank_peak_a": resonant_peak,
        "output_current_max_a": output_current_max,
        "primary_switch_voltage_stress_v": design.vin_max_v,
        "rectifier_reverse_voltage_stress_v": rectifier_reverse_voltage_stress_v,
        "source": "worst_feasible_coverage_corner_fha_estimate",
        "warnings": warnings,
    }


def _has_numeric_current_estimates(estimate: dict[str, object]) -> bool:
    required_keys = (
        "primary_switch_rms_a",
        "primary_switch_peak_a",
        "rectifier_diode_avg_a",
        "rectifier_diode_rms_a",
        "rectifier_diode_peak_a",
        "ir_rms_a",
        "ir_peak_a",
        "output_current_a",
    )
    return all(isinstance(estimate.get(key), (int, float)) for key in required_keys)


def _max_value_and_corner(estimates: list[dict[str, object]], key: str) -> tuple[float, str]:
    best = max(estimates, key=lambda estimate: float(estimate[key]))
    return float(best[key]), str(best.get("corner_name", "-"))


def _extract_llc_inputs(spec: TopologySpec) -> _LLCInputSpec:
    raw_input = spec.raw_input
    metadata = spec.metadata

    def read_float(key: str, fallback: float | None = None) -> float:
        value = raw_input.get(key, metadata.get(key, fallback))
        if value is None:
            raise ValueError(f"Missing LLC FHA input field: {key}")
        return float(value)

    inputs = _LLCInputSpec(
        topology_id=spec.topology_id,
        vin_min_v=read_float("vin_min", spec.vin_min),
        vin_nom_v=read_float("vin_nom", metadata.get("vin_nom")),
        vin_max_v=read_float("vin_max", spec.vin_max),
        vout_min_v=read_float("vout_min", metadata.get("vout_min")),
        vout_nom_v=read_float("vout_nom", spec.vout),
        vout_max_v=read_float("vout_max", metadata.get("vout_max")),
        pout_max_w=read_float("pout_max", spec.pout),
        min_load_ratio=read_float("min_load_ratio", metadata.get("min_load_ratio")),
        fs_min_hz=read_float("fs_min_hz", metadata.get("fs_min_hz")),
        fs_max_hz=read_float("fs_max_hz", metadata.get("fs_max_hz")),
        turns_ratio_tolerance_percent=read_float(
            "turns_ratio_tolerance_percent",
            metadata.get("turns_ratio_tolerance_percent", 5.0),
        ),
        primary_bridge_type=str(raw_input.get("primary_bridge_type", metadata.get("primary_bridge_type", "full_bridge"))),
        secondary_rectifier_type=str(
            raw_input.get("secondary_rectifier_type", metadata.get("secondary_rectifier_type", "full_bridge_rectifier"))
        ),
    )
    _validate_inputs(inputs)
    return inputs


def _validate_inputs(inputs: _LLCInputSpec) -> None:
    if min(inputs.vin_min_v, inputs.vin_nom_v, inputs.vin_max_v) <= 0.0:
        raise ValueError("LLC input voltage values must be positive.")
    if not inputs.vin_min_v <= inputs.vin_nom_v <= inputs.vin_max_v:
        raise ValueError("LLC nominal input voltage must be between min and max.")
    if min(inputs.vout_min_v, inputs.vout_nom_v, inputs.vout_max_v) <= 0.0:
        raise ValueError("LLC output voltage values must be positive.")
    if not inputs.vout_min_v <= inputs.vout_nom_v <= inputs.vout_max_v:
        raise ValueError("LLC nominal output voltage must be between min and max.")
    if inputs.pout_max_w <= 0.0:
        raise ValueError("LLC maximum output power must be positive.")
    if inputs.min_load_ratio < 0.0 or inputs.min_load_ratio > 1.0:
        raise ValueError("LLC minimum load ratio must be between 0 and 1.")
    if inputs.fs_min_hz <= 0.0 or inputs.fs_max_hz <= 0.0 or inputs.fs_max_hz < inputs.fs_min_hz:
        raise ValueError("LLC switching frequency limits are invalid.")
    if not 0.0 <= inputs.turns_ratio_tolerance_percent <= 100.0:
        raise ValueError("LLC turns-ratio tolerance percent must be between 0 and 100.")
    primary_bridge_gain_factor(inputs.primary_bridge_type)
    secondary_rectifier_note(inputs.secondary_rectifier_type)


def _replace_coverage(
    design: LLCFHADesign,
    coverage_results: list[LLCOperatingPointResult],
    overall_feasible: bool,
    *,
    current_estimates_nominal_full_load: dict[str, object] | None = None,
    current_estimates_by_corner: list[dict[str, object]] | None = None,
    worst_case_current_stress: dict[str, object] | None = None,
    semiconductor_topology_counts: dict[str, object] | None = None,
    warnings: list[str] | None = None,
) -> LLCFHADesign:
    zvs = _evaluate_first_pass_zvs_assessment(design, coverage_results, overall_feasible)
    return LLCFHADesign(
        topology_id=design.topology_id,
        vin_min_v=design.vin_min_v,
        vin_nom_v=design.vin_nom_v,
        vin_max_v=design.vin_max_v,
        vout_min_v=design.vout_min_v,
        vout_nom_v=design.vout_nom_v,
        vout_max_v=design.vout_max_v,
        pout_max_w=design.pout_max_w,
        min_load_ratio=design.min_load_ratio,
        pout_min_w=design.pout_min_w,
        fs_min_hz=design.fs_min_hz,
        fs_max_hz=design.fs_max_hz,
        fr_hz=design.fr_hz,
        primary_bridge_type=design.primary_bridge_type,
        secondary_rectifier_type=design.secondary_rectifier_type,
        primary_bridge_gain_factor=design.primary_bridge_gain_factor,
        secondary_rectifier_note=design.secondary_rectifier_note,
        np_turns=design.np_turns,
        ns_turns=design.ns_turns,
        turns_ratio=design.turns_ratio,
        ideal_turns_ratio=design.ideal_turns_ratio,
        turns_ratio_error=design.turns_ratio_error,
        rout_nom_ohm=design.rout_nom_ohm,
        rac_nom_ohm=design.rac_nom_ohm,
        ln=design.ln,
        q_nom=design.q_nom,
        zr_ohm=design.zr_ohm,
        lr_h=design.lr_h,
        cr_f=design.cr_f,
        lm_h=design.lm_h,
        turns_ratio_tolerance_percent=design.turns_ratio_tolerance_percent,
        turns_ratio_within_tolerance=design.turns_ratio_within_tolerance,
        coverage_results=coverage_results,
        current_estimates_nominal_full_load=(
            dict(current_estimates_nominal_full_load)
            if current_estimates_nominal_full_load is not None
            else dict(design.current_estimates_nominal_full_load)
        ),
        current_estimates_by_corner=(
            [dict(estimate) for estimate in current_estimates_by_corner]
            if current_estimates_by_corner is not None
            else [dict(estimate) for estimate in design.current_estimates_by_corner]
        ),
        worst_case_current_stress=(
            dict(worst_case_current_stress)
            if worst_case_current_stress is not None
            else dict(design.worst_case_current_stress)
        ),
        semiconductor_topology_counts=(
            dict(semiconductor_topology_counts)
            if semiconductor_topology_counts is not None
            else dict(design.semiconductor_topology_counts)
        ),
        zvs_assessment=zvs["zvs_assessment"],
        zvs_data_status=zvs["zvs_data_status"],
        zvs_all_checked_corners=zvs["zvs_all_checked_corners"],
        zvs_assessment_by_corner=zvs["zvs_assessment_by_corner"],
        zvs_worst_angle_deg=zvs["zvs_worst_angle_deg"],
        zvs_worst_corner=zvs["zvs_worst_corner"],
        zvs_assessment_basis=zvs["zvs_assessment_basis"],
        overall_feasible=overall_feasible,
        warnings=list(warnings or design.warnings),
    )


_ZVS_ASSESSMENT_BASIS = "first_pass_fha_input_impedance_angle_only_no_coss_deadtime_layout_parasitics"


def _evaluate_first_pass_zvs_assessment(
    design: LLCFHADesign,
    coverage_results: list[LLCOperatingPointResult],
    overall_feasible: bool,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for result in coverage_results:
        try:
            assessment = assess_llc_fha_input_impedance(
                fs_hz=result.fs_hz,
                lr_h=design.lr_h,
                cr_f=design.cr_f,
                lm_h=design.lm_h,
                turns_ratio=design.turns_ratio,
                vout_v=result.vout_v,
                pout_w=result.pout_w,
            )
            rows.append(
                {
                    "corner_name": result.label,
                    "vin_v": result.vin_v,
                    "vout_v": result.vout_v,
                    "pout_w": result.pout_w,
                    "fs_hz": result.fs_hz,
                    "fn": result.fn,
                    "angle_deg": assessment.angle_deg,
                    "tank_characteristic": assessment.tank_characteristic,
                    "zvs_assumed": assessment.zvs_assumed,
                    "basis": _ZVS_ASSESSMENT_BASIS,
                }
            )
        except ValueError as exc:
            rows.append(
                {
                    "corner_name": result.label,
                    "vin_v": result.vin_v,
                    "vout_v": result.vout_v,
                    "pout_w": result.pout_w,
                    "fs_hz": result.fs_hz,
                    "fn": result.fn,
                    "angle_deg": None,
                    "tank_characteristic": "not_evaluated",
                    "zvs_assumed": False,
                    "basis": _ZVS_ASSESSMENT_BASIS,
                    "error": str(exc),
                }
            )

    numeric_angle_rows = [row for row in rows if isinstance(row.get("angle_deg"), (int, float))]
    worst = min(numeric_angle_rows, key=lambda row: float(row["angle_deg"]), default=None)
    all_inductive = bool(rows) and all(row.get("tank_characteristic") == "inductive" for row in rows)

    if not overall_feasible:
        zvs_assessment = "diagnostic_only_fha_infeasible"
        zvs_data_status = "diagnostic_only"
        zvs_all_checked_corners: bool | None = None
    elif all_inductive:
        zvs_assessment = "first_pass_inductive_all_checked_corners"
        zvs_data_status = "first_pass_fha_tank_impedance"
        zvs_all_checked_corners = True
    else:
        zvs_assessment = "first_pass_non_inductive_corner_detected"
        zvs_data_status = "first_pass_fha_tank_impedance"
        zvs_all_checked_corners = False

    return {
        "zvs_assessment": zvs_assessment,
        "zvs_data_status": zvs_data_status,
        "zvs_all_checked_corners": zvs_all_checked_corners,
        "zvs_assessment_by_corner": rows,
        "zvs_worst_angle_deg": None if worst is None else float(worst["angle_deg"]),
        "zvs_worst_corner": None if worst is None else str(worst["corner_name"]),
        "zvs_assessment_basis": _ZVS_ASSESSMENT_BASIS,
    }


def _rank_score(design: LLCFHADesign) -> float:
    nominal = next(
        (result for result in design.coverage_results if result.label == "Vin_nom, Vout_nom, Pout_max"),
        None,
    )
    nominal_frequency_error = abs((nominal.fs_hz if nominal else design.fr_hz) - design.fr_hz) / design.fr_hz
    max_gain_error = max((result.gain_error for result in design.coverage_results), default=1.0)
    infeasible_count = sum(1 for result in design.coverage_results if not result.feasible)
    return (
        2.0 * abs(design.ln - 5.0)
        + 3.0 * abs(design.q_nom - 0.55)
        + nominal_frequency_error
        + 20.0 * max_gain_error
        + 10.0 * infeasible_count
    )
