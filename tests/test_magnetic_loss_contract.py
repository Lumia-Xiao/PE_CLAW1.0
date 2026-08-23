from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.libraries.magnetics.normalized_backend_loader import (
    V1_ENGINE_MATERIAL_COLUMNS,
    normalized_openmagnetics_to_engine_dataframes,
    normalized_v2_materials_to_v1_dataframe,
)
from pe_claw_gui.libraries.magnetics.openmagnetics_normalizer import (
    load_normalized_openmagnetics_cache,
    stable_v2_record_id,
)
from pe_claw_gui.models.magnetic_loss_contract import (
    CoreLossExcitation,
    CoreLossEvaluationContext,
    CoreLossResult,
    CoreLossValidityStatus,
    MaterialLossModel,
    MeasuredLossDataset,
    MeasuredLossPoint,
    NormalizedMagneticMaterialV2,
    SourceProvenance,
    TabulatedModelPoint,
)


_CACHE_SHA256 = "40d8f6fb0cdf9b20957806316db87db1f6e6aab81f7a316f978f8ed38a86636a"


def _provenance(*, index: int = 7, reference: str | None = "N87") -> SourceProvenance:
    return SourceProvenance(
        source_kind="packaged_ndjson",
        source_project="OpenMagnetics/MAS",
        source_file=r"data\core_materials.ndjson",
        source_commit="a" * 40,
        source_schema_version="MAS pinned schema",
        source_record_index=index,
        source_record_reference=reference,
        source_record_sha256="1" * 64,
        dataset_sha256="2" * 64,
    )


def _steinmetz_model(*, model_id: str = "model:n87:1") -> MaterialLossModel:
    return MaterialLossModel(
        model_id=model_id,
        method="steinmetz",
        scope="default",
        coefficients={"beta": 2.6, "k": 0.002, "alpha": 1.4},
        coefficient_units={"alpha": "1", "beta": "1", "k": "W/m3/Hz^alpha/T^beta"},
        input_flux_definition="ac_peak_t",
        output_basis="volumetric_w_per_m3",
        valid_frequency_range_hz=(10_000.0, 500_000.0),
        valid_flux_density_range_t=(0.01, 0.25),
        valid_temperature_range_c=(25.0, 120.0),
        tabulated_points=(),
        source_reference="volumetricLosses.default[0].ranges[0]",
        source_provenance=_provenance(),
    )


def _measured_dataset() -> MeasuredLossDataset:
    return MeasuredLossDataset(
        dataset_id="dataset:n87:1",
        scope="default",
        input_flux_definition="ac_peak_t",
        output_basis="volumetric_w_per_m3",
        points=(
            MeasuredLossPoint(
                frequency_hz=100_000.0,
                temperature_c=100.0,
                flux_density_t=0.1,
                volumetric_loss_w_per_m3=120_000.0,
                mass_loss_w_per_kg=None,
            ),
        ),
        valid_frequency_range_hz=(100_000.0, 100_000.0),
        valid_flux_density_range_t=(0.1, 0.1),
        valid_temperature_range_c=(100.0, 100.0),
        source_reference="volumetricLosses.measurements",
        source_provenance=_provenance(),
    )


def _material(
    *,
    material_id: str = "material:tdk_n87:1",
    material_name: str = "N87",
    loss_models: tuple[MaterialLossModel, ...] | None = None,
) -> NormalizedMagneticMaterialV2:
    return NormalizedMagneticMaterialV2(
        material_id=material_id,
        material_name=material_name,
        manufacturer="TDK",
        family="ferrite",
        composition="MnZn ferrite",
        application="power",
        density_kg_per_m3=4850.0,
        curie_temperature_c=220.0,
        thermal_conductivity_w_per_m_k=4.0,
        specific_heat_j_per_kg_k=750.0,
        resistivity_data={"temperature_c": [25.0, 100.0], "resistivity_ohm_m": [5.0, 2.0]},
        saturation_data={
            "b_sat_t": 0.49,
            "b_sat_100c_t": 0.39,
            "b_sat_100c_source": "exact",
        },
        remanence_data={},
        coercive_force_data={},
        permeability_data={"initial": 2200.0},
        dc_bias_data={},
        loss_models=(_steinmetz_model(),) if loss_models is None else loss_models,
        measured_loss_datasets=(_measured_dataset(),),
        recommended_frequency_range_hz=(25_000.0, 500_000.0),
        source_provenance=_provenance(),
    )


