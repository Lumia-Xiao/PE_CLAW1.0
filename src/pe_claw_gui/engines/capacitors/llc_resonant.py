"""First-pass LLC resonant capacitor candidate search."""

from __future__ import annotations

import csv
import math
from dataclasses import replace
from pathlib import Path

from matplotlib.figure import Figure

from ...models.capacitor import (
    CapacitorCandidate,
    LlcResonantCapacitorBankCandidate,
    LlcResonantCapacitorDesignRequest,
    LlcResonantCapacitorSearchResult,
)

MAX_LLC_RESONANT_CAPACITOR_PARALLEL_COUNT = 20
CAPACITANCE_ERROR_LIMIT_PERCENT = 10.0
CAPACITANCE_WARNING_PERCENT = 5.0
SUITABLE_APPLICATION_CATEGORIES = {
    "dc_link",
    "dc_link_candidate",
    "dc_link_legacy",
    "general_film",
    "high_ripple_film",
    "power_film",
    "pulse",
    "resonant",
    "snubber",
    "snubber_pulse",
}

_REJECTION_KEYS = (
    "missing_request",
    "invalid_cr_target",
    "missing_voltage_rating",
    "voltage_rating",
    "capacitance_error",
    "missing_current_rating",
    "current_rating",
    "missing_esr_or_df",
    "thermal",
    "missing_volume",
    "unsupported_application",
)

_CSV_FIELDS = [
    "design_id",
    "part_number",
    "manufacturer",
    "series",
    "application_category",
    "capacitance_nF",
    "parallel_count",
    "bank_capacitance_nF",
    "cr_target_nF",
    "capacitance_error_percent",
    "voltage_rating_v",
    "required_voltage_rating_v",
    "voltage_utilization",
    "current_rms_total_a",
    "current_rms_per_cap_a",
    "ripple_current_rating_a",
    "current_utilization",
    "esr_ohm",
    "esr_basis",
    "bank_esr_ohm",
    "loss_w",
    "loss_per_cap_w",
    "ambient_c",
    "temperature_rise_c",
    "hotspot_c",
    "estimated_volume_cm3",
    "warning",
    "representative_role",
    "representative_reason",
]


