"""Allow-aware staged search for fixed-inductor candidate frontiers."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from ...models.inductor import FixedInductorDesignCandidate, InductorDesignRequest
from .allow_profiles import MagneticAllowProfile
from .candidate_compression import CandidateCompressionResult, compress_candidates
from .candidate_metrics import MagneticCandidateContext, MagneticCandidateEngineeringMetrics
from .data_backend import MagneticDataBackendConfig, resolve_magnetic_data_backend
from .inductor_design import _DatabaseBundle, _generate_candidates, _sort_candidates


@dataclass(frozen=True)
class FixedInductorSearchBounds:
    """One fixed, auditable candidate-search stage."""

    stage_id: str
    core_limit: int
    material_limit: int = 8
    wire_limit: int = 8
    turns_min: int = 8
    turns_max: int = 80
    parallel_min: int = 1
    parallel_max: int = 8


@dataclass(frozen=True)
class FixedInductorFrontierStageAudit:
    """Compact evidence retained after one search stage."""

    bounds: FixedInductorSearchBounds
    generation_counts: dict[str, int]
    basic_feasible_count: int
    post_allow_count: int
    post_compression_count: int
    rejection_counts: dict[str, int]
    missing_metric_counts: dict[str, int]
    candidate_id_sha256: str
    filtered_candidate_id_sha256: str
    compressed_candidate_id_sha256: str
    boundary_candidates: dict[str, dict[str, object]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FixedInductorFrontierSearchResult:
    """Final feasible stage plus deterministic search and inventory evidence."""

    status: str
    selected_stage: str | None
    candidates: list[FixedInductorDesignCandidate]
    compression_result: CandidateCompressionResult
    stage_audits: tuple[FixedInductorFrontierStageAudit, ...]
    inventory_audit: dict[str, object]
    notes: tuple[str, ...] = ()

    def audit_dict(self) -> dict[str, object]:
        return {
            "contract_version": "fixed-inductor-frontier-search-v1",
            "status": self.status,
            "selected_stage": self.selected_stage,
            "stage_audits": [item.to_dict() for item in self.stage_audits],
            "inventory_audit": self.inventory_audit,
            "notes": list(self.notes),
        }


DEFAULT_FIXED_INDUCTOR_SEARCH_STAGES: tuple[FixedInductorSearchBounds, ...] = (
    FixedInductorSearchBounds("baseline_core_14", core_limit=14),
    FixedInductorSearchBounds("expanded_core_24", core_limit=24),
    FixedInductorSearchBounds("frontier_core_48", core_limit=48),
    FixedInductorSearchBounds("expanded_core_96", core_limit=96),
)


def search_fixed_inductor_candidate_frontier(
    request: InductorDesignRequest,
    *,
    context: MagneticCandidateContext,
    allow_profile: MagneticAllowProfile,
    backend_config: MagneticDataBackendConfig | None = None,
    stages: tuple[FixedInductorSearchBounds, ...] = DEFAULT_FIXED_INDUCTOR_SEARCH_STAGES,
    baseline_candidates: Iterable[FixedInductorDesignCandidate] | None = None,
    baseline_compression_result: CandidateCompressionResult | None = None,
) -> FixedInductorFrontierSearchResult:
    """Expand only the selected backend's core pool until the allow front is non-empty.

    Material, wire, turns, and parallel-conductor bounds stay fixed.  This is a
    bounded search repair, not a relaxation of any electrical or thermal rule.
    """

    if not stages:
        raise ValueError("At least one fixed-inductor frontier stage is required.")
    _validate_stages(stages)
    bundle = resolve_magnetic_data_backend(backend_config)
    database = _DatabaseBundle(
        cores=bundle.cores,
        materials=bundle.materials,
        wires=bundle.wires,
        catalog_cores=bundle.catalog_cores,
        selection_mode=bundle.selection_mode,
    )
    inventory_audit = _inventory_audit(database, stages)
    stage_audits: list[FixedInductorFrontierStageAudit] = []
    final_candidates: list[FixedInductorDesignCandidate] = []
    final_compression = _empty_compression()
    selected_stage: str | None = None
    cumulative_candidates: list[FixedInductorDesignCandidate] = []
    previous_core_limit = 0

    provided_baseline = list(baseline_candidates) if baseline_candidates is not None else None
    for stage_index, bounds in enumerate(stages):
        generation_counts: dict[str, int] = {}
        if stage_index == 0 and provided_baseline is not None:
            candidates = _sort_candidates(provided_baseline)
            cumulative_candidates = candidates
            compression = baseline_compression_result or compress_candidates(
                candidates,
                context=context,
                allow_profile=allow_profile,
            )
            generation_counts["provided_baseline_candidate_count"] = len(candidates)
        else:
            incremental_candidates = _generate_candidates(
                    request,
                    database,
                    core_limit=bounds.core_limit,
                    material_limit=bounds.material_limit,
                    wire_limit=bounds.wire_limit,
                    audit=generation_counts,
                    core_offset=previous_core_limit,
                )
            generation_counts["incremental_core_offset"] = previous_core_limit
            generation_counts["incremental_core_limit"] = bounds.core_limit
            cumulative_candidates = _sort_candidates([*cumulative_candidates, *incremental_candidates])
            candidates = cumulative_candidates
            compression = compress_candidates(
                candidates,
                context=context,
                allow_profile=allow_profile,
            )
        stage_audits.append(_stage_audit(bounds, candidates, compression, generation_counts))
        previous_core_limit = bounds.core_limit
        final_candidates = candidates
        final_compression = compression
        if compression.post_allow_count > 0:
            selected_stage = bounds.stage_id
            break

    status = (
        "feasible_selection_verified"
        if selected_stage is not None
        else "request_infeasible_under_current_library_and_limits"
    )
    inventory_audit["cartesian_scan_policy"] = (
        "stopped_after_verified_feasible_stage"
        if selected_stage is not None
        else "all_configured_bounded_stages_exhausted"
    )
    inventory_audit["selected_stage"] = selected_stage
    return FixedInductorFrontierSearchResult(
        status=status,
        selected_stage=selected_stage,
        candidates=final_candidates,
        compression_result=final_compression,
        stage_audits=tuple(stage_audits),
        inventory_audit=inventory_audit,
        notes=(
            "Only the eligible core pool is expanded; material, wire, turns, parallel, and engineering-allow bounds remain fixed.",
            "A feasible stage terminates the Cartesian scan deterministically.",
        ),
    )


def _validate_stages(stages: tuple[FixedInductorSearchBounds, ...]) -> None:
    first = stages[0]
    for previous, current in zip(stages, stages[1:]):
        if current.core_limit <= previous.core_limit:
            raise ValueError("Frontier core limits must be strictly increasing.")
        if (
            current.material_limit,
            current.wire_limit,
            current.turns_min,
            current.turns_max,
            current.parallel_min,
            current.parallel_max,
        ) != (
            first.material_limit,
            first.wire_limit,
            first.turns_min,
            first.turns_max,
            first.parallel_min,
            first.parallel_max,
        ):
            raise ValueError("Fixed-inductor frontier stages permit only core-pool expansion.")
    if (first.turns_min, first.turns_max, first.parallel_min, first.parallel_max) != (8, 80, 1, 8):
        raise ValueError("The fixed-inductor frontier keeps turns=8..80 and parallel=1..8 fixed.")


def _stage_audit(
    bounds: FixedInductorSearchBounds,
    candidates: list[FixedInductorDesignCandidate],
    compression: CandidateCompressionResult,
    generation_counts: dict[str, int],
) -> FixedInductorFrontierStageAudit:
    return FixedInductorFrontierStageAudit(
        bounds=bounds,
        generation_counts=dict(sorted(generation_counts.items())),
        basic_feasible_count=compression.basic_feasible_count,
        post_allow_count=compression.post_allow_count,
        post_compression_count=compression.post_compression_count,
        rejection_counts=dict(sorted(compression.rejection_counts.items())),
        missing_metric_counts=dict(sorted(compression.missing_metric_counts.items())),
        candidate_id_sha256=_candidate_id_hash(candidates),
        filtered_candidate_id_sha256=_candidate_id_hash(compression.filtered_candidates),
        compressed_candidate_id_sha256=_candidate_id_hash(compression.compressed_candidates),
        boundary_candidates=_boundary_candidates(compression.metrics_by_id),
    )


def _boundary_candidates(
    metrics_by_id: dict[str, MagneticCandidateEngineeringMetrics],
) -> dict[str, dict[str, object]]:
    margin_names = (
        "sat_margin",
        "loss_margin",
        "current_density_margin",
        "fill_margin",
    )
    result: dict[str, dict[str, object]] = {}
    for margin_name in margin_names:
        available = [
            metric
            for metric in metrics_by_id.values()
            if _finite(getattr(metric, margin_name))
        ]
        if available:
            best = max(available, key=lambda item: (float(getattr(item, margin_name)), item.candidate_id))
            result[margin_name] = _metric_summary(best)
    fully_defined = [
        metric
        for metric in metrics_by_id.values()
        if all(_finite(getattr(metric, name)) for name in margin_names)
    ]
    if fully_defined:
        closest = max(
            fully_defined,
            key=lambda item: (
                min(float(getattr(item, name)) for name in margin_names),
                item.candidate_id,
            ),
        )
        result["maximin"] = _metric_summary(closest)
    return dict(sorted(result.items()))


def _metric_summary(metric: MagneticCandidateEngineeringMetrics) -> dict[str, object]:
    return {
        "candidate_id": metric.candidate_id,
        "sat_margin": metric.sat_margin,
        "loss_margin": metric.loss_margin,
        "current_density_margin": metric.current_density_margin,
        "fill_margin": metric.fill_margin,
        "b_absolute_peak_t": metric.b_peak_t,
        "b_allow_t": metric.b_allow_t,
        "total_loss_w": metric.total_loss_w,
        "loss_allow_w": metric.p_loss_allow_w,
        "current_density_a_per_mm2": metric.current_density_a_per_mm2,
        "fill_factor": metric.fill_factor,
    }


def _inventory_audit(
    database: _DatabaseBundle,
    stages: tuple[FixedInductorSearchBounds, ...],
) -> dict[str, object]:
    core_ids = _identity_values(database.cores, "stable_core_id")
    material_ids = _identity_values(database.materials, "stable_material_id")
    wire_ids = _identity_values(database.wires, "stable_wire_id")
    return {
        "complete_identity_and_eligibility_scan": True,
        "selection_mode": database.selection_mode,
        "engine_eligible_counts": {
            "cores": len(database.cores),
            "materials": len(database.materials),
            "wires": len(database.wires),
        },
        "unique_identity_counts": {
            "cores": len(set(core_ids)),
            "materials": len(set(material_ids)),
            "wires": len(set(wire_ids)),
        },
        "identity_columns_available": {
            "cores": "stable_core_id" in database.cores.columns,
            "materials": "stable_material_id" in database.materials.columns,
            "wires": "stable_wire_id" in database.wires.columns,
        },
        "configured_core_limits": [stage.core_limit for stage in stages],
        "material_limit_fixed": stages[0].material_limit,
        "wire_limit_fixed": stages[0].wire_limit,
        "turns_bounds_fixed": [stages[0].turns_min, stages[0].turns_max],
        "parallel_bounds_fixed": [stages[0].parallel_min, stages[0].parallel_max],
    }


def _identity_values(frame: Any, column: str) -> list[str]:
    if column in frame.columns:
        return [str(value) for value in frame[column].tolist()]
    return [str(value) for value in frame.index.tolist()]


def _candidate_id_hash(candidates: Iterable[FixedInductorDesignCandidate]) -> str:
    payload = [candidate.candidate_id for candidate in candidates]
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("ascii")).hexdigest().upper()


def _empty_compression() -> CandidateCompressionResult:
    return CandidateCompressionResult(0, 0, 0)


def _finite(value: object) -> bool:
    return value is not None and math.isfinite(float(value))