def _excitation() -> CoreLossExcitation:
    return CoreLossExcitation(
        frequency_hz=100_000.0,
        temperature_c=100.0,
        flux_waveform_time_s=(0.0, 2.5e-6, 5e-6, 7.5e-6, 10e-6),
        flux_waveform_t=(0.0, 0.1, 0.0, -0.1, 0.0),
        flux_ac_peak_t=0.1,
        flux_peak_to_peak_t=0.2,
        flux_dc_offset_t=0.0,
        flux_absolute_peak_t=0.1,
        effective_volume_m3=1.2e-5,
        core_mass_kg=0.0582,
        magnetizing_inductance_h=100e-6,
        magnetizing_current_rms_a=2.0,
        waveform_definition="periodic_piecewise_linear",
        source_topology="llc_full_bridge_diode_rectifier",
        source_role="transformer_core",
    )


def _result(status: CoreLossValidityStatus = CoreLossValidityStatus.VALID) -> CoreLossResult:
    is_valid = status in {CoreLossValidityStatus.VALID, CoreLossValidityStatus.VALID_INTERPOLATED}
    return CoreLossResult(
        core_loss_w=1.44 if is_valid else None,
        volumetric_loss_w_per_m3=120_000.0 if is_valid else None,
        mass_loss_w_per_kg=None,
        method_used="steinmetz" if is_valid else None,
        model_policy="declared_material_model",
        material_id="material:tdk_n87:1",
        material_name="N87",
        temperature_c=100.0,
        frequency_hz=100_000.0,
        flux_ac_peak_t=0.1,
        flux_dc_offset_t=0.0,
        validity_status=status,
        validity_messages=("within declared model range",) if is_valid else (status.value,),
        interpolated=status is CoreLossValidityStatus.VALID_INTERPOLATED,
        fitted=False,
        extrapolated=False,
        proxy_used=False,
        source_provenance=_provenance(),
    )


def _evaluation_context() -> CoreLossEvaluationContext:
    return CoreLossEvaluationContext(
        fundamental_flux_amplitude_t=0.08,
        fundamental_extraction_method="closed_period_dft_excluding_duplicate_endpoint",
        eddy_current_path_area_m2=25e-6,
        source_fields=("flux_waveform_t", "core.columns[0].area_m2"),
    )


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(_provenance(), id="source-provenance"),
        pytest.param(
            TabulatedModelPoint(
                coordinates={"frequency_hz": 100_000.0},
                coordinate_units={"frequency_hz": "Hz"},
                value_name="loss_factor",
                value=0.01,
                value_unit="1",
                source_reference="volumetricLosses.default[0].factors[0]",
            ),
            id="tabulated-model-point",
        ),
        pytest.param(_steinmetz_model(), id="material-loss-model"),
        pytest.param(_measured_dataset().points[0], id="measured-loss-point"),
        pytest.param(_measured_dataset(), id="measured-loss-dataset"),
        pytest.param(_material(), id="normalized-material-v2"),
        pytest.param(_excitation(), id="core-loss-excitation"),
        pytest.param(_evaluation_context(), id="core-loss-evaluation-context"),
        pytest.param(_result(), id="core-loss-result"),
    ],
)
def test_contract_types_round_trip_deterministic_json(value) -> None:
    encoded = value.to_json()
    decoded = type(value).from_json(encoded)

    assert decoded == value
    assert decoded.to_json() == encoded
    assert json.loads(encoded) == value.to_dict()