def search_llc_resonant_capacitor_banks(
    request: LlcResonantCapacitorDesignRequest | None,
    candidates: tuple[CapacitorCandidate, ...],
    *,
    output_dir: Path,
    ambient_temp_c: float = 25.0,
) -> LlcResonantCapacitorSearchResult:
    """Evaluate LLC Cr bank candidates without using input/output ripple sizing."""

    rejection_counts = _empty_rejection_counts()
    part_rejection_counts = _empty_part_rejection_counts()
    bank_rejection_counts = _empty_bank_rejection_counts()
    if request is None:
        rejection_counts["missing_request"] += 1
        return LlcResonantCapacitorSearchResult(
            request=None,
            rejection_counts=rejection_counts,
            part_rejection_counts=part_rejection_counts,
            bank_rejection_counts=bank_rejection_counts,
            warnings=["LLC resonant capacitor search did not run because the design request is missing."],
        )
    if not request.is_design_required or request.cr_target_f <= 0.0:
        rejection_counts["invalid_cr_target"] += 1
        return LlcResonantCapacitorSearchResult(
            request=request,
            rejection_counts=rejection_counts,
            part_rejection_counts=part_rejection_counts,
            bank_rejection_counts=bank_rejection_counts,
            warnings=["LLC resonant capacitor search did not run because Cr target is invalid."],
        )

    evaluated: list[LlcResonantCapacitorBankCandidate] = []
    feasible: list[LlcResonantCapacitorBankCandidate] = []
    near_misses: list[LlcResonantCapacitorBankCandidate] = []
    for candidate in candidates:
        rejection_reason = _candidate_static_rejection(candidate)
        if rejection_reason:
            part_rejection_counts[rejection_reason] += 1
            rejection_counts[rejection_reason] += 1
            continue
        esr_ohm, esr_basis = _resolve_esr(candidate, request.fs_basis_hz)
        if esr_ohm <= 0.0 or not math.isfinite(esr_ohm):
            part_rejection_counts["missing_esr_or_df"] += 1
            rejection_counts["missing_esr_or_df"] += 1
            continue
        volume_cm3 = _candidate_volume_cm3(candidate)
        if volume_cm3 <= 0.0:
            part_rejection_counts["missing_volume"] += 1
            rejection_counts["missing_volume"] += 1
            continue
        for parallel_count in range(1, MAX_LLC_RESONANT_CAPACITOR_PARALLEL_COUNT + 1):
            bank = _evaluate_bank(
                request,
                candidate,
                parallel_count,
                esr_ohm,
                esr_basis,
                volume_cm3,
                ambient_temp_c,
            )
            evaluated.append(bank)
            if bank.rejection_reason:
                rejection_counts[bank.rejection_reason] += 1
                bank_rejection_counts[bank.rejection_reason] += 1
                if bank.rejection_reason == "capacitance_error":
                    near_misses.append(bank)
            else:
                feasible.append(bank)

    feasible = sorted(feasible, key=_recommendation_key)
    pareto = _extract_pareto_front(feasible)
    (
        feasible,
        pareto,
        recommended,
        min_volume,
        min_loss,
        compromise,
        chosen,
        pareto_notes,
    ) = _select_representatives(feasible, pareto)
    nearest_lower_bank, nearest_upper_bank = _nearest_brackets(evaluated, request.cr_target_f)
    closest_absolute_error_bank = min(evaluated, key=lambda bank: abs(bank.bank_capacitance_f - request.cr_target_f)) if evaluated else None
    lowest_loss_near_miss = min(near_misses, key=lambda bank: (bank.loss_w, abs(bank.capacitance_error_percent), bank.design_id)) if near_misses else None
    lowest_volume_near_miss = min(near_misses, key=lambda bank: (bank.estimated_volume_cm3, abs(bank.capacitance_error_percent), bank.design_id)) if near_misses else None
    capacitance_screened = [bank for bank in evaluated if abs(bank.capacitance_error_percent) <= CAPACITANCE_ERROR_LIMIT_PERCENT]
    feasible_csv_path = ""
    near_miss_csv_path = ""
    pareto_csv_path = ""
    chosen_csv_path = ""
    pareto_png_path = ""
    plot_diagnostics: dict[str, object] = {}
    if feasible:
        output_dir.mkdir(parents=True, exist_ok=True)
        feasible_csv_path = str(output_dir / "llc_resonant_capacitor_feasible_candidates.csv")
        _write_feasible_csv(Path(feasible_csv_path), feasible)
        if pareto:
            pareto_csv_path = str(output_dir / "llc_resonant_capacitor_pareto_front.csv")
            chosen_csv_path = str(output_dir / "llc_resonant_capacitor_chosen_candidates.csv")
            pareto_png_path = str(output_dir / "llc_resonant_capacitor_pareto_front.png")
            _write_feasible_csv(Path(pareto_csv_path), pareto)
            _write_feasible_csv(Path(chosen_csv_path), chosen)
            plot_diagnostics = _write_pareto_plot(Path(pareto_png_path), feasible, pareto, chosen)
    if near_misses:
        output_dir.mkdir(parents=True, exist_ok=True)
        near_miss_csv_path = str(output_dir / "llc_resonant_capacitor_near_miss_candidates.csv")
        _write_feasible_csv(Path(near_miss_csv_path), near_misses)
    within_5_percent = sum(1 for bank in evaluated if abs(bank.capacitance_error_percent) <= CAPACITANCE_WARNING_PERCENT)
    within_10_percent = len(capacitance_screened)
    within_10_and_usable = len(feasible)
    evaluated_capacitance_nF = [bank.bank_capacitance_nF for bank in evaluated]
    screened_capacitance_nF = [bank.bank_capacitance_nF for bank in capacitance_screened]
    notes = [
        "LLC resonant capacitor search uses Cr target, resonant tank RMS current, voltage rating, ESR/DF loss, and a first-pass thermal estimate.",
        f"Parallel count search range is 1..{MAX_LLC_RESONANT_CAPACITOR_PARALLEL_COUNT} for LLC Cr only.",
        (
            "Library coverage: "
            f"Cr target {request.cr_target_nF:.6g} nF, supported N=1..{MAX_LLC_RESONANT_CAPACITOR_PARALLEL_COUNT}, "
            f"within +/-5% = {within_5_percent}, within +/-10% = {within_10_percent}, "
            f"within +/-10% and passing voltage/current/ESR/thermal = {within_10_and_usable}."
        ),
        (
            "Nearest banks: "
            f"lower={_bank_label(nearest_lower_bank)}, "
            f"upper={_bank_label(nearest_upper_bank)}, "
            f"closest abs error={_bank_label(closest_absolute_error_bank)}."
        ),
        "LLC resonant capacitor Pareto front minimizes estimated bank volume and total capacitor bank loss.",
        "Resonant capacitor geometry is not implemented in this round.",
    ]
    notes.extend(pareto_notes)
    if _many_df_estimated(feasible):
        notes.append("ESR may be estimated from shared/default DF data; verify datasheet ESR for final design.")
    warnings = []
    if not feasible:
        warnings.append("No feasible LLC resonant capacitor bank within +/-10% Cr target.")
    return LlcResonantCapacitorSearchResult(
        request=request,
        candidates=evaluated,
        feasible_candidates=feasible,
        pareto_candidates=pareto,
        chosen_candidates=chosen,
        recommended_candidate=recommended,
        min_volume_candidate=min_volume,
        min_loss_candidate=min_loss,
        compromise_candidate=compromise,
        rejection_counts=rejection_counts,
        part_rejection_counts=part_rejection_counts,
        bank_rejection_counts=bank_rejection_counts,
        coverage_summary={
            "cr_target_nF": request.cr_target_nF,
            "parallel_count_min": 1,
            "parallel_count_max": MAX_LLC_RESONANT_CAPACITOR_PARALLEL_COUNT,
            "within_5_percent_count": within_5_percent,
            "within_10_percent_count": within_10_percent,
            "within_10_percent_and_feasible_count": within_10_and_usable,
            "nearest_lower_bank": nearest_lower_bank,
            "nearest_upper_bank": nearest_upper_bank,
            "closest_absolute_error_bank": closest_absolute_error_bank,
            "lowest_loss_near_miss": lowest_loss_near_miss,
            "lowest_volume_near_miss": lowest_volume_near_miss,
        },
        nearest_lower_bank=nearest_lower_bank,
        nearest_upper_bank=nearest_upper_bank,
        closest_absolute_error_bank=closest_absolute_error_bank,
        lowest_loss_near_miss=lowest_loss_near_miss,
        lowest_volume_near_miss=lowest_volume_near_miss,
        notes=notes,
        warnings=warnings,
        feasible_csv_path=feasible_csv_path,
        near_miss_csv_path=near_miss_csv_path,
        pareto_csv_path=pareto_csv_path,
        chosen_csv_path=chosen_csv_path,
        pareto_png_path=pareto_png_path,
        pareto_notes=pareto_notes,
        plot_diagnostics=plot_diagnostics,
    )


