"""First-pass split-link and neutral-point checks for the NPC inverter."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from ..models.capacitor import (
    CapacitorSelectionEntry,
    CapacitorSideResult,
    NpcCapacitorBankDesign,
    NpcCapacitorDesignResult,
    NpcMidpointScenario,
)
from ..models.design_report import DesignReport

NPC_TOPOLOGY_ID = "three_phase_three_level_npc_inverter"
BASELINE_PART_NUMBER = "B43705A9568M600"
BASELINE_CAPACITANCE_F = 5.6e-3
BASELINE_CAPACITOR_VOLUME_L = 0.4650020260901885
EQUALIZER_RESISTANCE_OHM = 100_000.0
EQUALIZER_POWER_RATING_W = 3.0
EQUALIZER_VOLTAGE_RATING_V = 500.0
FILM_CAPACITANCE_PER_LEG_F = 10e-6
FILM_VOLTAGE_RATING_V = 1_000.0
PRECHARGE_RESISTANCE_OHM = 10_000.0
SAFE_DISCHARGE_VOLTAGE_V = 60.0


def build_npc_capacitor_design(
    report: DesignReport,
    upper_side: CapacitorSideResult | None,
    lower_side: CapacitorSideResult | None,
    output_dir: str | Path,
) -> NpcCapacitorDesignResult:
    """Build and persist a deterministic analytical NPC capacitor audit."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    upper = _build_bank(report, "upper", upper_side)
    lower = _build_bank(report, "lower", lower_side)
    if upper is None or lower is None:
        result = NpcCapacitorDesignResult(
            status="not_evaluated",
            notes=["NPC capacitor audit requires recommended upper and lower split-link banks."],
            warnings=["NPC capacitor audit was not evaluated because one split-link recommendation is unavailable."],
        )
        return _write_result(result, output_path)

    scenarios = _build_scenarios(report, upper, lower)
    worst = max(scenarios, key=lambda item: item.midpoint_deviation_ratio, default=None)
    total_volume_l = upper.capacitor_count * _entry_volume_l(upper_side.recommended) + lower.capacitor_count * _entry_volume_l(lower_side.recommended)
    film_volume_l = 0.06
    checks = {
        "midpoint_deviation": all(item.pass_fail == "pass" for item in scenarios),
        "upper_bank": all(upper.checks.values()),
        "lower_bank": all(lower.checks.values()),
        "volume_target": total_volume_l + film_volume_l <= 1.86 * 1.10,
    }
    result = NpcCapacitorDesignResult(
        status="pass" if all(checks.values()) else "conditional",
        target_midpoint_deviation_ratio=0.02,
        upper_bank=upper,
        lower_bank=lower,
        baseline_total_volume_l=4.0 * BASELINE_CAPACITOR_VOLUME_L,
        installed_total_volume_l=total_volume_l,
        film_decoupling_total_volume_l=film_volume_l,
        total_design_volume_l=total_volume_l + film_volume_l,
        scenarios=scenarios,
        worst_midpoint_deviation_v=worst.midpoint_deviation_v if worst else 0.0,
        worst_midpoint_deviation_ratio=worst.midpoint_deviation_ratio if worst else 0.0,
        notes=[
            "NPC capacitor audit is a first-pass analytical/proxy model; closed-loop neutral-point control and hardware parasitics are not modeled.",
            "B43705A9568M600 is retained as the 2S baseline reference; the installed recommendation remains traceable to the capacitor selector.",
            "B43705 has typical ESR data but no normalized ESRmax or endurance row; ESR is doubled as a conservative hot-temperature screening value and life is an engineering estimate.",
            "Film decoupling is allocated as one 10 uF, 1 kV class bank per bridge leg, three legs total; select the final pulse-rated part from a verified datasheet.",
            "Precharge uses a 10 kOhm resistor and is a first-pass energy/time check; contactor, fuse, resistor pulse SOA, and inrush control require hardware validation.",
        ],
        warnings=[
            "Midpoint balance remains a proxy until the NPC switching redundancy, dead-time, current direction, and closed-loop balancing controller are simulated together.",
        ],
    )
    return _write_result(result, output_path)


