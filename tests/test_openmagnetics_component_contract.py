from __future__ import annotations

import json
import math
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pe_claw_gui.models.magnetic_loss_contract import SourceProvenance  # noqa: E402
from pe_claw_gui.models.openmagnetics_component_contract import (  # noqa: E402
    CatalogDistributorEntry,
    CatalogGapEntry,
    ComponentNormalizationBatch,
    ComponentNormalizationIssue,
    CoreShapeMetrics,
    DimensionRange,
    ReferenceResolution,
)


def test_dimension_range_round_trip_and_representative_policy() -> None:
    value = DimensionRange(1.0, None, 3.0, "m")
    assert value.representative_value() == (2.0, "midpoint")
    assert DimensionRange.from_json(value.to_json()) == value


def test_contract_json_is_deterministic_and_rejects_unknown_fields() -> None:
    first = DimensionRange.from_dict({"minimum": 1.0, "nominal": 2.0, "maximum": 3.0, "unit": "m"})
    second = DimensionRange.from_dict({"unit": "m", "maximum": 3.0, "minimum": 1.0, "nominal": 2.0})
    assert first.to_json() == second.to_json()
    with pytest.raises(ValueError, match="unknown"):
        DimensionRange.from_dict({"minimum": 1.0, "nominal": 2.0, "maximum": 3.0, "unit": "m", "extra": 1})


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_contract_rejects_nonfinite_values(value: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        DimensionRange(None, value, None, "m")


def test_reference_resolution_enforces_unique_and_ambiguous_semantics() -> None:
    unique = ReferenceResolution("E 20", "exact_unique", "exact", "shape:1", ("shape:1",))
    assert ReferenceResolution.from_json(unique.to_json()) == unique
    ambiguous = ReferenceResolution("ER 40", "alias_ambiguous", "alias", None, ("shape:2", "shape:1"))
    assert ambiguous.candidate_ids == ("shape:1", "shape:2")
    with pytest.raises(ValueError, match="Ambiguous"):
        ReferenceResolution("ER 40", "alias_ambiguous", "alias", "shape:1", ("shape:1", "shape:2"))


def test_effective_volume_must_match_area_times_path_length() -> None:
    metrics = CoreShapeMetrics(
        effective_area_m2=2e-4,
        effective_path_length_m=0.1,
        effective_magnetic_volume_m3=2e-5,
        minimum_cross_section_area_m2=1.8e-4,
        window_area_m2=None,
        mean_length_per_turn_m=None,
        physical_envelope_volume_m3=5e-5,
        solid_material_volume_m3=None,
        mass_kg=None,
        metric_source="fixture",
        volume_source="fixture",
        metric_status="valid_source",
        metric_messages=(),
    )
    assert CoreShapeMetrics.from_json(metrics.to_json()) == metrics
    payload = json.loads(metrics.to_json())
    payload["effective_magnetic_volume_m3"] = 1e-5
    with pytest.raises(ValueError, match="must equal"):
        CoreShapeMetrics.from_dict(payload)


def test_source_provenance_remains_the_step2_contract() -> None:
    source = SourceProvenance(
        source_kind="fixture",
        source_project="OpenMagnetics/MAS",
        source_file="data/core_shapes.ndjson",
        source_commit="a" * 40,
        source_schema_version="MAS",
        dataset_sha256="b" * 64,
    )
    assert SourceProvenance.from_json(source.to_json()) == source


def test_gap_distributor_issue_and_empty_batch_round_trip() -> None:
    gap = CatalogGapEntry("subtractive", 1e-3, 1e-4, (0.0, 0.0, 0.0), "rectangular", (0.01, 0.02), 0.03, 0.04)
    distributor = CatalogDistributorEntry("Digi-Key", "ABC", "USA", "International", "https://example.test", 3, "2026-07-25", 2.5, None, "source_currency_not_declared")
    issue = ComponentNormalizationIssue("warning", "fixture", "shape", 0, "Golden", "$.field", "Fixture issue.")
    assert CatalogGapEntry.from_json(gap.to_json()) == gap
    assert CatalogDistributorEntry.from_json(distributor.to_json()) == distributor
    assert ComponentNormalizationIssue.from_json(issue.to_json()) == issue
    batch = ComponentNormalizationBatch((), (), (), (), (issue,), {"core_shapes": 0}, {"core_shapes": 0})
    assert ComponentNormalizationBatch.from_json(batch.to_json()) == batch