def _candidate_static_rejection(candidate: CapacitorCandidate) -> str:
    if candidate.application_category not in SUITABLE_APPLICATION_CATEGORIES:
        return "unsupported_application"
    if candidate.voltage_rating_dc_v <= 0.0:
        return "missing_voltage_rating"
    if candidate.irms_rating_a <= 0.0 or candidate.irms_rating_a <= 1e-6:
        return "missing_current_rating"
    if candidate.capacitance_f <= 0.0:
        return "invalid_cr_target"
    return ""


def _evaluate_bank(
    request: LlcResonantCapacitorDesignRequest,
    candidate: CapacitorCandidate,
    parallel_count: int,
    esr_ohm: float,
    esr_basis: str,
    volume_cm3: float,
    ambient_temp_c: float,
) -> LlcResonantCapacitorBankCandidate:
    bank_capacitance_f = parallel_count * candidate.capacitance_f
    capacitance_error_percent = 100.0 * (bank_capacitance_f - request.cr_target_f) / request.cr_target_f
    current_rms_per_cap_a = request.current_rms_a / parallel_count
    bank_esr_ohm = esr_ohm / parallel_count
    loss_w = (request.current_rms_a**2) * bank_esr_ohm
    loss_per_cap_w = loss_w / parallel_count
    voltage_utilization = _safe_ratio(request.required_voltage_rating_v, candidate.voltage_rating_dc_v)
    current_utilization = _safe_ratio(current_rms_per_cap_a, candidate.irms_rating_a)
    hotspot_c = None
    temperature_rise_c = None
    rejection_reason = ""
    warnings: list[str] = []
    if abs(capacitance_error_percent) > CAPACITANCE_ERROR_LIMIT_PERCENT:
        rejection_reason = "capacitance_error"
    elif candidate.voltage_rating_dc_v < request.required_voltage_rating_v:
        rejection_reason = "voltage_rating"
    elif candidate.irms_rating_a < current_rms_per_cap_a:
        rejection_reason = "current_rating"
    elif candidate.rth_hotspot_to_ambient_c_per_w > 0.0:
        temperature_rise_c = loss_per_cap_w * candidate.rth_hotspot_to_ambient_c_per_w
        hotspot_c = ambient_temp_c + temperature_rise_c
        if hotspot_c > candidate.hotspot_temp_max_c or hotspot_c - ambient_temp_c > candidate.self_heating_limit_c:
            rejection_reason = "thermal"
    else:
        warnings.append("Capacitor thermal hotspot is first-pass or unavailable.")
    if not rejection_reason and abs(capacitance_error_percent) > CAPACITANCE_WARNING_PERCENT:
        warnings.append("Cr capacitance error exceeds 5%; verify LLC gain and resonant frequency shift.")
    if hotspot_c is None:
        warnings.append("Capacitor thermal hotspot is first-pass or unavailable.")
    return LlcResonantCapacitorBankCandidate(
        design_id=f"Cr_{_sanitize(candidate.part_number)}_N{parallel_count}",
        part_number=candidate.part_number,
        manufacturer=candidate.manufacturer,
        series=candidate.series,
        application_category=candidate.application_category,
        capacitance_f=candidate.capacitance_f,
        capacitance_nF=candidate.capacitance_f * 1e9,
        capacitance_tolerance_percent=candidate.tolerance_percent,
        parallel_count=parallel_count,
        bank_capacitance_f=bank_capacitance_f,
        bank_capacitance_nF=bank_capacitance_f * 1e9,
        cr_target_f=request.cr_target_f,
        cr_target_nF=request.cr_target_nF,
        capacitance_error_percent=capacitance_error_percent,
        voltage_rating_v=candidate.voltage_rating_dc_v,
        required_voltage_rating_v=request.required_voltage_rating_v,
        voltage_utilization=voltage_utilization,
        current_rms_total_a=request.current_rms_a,
        current_rms_per_cap_a=current_rms_per_cap_a,
        ripple_current_rating_a=candidate.irms_rating_a,
        current_utilization=current_utilization,
        esr_ohm=esr_ohm,
        esr_basis=esr_basis,
        bank_esr_ohm=bank_esr_ohm,
        loss_w=loss_w,
        loss_per_cap_w=loss_per_cap_w,
        package_shape=candidate.package_shape,
        body_width_mm=candidate.body_width_mm,
        body_depth_mm=candidate.body_depth_mm,
        body_height_mm=candidate.body_height_mm,
        diameter_mm=candidate.diameter_mm,
        height_mm=candidate.height_mm,
        terminal_count=candidate.terminal_count,
        terminal_diameter_mm=candidate.terminal_diameter_mm,
        terminal_pitch_mm=candidate.terminal_pitch_mm,
        terminal_pitch_secondary_mm=candidate.lead_spacing_secondary_mm,
        terminal_type=candidate.terminal_type,
        ambient_c=ambient_temp_c,
        temperature_rise_c=temperature_rise_c,
        hotspot_c=hotspot_c,
        estimated_volume_m3=volume_cm3 * parallel_count * 1e-6,
        estimated_volume_cm3=volume_cm3 * parallel_count,
        warning=" ".join(warnings),
        rejection_reason=rejection_reason,
    )


