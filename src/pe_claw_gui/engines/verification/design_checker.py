"""Structured report checker for deterministic AI-assisted design."""

from __future__ import annotations

from ...models.ai_design_report import DesignCheckResult


def check_design_report(report) -> DesignCheckResult:
    """Inspect an existing design report without recomputing physics."""

    blocking: list[str] = []
    warnings: list[str] = []
    actions: list[str] = []

    if report is None:
        return DesignCheckResult(
            passed=False,
            risk_level="blocking",
            blocking_issues=["No design report is available."],
            recommended_actions=["Run a topology design before checking feasibility."],
        )

    candidate = getattr(report, "candidate", None)
    if candidate is None:
        blocking.append("Missing topology candidate/electrical result.")
        actions.append("Run the topology synthesis stage.")
    elif getattr(candidate, "feasible", True) is False or getattr(candidate, "ccm_valid", True) is False:
        blocking.append(f"Core electrical synthesis failed: {getattr(candidate, 'failure_reason', 'unknown reason')}.")
        actions.append("Revise the topology inputs or select a different topology.")

    topology_result = getattr(report, "topology_result", None)
    if topology_result is None:
        warnings.append("Missing topology evaluation result.")

    device = getattr(report, "device", None)
    if device is None:
        warnings.append("Missing semiconductor selection result.")
        actions.append("Run semiconductor selection.")
    elif not getattr(device, "selected_devices", {}):
        warnings.append("Semiconductor selection did not select devices.")
        actions.append("Review semiconductor filters and electrical stress limits.")

    magnetic = getattr(report, "magnetic", None)
    if magnetic is None:
        warnings.append("Missing magnetic design result.")
        actions.append("Run magnetic design if the topology requires an inductor.")
    elif getattr(magnetic, "feasible_count", 0) == 0 and not getattr(magnetic, "chosen_designs", []):
        warnings.append("Magnetic design has no feasible selected candidate.")
        actions.append("Review inductance, current, frequency, and magnetic allow-profile limits.")

    capacitor = getattr(report, "capacitor", None)
    if capacitor is None:
        warnings.append("Missing capacitor selection result.")
        actions.append("Run capacitor selection for input/output ripple and loss checks.")
    else:
        _check_capacitor_side(capacitor, "input_selection", "input", warnings, actions)
        _check_capacitor_side(capacitor, "output_selection", "output", warnings, actions)

    loss = getattr(report, "loss", None)
    total_loss_w = getattr(loss, "total_loss_w", None) if loss is not None else None
    if loss is None:
        warnings.append("Missing loss result.")
        actions.append("Run loss estimation.")
    elif total_loss_w is None:
        warnings.append("Loss result is present but total loss is unavailable.")
    elif total_loss_w < 0.0:
        warnings.append("Loss result has abnormal negative total loss.")

    thermal = getattr(report, "thermal", None)
    if thermal is None:
        warnings.append("Missing thermal result.")
        actions.append("Run thermal estimation.")
    else:
        warnings.extend(str(note) for note in getattr(thermal, "notes", []) if "warning" in str(note).lower())

    if getattr(report, "geometry", None) is None:
        warnings.append("Missing magnetic/system geometry result.")
    if getattr(report, "semiconductor_geometry", None) is None:
        warnings.append("Missing semiconductor geometry result.")

    warnings.extend(_collect_report_warnings(report))
    warnings = _dedupe(warnings)
    actions = _dedupe(actions)

    if blocking:
        risk_level = "blocking"
    elif _has_hardware_selection_failure(warnings):
        risk_level = "high"
    elif warnings:
        risk_level = "medium"
    else:
        risk_level = "low"

    return DesignCheckResult(
        passed=not blocking and risk_level in {"low", "medium"},
        risk_level=risk_level,
        blocking_issues=_dedupe(blocking),
        warnings=warnings,
        recommended_actions=actions,
    )


def _check_capacitor_side(capacitor, attr_name: str, label: str, warnings: list[str], actions: list[str]) -> None:
    side = getattr(capacitor, attr_name, None)
    if side is None or getattr(side, "recommended", None) is None:
        warnings.append(f"Missing {label} capacitor recommendation.")
        actions.append(f"Review {label} capacitor current waveform and selection constraints.")
        return
    if getattr(side, "feasible_count", 1) == 0:
        warnings.append(f"{label.capitalize()} capacitor selection has no feasible candidates.")
    warnings.extend(str(item) for item in getattr(side, "warnings", []))


def _collect_report_warnings(report) -> list[str]:
    collected: list[str] = []
    for attr_name in ("notes",):
        for item in getattr(report, attr_name, []) or []:
            text = str(item)
            if "warning" in text.lower() or "skipped" in text.lower() or "missing" in text.lower():
                collected.append(text)
    for result_name in ("device", "magnetic", "capacitor", "loss", "thermal", "geometry", "semiconductor_geometry"):
        result = getattr(report, result_name, None)
        if result is None:
            continue
        for item in getattr(result, "warnings", []) or []:
            collected.append(str(item))
        for item in getattr(result, "notes", []) or []:
            text = str(item)
            if "warning" in text.lower() or "skipped" in text.lower():
                collected.append(text)
    return collected


def _has_hardware_selection_failure(warnings: list[str]) -> bool:
    joined = "\n".join(warnings).lower()
    return any(
        token in joined
        for token in (
            "did not select",
            "no feasible",
            "missing semiconductor",
            "missing magnetic",
            "missing capacitor",
        )
    )


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
