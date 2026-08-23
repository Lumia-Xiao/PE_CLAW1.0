"""Deterministic Step 7A coverage and input-completeness audit helpers."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import math
from typing import Any

from ...models.magnetic_loss_contract import (
    MaterialLossModel,
    NormalizedMagneticMaterialV2,
)


STEP7A_COVERAGE_CONTRACT_VERSION = "openmagnetics-step7a-model-coverage-v1"
PINNED_MKF_COMMIT = "8d3bad38297ddca92a2aafe9c88a4fc93ef75d5b"


@dataclass(frozen=True)
class CoreLossMethodSpecification:
    """Audited equation identity and required inputs for one loss method."""

    method: str
    formula_id: str
    formula: str
    output_basis: str
    coefficient_names: tuple[str, ...]
    material_inputs: tuple[str, ...]
    runtime_inputs: tuple[str, ...]
    source_reference: str
    native_unit_policy: str

    def to_dict(self) -> dict[str, object]:
        return {
            "method": self.method,
            "formula_id": self.formula_id,
            "formula": self.formula,
            "output_basis": self.output_basis,
            "coefficient_names": list(self.coefficient_names),
            "material_inputs": list(self.material_inputs),
            "runtime_inputs": list(self.runtime_inputs),
            "source_reference": self.source_reference,
            "native_unit_policy": self.native_unit_policy,
        }


METHOD_SPECIFICATIONS: tuple[CoreLossMethodSpecification, ...] = (
    CoreLossMethodSpecification(
        method="steinmetz",
        formula_id="steinmetz_si_v1",
        formula="Pv=k*temperature_factor*f_hz^alpha*B_model_t^beta",
        output_basis="volumetric_w_per_m3",
        coefficient_names=("alpha", "beta", "k"),
        material_inputs=(),
        runtime_inputs=("frequency_hz", "flux_ac_peak_t"),
        source_reference=f"MKF {PINNED_MKF_COMMIT} CoreLosses.cpp/CoreLosses.h",
        native_unit_policy="SI Hz,T,W/m3",
    ),
    CoreLossMethodSpecification(
        method="micrometals",
        formula_id="mkf_micrometals_v1",
        formula=(
            "Pv=f/(a/Bac^3+b/Bac^2.3+c/Bac^1.65)+d*Bac^2*f^2"
        ),
        output_basis="volumetric_w_per_m3",
        coefficient_names=("a", "b", "c", "d"),
        material_inputs=(),
        runtime_inputs=("frequency_hz", "flux_ac_peak_t"),
        source_reference=f"MKF {PINNED_MKF_COMMIT} CoreLosses.cpp",
        native_unit_policy="Parsed coefficients produce SI W/m3 from Hz and T",
    ),
    CoreLossMethodSpecification(
        method="magnetics",
        formula_id="mkf_magnetics_v1",
        formula=(
            "b<=2: Pv=a*Bac^b*f^c; b>2: "
            "Pv=a*Bfundamental^(b-2)*f^c*Bac^2"
        ),
        output_basis="volumetric_w_per_m3",
        coefficient_names=("a", "b", "c"),
        material_inputs=(),
        runtime_inputs=(
            "frequency_hz",
            "flux_ac_peak_t",
            "fundamental_flux_amplitude_t_when_b_gt_2",
        ),
        source_reference=f"MKF {PINNED_MKF_COMMIT} CoreLosses.cpp",
        native_unit_policy="Parsed coefficients produce SI W/m3 from Hz and T",
    ),
    CoreLossMethodSpecification(
        method="poco",
        formula_id="mkf_poco_v1",
        formula=(
            "Pv=1000*(a*(Bac*10)^b*(f/1000)+c*(Bac*10*f/1000)^2)"
        ),
        output_basis="volumetric_w_per_m3",
        coefficient_names=("a", "b", "c"),
        material_inputs=(),
        runtime_inputs=("frequency_hz", "flux_ac_peak_t"),
        source_reference=f"MKF {PINNED_MKF_COMMIT} CoreLosses.cpp",
        native_unit_policy="B*10 and f/1000 are local; native output*1000 gives W/m3",
    ),
    CoreLossMethodSpecification(
        method="tdg",
        formula_id="mkf_tdg_v1",
        formula=(
            "Pv=1000*(Bac*10)^a*(b*(f/1000)+c*(f/1000)^d)"
        ),
        output_basis="volumetric_w_per_m3",
        coefficient_names=("a", "b", "c", "d"),
        material_inputs=(),
        runtime_inputs=("frequency_hz", "flux_ac_peak_t"),
        source_reference=f"MKF {PINNED_MKF_COMMIT} CoreLosses.cpp",
        native_unit_policy="B*10 and f/1000 are local; native output*1000 gives W/m3",
    ),
    CoreLossMethodSpecification(
        method="lossFactor",
        formula_id="mkf_loss_factor_esr_v1",
        formula=(
            "loss_tangent=loss_factor*mu_i; "
            "Rseries=loss_tangent*2*pi*f*Lm; Pcore=Rseries*Imag_rms^2"
        ),
        output_basis="total_w",
        coefficient_names=(),
        material_inputs=("loss_factor_table", "initial_permeability"),
        runtime_inputs=(
            "frequency_hz",
            "temperature_c",
            "magnetizing_inductance_h",
            "magnetizing_current_rms_a",
        ),
        source_reference=f"MKF {PINNED_MKF_COMMIT} CoreLosses.cpp",
        native_unit_policy="Rseries*Irms^2 is total W and is never multiplied by volume",
    ),
    CoreLossMethodSpecification(
        method="roshen",
        formula_id="mkf_roshen_components_v1",
        formula="Pv_total=Pv_hysteresis+Pv_classical_eddy+Pv_excess_eddy",
        output_basis="volumetric_w_per_m3",
        coefficient_names=(),
        material_inputs=(
            "coercive_force",
            "remanence",
            "saturation_flux_density",
            "saturation_field_strength",
            "resistivity_or_complete_resistivity_fit",
        ),
        runtime_inputs=(
            "frequency_hz",
            "temperature_c",
            "closed_flux_waveform",
            "eddy_current_path_area_m2",
        ),
        source_reference=f"MKF {PINNED_MKF_COMMIT} CoreLosses.cpp",
        native_unit_policy="SI A/m,T,ohm*m,m2,s,W/m3",
    ),
    CoreLossMethodSpecification(
        method="magnetec",
        formula_id="mkf_magnetec_mass_v1",
        formula="Pmass=80*(f/100000)^1.8*(Bpp/0.3)^2",
        output_basis="mass_w_per_kg",
        coefficient_names=(),
        material_inputs=(),
        runtime_inputs=("frequency_hz", "flux_peak_to_peak_t", "core_mass_kg_for_total_w"),
        source_reference=f"MKF {PINNED_MKF_COMMIT} CoreLosses.cpp",
        native_unit_policy="W/kg remains mass based until multiplied by explicit core mass",
    ),
)

_SPEC_BY_METHOD = {spec.method: spec for spec in METHOD_SPECIFICATIONS}
_NON_STEINMETZ_METHODS = frozenset(_SPEC_BY_METHOD) - {"steinmetz"}
_ROSHEN_RESISTIVITY_COEFFICIENTS = frozenset(
    {
        "resistivityFrequencyCoefficient",
        "resistivityMagneticFluxDensityCoefficient",
        "resistivityOffset",
        "resistivityTemperatureCoefficient",
    }
)


def assess_material_loss_coverage(material: NormalizedMagneticMaterialV2) -> dict[str, object]:
    """Return method-level material and runtime input coverage for one material."""

    if not isinstance(material, NormalizedMagneticMaterialV2):
        raise TypeError("material must be NormalizedMagneticMaterialV2.")
    grouped: dict[str, list[MaterialLossModel]] = defaultdict(list)
    for model in material.loss_models:
        grouped[model.method].append(model)

    method_assessments: list[dict[str, object]] = []
    complete_methods: list[str] = []
    incomplete_methods: list[str] = []
    for method in sorted(grouped):
        model_assessments = [_assess_model(material, model) for model in sorted(
            grouped[method], key=lambda item: (item.scope, item.model_id)
        )]
        complete = any(bool(item["material_input_complete"]) for item in model_assessments)
        missing = sorted(
            {
                value
                for item in model_assessments
                for value in item["missing_material_inputs"]
            }
        )
        runtime = sorted(
            {
                value
                for item in model_assessments
                for value in item["required_runtime_inputs"]
            }
        )
        method_assessments.append(
            {
                "method": method,
                "material_input_complete": complete,
                "missing_material_inputs": [] if complete else missing,
                "required_runtime_inputs": runtime,
                "model_assessments": model_assessments,
            }
        )
        (complete_methods if complete else incomplete_methods).append(method)

    measured = _assess_measured_datasets(material)
    scopes = sorted({model.scope for model in material.loss_models})
    methods = sorted(grouped)
    return {
        "material_id": material.material_id,
        "material_name": material.material_name,
        "manufacturer": material.manufacturer,
        "source_record_index": material.source_provenance.source_record_index,
        "source_record_sha256": material.source_provenance.source_record_sha256,
        "declared_methods": methods,
        "declared_scopes": scopes,
        "method_count": len(methods),
        "model_record_count": len(material.loss_models),
        "has_multiple_methods": len(methods) > 1,
        "has_multiple_scopes": len(scopes) > 1,
        "has_steinmetz": "steinmetz" in grouped,
        "has_declared_non_steinmetz": bool(set(methods) & _NON_STEINMETZ_METHODS),
        "material_input_complete_methods": complete_methods,
        "material_input_incomplete_methods": incomplete_methods,
        "method_assessments": method_assessments,
        "measured_data": measured,
        "has_any_loss_data": bool(methods) or bool(material.measured_loss_datasets),
        "has_any_material_complete_model": bool(complete_methods),
        "has_any_material_complete_non_steinmetz_model": bool(
            set(complete_methods) & _NON_STEINMETZ_METHODS
        ),
    }


def summarize_material_loss_coverage(
    materials: Iterable[NormalizedMagneticMaterialV2],
    *,
    include_material_assessments: bool = True,
) -> dict[str, object]:
    """Aggregate unique-material coverage without conflating model records."""

    ordered = sorted(tuple(materials), key=lambda item: item.material_id)
    if len({material.material_id for material in ordered}) != len(ordered):
        raise ValueError("material_id values must be unique for coverage audit.")
    assessments = [assess_material_loss_coverage(material) for material in ordered]

    declared_counts: Counter[str] = Counter()
    complete_counts: Counter[str] = Counter()
    incomplete_counts: Counter[str] = Counter()
    model_counts: Counter[str] = Counter()
    missing_counts: dict[str, Counter[str]] = defaultdict(Counter)
    runtime_requirements: dict[str, set[str]] = defaultdict(set)
    scope_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for assessment in assessments:
        for method_assessment in assessment["method_assessments"]:
            method = str(method_assessment["method"])
            declared_counts[method] += 1
            if method_assessment["material_input_complete"]:
                complete_counts[method] += 1
            else:
                incomplete_counts[method] += 1
                missing_counts[method].update(method_assessment["missing_material_inputs"])
            runtime_requirements[method].update(method_assessment["required_runtime_inputs"])
            for model in method_assessment["model_assessments"]:
                model_counts[method] += 1
                scope_counts[method][str(model["scope"])] += 1

    summary: dict[str, object] = {
        "contract_version": STEP7A_COVERAGE_CONTRACT_VERSION,
        "material_count": len(assessments),
        "materials_with_loss_data": sum(bool(item["has_any_loss_data"]) for item in assessments),
        "materials_without_loss_data": sum(not bool(item["has_any_loss_data"]) for item in assessments),
        "materials_with_steinmetz": sum(bool(item["has_steinmetz"]) for item in assessments),
        "materials_with_declared_non_steinmetz": sum(
            bool(item["has_declared_non_steinmetz"]) for item in assessments
        ),
        "materials_with_multiple_methods": sum(
            bool(item["has_multiple_methods"]) for item in assessments
        ),
        "materials_with_multiple_scopes": sum(
            bool(item["has_multiple_scopes"]) for item in assessments
        ),
        "materials_with_any_material_complete_model": sum(
            bool(item["has_any_material_complete_model"]) for item in assessments
        ),
        "materials_with_any_material_complete_non_steinmetz_model": sum(
            bool(item["has_any_material_complete_non_steinmetz_model"])
            for item in assessments
        ),
        "declared_material_counts_by_method": dict(sorted(declared_counts.items())),
        "material_input_complete_counts_by_method": dict(sorted(complete_counts.items())),
        "material_input_incomplete_counts_by_method": dict(sorted(incomplete_counts.items())),
        "model_record_counts_by_method": dict(sorted(model_counts.items())),
        "missing_material_input_counts_by_method": {
            method: dict(sorted(counts.items()))
            for method, counts in sorted(missing_counts.items())
        },
        "required_runtime_inputs_by_method": {
            method: sorted(values) for method, values in sorted(runtime_requirements.items())
        },
        "scope_record_counts_by_method": {
            method: dict(sorted(counts.items()))
            for method, counts in sorted(scope_counts.items())
        },
        "measured_dataset_count": sum(
            int(item["measured_data"]["dataset_count"]) for item in assessments
        ),
        "measured_point_count": sum(
            int(item["measured_data"]["point_count"]) for item in assessments
        ),
        "materials_with_measured_data": sum(
            int(item["measured_data"]["dataset_count"]) > 0 for item in assessments
        ),
        "materials_with_measured_exact_lookup_ready": sum(
            bool(item["measured_data"]["exact_lookup_ready"]) for item in assessments
        ),
        "materials_with_measured_one_axis_interpolation_ready": sum(
            bool(item["measured_data"]["one_axis_interpolation_ready"])
            for item in assessments
        ),
        "method_specifications": [spec.to_dict() for spec in METHOD_SPECIFICATIONS],
        "material_input_incomplete_assessments": [
            item for item in assessments if item["material_input_incomplete_methods"]
        ],
        "materials_without_loss_assessments": [
            item for item in assessments if not item["has_any_loss_data"]
        ],
    }
    if include_material_assessments:
        summary["material_assessments"] = assessments
    return summary


def _assess_model(
    material: NormalizedMagneticMaterialV2,
    model: MaterialLossModel,
) -> dict[str, object]:
    spec = _SPEC_BY_METHOD.get(model.method)
    missing: list[str] = []
    runtime_inputs = tuple(spec.runtime_inputs) if spec is not None else ()
    if spec is None:
        missing.append("supported_method_implementation")
    else:
        for name in spec.coefficient_names:
            if name not in model.coefficients:
                missing.append(f"coefficient:{name}")
        if model.method == "lossFactor":
            if not model.tabulated_points:
                missing.append("loss_factor_table")
            if not _has_initial_permeability(material.permeability_data):
                missing.append("initial_permeability")
        elif model.method == "roshen":
            if not _has_positive_property_point(
                material.coercive_force_data, ("magnetic_field_a_per_m",)
            ):
                missing.append("coercive_force")
            if not _has_positive_property_point(
                material.remanence_data, ("magnetic_flux_density_t",)
            ):
                missing.append("remanence")
            if not _has_positive_property_point(
                material.saturation_data,
                ("magnetic_flux_density_t", "magnetic_field_a_per_m"),
            ):
                missing.extend(("saturation_flux_density", "saturation_field_strength"))
            has_resistivity = _has_positive_property_point(
                material.resistivity_data, ("resistivity_ohm_m",)
            )
            has_fit = _ROSHEN_RESISTIVITY_COEFFICIENTS.issubset(model.coefficients)
            if not has_resistivity and not has_fit:
                missing.append("resistivity_or_complete_resistivity_fit")
        elif model.method == "magnetec" and model.output_basis != "mass_w_per_kg":
            missing.append("mass_w_per_kg_output_basis")

    return {
        "model_id": model.model_id,
        "method": model.method,
        "scope": model.scope,
        "output_basis": model.output_basis,
        "formula_id": None if spec is None else spec.formula_id,
        "material_input_complete": not missing,
        "missing_material_inputs": sorted(set(missing)),
        "required_runtime_inputs": list(runtime_inputs),
        "source_reference": model.source_reference,
    }


def _assess_measured_datasets(material: NormalizedMagneticMaterialV2) -> dict[str, object]:
    point_count = sum(len(dataset.points) for dataset in material.measured_loss_datasets)
    exact_ready = any(
        point.frequency_hz is not None
        and point.flux_density_t is not None
        and point.temperature_c is not None
        for dataset in material.measured_loss_datasets
        for point in dataset.points
    )
    one_axis_ready = any(
        _dataset_has_one_axis_bracket(dataset.points)
        for dataset in material.measured_loss_datasets
    )
    return {
        "dataset_count": len(material.measured_loss_datasets),
        "point_count": point_count,
        "exact_lookup_ready": exact_ready,
        "one_axis_interpolation_ready": one_axis_ready,
        "dataset_ids": sorted(dataset.dataset_id for dataset in material.measured_loss_datasets),
    }


def _dataset_has_one_axis_bracket(points: Sequence[Any]) -> bool:
    coordinates = [
        (point.frequency_hz, point.flux_density_t, point.temperature_c)
        for point in points
        if point.frequency_hz is not None
        and point.flux_density_t is not None
        and point.temperature_c is not None
    ]
    for left_index, left in enumerate(coordinates):
        for right in coordinates[left_index + 1 :]:
            differing = sum(a != b for a, b in zip(left, right))
            if differing == 1:
                return True
    return False


def _has_initial_permeability(data: Mapping[str, Any]) -> bool:
    root = data.get("data")
    if not isinstance(root, Mapping):
        return False
    points = root.get("initial")
    if not _is_sequence(points):
        return False
    return any(
        isinstance(point, Mapping)
        and _positive_number(point.get("relative_permeability"))
        for point in points
    )


def _has_positive_property_point(
    data: Mapping[str, Any],
    required_fields: tuple[str, ...],
) -> bool:
    points = data.get("points")
    if not _is_sequence(points):
        return False
    return any(
        isinstance(point, Mapping)
        and all(_positive_number(point.get(field)) for field in required_fields)
        for point in points
    )


def _is_sequence(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _positive_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) > 0.0
    )


__all__ = [
    "CoreLossMethodSpecification",
    "METHOD_SPECIFICATIONS",
    "PINNED_MKF_COMMIT",
    "STEP7A_COVERAGE_CONTRACT_VERSION",
    "assess_material_loss_coverage",
    "summarize_material_loss_coverage",
]
