"""Generic engineering screening and redundancy compression for magnetic candidates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from ...models.inductor import FixedInductorDesignCandidate
from .allow_profiles import MagneticAllowProfile
from .candidate_metrics import (
    MagneticCandidateContext,
    MagneticCandidateEngineeringMetrics,
    compute_candidate_engineering_metrics,
)


@dataclass(frozen=True)
class CandidateCompressionResult:
    """Result of engineering screening and redundancy compression."""

    basic_feasible_count: int
    post_allow_count: int
    post_compression_count: int
    filtered_candidates: list[FixedInductorDesignCandidate] = field(default_factory=list)
    compressed_candidates: list[FixedInductorDesignCandidate] = field(default_factory=list)
    metrics_by_id: dict[str, MagneticCandidateEngineeringMetrics] = field(default_factory=dict)
    rejection_counts: dict[str, int] = field(default_factory=dict)
    missing_metric_counts: dict[str, int] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def apply_engineering_allow_screen(
    candidates: Iterable[FixedInductorDesignCandidate],
    context: MagneticCandidateContext,
    allow_profile: MagneticAllowProfile,
) -> tuple[list[FixedInductorDesignCandidate], dict[str, MagneticCandidateEngineeringMetrics], list[str]]:
    """Filter candidates against the resolved engineering-allow profile."""
    survivors, metrics_by_id, notes, _, _ = _apply_engineering_allow_screen_with_audit(
        candidates, context, allow_profile
    )
    return survivors, metrics_by_id, notes


def _apply_engineering_allow_screen_with_audit(
    candidates: Iterable[FixedInductorDesignCandidate],
    context: MagneticCandidateContext,
    allow_profile: MagneticAllowProfile,
) -> tuple[
    list[FixedInductorDesignCandidate],
    dict[str, MagneticCandidateEngineeringMetrics],
    list[str],
    dict[str, int],
    dict[str, int],
]:
    """Apply the allow screen and retain a deterministic rejection ledger."""
    survivors: list[FixedInductorDesignCandidate] = []
    metrics_by_id: dict[str, MagneticCandidateEngineeringMetrics] = {}
    counters = {
        "b_sat_fallback": 0,
        "sat_skipped": 0,
        "loss_skipped": 0,
        "current_density_skipped": 0,
        "fill_skipped": 0,
        "volume_fallback": 0,
    }
    rejection_counts = {
        "saturation": 0,
        "loss": 0,
        "current_density": 0,
        "fill": 0,
    }

    for candidate in candidates:
        metrics = compute_candidate_engineering_metrics(candidate, context, allow_profile)
        metrics_by_id[candidate.candidate_id] = metrics
        if _contains_note(metrics.notes, "B_sat(100C) was unavailable") or _contains_note(metrics.notes, "fallback source"):
            counters["b_sat_fallback"] += 1
        if _contains_note(metrics.notes, "gross magnetic volume metadata fallback") or _contains_note(metrics.notes, "reconstructed from core and winding volumes"):
            counters["volume_fallback"] += 1

        if not _passes_metric(metrics.sat_margin):
            if metrics.sat_margin is None:
                counters["sat_skipped"] += 1
            else:
                rejection_counts["saturation"] += 1
                continue
        if not _passes_metric(metrics.loss_margin):
            if metrics.loss_margin is None:
                counters["loss_skipped"] += 1
            else:
                rejection_counts["loss"] += 1
                continue
        if not _passes_metric(metrics.current_density_margin):
            if metrics.current_density_margin is None:
                counters["current_density_skipped"] += 1
            else:
                rejection_counts["current_density"] += 1
                continue
        if not _passes_metric(metrics.fill_margin):
            if metrics.fill_margin is None:
                counters["fill_skipped"] += 1
            else:
                rejection_counts["fill"] += 1
                continue

        survivors.append(candidate)

    notes: list[str] = []
    if counters["b_sat_fallback"]:
        notes.append(f"B_sat(100C) fallback was used for {counters['b_sat_fallback']} processed candidates.")
    if counters["volume_fallback"]:
        notes.append(f"Volume fallback was used for {counters['volume_fallback']} processed candidates.")
    if counters["sat_skipped"]:
        notes.append(f"Saturation-margin screening was skipped for {counters['sat_skipped']} candidates with missing data.")
    if counters["loss_skipped"]:
        notes.append(f"Loss-margin screening was skipped for {counters['loss_skipped']} candidates with missing data.")
    if counters["current_density_skipped"]:
        notes.append(f"Current-density screening was skipped for {counters['current_density_skipped']} candidates with missing data.")
    if counters["fill_skipped"]:
        notes.append(f"Fill-factor screening was skipped for {counters['fill_skipped']} candidates with missing data.")
    missing_metric_counts = {
        "saturation": counters["sat_skipped"],
        "loss": counters["loss_skipped"],
        "current_density": counters["current_density_skipped"],
        "fill": counters["fill_skipped"],
    }
    return survivors, metrics_by_id, notes, rejection_counts, missing_metric_counts


def compress_redundant_candidates(
    candidates: Iterable[FixedInductorDesignCandidate],
    metrics_by_id: dict[str, MagneticCandidateEngineeringMetrics] | None = None,
) -> list[FixedInductorDesignCandidate]:
    """Reduce near-duplicate magnetic candidates while retaining representative points."""
    groups: dict[tuple[str, str, int, int, str, str], list[FixedInductorDesignCandidate]] = {}
    for candidate in candidates:
        groups.setdefault(_candidate_signature(candidate), []).append(candidate)

    retained: list[FixedInductorDesignCandidate] = []
    seen_ids: set[str] = set()
    for group_candidates in groups.values():
        ordered_by_volume = sorted(group_candidates, key=lambda item: (_value_or_inf(item.total_volume_m3), item.candidate_id))
        ordered_by_loss = sorted(group_candidates, key=lambda item: (_candidate_loss(item, metrics_by_id), item.candidate_id))
        balanced = _best_balanced_candidate(group_candidates, metrics_by_id)
        for candidate in (ordered_by_volume[0], ordered_by_loss[0], balanced):
            if candidate.candidate_id in seen_ids:
                continue
            retained.append(candidate)
            seen_ids.add(candidate.candidate_id)
    return retained


def compress_candidates(
    candidates: Iterable[FixedInductorDesignCandidate],
    context: MagneticCandidateContext,
    allow_profile: MagneticAllowProfile,
) -> CandidateCompressionResult:
    """Apply engineering screening and redundancy compression to magnetic candidates."""
    candidate_list = list(candidates)
    filtered_candidates, metrics_by_id, screen_notes, rejection_counts, missing_metric_counts = _apply_engineering_allow_screen_with_audit(
        candidate_list,
        context,
        allow_profile,
    )
    compressed_candidates = compress_redundant_candidates(filtered_candidates, metrics_by_id=metrics_by_id)
    notes = [
        f"Engineering allow screening reduced the candidate set from {len(candidate_list)} to {len(filtered_candidates)}.",
        f"Redundancy compression reduced the candidate set from {len(filtered_candidates)} to {len(compressed_candidates)}.",
    ]
    notes.extend(screen_notes)
    return CandidateCompressionResult(
        basic_feasible_count=len(candidate_list),
        post_allow_count=len(filtered_candidates),
        post_compression_count=len(compressed_candidates),
        filtered_candidates=filtered_candidates,
        compressed_candidates=compressed_candidates,
        metrics_by_id=metrics_by_id,
        rejection_counts=rejection_counts,
        missing_metric_counts=missing_metric_counts,
        notes=notes,
    )


def _passes_metric(margin: float | None) -> bool:
    return margin is None or margin >= 1.0


def _candidate_signature(candidate: FixedInductorDesignCandidate) -> tuple[str, int, str, str, int, int, str, str]:
    metadata = candidate.metadata
    core_signature = str(metadata.get("family") or candidate.core_name or "unknown")
    wire_signature = str(metadata.get("wire_family") or candidate.wire_name or "unknown")
    gap_bucket = _gap_bucket(candidate.gap_m)
    return (
        candidate.assembly_type or "single_core",
        candidate.stack_count,
        core_signature,
        candidate.material_name,
        _turn_bucket(candidate.turns),
        _parallel_bucket(candidate.parallel_bundles),
        wire_signature,
        gap_bucket,
    )


def _gap_bucket(gap_m: float | None) -> str:
    if gap_m is None:
        return "gap:none"
    gap_mm = gap_m * 1e3
    return f"gap:{round(gap_mm / 0.05) * 0.05:.2f}mm"


def _turn_bucket(turns: int) -> int:
    if turns <= 0:
        return 0
    return int(round(turns / 2.0) * 2)


def _parallel_bucket(parallel_bundles: int) -> int:
    if parallel_bundles <= 0:
        return 0
    return parallel_bundles


def _best_balanced_candidate(
    candidates: list[FixedInductorDesignCandidate],
    metrics_by_id: dict[str, MagneticCandidateEngineeringMetrics] | None,
) -> FixedInductorDesignCandidate:
    volumes = [_value_or_inf(candidate.total_volume_m3) for candidate in candidates]
    losses = [_candidate_loss(candidate, metrics_by_id) for candidate in candidates]
    min_volume, max_volume = min(volumes), max(volumes)
    min_loss, max_loss = min(losses), max(losses)

    def normalize(value: float, low: float, high: float) -> float:
        if high <= low:
            return 0.0
        return (value - low) / (high - low)

    return min(
        candidates,
        key=lambda candidate: (
            0.5 * normalize(_value_or_inf(candidate.total_volume_m3), min_volume, max_volume)
            + 0.5 * normalize(_candidate_loss(candidate, metrics_by_id), min_loss, max_loss),
            _value_or_inf(candidate.total_volume_m3),
            _candidate_loss(candidate, metrics_by_id),
            candidate.candidate_id,
        ),
    )


def _candidate_loss(
    candidate: FixedInductorDesignCandidate,
    metrics_by_id: dict[str, MagneticCandidateEngineeringMetrics] | None,
) -> float:
    if metrics_by_id:
        metrics = metrics_by_id.get(candidate.candidate_id)
        if metrics is not None and metrics.total_loss_w is not None:
            return metrics.total_loss_w
    if candidate.reference_total_loss_w is not None:
        return candidate.reference_total_loss_w
    return _value_or_inf(None)


def _value_or_inf(value: float | None) -> float:
    if value is None:
        return float("inf")
    return float(value)


def _contains_note(notes: list[str], pattern: str) -> bool:
    return any(pattern in note for note in notes)
