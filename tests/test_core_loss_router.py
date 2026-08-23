from pe_claw_gui.engines.magnetics.core_loss_router import route_core_loss
from pe_claw_gui.models.magnetic_loss_contract import (
    CoreLossExcitation,
    MaterialLossModel,
    MeasuredLossDataset,
    MeasuredLossPoint,
    NormalizedMagneticMaterialV2,
    SourceProvenance,
)


def _provenance() -> SourceProvenance:
    return SourceProvenance("fixture", "MAS", "fixture.ndjson", "881cceaf1d91ee88c8c5b5b611a0703e6126e825", "v1", 0, "TP4", "0" * 64, "1" * 64)


def _excitation() -> CoreLossExcitation:
    return CoreLossExcitation(100000.0, 25.0, (0.0, 5e-6, 10e-6), (0.0, 0.1, 0.0), 0.06666666666666667, 0.1, 0.03333333333333333, 0.1, 1e-6, None, None, None, "triangular", "fixture", "core")


def _material(models=(), measured=()):
    return NormalizedMagneticMaterialV2("mat:fixture", "fixture", "test", None, None, None, 5000.0, None, None, None, {}, {}, {}, {}, {}, {}, tuple(models), tuple(measured), None, _provenance(), "openmagnetics-normalized-v2")


def test_router_records_measured_default_exclusion() -> None:
    dataset = MeasuredLossDataset("measured", "default", "triangular", "volumetric_w_per_m3", (MeasuredLossPoint(100000.0, 25.0, 0.1, 10.0, None),), (100000.0, 100000.0), (0.1, 0.1), (25.0, 25.0), "fixture", _provenance())
    result = route_core_loss(material=_material(measured=(dataset,)), excitation=_excitation())
    assert result.core_loss_w is None
    assert result.routing_attempts[-1]["method"] == "measured"
    assert result.routing_attempts[-1]["selected"] is False


def test_router_selects_steinmetz_and_preserves_attempts() -> None:
    model = MaterialLossModel("model:stein", "steinmetz", "default", {"k": 1.0, "alpha": 1.0, "beta": 1.0}, {"k": "SI", "alpha": "1", "beta": "1"}, "ac_peak_t", "volumetric_w_per_m3", (100000.0, 100000.0), (0.0, 0.1), (25.0, 25.0), (), "fixture", _provenance())
    result = route_core_loss(material=_material(models=(model,)), excitation=_excitation())
    assert result.volumetric_loss_w_per_m3 is not None
    assert result.routing_attempts
    assert any(attempt["selected"] for attempt in result.routing_attempts)


def test_router_rejects_out_of_range_igse_instead_of_selecting_diagnostic_value() -> None:
    model = MaterialLossModel("model:stein", "steinmetz", "default", {"k": 1.0, "alpha": 1.0, "beta": 1.0}, {"k": "SI", "alpha": "1", "beta": "1"}, "ac_peak_t", "volumetric_w_per_m3", (1.0, 50000.0), None, None, (), "fixture", _provenance())
    result = route_core_loss(material=_material(models=(model,)), excitation=_excitation())
    assert result.core_loss_w is None
    assert result.volumetric_loss_w_per_m3 is None
    assert result.validity_status.value == "loss_data_not_available"
    assert result.routing_attempts[0]["method"] == "igse"
    assert result.routing_attempts[0]["result_status"] == "outside_frequency_range"
    assert result.routing_attempts[0]["selected"] is False
