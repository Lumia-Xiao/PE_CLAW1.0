"""Compact current T-type scoped-system readback."""


def system_lines(report, section="loss"):
    s = getattr(getattr(report, "t_type_engineering", None), "system", None)
    if s is None:
        return ["T-type scoped system unavailable; select both semiconductor roles, three inductors and two banks."]
    lines = ["T-type conduction + magnetics + capacitors (switching and auxiliary losses excluded)."]
    if section == "loss":
        if s.total_loss_w is None:
            lines.append("Scoped total loss / efficiency: unavailable")
        else:
            lines.extend(f"  {role}: {value:.6f} W" for role, value in s.role_losses_w.items())
            lines.extend(f"  {key}: {value:.6f} W" for key, value in s.loss_components_w.items() if key not in {p.position_id for p in report.t_type_engineering.current_positions})
            lines.append(f"Scoped total loss: {s.total_loss_w:.6f} W")
            lines.append(f"Scoped efficiency: {s.efficiency_ratio * 100:.6f} %" if s.efficiency_ratio is not None else "Scoped efficiency: unavailable (zero output power)")
    elif section == "thermal":
        config = report.t_type_engineering.thermal_configuration
        lines.append(f"Shared sink: {config.sink_rth_k_per_w:.6g} K/W; airflow {config.design_airflow_m3_h:.6g} m3/h x {config.airflow_derating:.6g}; coupling {config.coupling_factor:.6g}")
        lines.append(f"Semiconductor shared-sink screen: {s.thermal_status}; passed={s.thermal_passed}")
        lines.extend(f"  {p.position_id}: Tj={p.junction_temp_c:.6f} C; margin={p.junction_margin_c:.6f} C" for p in s.position_thermal)
        for entry in getattr(report.thermal, "chosen_design_estimates", ()):
            lines.append(f"  {entry.design_id}: magnetic hotspot={entry.estimate.hotspot_proxy_temp_c:.6f} C (lumped proxy)")
        lines.append("Engineering TIM/airflow/pressure assumptions; fixed curve temperature, conduction scope only.")
    else:
        lines.append(f"Component model volume: {s.total_component_volume_cm3:.6f} cm3" if s.total_component_volume_cm3 is not None else "Component model volume: unavailable")
        lines.append("Package bodies + three inductors + two banks + one shared sink proxy; no physical placement/enclosure.")
    lines.extend(s.diagnostics)
    lines.extend([f"Hardware: {s.hardware_id}", f"Basis: {s.operating_basis}", f"Scope: {s.loss_scope_id}"])
    return lines
