"""Opt-in loader for normalized packaged OpenMagnetics magnetic data."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import json
from pathlib import Path

import pandas as pd

from ...models.magnetic_loss_contract import MaterialLossModel, NormalizedMagneticMaterialV2
from ...models.openmagnetics_component_contract import ComponentNormalizationBatch
from .openmagnetics_normalizer import NormalizedOpenMagneticsDatabase, load_normalized_openmagnetics_cache
from .openmagnetics_v2_production_locator import (
    get_normalized_v2_production_cache_dir,
    verify_normalized_v2_production_cache,
)


V1_ENGINE_MATERIAL_COLUMNS = (
    "manufacturer",
    "material_type",
    "B_sat",
    "B_sat_100c",
    "b_sat_100c_source",
    "density",
    "steinmetz_ranges",
    "f_min_recommended",
    "f_max_recommended",
    "material_metric_source",
    "material_metric_source_pdf",
    "material_metric_source_page",
    "material_metric_notes",
)


@dataclass(frozen=True)
class NormalizedOpenMagneticsV2Cache:
    """Explicitly selected v2 cache; never used by the default loader."""

    materials: tuple[NormalizedMagneticMaterialV2, ...]
    components: ComponentNormalizationBatch


def load_normalized_openmagnetics_v2_cache(cache_dir: str | Path) -> NormalizedOpenMagneticsV2Cache:
    """Load a v2 cache from an operator-supplied directory.

    The path is intentionally explicit so a v2 artifact cannot be selected by
    changing the packaged v1 resource or an ambient environment variable.
    """
    root = Path(cache_dir).resolve()
    materials_path = root / "materials_normalized_v2.json"
    components_path = root / "components_normalized_v2.json"
    if not materials_path.is_file() or not components_path.is_file():
        raise FileNotFoundError(
            "A normalized-v2 cache directory must contain materials_normalized_v2.json "
            "and components_normalized_v2.json."
        )
    material_payload = json.loads(materials_path.read_text(encoding="utf-8"))
    component_payload = json.loads(components_path.read_text(encoding="utf-8"))
    if not isinstance(material_payload, list) or not isinstance(component_payload, dict):
        raise ValueError("normalized-v2 cache files have invalid top-level JSON types.")
    materials = tuple(NormalizedMagneticMaterialV2.from_dict(item) for item in material_payload)
    components = ComponentNormalizationBatch.from_dict(component_payload)
    return NormalizedOpenMagneticsV2Cache(materials=materials, components=components)


def load_normalized_openmagnetics_v2_production_cache() -> NormalizedOpenMagneticsV2Cache:
    """Verify and load only the fixed Step 22B production cache."""
    verify_normalized_v2_production_cache()
    return load_normalized_openmagnetics_v2_cache(get_normalized_v2_production_cache_dir())


def validate_normalized_v2_cache_authority(cache_dir: str | Path) -> None:
    """Fail closed unless an explicit Step 20 authority bundle accompanies the cache."""
    root = Path(cache_dir).resolve()
    audit_path = root / "cache_audit.json"
    manifest_path = root / "source_manifest.json"
    if not audit_path.is_file() or not manifest_path.is_file():
        raise ValueError("normalized-v2 shadow/canary cache requires cache_audit.json and source_manifest.json authority files.")
    try:
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("normalized-v2 authority files are not valid JSON.") from exc
    source = audit.get("source", {})
    if manifest.get("status") != "ready" or manifest.get("source_kind") != "target_mas_881cceaf_647":
        raise ValueError("normalized-v2 source_manifest authority is not the ready Step 20 target source.")
    if source.get("commit") != "881cceaf1d91ee88c8c5b5b611a0703e6126e825":
        raise ValueError("normalized-v2 cache source commit does not match the Step 20 MAS pin.")
    if audit.get("production_loader_changed") is not False or audit.get("production_cache_changed") is not False:
        raise ValueError("normalized-v2 cache authority indicates a production mutation.")
    if audit.get("materials", {}).get("normalized_record_count") != 647:
        raise ValueError("normalized-v2 shadow/canary cache must contain the Step 20 647-material inventory.")


def normalized_v2_to_engine_dataframes(
    cache: NormalizedOpenMagneticsV2Cache,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Project an explicit v2 cache into the unchanged engine dataframe schema."""
    cores = _v2_core_shapes_to_dataframe(cache.components)
    materials = normalized_v2_materials_to_v1_dataframe(cache.materials)
    wires = _v2_litz_wires_to_dataframe(cache.components)
    _attach_v2_core_identity_columns(cores, cache.components)
    _attach_v2_material_identity_columns(materials, cache.materials)
    if cores.empty or materials.empty or wires.empty:
        raise ValueError("The selected normalized-v2 cache has no engine-compatible records.")
    return cores, materials, wires


