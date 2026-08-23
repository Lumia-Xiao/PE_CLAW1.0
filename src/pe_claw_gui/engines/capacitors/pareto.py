"""Pareto-front helpers for capacitor bank selection."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from ...models.capacitor import CapacitorSelectionEntry

RECOMMENDED_POLICY_NAME = "minimum-parallel margin-aware recommendation"
RECOMMENDED_SOURCE = "minimum_parallel_margin_aware"
COMPROMISE_RECOMMENDED_POLICY_NAME = "volume-loss compromise recommendation"
COMPROMISE_RECOMMENDED_SOURCE = "pareto_compromise"
COMFORTABLE_RIPPLE_UTILIZATION = 0.90
EDGE_RIPPLE_UTILIZATION = 0.95


@dataclass(frozen=True)
class CapacitorRecommendationDecision:
    """Recommended capacitor decision and UI/report metadata."""

    selected: CapacitorSelectionEntry | None
    reason: str
    policy_name: str = RECOMMENDED_POLICY_NAME
    source: str = RECOMMENDED_SOURCE
    minimum_feasible_parallel_count: int | None = None
    recommended_parallel_count: int | None = None
    recommended_ripple_utilization: float | None = None


def dominates(a: CapacitorSelectionEntry, b: CapacitorSelectionEntry) -> bool:
    """Return True when ``a`` dominates ``b`` on volume and total loss."""

    return (
        a.total_volume_cm3 <= b.total_volume_cm3
        and a.p_total_w <= b.p_total_w
        and (a.total_volume_cm3 < b.total_volume_cm3 or a.p_total_w < b.p_total_w)
    )


def extract_pareto_front(entries: list[CapacitorSelectionEntry]) -> list[CapacitorSelectionEntry]:
    """Return non-dominated feasible capacitor entries."""

    feasible = sorted(
        (entry for entry in entries if entry.feasible),
        key=lambda entry: (
            entry.total_volume_cm3,
            entry.p_total_w,
            entry.series_count,
            entry.parallel_count,
            entry.candidate.part_number,
        ),
    )
    front: list[CapacitorSelectionEntry] = []
    best_loss_w = math.inf
    tolerance_w = 1e-12
    for entry in feasible:
        if entry.p_total_w >= best_loss_w - tolerance_w:
            continue
        front.append(replace(entry, is_pareto=True))
        best_loss_w = entry.p_total_w
    return sorted(front, key=_pareto_sort_key)


def apply_representative_labels(
    feasible_entries: list[CapacitorSelectionEntry],
    pareto_front: list[CapacitorSelectionEntry],
    recommended_entry: CapacitorSelectionEntry | None = None,
) -> tuple[
    list[CapacitorSelectionEntry],
    list[CapacitorSelectionEntry],
    CapacitorSelectionEntry | None,
    CapacitorSelectionEntry | None,
    CapacitorSelectionEntry | None,
    CapacitorSelectionEntry | None,
]:
    """Mark Pareto status, representative labels, and recommended entry."""

    min_volume = select_min_volume(pareto_front)
    min_loss = select_min_loss(pareto_front)
    compromise = select_compromise(pareto_front)
    recommended = recommended_entry
    if recommended is None:
        recommended = choose_margin_aware_recommended_capacitor(pareto_front, feasible_entries).selected

    label_by_key: dict[tuple[str, int, int], list[str]] = {}
    for label, entry in (
        ("min-volume", min_volume),
        ("min-loss", min_loss),
        ("compromise", compromise),
    ):
        if entry is None:
            continue
        label_by_key.setdefault(_entry_key(entry), []).append(label)

    pareto_keys = {_entry_key(entry) for entry in pareto_front}
    recommended_key = _entry_key(recommended) if recommended is not None else None

    labeled_feasible = [
        _mark_entry(
            entry,
            is_pareto=_entry_key(entry) in pareto_keys,
            labels=label_by_key.get(_entry_key(entry), []),
            recommended=_entry_key(entry) == recommended_key,
        )
        for entry in feasible_entries
    ]
    labeled_front = [
        _mark_entry(
            entry,
            is_pareto=True,
            labels=label_by_key.get(_entry_key(entry), []),
            recommended=_entry_key(entry) == recommended_key,
        )
        for entry in pareto_front
    ]

    by_key = {_entry_key(entry): entry for entry in labeled_feasible}
    return (
        labeled_feasible,
        labeled_front,
        by_key.get(_entry_key(min_volume)) if min_volume is not None else None,
        by_key.get(_entry_key(min_loss)) if min_loss is not None else None,
        by_key.get(_entry_key(compromise)) if compromise is not None else None,
        by_key.get(_entry_key(recommended)) if recommended is not None else None,
    )


def choose_margin_aware_recommended_capacitor(
    pareto_entries: list[CapacitorSelectionEntry],
    feasible_entries: list[CapacitorSelectionEntry],
) -> CapacitorRecommendationDecision:
    """Choose the final recommendation without adding extra parallel parts for loss alone."""

    source_pool = pareto_entries if pareto_entries else feasible_entries
    pool = [entry for entry in source_pool if entry.feasible]
    if not pool:
        return CapacitorRecommendationDecision(
            selected=None,
            reason="No feasible capacitor bank candidate is available.",
        )

    n0 = min(entry.parallel_count for entry in pool)
    n0_entries = [entry for entry in pool if entry.parallel_count == n0]
    comfortable_n0 = [entry for entry in n0_entries if _ripple_utilization(entry) <= COMFORTABLE_RIPPLE_UTILIZATION]
    if comfortable_n0:
        selected = min(comfortable_n0, key=_entry_sort_key_for_min_parallel_recommendation)
        return _decision(
            selected,
            n0,
            f"selected an S/P={_bank_label(selected)} candidate because it satisfies ripple margin without extra parallel capacitors.",
        )

    best_n0 = min(n0_entries, key=_entry_sort_key_for_min_parallel_recommendation)
    best_n0_utilization = _ripple_utilization(best_n0)
    if best_n0_utilization <= EDGE_RIPPLE_UTILIZATION:
        return _decision(
            best_n0,
            n0,
            f"selected the smallest-volume S/P={_bank_label(best_n0)} candidate; ripple is acceptable but near the target.",
        )

    n1 = n0 + 1
    n1_entries = [entry for entry in pool if entry.parallel_count == n1]
    comfortable_n1 = [entry for entry in n1_entries if _ripple_utilization(entry) <= COMFORTABLE_RIPPLE_UTILIZATION]
    if comfortable_n1:
        selected = min(comfortable_n1, key=_entry_sort_key_for_min_parallel_recommendation)
        return _decision(
            selected,
            n0,
            f"P={n0} was too close to the ripple limit, so the recommendation increased only one step to P={n1}.",
        )

    return _decision(
        best_n0,
        n0,
        f"no comfortable P={n1} option was available, so the best P={n0} candidate remains recommended.",
    )


def choose_compromise_recommended_capacitor(
    pareto_entries: list[CapacitorSelectionEntry],
    feasible_entries: list[CapacitorSelectionEntry],
) -> CapacitorRecommendationDecision:
    """Choose the Pareto compromise point as the final recommendation."""

    source_pool = pareto_entries if pareto_entries else feasible_entries
    pool = [entry for entry in source_pool if entry.feasible]
    if not pool:
        return CapacitorRecommendationDecision(
            selected=None,
            reason="No feasible capacitor bank candidate is available.",
            policy_name=COMPROMISE_RECOMMENDED_POLICY_NAME,
            source=COMPROMISE_RECOMMENDED_SOURCE,
        )
    selected = select_compromise(pool)
    if selected is None:
        return CapacitorRecommendationDecision(
            selected=None,
            reason="No Pareto compromise capacitor bank candidate is available.",
            policy_name=COMPROMISE_RECOMMENDED_POLICY_NAME,
            source=COMPROMISE_RECOMMENDED_SOURCE,
        )
    minimum_parallel_count = min(entry.parallel_count for entry in pool)
    return CapacitorRecommendationDecision(
        selected=selected,
        reason=(
            f"{COMPROMISE_RECOMMENDED_POLICY_NAME}: selected the Pareto compromise candidate "
            "using normalized capacitor-bank volume and total bank loss."
        ),
        policy_name=COMPROMISE_RECOMMENDED_POLICY_NAME,
        source=COMPROMISE_RECOMMENDED_SOURCE,
        minimum_feasible_parallel_count=minimum_parallel_count,
        recommended_parallel_count=selected.parallel_count,
        recommended_ripple_utilization=_ripple_utilization(selected),
    )


def select_min_volume(pareto_front: list[CapacitorSelectionEntry]) -> CapacitorSelectionEntry | None:
    if not pareto_front:
        return None
    return min(
        pareto_front,
        key=lambda entry: (
            entry.total_volume_cm3,
            entry.p_total_w,
            entry.series_count,
            entry.parallel_count,
            entry.candidate.part_number,
        ),
    )


def select_min_loss(pareto_front: list[CapacitorSelectionEntry]) -> CapacitorSelectionEntry | None:
    if not pareto_front:
        return None
    return min(
        pareto_front,
        key=lambda entry: (
            entry.p_total_w,
            entry.total_volume_cm3,
            entry.series_count,
            entry.parallel_count,
            entry.candidate.part_number,
        ),
    )


def select_compromise(pareto_front: list[CapacitorSelectionEntry]) -> CapacitorSelectionEntry | None:
    if not pareto_front:
        return None

    volume_values = [entry.total_volume_cm3 for entry in pareto_front]
    loss_values = [entry.p_total_w for entry in pareto_front]
    return min(
        pareto_front,
        key=lambda entry: (
            math.hypot(
                _normalize(entry.total_volume_cm3, volume_values),
                _normalize(entry.p_total_w, loss_values),
            ),
            entry.series_count,
            entry.parallel_count,
            entry.total_volume_cm3,
            entry.p_total_w,
            entry.candidate.part_number,
        ),
    )


def _mark_entry(
    entry: CapacitorSelectionEntry,
    *,
    is_pareto: bool,
    labels: list[str],
    recommended: bool,
) -> CapacitorSelectionEntry:
    label_text = ", ".join(labels)
    if recommended and "recommended" not in labels:
        label_text = f"{label_text}, recommended" if label_text else "recommended"
    return replace(
        entry,
        is_pareto=is_pareto,
        representative_label=label_text,
        recommended_flag=recommended,
    )


def _decision(
    selected: CapacitorSelectionEntry,
    minimum_feasible_parallel_count: int,
    reason: str,
) -> CapacitorRecommendationDecision:
    return CapacitorRecommendationDecision(
        selected=selected,
        reason=f"{RECOMMENDED_POLICY_NAME}: {reason}",
        minimum_feasible_parallel_count=minimum_feasible_parallel_count,
        recommended_parallel_count=selected.parallel_count,
        recommended_ripple_utilization=_ripple_utilization(selected),
    )


def _ripple_utilization(entry: CapacitorSelectionEntry) -> float:
    if entry.ripple_allow_v <= 0.0:
        return math.inf
    return entry.ripple_total_pp_v / entry.ripple_allow_v


def _entry_sort_key_for_min_parallel_recommendation(entry: CapacitorSelectionEntry) -> tuple[float, float, float, int, int, str]:
    return (
        entry.total_volume_cm3,
        entry.p_total_w,
        entry.hotspot_temp_c,
        entry.series_count,
        entry.parallel_count,
        entry.candidate.part_number,
    )


def _entry_key(entry: CapacitorSelectionEntry | None) -> tuple[str, int, int]:
    if entry is None:
        return ("", 0, 0)
    return (entry.candidate.part_number, entry.series_count, entry.parallel_count)


def _pareto_sort_key(entry: CapacitorSelectionEntry) -> tuple[float, float, int, int, str]:
    return (entry.total_volume_cm3, entry.p_total_w, entry.series_count, entry.parallel_count, entry.candidate.part_number)


def _bank_label(entry: CapacitorSelectionEntry) -> str:
    return f"S={entry.series_count}, P={entry.parallel_count}"


def _normalize(value: float, values: list[float]) -> float:
    low = min(values)
    high = max(values)
    if high <= low:
        return 0.0
    return (value - low) / (high - low)
