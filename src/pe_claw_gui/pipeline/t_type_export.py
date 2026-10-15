"""T-type engineering exports for the fixed-hardware workflow."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from ..models.design_report import DesignReport
from ..reports.structured_output import build_structured_report


def write_t_type_bom_csv(report: DesignReport, output_dir: str | Path) -> Path:
    """Write the physical T-type package, magnetic, and bank inventory."""

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / "t_type_bom.csv"
    engineering = report.t_type_engineering
    hardware = getattr(engineering, "hardware", None)
    system = getattr(engineering, "system", None)
    basis = dict(getattr(system, "operating_basis", {}) or {})
    rows: list[dict[str, Any]] = []
    if engineering is not None and hardware is not None:
        position_loss = {
            item.position_id: item.position_loss_w
            for item in (engineering.current_positions or ())
        }
        for package in hardware.packages:
            position = package.member_position_ids[0] if package.member_position_ids else ""
            device = next((item for item in hardware.devices if position in item.position_ids), None)
            per_package_loss = None
            if device is not None and position_loss.get(position) is not None:
                per_package_loss = float(position_loss[position]) / max(int(device.parallel_count), 1)
            rows.append(_row(
                "semiconductor_package", package.package_instance_id,
                device.role if device is not None else None, package.part_number, 1,
                (system.component_volumes_cm3.get(package.package_instance_id)
                 if system is not None else None), per_package_loss, hardware, basis,
            ))
        if engineering.magnetics is not None:
            for phase in engineering.magnetics.phase_instances:
                rows.append(_row(
                    "phase_inductor", phase.instance_id, phase.instance_id,
                    phase.design.candidate_id, 1, phase.design.total_volume_m3 * 1e6,
                    phase.evaluation.total_loss_w if phase.evaluation is not None else None, hardware, basis,
                ))
        if engineering.capacitors is not None:
            for side, entry in (("upper", engineering.capacitors.current_upper),
                                ("lower", engineering.capacitors.current_lower)):
                if entry is None:
                    continue
                rows.append(_row(
                    "capacitor_bank", side, side, entry.candidate.part_number,
                    entry.total_capacitor_count, entry.total_volume_cm3, entry.p_total_w, hardware, basis,
                ))
        if system is not None and system.component_volumes_cm3.get("shared_sink") is not None:
            rows.append(_row(
                "shared_sink", "shared_sink", "thermal", "shared_extrusion_proxy", 1,
                system.component_volumes_cm3["shared_sink"], None, hardware, basis,
            ))
    fields = (
        "category", "item_id", "role", "part_number", "quantity", "volume_cm3", "loss_w",
        "hardware_id", "run_id", "candidate_fingerprint", "loss_scope_id", "operating_basis",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_t_type_structured_report(report: DesignReport, output_dir: str | Path) -> Path:
    """Write the current structured report as a run-local export."""

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / "t_type_structured_report.json"
    path.write_text(
        json.dumps(build_structured_report(report), indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )
    return path


def _row(category, item_id, role, part_number, quantity, volume_cm3, loss_w, hardware, basis) -> dict[str, Any]:
    return {
        "category": category,
        "item_id": item_id,
        "role": role or "",
        "part_number": part_number or "",
        "quantity": quantity,
        "volume_cm3": volume_cm3,
        "loss_w": loss_w,
        "hardware_id": hardware.hardware_id,
        "run_id": hardware.run_id,
        "candidate_fingerprint": hardware.candidate_fingerprint,
        "loss_scope_id": hardware.loss_scope_id,
        "operating_basis": json.dumps(basis, sort_keys=True),
    }
