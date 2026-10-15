"""T-type current-system handoff; no search, synthesis or reference fallback."""
from dataclasses import replace
import math

from ....models.t_type_engineering import TTypeSystemResult, TTypePositionThermal, EXCLUDED_COMPONENTS
from ....models.loss_result import LossResult
from ....models.thermal_result import ThermalResult
from ....models.geometry_result import GeometryResult, GeometryTarget
from .hardware_adapter import current_waveform_candidate, build_hardware_snapshot
from .engineering_adapter import ROLE_POSITIONS
from .capacitor_adapter import validate_bank_entry


def number(value, label, *, positive=False):
    if value is None or not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError(f"{label}: required finite {'positive' if positive else 'nonnegative'} value")
    return float(value)


def equal(actual, expected, label):
    if not math.isclose(number(actual, label), number(expected, label), rel_tol=1e-10, abs_tol=1e-10):
        raise ValueError(f"{label}: inconsistent published value")


def loss_snapshot(report):
    e = report.t_type_engineering
    current_waveform_candidate(report)
    hardware = build_hardware_snapshot(report)
    if (e.refresh_status != "available" or e.excluded_components != EXCLUDED_COMPONENTS
            or e.current_hardware_id != hardware.hardware_id):
        raise ValueError("T-type system requires current complete hardware and loss scope")
    point = report.operating_point
    if point is None or any(getattr(point, field) is not None and getattr(point, field) != e.current_basis[key]
            for field, key in (("vin_v", "vdc_v"), ("load_ratio", "load_ratio"), ("power_factor", "power_factor"))):
        raise ValueError("T-type system operating request/basis mismatch")
    selected = {d.role: d for d in hardware.devices}
    expected = {p for ids in ROLE_POSITIONS.values() for p in ids}
    if len(e.current_positions) != 12 or {p.position_id for p in e.current_positions} != expected:
        raise ValueError("T-type system requires twelve current positions")
    components, roles = {}, {role: 0.0 for role in ROLE_POSITIONS}
    for p in e.current_positions:
        d = selected[p.role]
        if p.position_id not in d.position_ids or p.part_number != d.part_number or p.parallel_count != d.parallel_count:
            raise ValueError(f"{p.position_id}: current role/part/count source mismatch")
        power = p.parallel_count * (number(p.per_device_channel_w, p.position_id) + number(p.per_device_diode_w, p.position_id))
        equal(p.position_loss_w, power, p.position_id)
        components[p.position_id] = power
        roles[p.role] += power
    m, c = e.magnetics, e.capacitors
    for stage in (m, c):
        if (stage is None or stage.status != "available" or stage.operating_basis != e.current_basis
                or stage.run_id != hardware.run_id or stage.candidate_fingerprint != hardware.candidate_fingerprint):
            raise ValueError("T-type system magnetic/capacitor operating source mismatch")
    for p in m.phase_instances:
        v = p.evaluation
        if v is None or p.operating_request is None or v.design_id != p.design.candidate_id:
            raise ValueError(f"{p.instance_id}: missing current magnetic evaluation")
        request = p.operating_request
        if (any(getattr(v, key) != getattr(request, key) for key in ("operating_vin_v", "fs_hz", "i_rms_a", "i_peak_a"))
                or request.operating_vin_v != e.current_basis["vdc_v"]
                or request.load_ratio != e.current_basis["load_ratio"]
                or request.metadata.get("operating_power_factor") != e.current_basis["power_factor"]
                or request.metadata.get("actual_inductance_h") != hardware.inductance_h):
            raise ValueError(f"{p.instance_id}: current magnetic evaluation basis mismatch")
        copper = number(v.copper_loss_w, f"{p.instance_id}.copper")
        core = number(v.core_loss_w, f"{p.instance_id}.core")
        equal(v.total_loss_w, copper + core, f"{p.instance_id}.total")
        components[p.instance_id + ".copper"] = copper
        components[p.instance_id + ".core"] = core
    equal(m.total_copper_loss_w, sum(components[p.instance_id + ".copper"] for p in m.phase_instances), "magnetic.copper")
    equal(m.total_core_loss_w, sum(components[p.instance_id + ".core"] for p in m.phase_instances), "magnetic.core")
    equal(m.total_loss_w, m.total_copper_loss_w + m.total_core_loss_w, "magnetic.total")
    for side, public in (("upper", report.capacitor.current_operating_input), ("lower", report.capacitor.current_operating_output)):
        bank = getattr(c, "current_" + side)
        validate_bank_entry(bank, side)
        if (public is None or bank != public.recommended or public.request is None
                or public.request.side != side or bank.candidate != getattr(c, "selected_" + side).candidate):
            raise ValueError(f"{side}: current bank source mismatch")
        components[side + ".capacitor"] = number(bank.p_total_w, side)
    equal(c.total_loss_w, components["upper.capacitor"] + components["lower.capacitor"], "capacitor.total")
    total = number(sum(components.values()), "system.total")
    output = number(e.current_basis["pout_w"], "system.output_power")
    input_power = number(output + total, "system.input_power")
    return TTypeSystemResult(hardware.hardware_id, hardware.run_id, hardware.candidate_fingerprint,
        dict(e.current_basis), loss_status="available", loss_components_w=components,
        role_losses_w=roles, total_loss_w=total, output_power_w=output,
        efficiency_ratio=output / input_power if output > 0 else None)