def _resolve_esr(candidate: CapacitorCandidate, fs_basis_hz: float) -> tuple[float, str]:
    if candidate.rs_ohm > 0.0:
        return candidate.rs_ohm, "datasheet_esr"
    if candidate.esr_mohm is not None and candidate.esr_mohm > 0.0:
        return candidate.esr_mohm * 1e-3, "datasheet_esr"
    if candidate.tan_delta_0 > 0.0 and fs_basis_hz > 0.0 and candidate.capacitance_f > 0.0:
        return candidate.tan_delta_0 / (2.0 * math.pi * fs_basis_hz * candidate.capacitance_f), "df_estimated"
    return 0.0, ""


def _candidate_volume_cm3(candidate: CapacitorCandidate) -> float:
    if candidate.total_volume_cm3 is not None and candidate.total_volume_cm3 > 0.0:
        return candidate.total_volume_cm3
    if candidate.package_shape == "rectangular_box":
        width_mm = candidate.body_width_mm or candidate.diameter_mm
        depth_mm = candidate.body_depth_mm or candidate.diameter_mm
        height_mm = candidate.body_height_mm or candidate.height_mm
        return width_mm * depth_mm * height_mm / 1000.0
    if candidate.diameter_mm > 0.0 and candidate.height_mm > 0.0:
        radius_cm = 0.05 * candidate.diameter_mm
        height_cm = 0.1 * candidate.height_mm
        return math.pi * radius_cm * radius_cm * height_cm
    return 0.0


