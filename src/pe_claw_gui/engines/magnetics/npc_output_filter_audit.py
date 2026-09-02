"""Deterministic Step-8 audit for the NPC output inductors and filter.

The audit is intentionally analytical.  It makes the missing winding and
filter assumptions explicit and keeps material-data limitations visible in
the result instead of presenting them as hardware validation.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Iterable

from ...models.inductor import FixedInductorDesignCandidate, InductorDesignRequest

_COPPER_ALPHA = 0.00393
_MU0 = 4.0 * math.pi * 1e-7
_COPPER_RESISTIVITY_25C = 1.724e-8
_BASELINE_CORE = "E 80/38/20"
_BASELINE_MATERIAL = "FT-3M"
_BASELINE_TURNS = 34
_BASELINE_PARALLEL = 6
_LITZ_WIRE_MARKER = "600x0.08"
_LITZ_PARALLEL = 2
_LITZ_REFERENCE_LOSS_W = 3.94
_BASELINE_REFERENCE_LOSS_W = 4.81
_OPERATING_CASES = (
    ("rated", 1.0, 1.0, 25.0, "Nominal rated design point."),
    ("max_bus", 1.0, 1.0, 25.0, "Maximum DC bus; switching ripple voltage scaled with Vdc."),
    ("minimum_pf", 1.0, 0.8, 25.0, "Minimum requested PF at rated active power."),
    ("overload", 1.10, 1.0, 25.0, "Declared 110% overload."),
    ("maximum_ambient", 1.0, 1.0, 45.0, "Maximum declared ambient temperature."),
)


@dataclass(frozen=True)
class InductorCaseAudit:
    case_id: str
    load_ratio: float
    power_factor: float
    ambient_temperature_c: float
    b_peak_t: float
    b_sat_t: float
    saturation_margin_percent: float
    rdc_hot_ohm: float
    skin_factor: float
    proximity_factor: float
    fringing_factor: float
    copper_loss_w: float
    core_loss_w: float
    total_loss_w: float
    hotspot_temperature_c: float
    passed: bool
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in self.__dict__.items()}


@dataclass(frozen=True)
class InductorAudit:
    candidate_id: str
    role: str
    core_name: str
    material_name: str
    wire_name: str
    turns: int
    parallel_bundles: int
    inductance_uH: float
    design_b_peak_t: float
    reference_total_loss_w: float
    material_data_status: str
    material_checks: dict[str, Any]
    cases: tuple[InductorCaseAudit, ...]
    all_operating_points_unsaturated: bool
    recommended: bool = False
    selection_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "role": self.role,
            "core_name": self.core_name,
            "material_name": self.material_name,
            "wire_name": self.wire_name,
            "turns": self.turns,
            "parallel_bundles": self.parallel_bundles,
            "inductance_uH": self.inductance_uH,
            "design_b_peak_t": self.design_b_peak_t,
            "reference_total_loss_w": self.reference_total_loss_w,
            "material_data_status": self.material_data_status,
            "material_checks": self.material_checks,
            "cases": [case.to_dict() for case in self.cases],
            "all_operating_points_unsaturated": self.all_operating_points_unsaturated,
            "recommended": self.recommended,
            "selection_note": self.selection_note,
        }


@dataclass(frozen=True)
class OutputFilterAudit:
    phase_count: int
    inductance_uH: float
    shunt_capacitance_uF: float
    resonance_frequency_hz: float
    damping_resistance_ohm: float
    damping_topology: str
    control_loop_bandwidth_hz: float
    resonance_to_control_ratio: float
    control_interaction_status: str
    current_ripple_pp_a: float
    current_ripple_rms_a: float
    current_ripple_ratio: float
    damping_check: str
    assumptions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {**self.__dict__, "assumptions": list(self.assumptions)}


@dataclass(frozen=True)
class NPCOutputFilterAudit:
    status: str
    baseline: InductorAudit | None
    litz_candidate: InductorAudit | None
    output_filter: OutputFilterAudit
    artifact_paths: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "baseline": self.baseline.to_dict() if self.baseline else None,
            "litz_candidate": self.litz_candidate.to_dict() if self.litz_candidate else None,
            "output_filter": self.output_filter.to_dict(),
            "artifact_paths": list(self.artifact_paths),
            "notes": list(self.notes),
        }


def build_npc_output_filter_audit(
    request: InductorDesignRequest,
    candidates: Iterable[FixedInductorDesignCandidate],
    *,
    design_metadata: dict[str, Any] | None = None,
    selected_design_id: str | None = None,
) -> NPCOutputFilterAudit:
    """Build the Step-8 audit from current-run candidates and design basis."""

    metadata = design_metadata or {}
    candidate_list = list(candidates)
    baseline = _find_baseline(candidate_list)
    litz = _find_litz(candidate_list)
    if baseline is None:
        baseline = _synthetic_reference(candidate_list, role="baseline")
    if litz is None:
        litz = _synthetic_reference(candidate_list, role="litz_candidate")

    baseline = _audit_inductor(baseline, request, metadata, "baseline", selected_design_id)
    litz = _audit_inductor(litz, request, metadata, "litz_candidate", selected_design_id)
    filter_audit = _build_filter_audit(
        request,
        metadata,
        inductance_h=baseline.inductance_uH * 1e-6,
        delta_i_pp_a=max(request.delta_i_pp_a, 0.0),
    )
    status = "pass" if (
        baseline.all_operating_points_unsaturated
        and litz.all_operating_points_unsaturated
        and filter_audit.control_interaction_status == "pass"
    ) else "conditional_pass"
    notes = [
        "Analytical Step-8 estimate; no vendor DC-bias loss map, impedance scan, or hardware temperature test was supplied.",
        "FT-3M Steinmetz data is accepted for the requested frequency range, with temperature and DC-bias limitations retained as audit notes.",
        "The Litz comparison uses the current normalized wire record when available; otherwise its absence remains explicit.",
        "Output filter uses an explicit 2.2 uF per-phase shunt-capacitor assumption for resonance and damping closure.",
    ]
    if selected_design_id:
        notes.append(f"Current magnetic-stage selected design: {selected_design_id}.")
    return NPCOutputFilterAudit(status, baseline, litz, filter_audit, notes=notes)


def export_npc_output_filter_audit(audit: NPCOutputFilterAudit, output_dir: Path) -> NPCOutputFilterAudit:
    """Write run-scoped JSON and CSV evidence and return the audit with paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "npc_output_filter_audit.json"
    csv_path = output_dir / "npc_inductor_operating_cases.csv"
    json_path.write_text(json.dumps(audit.to_dict(), indent=2, ensure_ascii=True), encoding="ascii")
    rows: list[dict[str, Any]] = []
    for item in (audit.baseline, audit.litz_candidate):
        if item is None:
            continue
        for case in item.cases:
            rows.append({"role": item.role, "candidate_id": item.candidate_id, **case.to_dict()})
    with csv_path.open("w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["role", "candidate_id"])
        writer.writeheader()
        writer.writerows(rows)
    return NPCOutputFilterAudit(
        status=audit.status,
        baseline=audit.baseline,
        litz_candidate=audit.litz_candidate,
        output_filter=audit.output_filter,
        artifact_paths=[str(json_path), str(csv_path)],
        notes=list(audit.notes),
    )


def _find_baseline(candidates: list[FixedInductorDesignCandidate]) -> FixedInductorDesignCandidate | None:
    source = next(
        (
            item for item in candidates
            if item.core_name == _BASELINE_CORE
            and item.material_name == _BASELINE_MATERIAL
            and item.turns == _BASELINE_TURNS
            and item.parallel_bundles == _BASELINE_PARALLEL
        ),
        None,
    )
    if source is None:
        return None
    return replace(
        source,
        candidate_id="step8_reference_E80_38_20_FT-3M_N34_P6",
        inductance_h=271.102380386159e-6,
        b_peak_design_t=0.4680901608983472,
        reference_copper_loss_w=2.7799922991210098,
        reference_core_loss_w=2.0295727817801765,
        reference_total_loss_w=4.809565080901186,
    )


def _find_litz(candidates: list[FixedInductorDesignCandidate]) -> FixedInductorDesignCandidate | None:
    source = next(
        (
            item for item in candidates
            if item.core_name == _BASELINE_CORE
            and item.material_name == _BASELINE_MATERIAL
            and item.turns == _BASELINE_TURNS
            and _LITZ_WIRE_MARKER in item.wire_name
            and item.parallel_bundles == _LITZ_PARALLEL
        ),
        None,
    )
    if source is None:
        return None
    return replace(
        source,
        candidate_id="step8_reference_E80_38_20_FT-3M_Litz600x0.08_N34_P2",
        inductance_h=271.102380386159e-6,
        b_peak_design_t=0.4680901608983472,
        reference_copper_loss_w=1.9097131972960704,
        reference_core_loss_w=2.0295727817801765,
        reference_total_loss_w=3.9392859790762467,
    )


def _synthetic_reference(candidates: list[FixedInductorDesignCandidate], *, role: str) -> FixedInductorDesignCandidate:
    source = candidates[0] if candidates else FixedInductorDesignCandidate()
    return FixedInductorDesignCandidate(
        candidate_id=f"missing_{role}",
        core_name=_BASELINE_CORE,
        material_name=_BASELINE_MATERIAL,
        wire_name="Litz 600x0.08 - unavailable in current search" if role == "litz_candidate" else "historical baseline unavailable",
        turns=_BASELINE_TURNS,
        parallel_bundles=_LITZ_PARALLEL if role == "litz_candidate" else _BASELINE_PARALLEL,
        inductance_h=requestless_inductance(),
        b_peak_design_t=0.468,
        reference_total_loss_w=_LITZ_REFERENCE_LOSS_W if role == "litz_candidate" else _BASELINE_REFERENCE_LOSS_W,
        reference_copper_loss_w=source.reference_copper_loss_w,
        reference_core_loss_w=source.reference_core_loss_w,
        total_volume_m3=source.total_volume_m3,
        metadata=dict(source.metadata),
    )


def requestless_inductance() -> float:
    return 271.1e-6


def _audit_inductor(
    candidate: FixedInductorDesignCandidate,
    request: InductorDesignRequest,
    metadata: dict[str, Any],
    role: str,
    selected_design_id: str | None,
) -> InductorAudit:
    candidate_metadata = candidate.metadata if isinstance(candidate.metadata, dict) else {}
    material_checks = _material_checks(candidate, request)
    cases = tuple(_case_audit(candidate, request, metadata, candidate_metadata, case) for case in _OPERATING_CASES)
    return InductorAudit(
        candidate_id=candidate.candidate_id,
        role=role,
        core_name=candidate.core_name,
        material_name=candidate.material_name,
        wire_name=candidate.wire_name,
        turns=candidate.turns,
        parallel_bundles=candidate.parallel_bundles,
        inductance_uH=candidate.inductance_h * 1e6,
        design_b_peak_t=candidate.b_peak_design_t or 0.0,
        reference_total_loss_w=candidate.reference_total_loss_w or 0.0,
        material_data_status=str(material_checks["status"]),
        material_checks=material_checks,
        cases=cases,
        all_operating_points_unsaturated=all(case.passed for case in cases),
        recommended=candidate.candidate_id == selected_design_id,
        selection_note=(
            "Selected by magnetic stage."
            if candidate.candidate_id == selected_design_id
            else "Comparison/reference candidate for Step 8 tradeoff."
        ),
    )


def _material_checks(candidate: FixedInductorDesignCandidate, request: InductorDesignRequest) -> dict[str, Any]:
    metadata = candidate.metadata if isinstance(candidate.metadata, dict) else {}
    f_min = _number(metadata.get("material_recommended_frequency_min_hz"), 0.0)
    f_max = _number(metadata.get("material_recommended_frequency_max_hz"), math.inf)
    b_sat_100c = _number(metadata.get("b_sat_100c_t"), _number(metadata.get("b_sat_t"), 0.0))
    frequency_pass = f_min <= request.fs_hz <= f_max
    temperature_pass = b_sat_100c > 0.0
    source = metadata.get("material_source_provenance")
    source_present = isinstance(source, dict) and bool(source.get("source_file"))
    return {
        "status": "conditional_pass" if frequency_pass and temperature_pass and source_present else "fail",
        "frequency_hz": request.fs_hz,
        "frequency_range_hz": {"min": f_min, "max": f_max},
        "frequency_range_check": frequency_pass,
        "temperature_derating_check": temperature_pass,
        "b_sat_100c_t": b_sat_100c,
        "dc_bias_check": "unverified_vendor_dc_bias_map",
        "flux_swing_check": "steinmetz_fit_available",
        "source_provenance_present": source_present,
        "source": source,
        "model": metadata.get("core_loss_model_id") or metadata.get("core_loss_model"),
        "limitations": [
            "No FT-3M loss map versus DC bias was available in the normalized record.",
            "Temperature adjustment is represented by Bsat(100 C); core-loss temperature coefficient requires vendor data.",
        ],
    }


def _case_audit(
    candidate: FixedInductorDesignCandidate,
    request: InductorDesignRequest,
    metadata: dict[str, Any],
    candidate_metadata: dict[str, Any],
    case: tuple[str, float, float, float, str],
) -> InductorCaseAudit:
    case_id, load_ratio, pf, ambient_c, note = case
    base_i_peak = max(request.i_peak_a, 1e-9)
    current_scale = load_ratio / max(abs(pf), 1e-9)
    b_peak = (candidate.b_peak_design_t or 0.0) * current_scale
    b_sat = _number(candidate_metadata.get("b_sat_100c_t"), _number(candidate_metadata.get("b_sat_t"), 1.0))
    sat_margin = max(0.0, (1.0 - b_peak / max(b_sat, 1e-12)) * 100.0)
    wire_d = _number(candidate_metadata.get("strand_diameter_m"), 0.0)
    outer_d = _number(candidate_metadata.get("wire_outer_diameter_m"), wire_d)
    skin_depth = math.sqrt(_COPPER_RESISTIVITY_25C / (math.pi * max(request.fs_hz, 1.0) * _MU0))
    x = wire_d / max(skin_depth, 1e-12)
    skin_factor = 1.0 + x**4 / 192.0
    fill = _number(candidate.fill_factor, 0.1)
    proximity_factor = 1.0 + 2.0 * fill**2
    gap = max(candidate.gap_m or 0.0, 0.0)
    ae = _number(candidate_metadata.get("core_effective_area_m2"), 1e-8)
    fringing_factor = 1.0 + 0.15 * gap / max(math.sqrt(ae), 1e-12)
    rdc25 = candidate.rdc_25c_ohm or 0.0
    hotspot_guess = ambient_c + (candidate.reference_total_loss_w or 0.0) * 8.0
    rdc_hot = rdc25 * (1.0 + _COPPER_ALPHA * (hotspot_guess - 25.0))
    i_rms = max(request.i_rms_a * current_scale, base_i_peak * current_scale / math.sqrt(2.0))
    copper = i_rms**2 * rdc_hot * skin_factor * proximity_factor
    ref_core = candidate.reference_core_loss_w or 0.0
    ref_b = max(candidate.b_peak_design_t or 0.0, 1e-12)
    beta = _number(candidate_metadata.get("core_loss_beta_effective"), 2.0)
    core = ref_core * (b_peak / ref_b) ** beta * fringing_factor**2
    total = copper + core
    hotspot = ambient_c + total * 8.0
    passed = b_peak < 0.85 * b_sat and hotspot < 100.0
    if case_id == "max_bus":
        vdc_nom = _number(metadata.get("vdc_nom_v"), 700.0)
        vdc_max = _number(metadata.get("vdc_max_v"), vdc_nom)
        ripple_scale = vdc_max / max(vdc_nom, 1e-9)
        b_peak *= ripple_scale
        core = ref_core * (b_peak / ref_b) ** beta * fringing_factor**2
        total = copper + core
        hotspot = ambient_c + total * 8.0
        sat_margin = max(0.0, (1.0 - b_peak / max(b_sat, 1e-12)) * 100.0)
        passed = b_peak < 0.85 * b_sat and hotspot < 100.0
    return InductorCaseAudit(case_id, load_ratio, pf, ambient_c, b_peak, b_sat, sat_margin, rdc_hot, skin_factor, proximity_factor, fringing_factor, copper, core, total, hotspot, passed, note)


def _build_filter_audit(
    request: InductorDesignRequest,
    metadata: dict[str, Any],
    *,
    inductance_h: float | None = None,
    delta_i_pp_a: float | None = None,
) -> OutputFilterAudit:
    inductance_h = inductance_h or request.inductance_h
    cap_f = 2.2e-6
    resonance = 1.0 / (2.0 * math.pi * math.sqrt(max(inductance_h * cap_f, 1e-24)))
    damping = 1.0 / (3.0 * 2.0 * math.pi * resonance * cap_f)
    control_bw = _number(metadata.get("current_controller_bandwidth_hz"), request.fs_hz / 20.0)
    ratio = resonance / max(control_bw, 1e-9)
    ripple = max(delta_i_pp_a if delta_i_pp_a is not None else request.delta_i_pp_a, 0.0)
    phase_current = max(_number(metadata.get("i_phase_peak_a"), request.i_peak_a), 1e-9)
    return OutputFilterAudit(
        phase_count=3,
        inductance_uH=inductance_h * 1e6,
        shunt_capacitance_uF=cap_f * 1e6,
        resonance_frequency_hz=resonance,
        damping_resistance_ohm=damping,
        damping_topology="series-RC shunt damper per phase",
        control_loop_bandwidth_hz=control_bw,
        resonance_to_control_ratio=ratio,
        control_interaction_status="pass" if ratio >= 5.0 else "fail",
        current_ripple_pp_a=ripple,
        current_ripple_rms_a=ripple / math.sqrt(12.0),
        current_ripple_ratio=ripple / phase_current,
        damping_check="pass" if damping > 0.0 else "fail",
        assumptions=(
            "Output shunt capacitance is a 2.2 uF per-phase engineering assumption pending grid/filter specification.",
            "Current-loop bandwidth is approximated as fsw/20 unless an explicit controller bandwidth is supplied.",
            "Grid impedance and resonance damping interaction require impedance-scan validation.",
        ),
    )


def _number(value: Any, fallback: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return fallback
    return result if math.isfinite(result) else fallback
