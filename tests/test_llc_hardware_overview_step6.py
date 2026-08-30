from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from pe_claw_gui.engines.hardware_overview import (
    build_and_generate_hardware_overview,
    build_hardware_overview_payload,
    build_integrated_hardware_layout_from_groups,
)
from pe_claw_gui.models.capacitor import CapacitorResult
from pe_claw_gui.models.device_result import DeviceSelectionResult
from pe_claw_gui.models.geometry_result import GeometryResult, GeometryTarget
from pe_claw_gui.models.llc_run_context import LlcRunContext
from pe_claw_gui.models.semiconductor_geometry_result import (
    SemiconductorGeometryLayout,
    SemiconductorGeometryResult,
    SemiconductorGeometryRoleLayout,
    SemiconductorGeometryTarget,
)
from pe_claw_gui.pipeline.run_magnetic_pipeline import build_llc_magnetic_combination_contract
from pe_claw_gui.visualization.hardware_overview.renderer import generate_hardware_overview_artifacts

from scripts.build_llc_magnetic_result_display_step1_baseline import build_baseline_report


TOPOLOGY_ID = "llc_resonant_converter_diode_rectifier"


def _succeeded_context(tmp_path: Path, *, include_ids: bool = True) -> LlcRunContext:
    context = LlcRunContext.create(TOPOLOGY_ID, {"fixture": "step6"}, output_root=tmp_path / "run")
    for stage in ("design", "magnetics", "capacitors", "geometry"):
        context = context.transition(stage, "succeeded")
    if include_ids:
        context = context.with_result_ids(
            transformer_design_id="transformer-current",
            external_lr_design_id="external-current",
            combined_magnetic_design_id="transformer-current+external-current",
            cr_design_id="cr-current",
            device_design_id="device-current",
        )
    return context