def _recommendation_key(candidate: LlcResonantCapacitorBankCandidate) -> tuple[float, float, float, float, float, int, str]:
    return (
        abs(candidate.capacitance_error_percent),
        candidate.voltage_utilization,
        candidate.current_utilization,
        candidate.loss_w,
        candidate.estimated_volume_cm3,
        candidate.parallel_count,
        candidate.design_id,
    )


def _extract_pareto_front(
    candidates: list[LlcResonantCapacitorBankCandidate],
) -> list[LlcResonantCapacitorBankCandidate]:
    feasible = [
        candidate
        for candidate in candidates
        if not candidate.rejection_reason
        and abs(candidate.capacitance_error_percent) <= CAPACITANCE_ERROR_LIMIT_PERCENT
    ]
    ordered = sorted(
        feasible,
        key=lambda candidate: (
            candidate.estimated_volume_cm3,
            candidate.loss_w,
            abs(candidate.capacitance_error_percent),
            candidate.parallel_count,
            candidate.design_id,
        ),
    )
    front: list[LlcResonantCapacitorBankCandidate] = []
    best_loss_w = math.inf
    tolerance_w = 1e-12
    for candidate in ordered:
        if candidate.loss_w >= best_loss_w - tolerance_w:
            continue
        front.append(replace(candidate, is_pareto=True))
        best_loss_w = candidate.loss_w
    return sorted(front, key=_pareto_sort_key)