def thermal_snapshot(report, system):
    from ....libraries.semiconductors.registry import build_default_semiconductor_registry
    from ....engines.devices.thermal_interface import resolve_thermal_interface_stack
    from ....engines.thermal.thermal_estimator import estimate_design_thermal_entry
    e = report.t_type_engineering
    config, basis = e.thermal_configuration, e.design_basis
    if config.model != "forced_air_shared_extrusion_proxy_v1":
        raise ValueError("thermal.configuration: unsupported sink model")
    for key in ("sink_rth_k_per_w", "design_airflow_m3_h", "airflow_derating", "coupling_factor", "contact_pressure_mpa"):
        number(getattr(config, key), "thermal.configuration." + key, positive=True)
    if config.airflow_derating > 1 or config.coupling_factor < 1:
        raise ValueError("thermal.configuration: invalid derating/coupling")
    registry = build_default_semiconductor_registry()
    scheme = next(s for s in report.device.scheme_results if s.scheme_id == report.device.active_scheme_id)
    sink_power = sum(system.role_losses_w.values()) * config.coupling_factor
    sink_temp = basis.ambient_temp_c + sink_power * config.sink_rth_k_per_w
    positions, allowed = [], []
    for p in e.current_positions:
        device = registry.get_device(p.part_number)
        interface = resolve_thermal_interface_stack(device, scheme.per_device_selection_stresses[p.role])
        # IGBT and FRD share a physical package; conservative path for combined power.
        rjc = number(max(device.payload.static.rth_jc_igbt_K_per_W,
            device.payload.static.rth_jc_frd_K_per_W), p.position_id + ".Rjc", positive=True)
        rcs = number(interface.total_rth_k_per_w, p.position_id + ".Rcs")
        per_device = p.position_loss_w / p.parallel_count
        case = sink_temp + per_device * rcs
        junction = case + per_device * rjc
        target = min(basis.target_junction_temp_c, number(device.static.tj_max_C, "device.Tjmax", positive=True))
        if not all(math.isfinite(v) for v in (case, junction, target, sink_temp)):
            raise ValueError("thermal: nonfinite temperature")
        positions.append(TTypePositionThermal(p.position_id, p.part_number, p.parallel_count,
            per_device, rjc, rcs, interface.model_name, sink_temp, case, junction, target - junction))
        if sink_power > 0:
            allowed.append((target - basis.ambient_temp_c - per_device * (rjc + rcs)) / sink_power)
    entries = [estimate_design_thermal_entry(design=p.design, evaluation=p.evaluation,
        ambient_temp_c=basis.ambient_temp_c) for p in e.magnetics.phase_instances]
    if any(entry.loss_basis != "operating_point" or entry.estimate is None
            or entry.estimate.hotspot_proxy_temp_c is None or not math.isfinite(entry.estimate.hotspot_proxy_temp_c)
            for entry in entries):
        raise ValueError("thermal: missing current magnetic temperature")
    required_flow = sum(system.role_losses_w.values()) / (1.2 * 1005 * max(basis.target_junction_temp_c - basis.ambient_temp_c, 1)) * 3600
    passed = all(p.junction_margin_c >= 0 for p in positions) and required_flow <= config.design_airflow_m3_h * config.airflow_derating
    system = replace(system, thermal_status="available", position_thermal=tuple(positions),
        required_sink_rth_k_per_w=min(allowed) if allowed else None,
        required_airflow_m3_h=required_flow, thermal_passed=passed)
    worst = max(entries, key=lambda entry: entry.estimate.hotspot_proxy_temp_c)
    thermal = ThermalResult(summary="T-type current conduction shared-sink screen and three independent magnetic thermal proxies.",
        ambient_temp_c=basis.ambient_temp_c, chosen_design_estimates=entries,
        recommended_design_id=worst.design_id, recommended_estimate=worst.estimate,
        status="valid", valid_loss_entry_count=3,
        notes=["Conduction scope only; fixed curve temperature, no electrothermal iteration.",
            "Shared sink excludes magnetic/capacitor heat; airflow/contact pressure/TIM are engineering assumptions."])
    return system, thermal


