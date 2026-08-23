from __future__ import annotations

import sys

import pytest

from pe_claw_gui import models
from pe_claw_gui.models import (
    CommonSpec,
    DesignReport,
    MaterialLossModel,
    OperatingPoint,
    SourceProvenance,
    WindingElectricalEvidence,
)
from pe_claw_gui.models.capacitor import CapacitorSizingRequest
from pe_claw_gui.topologies.base import build_default_registry
from pe_claw_gui.topologies.dc_dc.buck_diode_rectified_unidirectional import (
    PLUGIN as BUCK_PLUGIN,
    build_default_inputs as build_buck_default_inputs,
)


def _spec() -> CommonSpec:
    return CommonSpec(
        topology_id="buck_diode_rectified_unidirectional",
        display_name="Buck Diode Rectified Unidirectional",
        vin_min=300.0,
        vin_max=400.0,
        vout=200.0,
        pout=1000.0,
        fs_khz=100.0,
        ripple_current_ratio=0.3,
        ripple_voltage_ratio_percent=1.0,
    )


def test_model_package_excludes_ai_and_agentic_routing_contracts() -> None:
    assert not hasattr(models, "AIDesignReport")
    assert not hasattr(models, "TopologyRecommendation")
    assert not hasattr(models, "DesignCheckResult")

    forbidden = [
        name
        for name in sys.modules
        if name.startswith(("pe_claw_gui.agentic", "pe_claw_gui.agents"))
        or "ai_design" in name
        or "topology_recommendation" in name
    ]
    assert forbidden == []


def test_legacy_model_construction_preserves_new_field_defaults() -> None:
    report = DesignReport(spec=_spec())
    operating_point = OperatingPoint(400.0)
    capacitor_request = CapacitorSizingRequest(
        side="output",
        dc_voltage_v=200.0,
        ripple_ratio_percent=1.0,
        current_time_s=[0.0, 1.0e-6],
        current_waveform_a=[1.0, -1.0],
        switching_frequency_hz=100_000.0,
        ambient_temp_c=40.0,
    )

    assert report.bridge_rectifier is None
    assert report.assessment is None
    assert report.run_efficiency_sweep_runtime_seconds is None
    assert operating_point.load_ratio == 1.0
    assert operating_point.vout_v is None
    assert operating_point.power_factor is None
    assert operating_point.switching_frequency_hz is None
    assert capacitor_request.max_parallel_count == 5
    assert capacitor_request.max_series_count == 1
    assert capacitor_request.allowed_capacitor_technologies is None


def test_default_registry_keeps_phase7_resolvable_topology_contracts() -> None:
    registry = build_default_registry()
    definitions = registry.list_definitions()

    assert len(definitions) == 19
    assert {definition.category_id for definition in definitions} == {"dc_dc", "ac_dc", "dc_ac"}
    for definition in definitions:
        assert registry.get_plugin(definition.topology_id) is not None
        assert registry.get_form_class(definition.topology_id).__name__ == definition.form_class


def test_legacy_buck_plugin_builds_report_with_migrated_models() -> None:
    spec = BUCK_PLUGIN.build_spec(build_buck_default_inputs())
    candidate = BUCK_PLUGIN.synthesize(spec)
    waveform = BUCK_PLUGIN.generate_waveforms(candidate)
    stress = BUCK_PLUGIN.extract_stress(candidate, waveform)
    result = BUCK_PLUGIN.evaluate(candidate, waveform, stress)
    report = BUCK_PLUGIN.build_report(
        spec,
        candidate,
        waveform_set=waveform,
        stress_result=stress,
        topology_result=result,
    )

    assert report.spec.topology_id == "buck_diode_rectified_unidirectional"
    assert report.waveform is not None
    assert len(report.waveform.time_s) == 1200
    assert report.assessment is None
    assert report.bridge_rectifier is None


def test_magnetic_loss_model_json_is_deterministic() -> None:
    provenance = SourceProvenance(
        source_kind="packaged_ndjson",
        source_project="OpenMagnetics/MAS",
        source_file=r"data\core_materials.ndjson",
        source_commit="a" * 40,
        source_schema_version="MAS pinned schema",
        source_record_index=7,
        source_record_reference="N87",
        source_record_sha256="1" * 64,
        dataset_sha256="2" * 64,
    )
    model = MaterialLossModel(
        model_id="model:n87:1",
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
        source_provenance=provenance,
    )

    payload = model.to_json()
    assert MaterialLossModel.from_json(payload).to_json() == payload
    assert '"source_file":"data/core_materials.ndjson"' in payload


def test_winding_evidence_round_trip_and_loss_decomposition() -> None:
    conducting_area_m2 = 1.0e-6
    turns = 10
    mean_length_per_turn_m = 0.08
    parallel_count = 2
    rms_current_a = 3.0
    temperature_factor = 1.22
    rac_multiplier = 1.08
    total_length_m = turns * mean_length_per_turn_m
    rdc_25c_ohm = 1.724e-8 * total_length_m / (conducting_area_m2 * parallel_count)
    dc_loss_w = rms_current_a**2 * rdc_25c_ohm * temperature_factor
    total_loss_w = dc_loss_w * rac_multiplier
    evidence = WindingElectricalEvidence(
        wire_id="wire:maker:test:123456789abc",
        wire_name="Test Litz",
        source_wire_record={"wire_id": "wire:maker:test:123456789abc"},
        conducting_area_m2=conducting_area_m2,
        area_basis="source_area",
        strand_diameter_m=0.1e-3,
        strand_count=100,
        parallel_winding_count=parallel_count,
        turns=turns,
        mean_length_per_turn_m=mean_length_per_turn_m,
        total_conductor_length_m=total_length_m,
        rdc_25c_ohm=rdc_25c_ohm,
        resistance_temperature_c=80.0,
        resistance_temperature_factor=temperature_factor,
        rac_multiplier=rac_multiplier,
        rms_current_a=rms_current_a,
        dc_copper_loss_w=dc_loss_w,
        ac_copper_loss_w=total_loss_w - dc_loss_w,
        total_copper_loss_w=total_loss_w,
        fill_area_m2=22.0e-6,
    )

    restored = WindingElectricalEvidence.from_json(evidence.to_json())
    assert restored.to_json() == evidence.to_json()
    assert restored.total_copper_loss_w == pytest.approx(
        restored.dc_copper_loss_w + restored.ac_copper_loss_w,
        rel=1e-12,
    )