def _build_bank(report: DesignReport, side: str, side_result: CapacitorSideResult | None) -> NpcCapacitorBankDesign | None:
    entry = side_result.recommended if side_result is not None else None
    if entry is None:
        return None
    candidate = entry.candidate
    metadata = report.candidate.metadata if report.candidate is not None else {}
    vdc_max = _positive(metadata.get("vdc_max_v"), 750.0)
    vdc_nom = _positive(metadata.get("vdc_nom_v"), 700.0)
    ambient = _positive(metadata.get("ambient_temp_max_c"), 45.0)
    esr_typ = _positive(candidate.esr_typ_ohm, candidate.rs_ohm)
    esr_max = _positive(candidate.esr_max_ohm, 0.0)
    conservative_esr = max(esr_max, 2.0 * esr_typ)
    esr_basis = "datasheet ESRmax" if esr_max > 0.0 else "2.0 x datasheet typical ESR; hot-temperature conservative proxy"
    per_cap_current = max(float(entry.capacitor_current_rms_per_cap_a), 0.0)
    p_esr = per_cap_current * per_cap_current * conservative_esr
    hotspot = ambient + p_esr * float(candidate.rth_hotspot_to_ambient_c_per_w)
    life_base_h = _positive(candidate.endurance_hours, 5_000.0)
    life_reference = "datasheet endurance" if candidate.endurance_hours else "5,000 h at 85 C engineering estimate from the source family; Arrhenius 10 C doubling"
    expected_life = life_base_h * (2.0 ** max((85.0 - hotspot) / 10.0, -10.0))
    nominal_cap_v = 0.5 * vdc_nom
    worst_cap_v = 0.5 * vdc_max * (1.0 + candidate.tolerance_percent / 100.0)
    equalizer_power = worst_cap_v * worst_cap_v / EQUALIZER_RESISTANCE_OHM
    discharge_tau = EQUALIZER_RESISTANCE_OHM * float(candidate.capacitance_f)
    discharge_time = discharge_tau * math.log(max(worst_cap_v / SAFE_DISCHARGE_VOLTAGE_V, 1.0))
    ripple_rating = _positive(candidate.ripple_current_rated_a, candidate.irms_rating_a)
    surge_rating = max(10.0 * ripple_rating, 1.0)
    surge_peak = max(3.0 * per_cap_current, _positive(candidate.peak_current_a, 0.0))
    bank_voltage = float(entry.bank_voltage_rating_dc_v)
    checks = {
        "voltage": bank_voltage >= 1.15 * vdc_max / 2.0,
        "equalizer_power": equalizer_power <= EQUALIZER_POWER_RATING_W,
        "equalizer_voltage": EQUALIZER_VOLTAGE_RATING_V >= worst_cap_v,
        "hotspot": hotspot <= float(candidate.hotspot_temp_max_c),
        "life": expected_life >= 20_000.0,
        "ripple_current": per_cap_current <= ripple_rating,
        "surge_current": surge_peak <= surge_rating,
        "discharge": discharge_time <= 2_000.0,
    }
    return NpcCapacitorBankDesign(
        side=side,
        part_number=candidate.part_number,
        series_count=int(entry.series_count),
        parallel_count=int(entry.parallel_count),
        capacitor_count=int(entry.total_capacitor_count),
        capacitance_per_cap_f=float(candidate.capacitance_f),
        bank_capacitance_f=float(entry.equivalent_capacitance_f),
        bank_voltage_rating_v=bank_voltage,
        nominal_capacitor_voltage_v=nominal_cap_v,
        worst_case_capacitor_voltage_v=worst_cap_v,
        conservative_esr_ohm=conservative_esr,
        conservative_esr_basis=esr_basis,
        capacitor_hotspot_c=hotspot,
        expected_life_hours=expected_life,
        ripple_current_rms_a=per_cap_current,
        ripple_current_rating_a=ripple_rating,
        ripple_current_margin_ratio=_ratio(ripple_rating, per_cap_current),
        surge_current_peak_a=surge_peak,
        surge_current_rating_a=surge_rating,
        surge_current_margin_ratio=_ratio(surge_rating, surge_peak),
        equalizer_resistance_ohm=EQUALIZER_RESISTANCE_OHM,
        equalizer_power_per_cap_w=equalizer_power,
        equalizer_total_loss_w=equalizer_power * int(entry.total_capacitor_count),
        equalizer_voltage_rating_v=EQUALIZER_VOLTAGE_RATING_V,
        equalizer_tolerance_percent=1.0,
        discharge_time_constant_s=discharge_tau,
        discharge_to_safe_voltage_s=discharge_time,
        film_capacitance_per_leg_f=FILM_CAPACITANCE_PER_LEG_F,
        film_total_capacitance_f=3.0 * FILM_CAPACITANCE_PER_LEG_F,
        film_voltage_rating_v=FILM_VOLTAGE_RATING_V,
        film_ripple_current_per_leg_a=max(0.25 * surge_peak, 1.0),
        precharge_resistance_ohm=PRECHARGE_RESISTANCE_OHM,
        precharge_current_peak_a=vdc_max / PRECHARGE_RESISTANCE_OHM,
        precharge_energy_j=0.5 * float(entry.equivalent_capacitance_f) * vdc_max * vdc_max,
        precharge_time_to_95_percent_s=3.0 * PRECHARGE_RESISTANCE_OHM * float(entry.equivalent_capacitance_f),
        checks=checks,
        notes=[f"Life basis: {life_reference}."],
    )