def test_json_is_independent_of_mapping_insertion_order() -> None:
    first = _steinmetz_model()
    second = MaterialLossModel(
        **{
            **first.to_dict(),
            "coefficients": {"alpha": 1.4, "beta": 2.6, "k": 0.002},
            "coefficient_units": {"k": "W/m3/Hz^alpha/T^beta", "beta": "1", "alpha": "1"},
            "source_provenance": first.source_provenance,
        }
    )

    assert first.to_json() == second.to_json()


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_numbers_are_rejected(invalid: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        MeasuredLossPoint(100_000.0, 25.0, 0.1, invalid, None)
    with pytest.raises(ValueError, match="finite"):
        NormalizedMagneticMaterialV2(
            **{
                **_material().to_dict(),
                "resistivity_data": {"value": invalid},
                "loss_models": (),
                "measured_loss_datasets": (),
                "source_provenance": _provenance(),
            }
        )


def test_unknown_json_fields_are_rejected() -> None:
    payload = _provenance().to_dict()
    payload["unexpected"] = True

    with pytest.raises(ValueError, match="unknown=.*unexpected"):
        SourceProvenance.from_dict(payload)


@pytest.mark.parametrize("status", list(CoreLossValidityStatus))
def test_every_validity_status_round_trips(status: CoreLossValidityStatus) -> None:
    result = _result(status)

    assert CoreLossResult.from_json(result.to_json()).validity_status is status


def test_unavailable_loss_is_none_and_never_zero_filled() -> None:
    result = _result(CoreLossValidityStatus.LOSS_DATA_NOT_AVAILABLE)

    assert result.core_loss_w is None
    assert result.volumetric_loss_w_per_m3 is None
    assert result.mass_loss_w_per_kg is None


def test_core_loss_result_step7a_audit_fields_round_trip_and_freeze() -> None:
    result = CoreLossResult(
        **{
            **_result().to_dict(),
            "source_provenance": _provenance(),
            "validity_status": CoreLossValidityStatus.VALID,
            "validity_messages": ("valid",),
            "loss_components": {"hysteresis_loss_w": 0.4, "eddy_loss_w": 1.04},
            "model_evaluation_details": {
                "fundamental_flux_amplitude_t": 0.08,
                "native_unit_inputs": {"frequency_khz": 100.0},
            },
            "range_handling": "within_declared_range",
            "routing_attempts": (
                {
                    "method": "magnetics",
                    "eligible": True,
                    "selected": True,
                    "missing_required_inputs": [],
                },
            ),
        }
    )

    restored = CoreLossResult.from_json(result.to_json())

    assert restored == result
    assert restored.loss_components["hysteresis_loss_w"] == pytest.approx(0.4)
    assert restored.routing_attempts[0]["selected"] is True
    with pytest.raises(TypeError):
        restored.loss_components["hysteresis_loss_w"] = 0.0


def test_core_loss_result_reads_pre_step7a_payload_with_default_audit_fields() -> None:
    payload = _result().to_dict()
    for field in (
        "loss_components",
        "model_evaluation_details",
        "range_handling",
        "routing_attempts",
    ):
        payload.pop(field)

    restored = CoreLossResult.from_dict(payload)

    assert restored.loss_components is None
    assert restored.model_evaluation_details is None
    assert restored.range_handling is None
    assert restored.routing_attempts == ()


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"fundamental_flux_amplitude_t": float("nan")}, "finite"),
        ({"eddy_current_path_area_m2": 0.0}, "greater than zero"),
        (
            {
                "fundamental_flux_amplitude_t": 0.1,
                "fundamental_extraction_method": None,
            },
            "fundamental_extraction_method is required",
        ),
    ],
)
def test_evaluation_context_rejects_invalid_inputs(
    changes: dict[str, object], message: str
) -> None:
    values = _evaluation_context().to_dict()
    values.update(changes)

    with pytest.raises(ValueError, match=message):
        CoreLossEvaluationContext.from_dict(values)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"frequency_hz": 0.0}, "frequency_hz must be greater"),
        ({"flux_waveform_t": (0.0, 0.1)}, "equal length"),
        ({"flux_waveform_time_s": (0.0, 1e-6, 0.5e-6, 7.5e-6, 10e-6)}, "strictly increasing"),
        ({"effective_volume_m3": -1.0}, "effective_volume_m3 must be greater"),
        ({"flux_peak_to_peak_t": 0.1}, "conflicts with waveform"),
    ],
)
def test_excitation_rejects_invalid_or_conflicting_waveforms(changes: dict[str, object], message: str) -> None:
    values = _excitation().to_dict()
    values.update(changes)

    with pytest.raises(ValueError, match=message):
        CoreLossExcitation.from_dict(values)


