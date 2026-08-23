"""Packaged Micrometals MS Sendust toroid core dimensions."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from importlib import resources
from typing import Iterable

_PACKAGE = "pe_claw_gui.libraries.magnetics"
_DATA_DIR = "data"
_CORE_RESOURCE = "micrometals_ms_sendust_toroid_cores.csv"
_SIZE_RESOURCE = "micrometals_ms_sendust_toroid_unique_sizes.csv"
_INCH_TO_MM = 25.4


@dataclass(frozen=True)
class SendustToroidCore:
    """One Micrometals MS Sendust toroid part/material variant."""

    part_number: str
    material: str
    material_name: str
    relative_permeability: float
    al_nh_per_turn2: float
    od_mm: float
    id_mm: float
    ht_mm: float
    ae_cm2: float
    le_cm: float
    ve_cm3: float
    fmax_mhz: float | None = None
    stock_qty: int | None = None
    analyzer_url: str = ""

    @property
    def al_h_per_turn2(self) -> float:
        return self.al_nh_per_turn2 * 1e-9

    @property
    def ae_m2(self) -> float:
        return self.ae_cm2 * 1e-4

    @property
    def le_m(self) -> float:
        return self.le_cm * 1e-2

    @property
    def ve_m3(self) -> float:
        return self.ve_cm3 * 1e-6

    @property
    def mean_length_per_turn_m(self) -> float:
        mean_diameter_m = ((self.od_mm + self.id_mm) * 0.5) * 1e-3
        return math.pi * mean_diameter_m

    @property
    def window_area_mm2(self) -> float:
        radius_mm = 0.5 * self.id_mm
        return math.pi * radius_mm * radius_mm


@dataclass(frozen=True)
class SendustToroidSize:
    """One unique Micrometals MS Sendust toroid mechanical envelope."""

    example_part: str
    od_mm: float
    id_mm: float
    ht_mm: float
    part_count: int
    permeabilities: tuple[float, ...]
    ae_cm2: float
    le_cm: float
    ve_cm3: float

    @property
    def envelope_volume_cm3(self) -> float:
        return (self.od_mm * self.od_mm * self.ht_mm) / 1000.0


def list_sendust_toroid_cores() -> tuple[SendustToroidCore, ...]:
    """Return packaged Micrometals MS Sendust toroid part/material variants."""

    rows = _read_csv_resource(_CORE_RESOURCE)
    cores = tuple(_core_from_row(row) for row in rows)
    _validate_cores(cores)
    return cores


def list_sendust_toroid_sizes() -> tuple[SendustToroidSize, ...]:
    """Return unique packaged Micrometals MS Sendust toroid mechanical sizes."""

    rows = _read_csv_resource(_SIZE_RESOURCE)
    sizes = tuple(_size_from_row(row) for row in rows)
    _validate_sizes(sizes)
    return sizes


def filter_sendust_toroid_cores_by_permeability(
    cores: Iterable[SendustToroidCore],
    relative_permeability: float,
) -> tuple[SendustToroidCore, ...]:
    """Return cores matching one nominal Sendust relative permeability."""

    target = float(relative_permeability)
    return tuple(core for core in cores if math.isclose(core.relative_permeability, target, rel_tol=0.0, abs_tol=1e-6))


def _read_csv_resource(name: str) -> list[dict[str, str]]:
    resource = resources.files(_PACKAGE).joinpath(_DATA_DIR, name)
    with resource.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _core_from_row(row: dict[str, str]) -> SendustToroidCore:
    stock_text = str(row.get("stock_qty", "")).strip()
    stock_qty = int(float(stock_text)) if stock_text else None
    return SendustToroidCore(
        part_number=str(row["part_number"]).strip(),
        material=str(row["material"]).strip(),
        material_name=str(row["material_name"]).strip(),
        relative_permeability=_positive_float(row, "relative_permeability"),
        al_nh_per_turn2=_positive_float(row, "al_nh_per_turn2"),
        od_mm=_positive_float(row, "od_mm"),
        id_mm=_positive_float(row, "id_mm"),
        ht_mm=_positive_float(row, "ht_mm"),
        ae_cm2=_positive_float(row, "ae_cm2"),
        le_cm=_positive_float(row, "le_cm"),
        ve_cm3=_positive_float(row, "ve_cm3"),
        fmax_mhz=_optional_positive_float(row.get("fmax_mhz")),
        stock_qty=stock_qty,
        analyzer_url=str(row.get("analyzer_url", "")).strip(),
    )


def _size_from_row(row: dict[str, str]) -> SendustToroidSize:
    permeabilities = tuple(
        float(item.strip())
        for item in str(row["permeabilities"]).split(",")
        if item.strip()
    )
    return SendustToroidSize(
        example_part=str(row["example_part"]).strip(),
        od_mm=_positive_float(row, "od_mm"),
        id_mm=_positive_float(row, "id_mm"),
        ht_mm=_positive_float(row, "ht_mm"),
        part_count=int(float(row["part_count"])),
        permeabilities=permeabilities,
        ae_cm2=_positive_float(row, "ae_cm2"),
        le_cm=_positive_float(row, "le_cm"),
        ve_cm3=_positive_float(row, "ve_cm3"),
    )


def _positive_float(row: dict[str, str], key: str) -> float:
    value = float(row[key])
    if value <= 0.0:
        raise ValueError(f"{key} must be positive for Sendust toroid data.")
    return value


def _optional_positive_float(value: str | None) -> float | None:
    if value is None or not str(value).strip():
        return None
    resolved = float(value)
    return resolved if resolved > 0.0 else None


def _validate_cores(cores: tuple[SendustToroidCore, ...]) -> None:
    if not cores:
        raise ValueError("Packaged Sendust toroid core table is empty.")
    seen: set[str] = set()
    for core in cores:
        if core.part_number in seen:
            raise ValueError(f"Duplicate Sendust toroid part number: {core.part_number}")
        seen.add(core.part_number)
        if core.id_mm >= core.od_mm:
            raise ValueError(f"Sendust toroid ID must be smaller than OD: {core.part_number}")
        if core.al_nh_per_turn2 <= 0.0 or core.ae_cm2 <= 0.0 or core.ve_cm3 <= 0.0:
            raise ValueError(f"Sendust toroid has incomplete magnetic geometry: {core.part_number}")


def _validate_sizes(sizes: tuple[SendustToroidSize, ...]) -> None:
    if not sizes:
        raise ValueError("Packaged Sendust toroid size table is empty.")
    seen: set[tuple[float, float, float]] = set()
    for size in sizes:
        key = (round(size.od_mm, 6), round(size.id_mm, 6), round(size.ht_mm, 6))
        if key in seen:
            raise ValueError(f"Duplicate Sendust toroid size: {size.example_part}")
        seen.add(key)
        if size.id_mm >= size.od_mm:
            raise ValueError(f"Sendust toroid size ID must be smaller than OD: {size.example_part}")