def _complete_llc_report(tmp_path: Path):
    baseline = build_baseline_report()
    context = _succeeded_context(tmp_path)
    transformer = SimpleNamespace(
        candidate_id="transformer-current",
        core_id="E 80/38/32",
        material_id="SMP97",
        np=18,
        ns=18,
        gap_m=2.0e-3,
        lm_target_h=1.8e-3,
        lm_actual_h=1.82e-3,
        estimated_lk_h=0.12e-3,
        estimated_volume_cm3=108.9,
        total_loss_w=3.74,
        hotspot_c=76.2,
        current_basis_label="fixture",
    )
    external = SimpleNamespace(
        design_id="external-current",
        core_id="E 55/28/25",
        target_l_h=1.08e-3,
        actual_l_h=1.1e-3,
        total_lr_actual_h=1.22e-3,
        estimated_volume_cm3=41.9,
        total_loss_w=1.28,
    )
    external_target = SimpleNamespace(
        external_lr_target_h=1.08e-3,
        lr_total_target_h=1.2e-3,
        fs_basis_hz=85000.0,
        current_basis="sinusoidal_peak",
        current_rms_a=4.0,
        current_peak_a=6.0,
    )
    fha = SimpleNamespace(
        fr_hz=100000.0,
        lr_h=1.2e-3,
        vin_min_v=360.0,
        vin_nom_v=400.0,
        vin_max_v=420.0,
        vout_min_v=47.5,
        vout_nom_v=48.0,
        vout_max_v=48.5,
        worst_case_current_stress={"resonant_tank_peak_a": 6.0},
    )
    contract = build_llc_magnetic_combination_contract(
        report=replace(baseline, llc_run_context=context),
        fha_design=fha,
        transformer_target={"lr_target_h": 1.2e-3},
        transformer=transformer,
        external_lr=external,
        external_lr_target=external_target,
        transformer_artifact_paths=[],
        external_lr_artifact_paths=[],
        external_lr_status="available",
    )
    magnetic = replace(
        baseline.magnetic,
        llc_transformer_result=SimpleNamespace(
            recommended_preliminary_candidate=transformer,
            feasible_candidates=[transformer],
        ),
        transformer_pareto_candidates=[transformer],
        llc_external_resonant_inductor_search_result=SimpleNamespace(
            candidates=[external], feasible_candidates=[external], recommended_candidate=external
        ),
        llc_magnetic_contract=contract,
    )
    cr = SimpleNamespace(
        design_id="cr-current",
        part_number="CR-FIXTURE",
        manufacturer="Fixture",
        series="Cr",
        parallel_count=2,
        bank_capacitance_f=80e-9,
        bank_capacitance_nF=80.0,
        cr_target_f=80e-9,
        cr_target_nF=80.0,
        capacitance_error_percent=0.0,
        estimated_volume_cm3=8.0,
        loss_w=0.2,
        package_shape="rectangular_box",
        body_width_mm=20.0,
        body_depth_mm=10.0,
        body_height_mm=8.0,
    )
    capacitor = CapacitorResult(
        llc_resonant_capacitor_search_result=SimpleNamespace(recommended_candidate=cr)
    )
    device = DeviceSelectionResult(
        selected_devices={"main_switch": "Q1", "rectifier_diode": "D1"},
        recommended_scheme_id="device-current",
    )
    semiconductor_layout = SemiconductorGeometryLayout(
        scheme_id="device-current",
        scheme_label="Fixture semiconductor",
        parallel_count=1,
        part_number="Q1",
        package="TO-247",
        normalized_package="TO-247",
        canonical_package="TO-247",
        package_template_key="to_247",
        package_style="through_hole",
        renderer_template_id="to_247",
        package_family="TO-247",
        package_lead_count=3,
        mounting_style="through_hole",
        package_fallback_warning=None,
        role="main_switch",
        case_id="fixture-case",
        sink_volume_cm3=12.0,
        sink_model_label="Fixture heatsink",
        cooling_mode="natural_convection",
        package_body_width_mm=10.0,
        package_body_height_mm=20.0,
        package_body_thickness_mm=4.0,
        package_tab_width_mm=10.0,
        package_tab_height_mm=15.0,
        package_hole_diameter_mm=3.0,
        lead_pitch_mm=5.0,
        lead_width_mm=1.0,
        lead_length_mm=10.0,
        sink_width_mm=40.0,
        sink_height_mm=25.0,
        sink_depth_mm=20.0,
        sink_fin_count=4,
        scale_bar_mm=10.0,
    )
    semiconductor_role = SemiconductorGeometryRoleLayout(
        role_name="main_switch",
        role_label="Main switch",
        part_number="Q1",
        vendor="Fixture",
        package="TO-247",
        quantity=1,
        total_physical_device_count=1,
        layout=semiconductor_layout,
        package_level="discrete",
    )
    semiconductor_geometry = SemiconductorGeometryResult(
        recommended_scheme_id="device-current",
        targets=(SemiconductorGeometryTarget(
            scheme_id="device-current",
            label="Fixture semiconductor",
            parallel_count=1,
            part_number="Q1",
            package="TO-247",
            role="main_switch",
            role_layouts=(semiconductor_role,),
            estimated_sink_dims_mm=(40.0, 25.0, 20.0),
        ),),
    )
    run_root = Path(context.output_root)
    run_root.mkdir(parents=True, exist_ok=True)
    artifact = run_root / "geometry" / "external-current_2d.png"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("fixture", encoding="ascii")
    layout = SimpleNamespace(
        overall_width_mm=55.0,
        overall_height_mm=28.0,
        overall_depth_mm=25.0,
    )
    geometry = GeometryResult(
        selected_design_id="external-current",
        targets=[GeometryTarget(role="recommended", label="Recommended", design_id="external-current", layout=layout, artifact_paths=[str(artifact)])],
        artifact_paths=[str(artifact)],
    )
    report = replace(
        baseline,
        magnetic=magnetic,
        capacitor=capacitor,
        device=device,
        geometry=geometry,
        semiconductor_geometry=semiconductor_geometry,
        llc_run_context=context,
    )
    return report, context, transformer, external, cr