def _select_representatives(
    feasible: list[LlcResonantCapacitorBankCandidate],
    pareto: list[LlcResonantCapacitorBankCandidate],
) -> tuple[
    list[LlcResonantCapacitorBankCandidate],
    list[LlcResonantCapacitorBankCandidate],
    LlcResonantCapacitorBankCandidate | None,
    LlcResonantCapacitorBankCandidate | None,
    LlcResonantCapacitorBankCandidate | None,
    LlcResonantCapacitorBankCandidate | None,
    list[LlcResonantCapacitorBankCandidate],
    list[str],
]:
    if not pareto:
        return feasible, pareto, None, None, None, None, [], []

    min_volume = min(pareto, key=_min_volume_key)
    min_loss = min(pareto, key=_min_loss_key)
    compromise = min(pareto, key=_compromise_key_factory(pareto))
    recommended = _select_recommended(compromise, pareto)
    reason_by_role = {
        "min-volume": "minimum estimated resonant capacitor bank volume on Pareto front",
        "min-loss": "minimum total resonant capacitor bank loss on Pareto front",
        "compromise": "closest Pareto candidate to normalized volume-loss ideal point",
        "recommended": "recommended from LLC resonant capacitor Pareto compromise using normalized volume-loss distance and Cr-error tie-break",
    }
    role_by_id: dict[str, list[str]] = {}
    for role, candidate in (
        ("min-volume", min_volume),
        ("min-loss", min_loss),
        ("compromise", compromise),
        ("recommended", recommended),
    ):
        if candidate is None:
            continue
        role_by_id.setdefault(candidate.design_id, []).append(role)

    def mark(candidate: LlcResonantCapacitorBankCandidate, *, is_pareto: bool) -> LlcResonantCapacitorBankCandidate:
        roles = role_by_id.get(candidate.design_id, [])
        reasons = [reason_by_role[role] for role in roles]
        return replace(
            candidate,
            is_pareto=is_pareto,
            representative_role=", ".join(roles),
            representative_reason=" | ".join(reasons),
            recommended_flag="recommended" in roles,
        )

    feasible_by_id = {candidate.design_id: mark(candidate, is_pareto=False) for candidate in feasible}
    pareto_by_id = {candidate.design_id: mark(candidate, is_pareto=True) for candidate in pareto}
    for candidate_id, candidate in list(feasible_by_id.items()):
        if candidate_id in pareto_by_id:
            feasible_by_id[candidate_id] = pareto_by_id[candidate_id]

    labeled_feasible = [feasible_by_id[candidate.design_id] for candidate in feasible]
    labeled_pareto = [pareto_by_id[candidate.design_id] for candidate in pareto]
    chosen = _dedupe_candidates(
        [
            pareto_by_id[candidate.design_id]
            for candidate in (recommended, min_volume, min_loss, compromise)
            if candidate is not None
        ]
    )
    notes = [
        "Pareto front minimizes estimated resonant capacitor bank volume and total bank loss.",
        "Recommended candidate defaults to the normalized volume-loss compromise with Cr-error tie-break.",
    ]
    return (
        labeled_feasible,
        labeled_pareto,
        pareto_by_id.get(recommended.design_id) if recommended is not None else None,
        pareto_by_id.get(min_volume.design_id) if min_volume is not None else None,
        pareto_by_id.get(min_loss.design_id) if min_loss is not None else None,
        pareto_by_id.get(compromise.design_id) if compromise is not None else None,
        chosen,
        notes,
    )


def _select_recommended(
    compromise: LlcResonantCapacitorBankCandidate,
    pareto: list[LlcResonantCapacitorBankCandidate],
) -> LlcResonantCapacitorBankCandidate:
    if abs(compromise.capacitance_error_percent) <= CAPACITANCE_WARNING_PERCENT:
        return compromise
    key = _compromise_key_factory(pareto)
    compromise_distance = key(compromise)[0]
    comparable_limit = compromise_distance * 1.10 + 0.02
    low_error = [
        candidate
        for candidate in pareto
        if abs(candidate.capacitance_error_percent) <= CAPACITANCE_WARNING_PERCENT
        and key(candidate)[0] <= comparable_limit
    ]
    return min(low_error, key=key) if low_error else compromise


def _min_volume_key(candidate: LlcResonantCapacitorBankCandidate) -> tuple[float, float, float, float, int, str]:
    return (
        candidate.estimated_volume_cm3,
        candidate.loss_w,
        abs(candidate.capacitance_error_percent),
        _hotspot_sort_value(candidate),
        candidate.parallel_count,
        candidate.design_id,
    )


