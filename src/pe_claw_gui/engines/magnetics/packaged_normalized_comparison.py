"""Opt-in parity diagnostics for the packaged-normalized magnetic backend."""

from __future__ import annotations

from dataclasses import dataclass, field

from ...libraries.magnetics.normalized_backend_loader import normalized_openmagnetics_to_engine_dataframes
from ...libraries.magnetics.normalized_inventory import build_normalized_openmagnetics_inventory
from ...models.inductor import FixedInductorDesignCandidate, InductorDesignRequest
from ...visualization.geometry.layout_builder import build_inductor_geometry_layout
from .data_backend import MagneticDataBackendConfig, get_normalized_v1_rollback_backend_config
from .inductor_design import build_pareto_front, choose_representative_designs, synthesize_fixed_inductor_candidates_with_backend
from .legacy_external_openmagnetics import InductorDatabaseUnavailableError


@dataclass(frozen=True)
class PackagedNormalizedCandidateComparison:
    """Candidate-generation comparison for legacy external versus packaged-normalized data."""

    external_available: bool
    packaged_available: bool
    parity_status: str
    external_candidate_count: int = 0
    packaged_candidate_count: int = 0
    external_feasible_count: int = 0
    packaged_feasible_count: int = 0
    external_pareto_count: int = 0
    packaged_pareto_count: int = 0
    external_summary: dict[str, object] = field(default_factory=dict)
    packaged_summary: dict[str, object] = field(default_factory=dict)
    selected_design_parity: dict[str, object] = field(default_factory=dict)
    geometry_artifact_parity: dict[str, object] = field(default_factory=dict)
    coverage_diagnostics: dict[str, object] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Return a serializable summary dictionary."""
        return {
            "external_available": self.external_available,
            "packaged_available": self.packaged_available,
            "parity_status": self.parity_status,
            "external_candidate_count": self.external_candidate_count,
            "packaged_candidate_count": self.packaged_candidate_count,
            "external_feasible_count": self.external_feasible_count,
            "packaged_feasible_count": self.packaged_feasible_count,
            "external_pareto_count": self.external_pareto_count,
            "packaged_pareto_count": self.packaged_pareto_count,
            "external_summary": dict(self.external_summary),
            "packaged_summary": dict(self.packaged_summary),
            "selected_design_parity": dict(self.selected_design_parity),
            "geometry_artifact_parity": dict(self.geometry_artifact_parity),
            "coverage_diagnostics": dict(self.coverage_diagnostics),
            "warnings": list(self.warnings),
        }


def compare_packaged_normalized_to_external(
    request: InductorDesignRequest,
) -> PackagedNormalizedCandidateComparison:
    """Compare legacy external candidate generation with packaged-normalized data."""
    try:
        external_candidates = synthesize_fixed_inductor_candidates_with_backend(
            request,
            MagneticDataBackendConfig(backend="legacy_external", comparison_mode=True),
        )
    except InductorDatabaseUnavailableError as exc:
        return PackagedNormalizedCandidateComparison(
            external_available=False,
            packaged_available=False,
            parity_status="backend unavailable",
            warnings=(str(exc),),
        )

    try:
        packaged_candidates = synthesize_fixed_inductor_candidates_with_backend(
            request,
            get_normalized_v1_rollback_backend_config(),
        )
    except Exception as exc:
        return PackagedNormalizedCandidateComparison(
            external_available=True,
            packaged_available=False,
            parity_status="backend unavailable",
            external_candidate_count=len(external_candidates),
            external_feasible_count=len(external_candidates),
            external_pareto_count=len(build_pareto_front(external_candidates)),
            external_summary=_candidate_summary(external_candidates),
            coverage_diagnostics=_coverage_diagnostics(external_candidates, []),
            warnings=(f"{type(exc).__name__}: {exc}",),
        )

    external_summary = _candidate_summary(external_candidates)
    packaged_summary = _candidate_summary(packaged_candidates)
    selected_parity = _selected_design_parity(external_candidates, packaged_candidates)
    geometry_parity = _geometry_parity(external_candidates, packaged_candidates)
    coverage = _coverage_diagnostics(external_candidates, packaged_candidates)
    status = _parity_status(external_summary, packaged_summary, selected_parity, geometry_parity, coverage)
    warnings = _warnings(status, external_summary, packaged_summary, selected_parity, coverage)
    return PackagedNormalizedCandidateComparison(
        external_available=True,
        packaged_available=True,
        parity_status=status,
        external_candidate_count=len(external_candidates),
        packaged_candidate_count=len(packaged_candidates),
        external_feasible_count=len(external_candidates),
        packaged_feasible_count=len(packaged_candidates),
        external_pareto_count=external_summary["pareto_count"],
        packaged_pareto_count=packaged_summary["pareto_count"],
        external_summary=external_summary,
        packaged_summary=packaged_summary,
        selected_design_parity=selected_parity,
        geometry_artifact_parity=geometry_parity,
        coverage_diagnostics=coverage,
        warnings=tuple(warnings),
    )


def _candidate_summary(candidates: list[FixedInductorDesignCandidate]) -> dict[str, object]:
    pareto = build_pareto_front(candidates)
    chosen = choose_representative_designs(pareto, count=5)
    selected = chosen[len(chosen) // 2] if chosen else None
    min_volume = min(candidates, key=lambda item: (float("inf") if item.total_volume_m3 is None else item.total_volume_m3, item.candidate_id), default=None)
    min_loss = min(candidates, key=lambda item: (float("inf") if item.reference_total_loss_w is None else item.reference_total_loss_w, item.candidate_id), default=None)
    return {
        "feasible_count": len(candidates),
        "pareto_count": len(pareto),
        "min_volume_signature": _candidate_signature(min_volume) if min_volume else None,
        "min_loss_signature": _candidate_signature(min_loss) if min_loss else None,
        "recommended_signature": _candidate_signature(selected) if selected else None,
        "selected_signature": _candidate_signature(selected) if selected else None,
        "selected_detail": _candidate_detail(selected) if selected else None,
        "inductance_range_h": _range_for(candidates, "inductance_h"),
        "total_loss_range_w": _range_for(candidates, "reference_total_loss_w"),
        "volume_range_m3": _range_for(candidates, "total_volume_m3"),
        "core_loss_range_w": _range_for(candidates, "reference_core_loss_w"),
        "copper_loss_range_w": _range_for(candidates, "reference_copper_loss_w"),
        "current_density_range_a_per_mm2": _current_density_range(candidates),
        "fill_factor_range": _range_for(candidates, "fill_factor"),
        "flux_density_range_t": _range_for(candidates, "b_peak_design_t"),
    }


def _candidate_signature(candidate: FixedInductorDesignCandidate) -> dict[str, object]:
    return {
        "core_name": candidate.core_name,
        "material_name": candidate.material_name,
        "wire_name": candidate.wire_name,
        "turns": candidate.turns,
        "parallel_bundles": candidate.parallel_bundles,
    }


def _candidate_detail(candidate: FixedInductorDesignCandidate) -> dict[str, object]:
    detail = _candidate_signature(candidate)
    detail.update(
        {
            "core_family": candidate.metadata.get("family"),
            "geometry_template_id": candidate.metadata.get("template_name"),
            "stack_count": candidate.stack_count,
            "inductance_h": candidate.inductance_h,
            "total_loss_w": candidate.reference_total_loss_w,
            "volume_m3": candidate.total_volume_m3,
            "core_loss_w": candidate.reference_core_loss_w,
            "copper_loss_w": candidate.reference_copper_loss_w,
            "fill_factor": candidate.fill_factor,
            "current_density_a_per_mm2": _candidate_current_density(candidate),
            "flux_density_t": candidate.b_peak_design_t,
        }
    )
    return detail


def _selected_design_parity(
    external_candidates: list[FixedInductorDesignCandidate],
    packaged_candidates: list[FixedInductorDesignCandidate],
) -> dict[str, object]:
    external_selected = _recommended_candidate(external_candidates)
    packaged_selected = _recommended_candidate(packaged_candidates)
    external_detail = _candidate_detail(external_selected) if external_selected else None
    packaged_detail = _candidate_detail(packaged_selected) if packaged_selected else None
    candidate_exists = _contains_signature(packaged_candidates, external_detail)
    on_packaged_pareto = _contains_signature(build_pareto_front(packaged_candidates), external_detail)
    differences = _numeric_differences(packaged_detail, external_detail)
    if external_detail is None or packaged_detail is None:
        status = "not attempted"
    elif _signature_from_detail(external_detail) != _signature_from_detail(packaged_detail):
        status = "selected-design mismatch"
    elif _differences_within_tolerance(differences):
        status = "exact-signature match"
    else:
        status = "numerically close"
    return {
        "status": status,
        "external_selected": external_detail,
        "packaged_selected": packaged_detail,
        "external_selected_exists_in_packaged_candidates": candidate_exists,
        "external_selected_on_packaged_pareto_front": on_packaged_pareto,
        "numeric_differences": differences,
        "explanation": _selected_explanation(status, candidate_exists, on_packaged_pareto),
    }


def _geometry_parity(
    external_candidates: list[FixedInductorDesignCandidate],
    packaged_candidates: list[FixedInductorDesignCandidate],
) -> dict[str, object]:
    external_layout = _layout_summary(_recommended_candidate(external_candidates))
    packaged_layout = _layout_summary(_recommended_candidate(packaged_candidates))
    if not external_layout.get("available") or not packaged_layout.get("available"):
        return {
            "status": "not attempted",
            "external_layout": external_layout,
            "packaged_layout": packaged_layout,
            "template_ids_match": False,
            "dimension_differences": {},
        }
    differences = _geometry_dimension_differences(packaged_layout, external_layout)
    template_match = external_layout.get("template_name") == packaged_layout.get("template_name")
    if not template_match:
        status = "representative mismatch"
    elif _differences_within_tolerance(differences):
        status = "exact-signature match"
    else:
        status = "numerically close"
    return {
        "status": status,
        "external_layout": external_layout,
        "packaged_layout": packaged_layout,
        "template_ids_match": template_match,
        "dimension_differences": differences,
    }


def _coverage_diagnostics(
    external_candidates: list[FixedInductorDesignCandidate],
    packaged_candidates: list[FixedInductorDesignCandidate],
) -> dict[str, object]:
    inventory = build_normalized_openmagnetics_inventory()
    cores, materials, wires = normalized_openmagnetics_to_engine_dataframes()
    external_selected = _recommended_candidate(external_candidates)
    packaged_core_ids = set(str(item) for item in cores.index)
    packaged_material_ids = set(str(item) for item in materials.index)
    packaged_wire_ids = set(str(item) for item in wires.index)
    external_signature = _candidate_signature(external_selected) if external_selected else {}
    return {
        "engine_compatible_core_count": len(cores),
        "normalized_material_count": inventory.material_count,
        "steinmetz_compatible_material_count": len(materials),
        "litz_wire_count": len(wires),
        "incomplete_core_shape_count": inventory.missing_or_incomplete_field_counts["core_shapes_missing_required_unit_fields"],
        "incomplete_material_count": inventory.missing_or_incomplete_field_counts["materials_missing_required_unit_fields"],
        "incomplete_wire_count": inventory.missing_or_incomplete_field_counts["wires_missing_required_unit_fields"],
        "commercial_cores_unresolved_shape": inventory.missing_or_incomplete_field_counts["commercial_cores_unresolved_shape"],
        "stock_cores_unresolved_shape": inventory.missing_or_incomplete_field_counts["stock_cores_unresolved_shape"],
        "external_selected_core_exists": external_signature.get("core_name") in packaged_core_ids,
        "external_selected_material_exists": external_signature.get("material_name") in packaged_material_ids,
        "external_selected_wire_exists": external_signature.get("wire_name") in packaged_wire_ids,
        "external_selected_candidate_exists": _contains_signature(packaged_candidates, _candidate_detail(external_selected) if external_selected else None),
    }


def _parity_status(
    external_summary: dict[str, object],
    packaged_summary: dict[str, object],
    selected_parity: dict[str, object],
    geometry_parity: dict[str, object],
    coverage: dict[str, object],
) -> str:
    if not packaged_summary["feasible_count"]:
        return "not attempted"
    if not coverage.get("external_selected_core_exists") or not coverage.get("external_selected_material_exists") or not coverage.get("external_selected_wire_exists"):
        return "local coverage limited"
    if packaged_summary["feasible_count"] != external_summary["feasible_count"]:
        return "candidate-count mismatched"
    if packaged_summary["pareto_count"] != external_summary["pareto_count"]:
        return "Pareto-count mismatched"
    for key in ("min_volume_signature", "min_loss_signature", "recommended_signature"):
        if packaged_summary.get(key) != external_summary.get(key):
            return "representative mismatch"
    if selected_parity.get("status") != "exact-signature match":
        return str(selected_parity.get("status") or "selected-design mismatch")
    if geometry_parity.get("status") not in {"exact-signature match", "numerically close"}:
        return "representative mismatch"
    if not _ranges_close(packaged_summary, external_summary):
        return "numerically close"
    return "exact-signature match"


def _warnings(
    status: str,
    external_summary: dict[str, object],
    packaged_summary: dict[str, object],
    selected_parity: dict[str, object],
    coverage: dict[str, object],
) -> list[str]:
    warnings: list[str] = []
    if packaged_summary["feasible_count"] != external_summary["feasible_count"]:
        warnings.append(
            f"Candidate count differs: packaged_normalized={packaged_summary['feasible_count']}, external={external_summary['feasible_count']}."
        )
    if packaged_summary["pareto_count"] != external_summary["pareto_count"]:
        warnings.append(
            f"Pareto count differs: packaged_normalized={packaged_summary['pareto_count']}, external={external_summary['pareto_count']}."
        )
    if selected_parity.get("status") != "exact-signature match":
        warnings.append(f"Selected design parity status: {selected_parity.get('status')}.")
    if coverage.get("steinmetz_compatible_material_count", 0) < coverage.get("normalized_material_count", 0):
        warnings.append(
            "Only materials with Steinmetz ranges are engine-compatible in packaged_normalized candidate generation."
        )
    if coverage.get("incomplete_wire_count", 0):
        warnings.append("Some normalized wire records are incomplete and excluded from engine-compatible Litz data.")
    if status != "exact-signature match":
        warnings.append(f"Packaged-normalized parity status: {status}.")
    return warnings


def _recommended_candidate(candidates: list[FixedInductorDesignCandidate]) -> FixedInductorDesignCandidate | None:
    pareto = build_pareto_front(candidates)
    chosen = choose_representative_designs(pareto, count=5)
    if not chosen:
        return None
    return chosen[len(chosen) // 2]


def _contains_signature(
    candidates: list[FixedInductorDesignCandidate],
    expected_detail: dict[str, object] | None,
) -> bool:
    if expected_detail is None:
        return False
    expected = _signature_from_detail(expected_detail)
    return any(_candidate_signature(candidate) == expected for candidate in candidates)


def _signature_from_detail(detail: dict[str, object]) -> dict[str, object]:
    return {
        key: detail[key]
        for key in ("core_name", "material_name", "wire_name", "turns", "parallel_bundles")
    }


def _selected_explanation(status: str, candidate_exists: bool, on_pareto: bool) -> str:
    if status == "exact-signature match":
        return "selected design exists in packaged_normalized candidates and matches"
    if not candidate_exists:
        return "external selected design is missing from packaged_normalized candidates"
    if not on_pareto:
        return "external selected design exists but is not on the packaged_normalized Pareto front"
    if status == "selected-design mismatch":
        return "external selected design exists but packaged_normalized selected a different representative"
    return "selected design is numerically close but not exact"


def _layout_summary(candidate: FixedInductorDesignCandidate | None) -> dict[str, object]:
    if candidate is None:
        return {"available": False, "error": "No selected magnetic design candidate is available."}
    try:
        layout = build_inductor_geometry_layout(candidate)
    except Exception as exc:
        return {"available": False, "design_id": candidate.candidate_id, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "available": True,
        "design_id": layout.design_id,
        "template_name": layout.template_name,
        "core_family": layout.core_family,
        "core_bbox_width_mm": layout.outer_width_mm,
        "core_bbox_height_mm": layout.outer_height_mm,
        "core_bbox_depth_mm": layout.overall_depth_mm,
        "winding_bbox_width_mm": layout.winding_block_width_mm,
        "winding_bbox_height_mm": layout.winding_block_height_mm,
        "winding_bbox_depth_mm": layout.winding_block_depth_mm,
        "total_magnetic_volume_m3": candidate.total_volume_m3,
    }


def _geometry_dimension_differences(packaged_layout: dict[str, object], external_layout: dict[str, object]) -> dict[str, float | None]:
    fields = (
        "core_bbox_width_mm",
        "core_bbox_height_mm",
        "core_bbox_depth_mm",
        "winding_bbox_width_mm",
        "winding_bbox_height_mm",
        "winding_bbox_depth_mm",
        "total_magnetic_volume_m3",
    )
    return {f"{field}_relative_difference": _optional_relative_difference(packaged_layout.get(field), external_layout.get(field)) for field in fields}


def _numeric_differences(packaged_detail: dict[str, object] | None, external_detail: dict[str, object] | None) -> dict[str, float | None]:
    if packaged_detail is None or external_detail is None:
        return {}
    relative_fields = ("total_loss_w", "volume_m3", "inductance_h")
    absolute_fields = ("fill_factor", "current_density_a_per_mm2", "flux_density_t")
    differences: dict[str, float | None] = {}
    for field in relative_fields:
        differences[f"{field}_relative_difference"] = _optional_relative_difference(packaged_detail.get(field), external_detail.get(field))
    for field in absolute_fields:
        differences[f"{field}_difference"] = _optional_absolute_difference(packaged_detail.get(field), external_detail.get(field))
    return differences


def _range_for(candidates: list[FixedInductorDesignCandidate], field_name: str) -> tuple[float, float] | None:
    values = [getattr(candidate, field_name) for candidate in candidates if getattr(candidate, field_name) is not None]
    if not values:
        return None
    return (float(min(values)), float(max(values)))


def _current_density_range(candidates: list[FixedInductorDesignCandidate]) -> tuple[float, float] | None:
    values: list[float] = []
    for candidate in candidates:
        current_density = _candidate_current_density(candidate)
        if current_density is not None:
            values.append(current_density)
    if not values:
        return None
    return (min(values), max(values))


def _candidate_current_density(candidate: FixedInductorDesignCandidate) -> float | None:
    bundle_area_m2 = candidate.metadata.get("bundle_copper_area_m2")
    reference_i_rms_a = candidate.metadata.get("reference_i_rms_a")
    if bundle_area_m2 is None or reference_i_rms_a is None:
        return None
    total_area_mm2 = float(bundle_area_m2) * max(candidate.parallel_bundles, 1) * 1e6
    if total_area_mm2 <= 0.0:
        return None
    return float(reference_i_rms_a) / total_area_mm2


def _ranges_close(packaged_summary: dict[str, object], external_summary: dict[str, object]) -> bool:
    range_keys = (
        "inductance_range_h",
        "total_loss_range_w",
        "volume_range_m3",
        "core_loss_range_w",
        "copper_loss_range_w",
        "fill_factor_range",
        "flux_density_range_t",
    )
    for key in range_keys:
        packaged_range = packaged_summary.get(key)
        external_range = external_summary.get(key)
        if packaged_range is None or external_range is None:
            continue
        for packaged_value, external_value in zip(packaged_range, external_range):
            if _relative_difference(float(packaged_value), float(external_value)) > 1e-6:
                return False
    return True


def _differences_within_tolerance(differences: dict[str, float | None], tolerance: float = 1e-6) -> bool:
    return all(value is None or value <= tolerance for value in differences.values())


def _optional_relative_difference(packaged_value: object, external_value: object) -> float | None:
    if packaged_value is None or external_value is None:
        return None
    return _relative_difference(float(packaged_value), float(external_value))


def _optional_absolute_difference(packaged_value: object, external_value: object) -> float | None:
    if packaged_value is None or external_value is None:
        return None
    return abs(float(packaged_value) - float(external_value))


def _relative_difference(packaged_value: float, external_value: float) -> float:
    denominator = max(abs(external_value), 1e-30)
    return abs(packaged_value - external_value) / denominator