def test_complete_llc_overview_uses_current_contract_ids_and_integrated_roles(tmp_path: Path) -> None:
    report, context, _, _, _ = _complete_llc_report(tmp_path)

    payload = build_hardware_overview_payload(report)

    assert payload.status == "available"
    assert payload.run_id == context.run_id
    assert payload.source_ids == {
        "transformer_design_id": "transformer-current",
        "external_lr_design_id": "external-current",
        "combined_magnetic_design_id": "transformer-current+external-current",
        "cr_design_id": "cr-current",
        "device_design_id": "device-current",
    }
    assert [group.group_id for group in payload.component_groups] == ["semiconductor", "transformer", "inductor", "capacitor"]
    assert {obj.id for obj in payload.integrated_layout.groups} == {
        "transformer",
        "semiconductor",
        "inductor",
        "llc_resonant_capacitor",
    }
    assert payload.integrated_layout.groups[0].id == "transformer"


def test_llc_overview_rejects_stale_geometry_and_does_not_use_old_loss_ids(tmp_path: Path) -> None:
    report, context, _, _, _ = _complete_llc_report(tmp_path)
    stale_target = replace(report.geometry.targets[0], design_id="old-external-lr")
    stale_geometry = replace(report.geometry, selected_design_id="old-external-lr", targets=[stale_target])
    stale_magnetic = replace(report.magnetic, selected_design_id="old-magnetic", chosen_designs=[SimpleNamespace(candidate_id="old-magnetic")])
    report = replace(report, geometry=stale_geometry, magnetic=replace(stale_magnetic, llc_magnetic_contract=report.magnetic.llc_magnetic_contract))

    payload = build_hardware_overview_payload(report)

    assert payload.status == "blocked"
    assert "geometry selected_design_id" in payload.blocked_reason
    assert payload.run_id == context.run_id
    assert not payload.overview_artifacts
    assert not payload.integrated_overview_artifacts


def test_missing_llc_dependency_is_diagnostic_only(tmp_path: Path) -> None:
    report = replace(build_baseline_report(), llc_run_context=_succeeded_context(tmp_path, include_ids=False))

    payload = build_hardware_overview_payload(report)

    assert payload.status == "blocked"
    assert payload.component_groups
    assert payload.artifact_paths == [str(Path(report.llc_run_context.output_root) / "hardware_overview" / "hardware_overview_payload.json")]
    assert not payload.integrated_overview_artifacts


def test_blocked_renderer_writes_only_diagnostic_json(tmp_path: Path) -> None:
    report = replace(build_baseline_report(), llc_run_context=_succeeded_context(tmp_path, include_ids=False))
    payload = build_hardware_overview_payload(report)
    output_dir = tmp_path / "rendered"

    rendered = generate_hardware_overview_artifacts(payload, output_dir)

    assert rendered.status == "blocked"
    assert (output_dir / "hardware_overview_payload.json").exists()
    assert list(output_dir.iterdir()) == [output_dir / "hardware_overview_payload.json"]


def test_integrated_layout_supports_transformer_and_llc_cr_child() -> None:
    from pe_claw_gui.engines.hardware_overview import HardwareOverviewBoundingBox, HardwareOverviewChildEntry, HardwareOverviewComponentGroup

    transformer = HardwareOverviewComponentGroup(
        group_id="transformer", display_name="LLC Transformer", status="available",
        bounding_box_mm=HardwareOverviewBoundingBox(80.0, 38.0, 32.0), metadata={"topology_id": TOPOLOGY_ID}
    )
    capacitor = HardwareOverviewComponentGroup(
        group_id="capacitor", display_name="LLC Cr", status="available",
        bounding_box_mm=HardwareOverviewBoundingBox(48.0, 8.0, 10.0), metadata={"topology_id": TOPOLOGY_ID},
        child_entries=[HardwareOverviewChildEntry(
            entry_id="llc_resonant_capacitor", display_name="Cr", bounding_box_mm=HardwareOverviewBoundingBox(48.0, 8.0, 10.0)
        )],
    )

    layout = build_integrated_hardware_layout_from_groups([transformer, capacitor])

    assert [obj.id for obj in layout.groups] == ["transformer", "llc_resonant_capacitor"]
