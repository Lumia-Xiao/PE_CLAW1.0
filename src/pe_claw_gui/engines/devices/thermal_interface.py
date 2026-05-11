"""Semiconductor case-to-sink thermal-interface defaults."""

from __future__ import annotations

from dataclasses import dataclass, field

from ...libraries.semiconductors.packages import resolve_package_template
from ...libraries.semiconductors.power_device import PowerDevice
from ...models.device_loss import SwitchStress

DEFAULT_DISCRETE_CONTACT_AREA_MM2 = 220.0
DEFAULT_MODULE_CONTACT_AREA_MM2 = 2500.0


@dataclass(frozen=True)
class ThermalInterfaceLayer:
    """One layer in a first-pass case-to-sink interface stack."""

    name: str
    material_type: str
    thickness_mm: float
    thermal_conductivity_w_mk: float
    contact_area_mm2: float
    electrical_insulation: bool = False
    rth_k_per_w: float | None = None
    note: str = ""


@dataclass(frozen=True)
class ThermalInterfaceStack:
    """Resolved case-to-sink interface used by thermal backsolve."""

    model_name: str
    contact_area_mm2: float | None
    total_rth_k_per_w: float
    layers: tuple[ThermalInterfaceLayer, ...] = ()
    electrical_insulation: bool = False
    source: str = "default"
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def layer_summary(self) -> str:
        if not self.layers:
            return "-"
        return ", ".join(_format_layer(layer) for layer in self.layers)


def layer_rth_k_per_w(layer: ThermalInterfaceLayer) -> float:
    """Return K/W for one planar interface layer."""

    if layer.rth_k_per_w is not None:
        return layer.rth_k_per_w
    return 1000.0 * layer.thickness_mm / (layer.thermal_conductivity_w_mk * layer.contact_area_mm2)


def interface_stack_rth_k_per_w(layers: tuple[ThermalInterfaceLayer, ...]) -> float:
    """Return total K/W for a stack of planar interface layers."""

    return sum(layer_rth_k_per_w(layer) for layer in layers)


def build_default_discrete_interface_stack(contact_area_mm2: float) -> ThermalInterfaceStack:
    """Return the default discrete grease-pad-grease case-to-sink stack."""

    layers = (
        ThermalInterfaceLayer(
            name="case grease",
            material_type="thermal_grease",
            thickness_mm=0.03,
            thermal_conductivity_w_mk=3.0,
            contact_area_mm2=contact_area_mm2,
        ),
        ThermalInterfaceLayer(
            name="insulation pad",
            material_type="insulation_pad",
            thickness_mm=0.10,
            thermal_conductivity_w_mk=4.0,
            contact_area_mm2=contact_area_mm2,
            electrical_insulation=True,
        ),
        ThermalInterfaceLayer(
            name="sink grease",
            material_type="thermal_grease",
            thickness_mm=0.03,
            thermal_conductivity_w_mk=3.0,
            contact_area_mm2=contact_area_mm2,
        ),
    )
    return ThermalInterfaceStack(
        model_name="discrete_grease_pad_grease_v1",
        contact_area_mm2=contact_area_mm2,
        total_rth_k_per_w=interface_stack_rth_k_per_w(layers),
        layers=layers,
        electrical_insulation=True,
        source="default_discrete_stack",
        notes=["default discrete grease-pad-grease interface"],
    )


def build_default_module_interface_stack(contact_area_mm2: float) -> ThermalInterfaceStack:
    """Return the default module grease-only case-to-sink stack."""

    layers = (
        ThermalInterfaceLayer(
            name="baseplate grease",
            material_type="thermal_grease",
            thickness_mm=0.05,
            thermal_conductivity_w_mk=3.0,
            contact_area_mm2=contact_area_mm2,
        ),
    )
    return ThermalInterfaceStack(
        model_name="module_grease_only_v1",
        contact_area_mm2=contact_area_mm2,
        total_rth_k_per_w=interface_stack_rth_k_per_w(layers),
        layers=layers,
        electrical_insulation=False,
        source="default_module_stack",
        notes=["default module grease-only interface"],
    )


def resolve_thermal_interface_stack(device: PowerDevice, stress: SwitchStress) -> ThermalInterfaceStack:
    """Resolve explicit or default case-to-sink interface for a device/stress pair."""

    if stress.interface_rth_cs_K_per_W is not None:
        return _explicit_override(float(stress.interface_rth_cs_K_per_W), "stress_explicit_rth_cs")
    if device.interface_rth_cs_K_per_W is not None:
        return _explicit_override(float(device.interface_rth_cs_K_per_W), "device_explicit_rth_cs")

    contact_area_mm2, area_notes, area_warnings = resolve_interface_contact_area(device)
    stack = (
        build_default_module_interface_stack(contact_area_mm2)
        if _is_module_like_device(device)
        else build_default_discrete_interface_stack(contact_area_mm2)
    )
    return ThermalInterfaceStack(
        model_name=stack.model_name,
        contact_area_mm2=stack.contact_area_mm2,
        total_rth_k_per_w=stack.total_rth_k_per_w,
        layers=stack.layers,
        electrical_insulation=stack.electrical_insulation,
        source=stack.source,
        notes=[*stack.notes, *area_notes],
        warnings=area_warnings,
    )


def resolve_interface_contact_area(device: PowerDevice) -> tuple[float, list[str], list[str]]:
    """Resolve or estimate contact area for the case-to-sink interface."""

    if _is_module_like_device(device):
        if device.static.module_length_mm and device.static.module_width_mm:
            return (
                float(device.static.module_length_mm) * float(device.static.module_width_mm),
                ["thermal interface contact area from module baseplate dimensions"],
                [],
            )
        fallback_area_mm2 = DEFAULT_MODULE_CONTACT_AREA_MM2
    else:
        fallback_area_mm2 = DEFAULT_DISCRETE_CONTACT_AREA_MM2

    try:
        resolved_package = resolve_package_template(device.static.package)
        if resolved_package.fallback_warning is not None:
            raise ValueError(resolved_package.fallback_warning)
        template = resolved_package.template
        area_mm2 = float(template.body_width_mm) * float(template.body_height_mm)
    except (AttributeError, TypeError, ValueError):
        area_mm2 = 0.0
    if area_mm2 > 0.0:
        return area_mm2, ["thermal interface contact area estimated from package body footprint"], []

    warning = f"thermal interface contact area defaulted to {fallback_area_mm2:g} mm^2"
    return fallback_area_mm2, [warning], [warning]


def _explicit_override(rth_cs_k_per_w: float, source: str) -> ThermalInterfaceStack:
    note = "explicit interface Rth override"
    return ThermalInterfaceStack(
        model_name="explicit_rth_cs_override",
        contact_area_mm2=None,
        total_rth_k_per_w=rth_cs_k_per_w,
        layers=(),
        electrical_insulation=False,
        source=source,
        notes=[note],
    )


def _is_module_like_device(device: PowerDevice) -> bool:
    return bool(device.is_module or device.package_level == "power_module")


def _format_layer(layer: ThermalInterfaceLayer) -> str:
    return (
        f"{layer.material_type.replace('_', ' ')} "
        f"{layer.thickness_mm:.3g} mm k={layer.thermal_conductivity_w_mk:.3g}"
    )
