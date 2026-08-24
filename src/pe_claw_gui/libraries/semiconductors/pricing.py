"""Runtime semiconductor price-table loading and matching helpers."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path


PRICE_BASIS_POLICY = "qty100 preferred; fallback qty10, qty1, then qty1000"
NO_PRICE_RECORD_STATUS = "no_purchasable_price_record"
NO_PRICE_RECORD_NOTE = "no purchasable price record in current price table"


@dataclass(frozen=True)
class SemiconductorPriceRecord:
    """One purchasable semiconductor price row."""

    purchasable_part_number: str = ""
    manufacturer: str = ""
    representative_part_number: str = ""
    module_group_id: str = ""
    device_type: str = ""
    structure: str = ""
    package: str = ""
    price_entity_type: str = ""
    unit_price_qty1: float | None = None
    unit_price_qty10: float | None = None
    unit_price_qty100: float | None = None
    unit_price_qty1000: float | None = None
    selected_unit_price: float | None = None
    selected_price_basis: str = ""
    currency: str = ""
    stock_qty: float | None = None
    availability_status: str = "unknown_stock"
    moq: float | None = None
    basis_note: str = ""
    price_match_confidence: str = ""
    match_status: str = ""
    raw_row: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SemiconductorPriceMatch:
    """Price lookup outcome for one runtime semiconductor device."""

    status: str
    record: SemiconductorPriceRecord | None = None
    match_method: str = ""
    match_confidence: str = ""
    matched_purchasable_part_number: str = ""
    note: str = ""


class SemiconductorPriceTable:
    """Indexed purchasable price table used for audit/display metadata."""

    def __init__(self, records: tuple[SemiconductorPriceRecord, ...], source_path: Path | None = None) -> None:
        self.records = records
        self.source_path = source_path
        self._by_manufacturer_purchasable: dict[tuple[str, str], list[SemiconductorPriceRecord]] = {}
        self._by_purchasable: dict[str, list[SemiconductorPriceRecord]] = {}
        self._by_manufacturer_representative: dict[tuple[str, str], list[SemiconductorPriceRecord]] = {}
        self._by_representative: dict[str, list[SemiconductorPriceRecord]] = {}
        self._by_module_group: dict[str, list[SemiconductorPriceRecord]] = {}
        for record in records:
            manufacturer_key = normalize_price_key(record.manufacturer)
            purchasable_key = normalize_price_key(record.purchasable_part_number)
            if purchasable_key:
                self._by_purchasable.setdefault(purchasable_key, []).append(record)
                if manufacturer_key:
                    self._by_manufacturer_purchasable.setdefault((manufacturer_key, purchasable_key), []).append(record)
            representative_key = normalize_price_key(record.representative_part_number)
            if representative_key:
                self._by_representative.setdefault(representative_key, []).append(record)
                if manufacturer_key:
                    self._by_manufacturer_representative.setdefault((manufacturer_key, representative_key), []).append(record)
            module_key = normalize_price_key(record.module_group_id)
            if module_key:
                self._by_module_group.setdefault(module_key, []).append(record)

    def match_device(
        self,
        *,
        part_number: str | None,
        manufacturer: str | None = None,
        representative_part_number: str | None = None,
        module_group_id: str | None = None,
    ) -> SemiconductorPriceMatch:
        """Match a runtime device to one purchasable price record."""

        part_key = normalize_price_key(part_number)
        manufacturer_key = normalize_price_key(manufacturer)
        representative_key = normalize_price_key(representative_part_number)
        module_key = normalize_price_key(module_group_id)

        attempts: list[tuple[str, list[SemiconductorPriceRecord]]] = []
        if manufacturer_key and part_key:
            attempts.append(("manufacturer_and_part_number", self._by_manufacturer_purchasable.get((manufacturer_key, part_key), [])))
        if part_key:
            attempts.append(("part_number", self._by_purchasable.get(part_key, [])))
        if manufacturer_key and representative_key:
            attempts.append(
                (
                    "manufacturer_and_representative_part_number",
                    self._by_manufacturer_representative.get((manufacturer_key, representative_key), []),
                )
            )
        if representative_key:
            attempts.append(("representative_part_number", self._by_representative.get(representative_key, [])))
        if module_key:
            attempts.append(("module_group_id", self._by_module_group.get(module_key, [])))

        for method, records in attempts:
            if records:
                record = _select_best_record(records)
                return SemiconductorPriceMatch(
                    status="matched",
                    record=record,
                    match_method=method,
                    match_confidence=record.price_match_confidence,
                    matched_purchasable_part_number=record.purchasable_part_number,
                )
        return SemiconductorPriceMatch(status=NO_PRICE_RECORD_STATUS, note=NO_PRICE_RECORD_NOTE)


def default_semiconductor_price_table_path() -> Path:
    """Return the repository-local purchasable semiconductor price CSV path."""

    return Path(__file__).resolve().parents[4] / "outputs" / "semiconductor_unique_purchasable_parts.csv"


def load_semiconductor_price_table(path: str | Path) -> SemiconductorPriceTable:
    """Load purchasable semiconductor prices from CSV."""

    source_path = Path(path)
    records: list[SemiconductorPriceRecord] = []
    with source_path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            records.append(_row_to_record(row))
    return SemiconductorPriceTable(tuple(records), source_path=source_path)


def normalize_price_key(value: object | None) -> str:
    """Normalize part/manufacturer keys for transparent price matching."""

    if value is None:
        return ""
    return re.sub(r"[^A-Z0-9]", "", str(value).upper())


def _row_to_record(row: dict[str, str]) -> SemiconductorPriceRecord:
    qty1 = _parse_number(_field(row, "unit_price_qty1", "price_qty1", "qty1"))
    qty10 = _parse_number(_field(row, "unit_price_qty10", "price_qty10", "qty10"))
    qty100 = _parse_number(_field(row, "unit_price_qty100", "price_qty100", "qty100"))
    qty1000 = _parse_number(_field(row, "unit_price_qty1000", "price_qty1000", "qty1000"))
    selected_price, selected_basis = _select_display_price(qty1=qty1, qty10=qty10, qty100=qty100, qty1000=qty1000)
    stock_qty = _parse_number(_field(row, "stock_qty", "stock"))
    return SemiconductorPriceRecord(
        purchasable_part_number=_field(row, "purchasable_part_number", "distributor_sku", "digikey_candidate_mpn"),
        manufacturer=_field(row, "manufacturer", "vendor"),
        representative_part_number=_field(row, "representative_part_number", "part_number"),
        module_group_id=_field(row, "module_group_id"),
        device_type=_field(row, "representative_device_type", "device_type"),
        structure=_field(row, "representative_structure", "structure"),
        package=_field(row, "representative_package", "package"),
        price_entity_type=_field(row, "price_entity_type"),
        unit_price_qty1=qty1,
        unit_price_qty10=qty10,
        unit_price_qty100=qty100,
        unit_price_qty1000=qty1000,
        selected_unit_price=selected_price,
        selected_price_basis=selected_basis,
        currency=_field(row, "currency") or "USD",
        stock_qty=stock_qty,
        availability_status=_availability_status(stock_qty),
        moq=_parse_number(_field(row, "moq", "minimum_order_quantity")),
        basis_note=_basis_note(qty1=qty1, qty10=qty10, qty100=qty100, qty1000=qty1000, selected_basis=selected_basis),
        price_match_confidence=_field(row, "price_match_confidence", "digikey_match_confidence"),
        match_status=_field(row, "digikey_match_status", "match_status"),
        raw_row=dict(row),
    )


def _field(row: dict[str, str], *names: str) -> str:
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _parse_number(value: str) -> float | None:
    cleaned = (value or "").strip()
    if not cleaned or cleaned in {"-", "N/A", "n/a"}:
        return None
    cleaned = cleaned.replace(",", "").replace("$", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _select_display_price(
    *,
    qty1: float | None,
    qty10: float | None,
    qty100: float | None,
    qty1000: float | None,
) -> tuple[float | None, str]:
    for basis, value in (("qty100", qty100), ("qty10", qty10), ("qty1", qty1), ("qty1000", qty1000)):
        if value is not None:
            return value, basis
    return None, ""


def _availability_status(stock_qty: float | None) -> str:
    if stock_qty is None:
        return "unknown_stock"
    if stock_qty > 0:
        return "in_stock"
    return "out_of_stock"


def _basis_note(
    *,
    qty1: float | None,
    qty10: float | None,
    qty100: float | None,
    qty1000: float | None,
    selected_basis: str,
) -> str:
    if selected_basis == "qty100":
        return ""
    if selected_basis == "qty10" and qty100 is None:
        return "qty100 unavailable; using qty10 fallback"
    if selected_basis == "qty1" and qty100 is None and qty10 is None:
        return "qty100 unavailable; using qty1 fallback"
    if selected_basis == "qty1000" and qty100 is None and qty10 is None and qty1 is None:
        return "qty100 unavailable; using qty1000 fallback"
    return ""


def _select_best_record(records: list[SemiconductorPriceRecord]) -> SemiconductorPriceRecord:
    confidence_order = {"high": 0, "medium": 1, "low": 2}
    return sorted(
        records,
        key=lambda record: (
            record.selected_unit_price is None,
            confidence_order.get(record.price_match_confidence.casefold(), 9),
            record.purchasable_part_number,
        ),
    )[0]