def _build_scenarios(report: DesignReport, upper: NpcCapacitorBankDesign, lower: NpcCapacitorBankDesign) -> list[NpcMidpointScenario]:
    metadata = report.candidate.metadata if report.candidate is not None else {}
    waveform = report.waveform
    wave_meta = waveform.metadata if waveform is not None and isinstance(waveform.metadata, dict) else {}
    base_waveforms = wave_meta.get("three_phase_npc_pd_spwm_waveforms", {})
    upper_v = list(base_waveforms.get("upper_dc_link_voltage_v", [])) if isinstance(base_waveforms, dict) else []
    lower_v = list(base_waveforms.get("lower_dc_link_voltage_v", [])) if isinstance(base_waveforms, dict) else []
    base_deviation = abs(_mean(upper_v) - _mean(lower_v))
    upper_ripple = _peak_to_peak(upper_v)
    lower_ripple = _peak_to_peak(lower_v)
    vdc = _positive(metadata.get("vdc_nom_v"), 700.0)
    scenarios = [
        ("rated", 1.0, _positive(metadata.get("power_factor"), 1.0), 1.0, 0.0, 0.0),
        ("load_variation", 0.05, _positive(metadata.get("power_factor"), 1.0), 0.95, 0.0, 0.0),
        ("pf_variation", 1.0, _positive(metadata.get("power_factor_min"), 0.8), 1.0, 0.0, 0.0),
        ("modulation_variation", 1.0, _positive(metadata.get("power_factor"), 1.0), 0.85, 0.0, 0.0),
        ("capacitor_mismatch", 1.0, _positive(metadata.get("power_factor"), 1.0), 1.0, 0.20, 0.0),
        ("three_phase_imbalance", 1.0, _positive(metadata.get("power_factor"), 1.0), 1.0, 0.10, 0.10),
    ]
    results: list[NpcMidpointScenario] = []
    for scenario_id, load, pf, modulation, mismatch, phase_imbalance in scenarios:
        stress_factor = load * (1.0 + (1.0 - min(abs(pf), 1.0))) * (1.0 + abs(1.0 - modulation))
        deviation = base_deviation + 0.5 * vdc * (0.08 * mismatch + 0.04 * phase_imbalance) * stress_factor
        upper_mean = 0.5 * vdc + 0.5 * deviation
        lower_mean = 0.5 * vdc - 0.5 * deviation
        ratio = deviation / max(vdc, 1e-9)
        results.append(NpcMidpointScenario(
            scenario_id=scenario_id,
            load_ratio=load,
            power_factor=pf,
            modulation_index_ratio=modulation,
            capacitor_mismatch_ratio=mismatch,
            phase_imbalance_ratio=phase_imbalance,
            upper_voltage_v=upper_mean,
            lower_voltage_v=lower_mean,
            midpoint_deviation_v=deviation,
            midpoint_deviation_ratio=ratio,
            upper_ripple_vpp=upper_ripple * stress_factor,
            lower_ripple_vpp=lower_ripple * stress_factor,
            pass_fail="pass" if ratio <= 0.02 and upper_mean <= upper.worst_case_capacitor_voltage_v and lower_mean <= lower.worst_case_capacitor_voltage_v else "fail",
            basis="NPC PD-SPWM waveform ripple plus deterministic load/PF/modulation/mismatch/phase-imbalance proxy; not closed-loop hardware simulation",
        ))
    return results


def _write_result(result: NpcCapacitorDesignResult, output_dir: Path) -> NpcCapacitorDesignResult:
    json_path = output_dir / "npc_split_link_capacitor_design.json"
    csv_path = output_dir / "npc_midpoint_balance_scenarios.csv"
    payload = _jsonable(result)
    json_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True), encoding="ascii")
    with csv_path.open("w", newline="", encoding="ascii") as handle:
        rows = payload.get("scenarios", [])
        fieldnames = list(rows[0]) if rows else ["scenario_id", "pass_fail"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return replace(result, artifact_paths=[str(json_path), str(csv_path)])


def _jsonable(result: NpcCapacitorDesignResult) -> dict[str, Any]:
    return asdict(result)


def _entry_volume_l(entry: CapacitorSelectionEntry | None) -> float:
    return float(entry.candidate.total_volume_cm3 or 0.0) / 1000.0 if entry is not None else 0.0


def _positive(value: object, fallback: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return fallback
    return result if result > 0.0 else fallback


def _ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator > 0.0 else math.inf


def _peak_to_peak(values: list[float]) -> float:
    return max(values) - min(values) if values else 0.0


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
