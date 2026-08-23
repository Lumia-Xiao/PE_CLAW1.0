from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.libraries.semiconductors.packages import (
    normalize_package_name,
    resolve_package_template,
    validate_registered_packages,
)
from pe_claw_gui.libraries.semiconductors.power_device import PowerDevice
from pe_claw_gui.libraries.semiconductors.registry import build_default_semiconductor_registry
from pe_claw_gui.models.common_spec import CommonSpec
from pe_claw_gui.models.design_report import DesignReport
from pe_claw_gui.models.device_loss import DeviceLossResult
from pe_claw_gui.models.device_result import DeviceSelectionResult
from pe_claw_gui.pipeline.run_semiconductor_geometry_pipeline import run_semiconductor_geometry_pipeline
from pe_claw_gui.visualization.semiconductors.layout_builder import build_semiconductor_geometry_layout


def _loss_result(part_number: str) -> DeviceLossResult:
    return DeviceLossResult(
        part_number=part_number,
        role="main_switch",
        mode="ccm",
        p_cond_W=0.9,
        p_sw_on_W=0.4,
        p_sw_off_W=0.3,
        p_rr_W=0.0,
        p_eoss_W=0.2,
        p_gate_W=0.1,
        p_total_W=1.9,
        tj_est_C=96.0,
        target_junction_temp_c=100.0,
        required_total_rth_k_per_w=39.0,
        required_sink_rth_k_per_w=32.0,
        estimated_sink_volume_cm3=6.5,
        sink_volume_model="surface_proxy_natural_v1",
        cooling_mode_assumed="natural",
        thermal_feasible=True,
    )


def test_package_normalization_accepts_common_to247_4_aliases() -> None:
    assert normalize_package_name("PG-TO247-4") == "pg-to247-4"

    for raw_name in ("PG-TO247-4", "TO-247-4", "PG_TO247_4", "pg-to247-4"):
        resolved = resolve_package_template(raw_name)
        assert resolved.canonical_package == "PG-TO247-4"
        assert resolved.canonical_key == "pg-to247-4"
        assert resolved.renderer_template_id == "to247_4_tht"
        assert resolved.fallback_warning is None


def test_package_normalization_accepts_rohm_to247_aliases() -> None:
    alias_expectations = {
        "TO-247-2L": ("PG-TO247-2", "to247_2_tht"),
        "TO247-2L": ("PG-TO247-2", "to247_2_tht"),
        "TO-247N-4L": ("PG-TO247-4", "to247_4_tht"),
        "TO-247N-4L Kelvin": ("PG-TO247-4", "to247_4_tht"),
        "TO-247-7L Kelvin": ("PG-TO247-4", "to247_4_tht"),
        "DOT-247-7L": ("PG-TO247-4", "to247_4_tht"),
        "rohm_bsm_sic_module": ("rohm_bsm_sic_module", "module_half_bridge"),
    }

    for raw_name, (canonical_name, renderer_template_id) in alias_expectations.items():
        resolved = resolve_package_template(raw_name)
        assert resolved.canonical_package == canonical_name
        assert resolved.renderer_template_id == renderer_template_id
        assert resolved.fallback_warning is None


def test_package_normalization_accepts_pg_to263_7_aliases() -> None:
    for raw_name in ("PG-TO263-7", "TO-263-7", "D2PAK-7", "PG_TO263_7", "pg-to263-7"):
        resolved = resolve_package_template(raw_name)
        assert resolved.canonical_package == "PG-TO263-7"
        assert resolved.canonical_key == "pg-to263-7"
        assert resolved.renderer_template_id == "to263_7_d2pak"
        assert resolved.fallback_warning is None


def test_package_lookup_returns_explicit_warning_for_unsupported_package() -> None:
    resolved = resolve_package_template("PG-FAKE-99")

    assert resolved.normalized_package == "pg-fake-99"
    assert resolved.renderer_template_id == "generic_power_package"
    assert resolved.fallback_warning is not None
    assert "Unsupported package" in resolved.fallback_warning


def test_package_normalization_accepts_new_coolgan_package_aliases() -> None:
    alias_expectations = {
        "PGHDSOP16": ("PG-HDSOP-16", "hdsop_16_top"),
        "TOLT": ("PG-HDSOP-16", "hdsop_16_top"),
        "PGDSO20": ("PG-DSO-20", "dso_20_top"),
        "PGTSON8": ("PG-TSON-8", "tson_8_top"),
        "PGLSON8": ("PG-LSON-8", "lson_8_top"),
        "PGHSOF8": ("PG-HSOF-8", "hsof_8_top"),
    }

    for raw_name, (canonical_name, renderer_template_id) in alias_expectations.items():
        resolved = resolve_package_template(raw_name)
        assert resolved.canonical_package == canonical_name
        assert resolved.renderer_template_id == renderer_template_id
        assert resolved.fallback_warning is None