def _min_loss_key(candidate: LlcResonantCapacitorBankCandidate) -> tuple[float, float, float, float, int, str]:
    return (
        candidate.loss_w,
        candidate.estimated_volume_cm3,
        abs(candidate.capacitance_error_percent),
        _hotspot_sort_value(candidate),
        candidate.parallel_count,
        candidate.design_id,
    )


def _compromise_key_factory(candidates: list[LlcResonantCapacitorBankCandidate]):
    volume_values = [candidate.estimated_volume_cm3 for candidate in candidates]
    loss_values = [candidate.loss_w for candidate in candidates]

    def key(candidate: LlcResonantCapacitorBankCandidate) -> tuple[float, float, float, float, int, str]:
        distance = math.hypot(
            _normalize(candidate.estimated_volume_cm3, volume_values),
            _normalize(candidate.loss_w, loss_values),
        )
        return (
            distance,
            abs(candidate.capacitance_error_percent),
            candidate.voltage_utilization,
            candidate.current_utilization,
            candidate.parallel_count,
            candidate.design_id,
        )

    return key


def _pareto_sort_key(candidate: LlcResonantCapacitorBankCandidate) -> tuple[float, float, float, int, str]:
    return (
        candidate.estimated_volume_cm3,
        candidate.loss_w,
        abs(candidate.capacitance_error_percent),
        candidate.parallel_count,
        candidate.design_id,
    )


def _normalize(value: float, values: list[float]) -> float:
    low = min(values)
    high = max(values)
    if high <= low:
        return 0.0
    return (value - low) / (high - low)


def _hotspot_sort_value(candidate: LlcResonantCapacitorBankCandidate) -> float:
    return candidate.hotspot_c if candidate.hotspot_c is not None else math.inf


def _dedupe_candidates(
    candidates: list[LlcResonantCapacitorBankCandidate],
) -> list[LlcResonantCapacitorBankCandidate]:
    deduped: list[LlcResonantCapacitorBankCandidate] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate.design_id in seen:
            continue
        seen.add(candidate.design_id)
        deduped.append(candidate)
    return deduped


def _many_df_estimated(candidates: list[LlcResonantCapacitorBankCandidate]) -> bool:
    if not candidates:
        return False
    df_count = sum(1 for candidate in candidates if candidate.esr_basis == "df_estimated")
    return df_count >= 10 and df_count / len(candidates) >= 0.25