def _attach_v2_core_identity_columns(frame: pd.DataFrame, batch: ComponentNormalizationBatch) -> None:
    """Attach audit-only stable identities without changing index or ordering."""
    by_name = {record.name: record for record in batch.shapes}
    frame["stable_core_id"] = [by_name[str(name)].shape_id for name in frame.index]
    frame["core_source_provenance"] = [
        by_name[str(name)].source_provenance.to_dict() for name in frame.index
    ]


def _attach_v2_material_identity_columns(
    frame: pd.DataFrame,
    materials: Iterable[NormalizedMagneticMaterialV2],
) -> None:
    """Attach the first-record v1 projection identity used by each engine row."""
    by_name: dict[str, NormalizedMagneticMaterialV2] = {}
    for material in materials:
        b_sat_t, _, _ = _v2_saturation_compatibility(material.saturation_data)
        if not _v2_steinmetz_ranges(material.loss_models) or not _positive(b_sat_t):
            continue
        by_name.setdefault(material.material_name, material)
    frame["stable_material_id"] = [by_name[str(name)].material_id for name in frame.index]
    frame["material_source_provenance"] = [
        by_name[str(name)].source_provenance.to_dict() for name in frame.index
    ]


def normalized_openmagnetics_to_engine_dataframes(
    database: NormalizedOpenMagneticsDatabase | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Convert normalized packaged records to current engine dataframe columns."""
    resolved = database or load_normalized_openmagnetics_cache()
    cores = _core_shapes_to_dataframe(resolved)
    materials = _materials_to_dataframe(resolved)
    wires = _litz_wires_to_dataframe(resolved)
    if cores.empty:
        raise ValueError("Normalized packaged magnetic backend has no engine-compatible core records.")
    if materials.empty:
        raise ValueError("Normalized packaged magnetic backend has no engine-compatible material records.")
    if wires.empty:
        raise ValueError("Normalized packaged magnetic backend has no engine-compatible Litz wire records.")
    return cores, materials, wires


def normalized_v2_materials_to_v1_dataframe(
    materials: Iterable[NormalizedMagneticMaterialV2],
) -> pd.DataFrame:
    """Project v2 materials into the current engine material schema.

    This compatibility adapter is deliberately not used by the production
    loader in Step 2. Non-Steinmetz materials remain valid v2 records but are
    excluded from the legacy engine projection.
    """

    rows: list[dict[str, object]] = []
    for material in materials:
        if not isinstance(material, NormalizedMagneticMaterialV2):
            raise TypeError("materials must contain only NormalizedMagneticMaterialV2 values.")
        steinmetz_ranges = _v2_steinmetz_ranges(material.loss_models)
        b_sat_t, b_sat_100c_t, b_sat_100c_source = _v2_saturation_compatibility(material.saturation_data)
        if not steinmetz_ranges or not _positive(b_sat_t):
            continue
        recommended = material.recommended_frequency_range_hz
        provenance = material.source_provenance
        source_page = provenance.source_record_reference
        if source_page is None and provenance.source_record_index is not None:
            source_page = str(provenance.source_record_index)
        rows.append(
            {
                "mat_name": material.material_name,
                "manufacturer": material.manufacturer,
                "material_type": material.composition or material.family or "",
                "B_sat": b_sat_t,
                "B_sat_100c": b_sat_100c_t,
                "b_sat_100c_source": b_sat_100c_source,
                "density": material.density_kg_per_m3 or 4800.0,
                "steinmetz_ranges": steinmetz_ranges,
                "f_min_recommended": recommended[0] if recommended else 1.0,
                "f_max_recommended": recommended[1] if recommended else 1e9,
                "material_metric_source": provenance.source_project,
                "material_metric_source_pdf": provenance.source_file,
                "material_metric_source_page": source_page or "",
                "material_metric_notes": (
                    "normalized-v2 compatibility projection; "
                    f"source_commit={provenance.source_commit or 'unknown'}"
                ),
            }
        )
    if not rows:
        empty = pd.DataFrame(columns=("mat_name", *V1_ENGINE_MATERIAL_COLUMNS))
        return empty.set_index("mat_name")
    return (
        pd.DataFrame(rows, columns=("mat_name", *V1_ENGINE_MATERIAL_COLUMNS))
        .drop_duplicates(subset=["mat_name"], keep="first")
        .set_index("mat_name")
    )


def audit_normalized_v2_material_projection(
    materials: Iterable[NormalizedMagneticMaterialV2],
    *,
    v1_cache_sha256: str,
    expected_v1_cache_sha256: str,
) -> dict[str, object]:
    """Return explicit inclusion/exclusion evidence for the legacy projection."""
    values = tuple(materials)
    included: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    names: dict[str, str] = {}
    for material in values:
        ranges = _v2_steinmetz_ranges(material.loss_models)
        b_sat, _, _ = _v2_saturation_compatibility(material.saturation_data)
        if ranges and _positive(b_sat):
            status = "projected"
            names.setdefault(material.material_name, material.material_id)
            if names[material.material_name] != material.material_id:
                status = "projected_duplicate_name_first_record"
            included.append({
                "source_v2_material_id": material.material_id,
                "projected_v1_name": material.material_name,
                "projection_status": status,
                "loss_basis": "steinmetz_volumetric_w_per_m3",
                "saturation_basis": "valid_b_sat_t",
                "source_provenance": material.source_provenance.to_dict(),
            })
            continue
        methods = sorted({model.method for model in material.loss_models})
        reason = "non_steinmetz_or_missing_saturation"
        if not methods and not material.measured_loss_datasets:
            reason = "loss_data_not_available"
        elif material.measured_loss_datasets and not methods:
            reason = "measured_only"
        excluded.append({
            "source_v2_material_id": material.material_id,
            "projected_v1_name": material.material_name,
            "projection_status": "excluded_from_v1_projection",
            "excluded_reason": reason,
            "loss_basis": methods or ["none"],
            "saturation_basis": "unavailable" if not _positive(b_sat) else "available",
            "source_provenance": material.source_provenance.to_dict(),
        })
    return {
        "contract_version": "openmagnetics-step21-v1-projection-audit-v1",
        "v2_material_count": len(values),
        "projected_material_count": len(included),
        "excluded_material_count": len(excluded),
        "excluded_reasons": {
            reason: sum(item.get("excluded_reason") == reason for item in excluded)
            for reason in sorted({str(item.get("excluded_reason")) for item in excluded})
        },
        "duplicate_name_policy": "first_record_preserved_for_v1_name_projection",
        "schema_equal_to_v1": True,
        "v1_cache_unchanged": v1_cache_sha256.upper() == expected_v1_cache_sha256.upper(),
        "projected_records": included,
        "excluded_records": excluded,
    }


def _core_shapes_to_dataframe(database: NormalizedOpenMagneticsDatabase) -> pd.DataFrame:
    rows = []
    for record in database.core_shapes:
        if not _positive(record.get("effective_area_mm2")) or not _positive(record.get("window_area_mm2")):
            continue
        core_name = str(record["name"])
        rows.append(
            {
                "core_name": core_name,
                "shape_label": core_name,
                "family": record.get("family") or "",
                "template_name": record.get("template_name") or record.get("geometry_template_id") or "",
                "Ae": float(record["effective_area_mm2"]) * 1e-6,
                "Aw": float(record["window_area_mm2"]) * 1e-6,
                "Ve": float(record["effective_volume_cm3"]) * 1e-6,
                "le": float(record["magnetic_path_length_mm"]) * 1e-3,
                "mlt": float(record["mean_length_per_turn_mm"] or record["magnetic_path_length_mm"]) * 1e-3,
                "gross_volume": float(record["gross_volume_cm3"] or record["effective_volume_cm3"]) * 1e-6,
                "width": float(record["outer_width_mm"]) * 1e-3,
                "height": float(record["outer_height_mm"]) * 1e-3,
                "depth": float(record["outer_depth_mm"]) * 1e-3,
                "library_width": float(record["outer_width_mm"]) * 1e-3,
                "library_height": (
                    float(record["outer_height_mm"]) / max(int(record.get("half_cores_per_assembly") or 1), 1)
                    if record.get("library_item_is_half_core")
                    else float(record["outer_height_mm"])
                )
                * 1e-3,
                "library_depth": float(record["outer_depth_mm"]) * 1e-3,
                "library_item_is_half_core": bool(record.get("library_item_is_half_core")),
                "half_cores_per_assembly": int(record.get("half_cores_per_assembly") or 1),
                "Ap": float(record["effective_area_mm2"]) * float(record["window_area_mm2"]) * 1e-12,
            }
        )
    return pd.DataFrame(rows).drop_duplicates(subset=["core_name"]).set_index("core_name").sort_values("Ve")


def _v2_core_shapes_to_dataframe(batch: ComponentNormalizationBatch) -> pd.DataFrame:
    """Build the legacy core frame from v2 shape metrics without changing v1."""
    rows: list[dict[str, object]] = []
    for record in batch.shapes:
        metrics = record.metrics
        if metrics.effective_area_m2 is None or metrics.window_area_m2 is None:
            continue
        dimensions = record.dimensions

        def dimension(name: str) -> float | None:
            value = dimensions.get(name)
            return None if value is None else value.representative_value()[0]

        if metrics.effective_magnetic_volume_m3 is None or metrics.effective_path_length_m is None:
            continue
        width, height, depth = (dimension(name) for name in ("A", "B", "C"))
        if width is None or height is None or depth is None:
            continue
        rows.append(
            {
                "core_name": record.name,
                "shape_label": record.name,
                "family": record.canonical_family,
                "template_name": record.canonical_family,
                "Ae": metrics.effective_area_m2,
                "Aw": metrics.window_area_m2,
                "Ve": metrics.effective_magnetic_volume_m3,
                "le": metrics.effective_path_length_m,
                "mlt": metrics.mean_length_per_turn_m or metrics.effective_path_length_m,
                "gross_volume": metrics.physical_envelope_volume_m3 or metrics.effective_magnetic_volume_m3,
                "width": width,
                "height": height,
                "depth": depth,
                "library_width": width,
                "library_height": height,
                "library_depth": depth,
                "library_item_is_half_core": False,
                "half_cores_per_assembly": 1,
                "Ap": metrics.effective_area_m2 * metrics.window_area_m2,
                "physical_envelope_volume_m3": metrics.physical_envelope_volume_m3,
                "solid_material_volume_m3": metrics.solid_material_volume_m3,
                "core_mass_kg": metrics.mass_kg,
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).drop_duplicates(subset=["core_name"]).set_index("core_name").sort_values("Ve")


def _materials_to_dataframe(database: NormalizedOpenMagneticsDatabase) -> pd.DataFrame:
    rows = []
    for record in database.core_materials:
        ranges = record.get("steinmetz_ranges")
        if not ranges or not record.get("b_sat_t"):
            continue
        rows.append(
            {
                "mat_name": record["material_name"],
                "manufacturer": record.get("vendor") or "",
                "material_type": record.get("material_type") or "",
                "B_sat": record.get("b_sat_t"),
                "B_sat_100c": record.get("b_sat_100c_t"),
                "b_sat_100c_source": record.get("b_sat_100c_source") or "",
                "density": record.get("density_kg_per_m3") or 4800.0,
                "steinmetz_ranges": [
                    {
                        "minimumFrequency": item["frequency_min_hz"],
                        "maximumFrequency": item["frequency_max_hz"],
                        "k": item["steinmetz_k"],
                        "alpha": item["steinmetz_alpha"],
                        "beta": item["steinmetz_beta"],
                    }
                    for item in ranges
                ],
                "f_min_recommended": record.get("frequency_min_hz") or 1.0,
                "f_max_recommended": record.get("frequency_max_hz") or 1e9,
                "material_metric_source": record.get("material_metric_source") or "",
                "material_metric_source_pdf": record.get("material_metric_source_pdf") or "",
                "material_metric_source_page": record.get("material_metric_source_page") or "",
                "material_metric_notes": record.get("material_metric_notes") or "",
            }
        )
    return pd.DataFrame(rows).drop_duplicates(subset=["mat_name"]).set_index("mat_name")


def _v2_steinmetz_ranges(loss_models: tuple[MaterialLossModel, ...]) -> list[dict[str, float]]:
    ranges: list[dict[str, float]] = []
    for model in loss_models:
        if model.method.casefold() != "steinmetz" or model.valid_frequency_range_hz is None:
            continue
        required = ("k", "alpha", "beta")
        if any(name not in model.coefficients for name in required):
            continue
        ranges.append(
            {
                "minimumFrequency": model.valid_frequency_range_hz[0],
                "maximumFrequency": model.valid_frequency_range_hz[1],
                "k": float(model.coefficients["k"]),
                "alpha": float(model.coefficients["alpha"]),
                "beta": float(model.coefficients["beta"]),
            }
        )
    return ranges


def _v2_saturation_compatibility(data: Mapping[str, object]) -> tuple[float | None, float | None, str]:
    b_sat_t = _float_or_none(data.get("b_sat_t"))
    b_sat_100c_t = _float_or_none(data.get("b_sat_100c_t"))
    source = str(data.get("b_sat_100c_source") or "")
    return b_sat_t, b_sat_100c_t, source


def _litz_wires_to_dataframe(database: NormalizedOpenMagneticsDatabase) -> pd.DataFrame:
    rows = []
    for record in database.wires:
        if record.get("wire_type") != "litz":
            continue
        if not _positive(record.get("strand_diameter_mm")) or not _positive(record.get("copper_area_mm2")):
            continue
        rows.append(
            {
                "wire_id": record["wire_name"],
                "stable_wire_id": record["wire_id"],
                "wire_name": record["wire_name"],
                "d_strand": float(record["strand_diameter_mm"]) * 1e-3,
                "strands_per_bundle": int(record.get("strand_count") or 1),
                "bundle_copper_area": float(record["copper_area_mm2"]) * 1e-6,
                "outer_diameter": float(record.get("outer_diameter_mm") or record["strand_diameter_mm"]) * 1e-3,
                "conducting_area_basis": "normalized_v1_copper_area",
                "source_wire_record": {
                    "record_version": record.get("record_version"),
                    "wire_id": record["wire_id"],
                    "wire_name": record["wire_name"],
                    "source": record.get("source"),
                },
            }
        )
    return pd.DataFrame(rows).drop_duplicates(subset=["wire_id"]).sort_values("bundle_copper_area").set_index("wire_id")


def _v2_litz_wires_to_dataframe(batch: ComponentNormalizationBatch) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    by_id = {record.wire_id: record for record in batch.wires}
    for record in batch.wires:
        if record.wire_type != "litz" or record.strand_wire_id is None:
            continue
        area = record.conducting_area
        strand_record = by_id.get(record.strand_wire_id)
        strand = strand_record.conducting_diameter if strand_record is not None else None
        outer = record.outer_diameter
        if area is None or strand is None:
            continue
        area_m2 = area.representative_value()[0]
        strand_m = strand.representative_value()[0]
        outer_m = outer.representative_value()[0] if outer is not None else strand_m
        rows.append(
            {
                "wire_id": record.wire_name,
                "stable_wire_id": record.wire_id,
                "wire_name": record.wire_name,
                "d_strand": strand_m,
                "strands_per_bundle": record.number_conductors,
                "bundle_copper_area": area_m2,
                "outer_diameter": outer_m,
                "conducting_area_basis": record.conducting_area_basis,
                "source_wire_record": {
                    "record_version": record.record_version,
                    "wire_id": record.wire_id,
                    "wire_name": record.wire_name,
                    "wire_type": record.wire_type,
                    "strand_wire_id": record.strand_wire_id,
                    "source_provenance": record.source_provenance.to_dict(),
                },
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).drop_duplicates(subset=["wire_id"]).sort_values("bundle_copper_area").set_index("wire_id")


def _positive(value: object) -> bool:
    return value is not None and float(value) > 0.0


def _float_or_none(value: object) -> float | None:
    return None if value is None else float(value)