def test_registry_packages_all_resolve_without_fallback() -> None:
    registry = build_default_semiconductor_registry()

    resolved = validate_registered_packages((device.static.package for device in registry.devices), require_supported=True)

    assert len(resolved) == len(registry.devices)
    assert all(item.fallback_warning is None for item in resolved)


def test_to247_4_device_uses_to247_4_template_without_to220_remap() -> None:
    registry = build_default_semiconductor_registry()
    device = registry.get_device("IPZA60R037CM8")

    layout = build_semiconductor_geometry_layout(device, _loss_result(device.part_number), case_id="nominal")

    assert layout.package == "PG-TO247-4"
    assert layout.canonical_package == "PG-TO247-4"
    assert layout.package_template_key == "pg-to247-4"
    assert layout.renderer_template_id == "to247_4_tht"
    assert layout.package_template_key != "pg-to220-3"
    assert layout.package_fallback_warning is None


def test_pg_to252_3_device_uses_dpak_template() -> None:
    registry = build_default_semiconductor_registry()
    device = registry.get_device("IPD60R180CM8")

    layout = build_semiconductor_geometry_layout(device, _loss_result(device.part_number), case_id="nominal")

    assert layout.package == "PG-TO252-3"
    assert layout.canonical_package == "PG-TO252-3"
    assert layout.renderer_template_id == "to252_3_dpak"
    assert layout.package_fallback_warning is None


def test_pg_to263_7_device_uses_d2pak_template_without_wrong_known_fallback() -> None:
    registry = build_default_semiconductor_registry()
    device = registry.get_device("IMBG75R007M2H")

    layout = build_semiconductor_geometry_layout(device, _loss_result(device.part_number), case_id="nominal")

    assert layout.package == "PG-TO263-7"
    assert layout.canonical_package == "PG-TO263-7"
    assert layout.package_template_key == "pg-to263-7"
    assert layout.renderer_template_id == "to263_7_d2pak"
    assert layout.package_template_key != "pg-to252-3"
    assert layout.package_fallback_warning is None


def test_coolgan_packages_use_registered_geometry_templates() -> None:
    registry = build_default_semiconductor_registry()
    expectations = {
        "IGLT65R025D2": ("PG-HDSOP-16", "hdsop_16_top"),
        "IGOT65R025D2": ("PG-DSO-20", "dso_20_top"),
        "IGL65R055D2": ("PG-TSON-8", "tson_8_top"),
        "IGLD65R055D2": ("PG-LSON-8", "lson_8_top"),
    }

    for part_number, (package_name, renderer_template_id) in expectations.items():
        device = registry.get_device(part_number)
        layout = build_semiconductor_geometry_layout(device, _loss_result(device.part_number), case_id="nominal")
        assert layout.package == package_name
        assert layout.renderer_template_id == renderer_template_id
        assert layout.package_fallback_warning is None


def test_unsupported_package_uses_generic_renderer_with_explicit_note() -> None:
    registry = build_default_semiconductor_registry()
    real_device = registry.get_device("IPW60R037CM8")
    fake_device = PowerDevice(
        static=replace(real_device.static, package="PG-FAKE-99"),
        dynamic=real_device.dynamic,
    )

    layout = build_semiconductor_geometry_layout(fake_device, _loss_result(fake_device.part_number), case_id="nominal")

    assert layout.renderer_template_id == "generic_power_package"
    assert layout.package_fallback_warning is not None
    assert any("Unsupported package" in note for note in layout.notes)


def test_geometry_pipeline_exposes_resolved_package_metadata() -> None:
    loss_result = _loss_result("IPZA60R037CM8")
    report = DesignReport(
        spec=CommonSpec(
            topology_id="test",
            display_name="Test",
            vin_min=300.0,
            vin_max=400.0,
            vout=48.0,
            pout=100.0,
            fs_khz=100.0,
            ripple_current_ratio=0.2,
            ripple_voltage_ratio_percent=1.0,
        ),
        device=DeviceSelectionResult(
            selected_devices={"main_switch": "IPZA60R037CM8"},
            design_point_losses={"nominal:main_switch": loss_result},
        ),
    )

    updated_report = run_semiconductor_geometry_pipeline(report)
    geometry = updated_report.semiconductor_geometry

    assert geometry is not None
    assert geometry.package == "PG-TO247-4"
    assert geometry.canonical_package == "PG-TO247-4"
    assert geometry.normalized_package == "pg-to247-4"
    assert geometry.renderer_template_id == "to247_4_tht"
    assert geometry.package_fallback_warning is None