def _write_feasible_csv(path: Path, candidates: list[LlcResonantCapacitorBankCandidate]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        for candidate in candidates:
            writer.writerow({field: getattr(candidate, field) for field in _CSV_FIELDS})


def _write_pareto_plot(
    path: Path,
    feasible: list[LlcResonantCapacitorBankCandidate],
    pareto: list[LlcResonantCapacitorBankCandidate],
    chosen: list[LlcResonantCapacitorBankCandidate],
) -> dict[str, object]:
    volume_limit = _plot_limit([candidate.estimated_volume_cm3 for candidate in feasible])
    loss_limit = _plot_limit([candidate.loss_w for candidate in feasible])
    always_plot_ids = {candidate.design_id for candidate in [*pareto, *chosen]}
    background = [
        candidate
        for candidate in feasible
        if (
            candidate.estimated_volume_cm3 <= volume_limit
            and candidate.loss_w <= loss_limit
        )
        or candidate.design_id in always_plot_ids
    ]
    hidden_count = max(len(feasible) - len({candidate.design_id for candidate in background}), 0)
    figure = Figure(figsize=(7.2, 4.8), dpi=120)
    axis = figure.add_subplot(111)
    axis.scatter(
        [candidate.estimated_volume_cm3 for candidate in background],
        [candidate.loss_w for candidate in background],
        s=18,
        alpha=0.35,
        color="#7f7f7f",
        label="feasible",
    )
    if pareto:
        ordered = sorted(pareto, key=lambda candidate: candidate.estimated_volume_cm3)
        axis.plot(
            [candidate.estimated_volume_cm3 for candidate in ordered],
            [candidate.loss_w for candidate in ordered],
            color="black",
            linewidth=1.2,
            label="Pareto front",
        )
    markers = {
        "recommended": ("*", "#ff7f0e"),
        "min-volume": ("s", "#d62728"),
        "min-loss": ("D", "#2ca02c"),
        "compromise": ("P", "#9467bd"),
    }
    for candidate in chosen:
        role = (candidate.representative_role.split(", ")[0] or "chosen").strip()
        marker, color = markers.get(role, ("o", "#1f77b4"))
        axis.scatter(
            [candidate.estimated_volume_cm3],
            [candidate.loss_w],
            s=105,
            marker=marker,
            color=color,
            edgecolor="black",
            linewidth=0.7,
            label=candidate.representative_role or role,
            zorder=5,
        )
    axis.set_title("LLC Resonant Capacitor Pareto Front")
    axis.set_xlabel("Estimated resonant capacitor bank volume (cm^3)")
    axis.set_ylabel("Total resonant capacitor bank loss (W)")
    axis.set_xlim(left=0.0, right=volume_limit * 1.05 if volume_limit > 0.0 else None)
    axis.set_ylim(bottom=0.0, top=loss_limit * 1.05 if loss_limit > 0.0 else None)
    axis.grid(True, alpha=0.25)
    handles, labels = axis.get_legend_handles_labels()
    deduped: dict[str, object] = {}
    for handle, label in zip(handles, labels):
        deduped.setdefault(label, handle)
    axis.legend(deduped.values(), deduped.keys(), loc="best", fontsize=8)
    figure.tight_layout()
    figure.savefig(path)
    figure.clear()
    return {
        "plotted_feasible_background_points": len(background),
        "hidden_feasible_outliers_png_only": hidden_count,
        "volume_plot_limit_cm3": volume_limit,
        "loss_plot_limit_w": loss_limit,
        "full_feasible_csv_unfiltered": True,
        "pareto_chosen_candidates_always_plotted": True,
    }


def _plot_limit(values: list[float]) -> float:
    finite = sorted(value for value in values if math.isfinite(value) and value >= 0.0)
    if not finite:
        return 0.0
    index = min(int(0.95 * (len(finite) - 1)), len(finite) - 1)
    return max(finite[index], finite[0])


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0.0:
        return math.inf
    return numerator / denominator


def _sanitize(value: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in str(value))
    return safe.strip("_") or "candidate"


def _empty_rejection_counts() -> dict[str, int]:
    return {key: 0 for key in _REJECTION_KEYS}


def _empty_part_rejection_counts() -> dict[str, int]:
    return {
        "missing_voltage_rating": 0,
        "missing_current_rating": 0,
        "missing_esr_or_df": 0,
        "missing_volume": 0,
        "unsupported_application": 0,
    }


def _empty_bank_rejection_counts() -> dict[str, int]:
    return {
        "capacitance_error": 0,
        "voltage_rating": 0,
        "current_rating": 0,
        "thermal": 0,
    }


def _nearest_brackets(
    candidates: list[LlcResonantCapacitorBankCandidate],
    target_f: float,
) -> tuple[LlcResonantCapacitorBankCandidate | None, LlcResonantCapacitorBankCandidate | None]:
    lower = [candidate for candidate in candidates if candidate.bank_capacitance_f <= target_f]
    upper = [candidate for candidate in candidates if candidate.bank_capacitance_f >= target_f]
    nearest_lower = max(lower, key=lambda candidate: (candidate.bank_capacitance_f, -candidate.parallel_count), default=None)
    nearest_upper = min(upper, key=lambda candidate: (candidate.bank_capacitance_f, candidate.parallel_count), default=None)
    return nearest_lower, nearest_upper


def _bank_label(candidate: LlcResonantCapacitorBankCandidate | None) -> str:
    if candidate is None:
        return "-"
    return f"{candidate.part_number} / {candidate.series} / N={candidate.parallel_count}"
