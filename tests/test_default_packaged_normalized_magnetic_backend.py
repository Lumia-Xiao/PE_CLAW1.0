from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.engines.magnetics.data_backend import (
    MagneticDataBackendConfig,
    get_normalized_v1_rollback_backend_config,
    get_production_magnetic_backend_config,
    resolve_magnetic_data_backend,
)
from pe_claw_gui.engines.magnetics.legacy_external_openmagnetics import InductorDatabaseUnavailableError
from pe_claw_gui.engines.magnetics.inductor_adapter import build_inductor_design_request
from pe_claw_gui.engines.magnetics.inductor_design import (
    build_pareto_front,
    choose_representative_designs,
    synthesize_fixed_inductor_candidates,
    synthesize_fixed_inductor_candidates_with_backend,
)
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.pipeline.run_geometry_pipeline import run_geometry_pipeline
from pe_claw_gui.pipeline.run_loss_pipeline import run_loss_pipeline
from pe_claw_gui.pipeline.run_magnetic_pipeline import run_magnetic_pipeline
from pe_claw_gui.pipeline.run_thermal_pipeline import run_thermal_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry


def test_default_backend_config_is_packaged_normalized_v2_production() -> None:
    bundle = resolve_magnetic_data_backend()

    assert MagneticDataBackendConfig().backend == "packaged_normalized_v2"
    assert bundle.backend == "packaged_normalized_v2"
    assert bundle.mode == "normalized_v2_production"
    assert not bundle.cores.empty
    assert not bundle.materials.empty
    assert not bundle.wires.empty


def test_legacy_external_backend_remains_explicit_reference_path() -> None:
    try:
        bundle = resolve_magnetic_data_backend(MagneticDataBackendConfig(backend="legacy_external"))
    except InductorDatabaseUnavailableError as exc:
        pytest.skip(f"legacy external OpenMagnetics reference data is unavailable: {exc}")

    assert bundle.backend == "legacy_external"
    assert not bundle.cores.empty
    assert not bundle.materials.empty
    assert not bundle.wires.empty


def test_default_candidate_generation_does_not_require_external_environment(monkeypatch) -> None:
    monkeypatch.delenv("PE_CLAW_OPENMAGNETICS_DATA", raising=False)
    request = _default_buck_inductor_request()

    default_candidates = synthesize_fixed_inductor_candidates(request)
    explicit_candidates = synthesize_fixed_inductor_candidates_with_backend(
        request,
        get_production_magnetic_backend_config(),
    )

    # Step 18F uses the physical absolute peak L*Ipeak/(N*Ae) for saturation;
    # the voltage-second Bpp remains a separate core-loss input.
    assert len(default_candidates) == len(explicit_candidates)
    assert default_candidates
    assert build_pareto_front(default_candidates)
    assert choose_representative_designs(build_pareto_front(default_candidates), count=5)


def test_run_magnetics_default_uses_packaged_normalized_and_produces_representatives(monkeypatch) -> None:
    monkeypatch.delenv("PE_CLAW_OPENMAGNETICS_DATA", raising=False)
    report = _default_buck_design_report()

    magnetic_report = run_magnetic_pipeline(report)

    assert magnetic_report.magnetic is not None
    assert magnetic_report.magnetic.feasible_count > 0
    assert magnetic_report.magnetic.pareto_count > 0
    assert magnetic_report.magnetic.chosen_designs
    assert magnetic_report.magnetic.selected_design_id


def test_default_magnetic_chain_produces_loss_thermal_and_geometry_payloads(monkeypatch) -> None:
    monkeypatch.delenv("PE_CLAW_OPENMAGNETICS_DATA", raising=False)
    options = PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=False)
    report = run_magnetic_pipeline(_default_buck_design_report())
    report = run_loss_pipeline(report, pipeline_options=options)
    report = run_thermal_pipeline(report, pipeline_options=options)
    report = run_geometry_pipeline(report, pipeline_options=options)

    assert report.magnetic is not None
    assert report.loss is not None
    assert report.thermal is not None
    assert report.geometry is not None
    assert report.geometry.selected_layout is not None
    assert report.geometry.targets


def test_normalized_v1_remains_available_only_as_explicit_rollback() -> None:
    bundle = resolve_magnetic_data_backend(get_normalized_v1_rollback_backend_config())
    assert bundle.backend == "packaged_normalized"
    assert bundle.mode == "normalized_v1_production"
    assert len(bundle.materials) == 94


def _default_buck_design_report():
    plugin = build_default_registry().get_plugin("buck_diode_rectified_unidirectional")
    module = import_module(plugin.__module__)
    return run_full_pipeline(
        plugin=plugin,
        raw_input=module.build_default_inputs(),
        include_waveforms=False,
        pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
    )


def _default_buck_inductor_request():
    return build_inductor_design_request(_default_buck_design_report())
