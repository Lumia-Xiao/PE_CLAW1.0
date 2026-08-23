"""Coverage audit helpers for the Wolfspeed full-source registration pass."""

from __future__ import annotations

from dataclasses import dataclass

from .diodes import WOLFSPEED_DIODE_STATIC_MANIFEST
from .inference import list_packaged_xml_filenames, normalize_wolfspeed_source_part
from .legacy_mosfets import WOLFSPEED_LEGACY_MOSFET_STATIC_MANIFEST, WOLFSPEED_LEGACY_MOSFET_XML_SUBDIR
from .module_readiness import discover_wolfspeed_module_readiness_inventory
from .modules import WOLFSPEED_MODULE_STATIC_MANIFEST
from .mosfet_with_diode import WOLFSPEED_MOSFET_WITH_DIODE_STATIC_MANIFEST, WOLFSPEED_MOSFET_WITH_DIODE_XML_SUBDIR


@dataclass(frozen=True)
class WolfspeedCoverageItem:
    """One source part coverage decision."""

    source_group: str
    part_number: str
    section_kind: str
    status: str
    registered_as: str
    reason: str


@dataclass(frozen=True)
class WolfspeedCoverageAudit:
    """Deterministic source-to-registry coverage summary."""

    items: tuple[WolfspeedCoverageItem, ...]

    @property
    def blocked_items(self) -> tuple[WolfspeedCoverageItem, ...]:
        return tuple(item for item in self.items if item.status == "blocked_with_reason")

    @property
    def override_items(self) -> tuple[WolfspeedCoverageItem, ...]:
        return tuple(item for item in self.items if item.status == "registered_with_curated_static_override")

    @property
    def registered_count(self) -> int:
        return sum(1 for item in self.items if item.status in {"registered", "registered_with_curated_static_override"})


def build_wolfspeed_full_coverage_audit() -> WolfspeedCoverageAudit:
    """Return source-part coverage for all packaged Wolfspeed XML assets."""

    mwd_entries = {entry["part_number"]: entry for entry in WOLFSPEED_MOSFET_WITH_DIODE_STATIC_MANIFEST}
    legacy_entries = {entry["part_number"]: entry for entry in WOLFSPEED_LEGACY_MOSFET_STATIC_MANIFEST}
    diode_entries = {entry["part_number"]: entry for entry in WOLFSPEED_DIODE_STATIC_MANIFEST}
    module_parts = {record.part_number for record in WOLFSPEED_MODULE_STATIC_MANIFEST}

    items: list[WolfspeedCoverageItem] = []
    for filename in list_packaged_xml_filenames(WOLFSPEED_MOSFET_WITH_DIODE_XML_SUBDIR):
        part = normalize_wolfspeed_source_part(filename)
        items.append(_manifest_item("mosfet_with_diode", part, "main", mwd_entries.get(part), part))

    for filename in list_packaged_xml_filenames(WOLFSPEED_LEGACY_MOSFET_XML_SUBDIR):
        if "bodydiode" in filename.casefold():
            continue
        part = normalize_wolfspeed_source_part(filename)
        if part in mwd_entries:
            items.append(WolfspeedCoverageItem("legacy_mosfet", part, "main", "registered", part, "covered by MOSFET-with-diode priority source"))
        else:
            items.append(_manifest_item("legacy_mosfet", part, "main", legacy_entries.get(part), part))

    for entry in diode_entries.values():
        items.append(_manifest_item("standalone_diode", entry["part_number"], "diode", entry, entry["part_number"]))

    readiness = discover_wolfspeed_module_readiness_inventory()
    for family in readiness.families:
        if family.main_xml is not None:
            items.append(_module_item(family.part_number, "main", module_parts))
        if family.bodydiode_xml is not None:
            items.append(_module_item(family.part_number, "bodydiode", module_parts, suffix="_BODY_DIODE"))
        if family.schottkydiode_xml is not None:
            items.append(_module_item(family.part_number, "schottkydiode", module_parts, suffix="_SBD"))
        if family.diode_xml is not None:
            entry = diode_entries.get(family.part_number)
            items.append(_manifest_item("module_diode_only", family.part_number, "diode", entry, family.part_number))

    return WolfspeedCoverageAudit(items=tuple(sorted(items, key=lambda item: (item.source_group, item.part_number, item.section_kind))))


def _manifest_item(source_group: str, part: str, section_kind: str, entry: dict | None, registered_as: str) -> WolfspeedCoverageItem:
    if entry is None:
        return WolfspeedCoverageItem(source_group, part, section_kind, "blocked_with_reason", "-", "no registered manifest entry")
    if entry.get("datasheet_rev") == "curated-static-override" or entry.get("pdf_filename") is None:
        return WolfspeedCoverageItem(
            source_group,
            part,
            section_kind,
            "registered_with_curated_static_override",
            registered_as,
            "XML is registered with explicit source-derived static override",
        )
    return WolfspeedCoverageItem(source_group, part, section_kind, "registered", registered_as, "registered with packaged XML and static record")


def _module_item(part: str, section_kind: str, module_parts: set[str], *, suffix: str = "") -> WolfspeedCoverageItem:
    if part not in module_parts:
        return WolfspeedCoverageItem("module", part, section_kind, "blocked_with_reason", "-", "module source section has no module manifest entry")
    override_parts = {
        "CAB320M17XM3",
        "CBB010A12FM4",
        "CBB010A23GM4",
        "CBB014A12FM4",
        "CBB030A23FM4",
        "CHB7R5A23GM4_M11",
        "CHB7R5A23GM4_M13",
    }
    status = "registered_with_curated_static_override" if part in override_parts else "registered"
    reason = "module XML is registered with explicit source-derived static override" if part in override_parts else "module XML is registered"
    return WolfspeedCoverageItem("module", part, section_kind, status, f"{part}{suffix}", reason)


__all__ = [
    "WolfspeedCoverageAudit",
    "WolfspeedCoverageItem",
    "build_wolfspeed_full_coverage_audit",
]