def geometry_snapshot(report, system):
    from ....libraries.semiconductors.registry import build_default_semiconductor_registry
    from ....libraries.semiconductors.packages import resolve_package_template
    from ....engines.devices.thermal_backsolve import estimate_sink_volume
    from ....visualization.geometry import build_inductor_geometry_layout
    e = report.t_type_engineering
    volumes, sources, diagnostics, targets = {}, {}, [], []
    registry = build_default_semiconductor_registry()
    for package in e.hardware.packages:
        resolved = resolve_package_template(registry.get_device(package.part_number).static.package)
        if resolved.fallback_warning:
            diagnostics.append(f"{package.package_instance_id}: unknown package dimensions")
            continue
        t = resolved.template
        dimensions = (t.body_width_mm, t.body_height_mm, t.body_thickness_mm)
        try:
            volumes[package.package_instance_id] = math.prod(number(v, package.package_instance_id, positive=True) for v in dimensions) / 1000
            sources[package.package_instance_id] = t.datasheet_basis
        except ValueError as exc:
            diagnostics.append(str(exc))
    for p in e.magnetics.phase_instances:
        try:
            layout = build_inductor_geometry_layout(p.design)
            for v in (layout.overall_width_mm, layout.overall_height_mm, layout.overall_depth_mm):
                number(v, p.instance_id + ".dimension", positive=True)
            volumes[p.instance_id] = number(p.design.total_volume_m3, p.instance_id + ".volume", positive=True) * 1e6
            sources[p.instance_id] = layout.geometry_dimension_source + "; selected design model volume"
            targets.append(GeometryTarget(p.instance_id, p.instance_id, p.design.candidate_id,
                layout, p.design.total_volume_m3, p.evaluation.total_loss_w))
        except (ValueError, KeyError, TypeError) as exc:
            diagnostics.append(f"{p.instance_id}: {exc}")
    for side in ("upper", "lower"):
        bank = getattr(e.capacitors, "current_" + side)
        try:
            part = bank.candidate
            if part.package_shape == "cylindrical_can":
                number(part.diameter_mm, side + ".diameter", positive=True)
                number(part.height_mm, side + ".height", positive=True)
            else:
                for value in (part.body_width_mm, part.body_depth_mm, part.body_height_mm):
                    number(value, side + ".dimension", positive=True)
            volumes[side + ".capacitor"] = number(bank.total_volume_cm3, side + ".volume", positive=True)
            sources[side + ".capacitor"] = part.source
        except ValueError as exc:
            diagnostics.append(str(exc))
    sink, model = estimate_sink_volume(e.thermal_configuration.sink_rth_k_per_w, cooling_mode="forced_air")
    volumes["shared_sink"] = number(sink, "sink.volume", positive=True)
    sources["shared_sink"] = model + "; engineering proxy, no physical layout"
    available = not diagnostics
    system = replace(system, geometry_status="available" if available else "unavailable",
        component_volumes_cm3=volumes, geometry_sources=sources,
        total_component_volume_cm3=number(sum(volumes.values()), "geometry.total", positive=True) if available else None,
        diagnostics=(*system.diagnostics, *diagnostics))
    geometry = GeometryResult(summary="T-type component model volumes; no enclosure, spacing or physical placement.",
        selected_design_id=e.magnetics.selected_library_design_id,
        selected_layout=targets[0].layout if targets else None, targets=targets,
        notes=[*diagnostics, "Twelve positions with n packages each, three inductors, two banks and one shared sink; counted once."])
    return system, geometry


def magnetic_loss_result(report):
    m = report.t_type_engineering.magnetics
    return LossResult(total_loss_w=m.total_loss_w,
        breakdown_w={"copper": m.total_copper_loss_w, "core": m.total_core_loss_w},
        recommended_design_id=m.selected_library_design_id, recommended_design_total_volume_m3=m.total_volume_m3,
        notes=["Three-phase magnetic subtotal only; scoped system owner is t_type_engineering.system."])