@pytest.mark.parametrize(
    ("name", "manufacturer", "indices"),
    [("TMFD", "TDG", (370, 371)), ("XFlux 125", "Magnetics", (102, 103))],
)
def test_v2_ids_separate_real_duplicate_material_names(
    name: str,
    manufacturer: str,
    indices: tuple[int, int],
) -> None:
    common = {
        "manufacturer": manufacturer,
        "record_name": name,
        "record_type": "material",
        "source_file": r"data\core_materials.ndjson",
        "source_record_sha256": "b" * 64,
    }
    first = stable_v2_record_id(**common, source_record_index=indices[0])
    second = stable_v2_record_id(**common, source_record_index=indices[1])

    assert first != second
    assert first == stable_v2_record_id(**common, source_record_index=indices[0])
    assert first.startswith(f"material:{manufacturer.casefold()}_")


def test_v2_id_normalizes_unicode_case_whitespace_and_paths() -> None:
    first = stable_v2_record_id(
        manufacturer="  TDK  ",
        record_name="Ｎ８７",
        record_type="Material",
        source_file=r"data\core_materials.ndjson",
        source_record_reference=" N87 ",
    )
    second = stable_v2_record_id(
        manufacturer="tdk",
        record_name="n87",
        record_type="material",
        source_file="data/core_materials.ndjson",
        source_record_reference="n87",
    )

    assert first == second


def test_v2_steinmetz_projection_matches_exact_v1_dataframe_contract() -> None:
    first = _material(material_id="material:first")
    duplicate = _material(material_id="material:second")
    roshen = MaterialLossModel(
        model_id="model:roshen:1",
        method="roshen",
        scope="default",
        coefficients={"mu": 1.0},
        coefficient_units={"mu": "1"},
        input_flux_definition="ac_peak_t",
        output_basis="method_specific",
        valid_frequency_range_hz=None,
        valid_flux_density_range_t=None,
        valid_temperature_range_c=None,
        tabulated_points=(),
        source_reference="volumetricLosses.default[0]",
        source_provenance=_provenance(),
    )
    non_steinmetz = _material(
        material_id="material:roshen",
        material_name="R-material",
        loss_models=(roshen,),
    )

    dataframe = normalized_v2_materials_to_v1_dataframe((first, duplicate, non_steinmetz))

    assert tuple(dataframe.columns) == V1_ENGINE_MATERIAL_COLUMNS
    assert dataframe.index.name == "mat_name"
    assert list(dataframe.index) == ["N87"]
    row = dataframe.loc["N87"]
    assert row["manufacturer"] == "TDK"
    assert row["material_type"] == "MnZn ferrite"
    assert row["B_sat"] == pytest.approx(0.49)
    assert row["B_sat_100c"] == pytest.approx(0.39)
    assert row["density"] == pytest.approx(4850.0)
    assert row["steinmetz_ranges"] == [
        {
            "minimumFrequency": 10_000.0,
            "maximumFrequency": 500_000.0,
            "k": 0.002,
            "alpha": 1.4,
            "beta": 2.6,
        }
    ]


def test_non_steinmetz_material_remains_v2_but_projects_to_empty_v1_dataframe() -> None:
    material = _material(loss_models=())
    restored = NormalizedMagneticMaterialV2.from_json(material.to_json())
    dataframe = normalized_v2_materials_to_v1_dataframe((restored,))

    assert restored.material_name == "N87"
    assert restored.loss_models == ()
    assert dataframe.empty
    assert tuple(dataframe.columns) == V1_ENGINE_MATERIAL_COLUMNS


def test_normalized_v1_cache_and_engine_material_baselines_remain_unchanged() -> None:
    root = Path(__file__).resolve().parents[1]
    cache_path = (
        root
        / "src"
        / "pe_claw_gui"
        / "libraries"
        / "magnetics"
        / "normalized_openmagnetics"
        / "core_materials_normalized.json"
    )
    database = load_normalized_openmagnetics_cache()
    _, engine_materials, _ = normalized_openmagnetics_to_engine_dataframes(database)

    assert len(database.core_materials) == 411
    assert len(engine_materials) == 94
    assert hashlib.sha256(cache_path.read_bytes()).hexdigest() == _CACHE_SHA256
