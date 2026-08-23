"""Read-only Wolfspeed legacy module source readiness inventory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from ..xml_parser import parse_plecs_xml
from .mosfet_with_diode import DEFAULT_WOLFSPEED_SOURCE_ROOT

WOLFSPEED_LEGACY_MODULE_SOURCE_SUBDIR = Path("Legacy MOSFETs") / "Modules"


@dataclass(frozen=True)
class WolfspeedModuleFamilyRecord:
    """One normalized module family and its available XML/PDF source sections."""

    part_number: str
    main_xml: Path | None
    bodydiode_xml: Path | None
    schottkydiode_xml: Path | None
    diode_xml: Path | None
    main_pdf: Path | None
    bodydiode_pdf: Path | None
    schottkydiode_pdf: Path | None
    diode_pdf: Path | None

    @property
    def has_main_pair(self) -> bool:
        return self.main_xml is not None and self.main_pdf is not None

    @property
    def has_bodydiode_pair(self) -> bool:
        return self.bodydiode_xml is not None and self.bodydiode_pdf is not None

    @property
    def has_schottkydiode_pair(self) -> bool:
        return self.schottkydiode_xml is not None and self.schottkydiode_pdf is not None

    @property
    def has_diode_pair(self) -> bool:
        return self.diode_xml is not None and self.diode_pdf is not None

    @property
    def has_any_diode_section_pair(self) -> bool:
        return self.has_bodydiode_pair or self.has_schottkydiode_pair or self.has_diode_pair

    @property
    def available_section_kinds(self) -> tuple[str, ...]:
        kinds: list[str] = []
        if self.main_xml is not None or self.main_pdf is not None:
            kinds.append("main")
        if self.bodydiode_xml is not None or self.bodydiode_pdf is not None:
            kinds.append("bodydiode")
        if self.schottkydiode_xml is not None or self.schottkydiode_pdf is not None:
            kinds.append("schottkydiode")
        if self.diode_xml is not None or self.diode_pdf is not None:
            kinds.append("diode")
        return tuple(kinds)


@dataclass(frozen=True)
class WolfspeedModuleSeedCandidate:
    """Read-only registration-risk classification for one module family."""

    part_number: str
    candidate_class: str
    diode_section_kind: str
    registration_priority: str
    registration_ready: bool
    reasons: tuple[str, ...]
    blocking_issue_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class WolfspeedModuleReadinessInventory:
    """Deterministic source readiness summary for Wolfspeed legacy modules."""

    source_dir: Path
    xml_count: int
    pdf_count: int
    main_xml_count: int
    bodydiode_xml_count: int
    schottkydiode_xml_count: int
    diode_xml_count: int
    main_pdf_count: int
    bodydiode_pdf_count: int
    schottkydiode_pdf_count: int
    diode_pdf_count: int
    family_count: int
    main_pair_count: int
    module_with_any_diode_pair_count: int
    module_with_bodydiode_pair_count: int
    module_with_schottkydiode_pair_count: int
    module_with_diode_pair_count: int
    parse_ok_count: int
    parse_failed: tuple[str, ...]
    seed_candidates: tuple[WolfspeedModuleSeedCandidate, ...]
    ready_bodydiode_seed_count: int
    ready_schottkydiode_seed_count: int
    diode_only_deferred_count: int
    incomplete_or_failed_count: int
    families: tuple[WolfspeedModuleFamilyRecord, ...]


def discover_wolfspeed_module_readiness_inventory(
    source_dir: str | Path,
) -> WolfspeedModuleReadinessInventory:
    """Scan Wolfspeed legacy module sources without registering runtime devices."""

    source_path = Path(source_dir)
    if not source_path.exists():
        raise FileNotFoundError(f"Wolfspeed legacy module source folder not found: {source_path}")

    xml_by_kind = _collect_files_by_kind(source_path, "*.xml")
    pdf_by_kind = _collect_files_by_kind(source_path, "*.pdf")
    family_parts = sorted(
        set().union(
            *(set(files) for files in xml_by_kind.values()),
            *(set(files) for files in pdf_by_kind.values()),
        )
    )
    families = tuple(
        WolfspeedModuleFamilyRecord(
            part_number=part,
            main_xml=xml_by_kind["main"].get(part),
            bodydiode_xml=xml_by_kind["bodydiode"].get(part),
            schottkydiode_xml=xml_by_kind["schottkydiode"].get(part),
            diode_xml=xml_by_kind["diode"].get(part),
            main_pdf=pdf_by_kind["main"].get(part),
            bodydiode_pdf=pdf_by_kind["bodydiode"].get(part),
            schottkydiode_pdf=pdf_by_kind["schottkydiode"].get(part),
            diode_pdf=pdf_by_kind["diode"].get(part),
        )
        for part in family_parts
    )
    parse_ok_count = 0
    parse_failed: list[str] = []
    parse_ok_keys: set[tuple[str, str]] = set()
    for kind in ("main", "bodydiode", "schottkydiode", "diode"):
        for part, xml_path in sorted(xml_by_kind[kind].items()):
            try:
                parse_plecs_xml(xml_path)
            except Exception as exc:
                parse_failed.append(f"{part}:{kind}:{type(exc).__name__}")
            else:
                parse_ok_keys.add((part, kind))
                parse_ok_count += 1
    seed_candidates = tuple(_classify_seed_candidate(family, parse_ok_keys) for family in families)

    return WolfspeedModuleReadinessInventory(
        source_dir=source_path,
        xml_count=sum(len(files) for files in xml_by_kind.values()),
        pdf_count=sum(len(files) for files in pdf_by_kind.values()),
        main_xml_count=len(xml_by_kind["main"]),
        bodydiode_xml_count=len(xml_by_kind["bodydiode"]),
        schottkydiode_xml_count=len(xml_by_kind["schottkydiode"]),
        diode_xml_count=len(xml_by_kind["diode"]),
        main_pdf_count=len(pdf_by_kind["main"]),
        bodydiode_pdf_count=len(pdf_by_kind["bodydiode"]),
        schottkydiode_pdf_count=len(pdf_by_kind["schottkydiode"]),
        diode_pdf_count=len(pdf_by_kind["diode"]),
        family_count=len(families),
        main_pair_count=sum(1 for family in families if family.has_main_pair),
        module_with_any_diode_pair_count=sum(1 for family in families if family.has_any_diode_section_pair),
        module_with_bodydiode_pair_count=sum(1 for family in families if family.has_bodydiode_pair),
        module_with_schottkydiode_pair_count=sum(1 for family in families if family.has_schottkydiode_pair),
        module_with_diode_pair_count=sum(1 for family in families if family.has_diode_pair),
        parse_ok_count=parse_ok_count,
        parse_failed=tuple(parse_failed),
        seed_candidates=seed_candidates,
        ready_bodydiode_seed_count=sum(
            1 for candidate in seed_candidates
            if candidate.registration_ready and candidate.diode_section_kind == "body_diode"
        ),
        ready_schottkydiode_seed_count=sum(
            1 for candidate in seed_candidates
            if candidate.registration_ready and candidate.diode_section_kind == "sic_sbd"
        ),
        diode_only_deferred_count=sum(1 for candidate in seed_candidates if candidate.candidate_class == "diode_only_deferred"),
        incomplete_or_failed_count=sum(
            1 for candidate in seed_candidates
            if candidate.candidate_class in {"incomplete", "parse_failed"}
        ),
        families=families,
    )


def classify_wolfspeed_module_section_kind(source_kind: str) -> str:
    """Map Wolfspeed source section suffixes to PE-Claw diode subtype semantics."""

    normalized = source_kind.strip().casefold()
    if normalized == "bodydiode":
        return "body_diode"
    if normalized == "schottkydiode":
        return "sic_sbd"
    if normalized == "diode":
        return "module_diode"
    if normalized == "main":
        return "module_switch"
    return "unknown"


def _classify_seed_candidate(
    family: WolfspeedModuleFamilyRecord,
    parse_ok_keys: set[tuple[str, str]],
) -> WolfspeedModuleSeedCandidate:
    reasons: list[str] = []
    main_ok = family.has_main_pair and (family.part_number, "main") in parse_ok_keys
    body_ok = family.has_bodydiode_pair and (family.part_number, "bodydiode") in parse_ok_keys
    schottky_ok = family.has_schottkydiode_pair and (family.part_number, "schottkydiode") in parse_ok_keys
    diode_ok = family.has_diode_pair and (family.part_number, "diode") in parse_ok_keys

    if main_ok and body_ok:
        return WolfspeedModuleSeedCandidate(
            part_number=family.part_number,
            candidate_class="main_with_bodydiode",
            diode_section_kind=classify_wolfspeed_module_section_kind("bodydiode"),
            registration_priority="primary",
            registration_ready=True,
            reasons=("main XML/PDF pair parses", "bodydiode XML/PDF pair parses", "bodydiode maps to body_diode"),
            blocking_issue_codes=(),
        )
    if main_ok and schottky_ok:
        return WolfspeedModuleSeedCandidate(
            part_number=family.part_number,
            candidate_class="main_with_schottkydiode",
            diode_section_kind=classify_wolfspeed_module_section_kind("schottkydiode"),
            registration_priority="primary",
            registration_ready=True,
            reasons=("main XML/PDF pair parses", "schottkydiode XML/PDF pair parses", "schottkydiode maps to sic_sbd"),
            blocking_issue_codes=(),
        )
    if diode_ok and not main_ok:
        return WolfspeedModuleSeedCandidate(
            part_number=family.part_number,
            candidate_class="diode_only_deferred",
            diode_section_kind=classify_wolfspeed_module_section_kind("diode"),
            registration_priority="deferred",
            registration_ready=False,
            reasons=("diode XML/PDF pair parses", "no paired module switch main section"),
            blocking_issue_codes=("module_diode_only_no_switch_pair",),
        )

    blocking_codes = _blocking_issue_codes(family, parse_ok_keys)
    if family.has_main_pair and not main_ok:
        reasons.append("main pair exists but parser failed")
    elif not family.has_main_pair:
        reasons.append("missing main XML/PDF pair")
    if family.has_any_diode_section_pair:
        reasons.append("no parse-ready paired bodydiode or schottkydiode section")
        candidate_class = "parse_failed"
    else:
        reasons.append("missing paired diode section")
        candidate_class = "incomplete"
    return WolfspeedModuleSeedCandidate(
        part_number=family.part_number,
        candidate_class=candidate_class,
        diode_section_kind="unknown",
        registration_priority="blocked",
        registration_ready=False,
        reasons=tuple(reasons),
        blocking_issue_codes=blocking_codes,
    )


def _blocking_issue_codes(
    family: WolfspeedModuleFamilyRecord,
    parse_ok_keys: set[tuple[str, str]],
) -> tuple[str, ...]:
    codes: list[str] = []
    _append_missing_pair_codes(codes, "main", family.main_xml, family.main_pdf)
    _append_missing_pair_codes(codes, "bodydiode", family.bodydiode_xml, family.bodydiode_pdf)
    _append_missing_pair_codes(codes, "schottkydiode", family.schottkydiode_xml, family.schottkydiode_pdf)
    _append_missing_pair_codes(codes, "diode", family.diode_xml, family.diode_pdf)

    for kind, xml_path in (
        ("main", family.main_xml),
        ("bodydiode", family.bodydiode_xml),
        ("schottkydiode", family.schottkydiode_xml),
        ("diode", family.diode_xml),
    ):
        if xml_path is not None and (family.part_number, kind) not in parse_ok_keys:
            codes.append(f"{kind}_xml_parse_failed")

    if family.main_xml is None and family.main_pdf is not None:
        codes.append("datasheet_alias_family_without_xml")

    return tuple(dict.fromkeys(codes))


def _append_missing_pair_codes(codes: list[str], kind: str, xml_path: Path | None, pdf_path: Path | None) -> None:
    if xml_path is None and pdf_path is None:
        return
    if xml_path is None:
        codes.append(f"{kind}_xml_missing")
    if pdf_path is None:
        codes.append(f"{kind}_pdf_missing")


def _collect_files_by_kind(source_path: Path, pattern: str) -> dict[str, dict[str, Path]]:
    grouped: dict[str, dict[str, Path]] = {
        "main": {},
        "bodydiode": {},
        "schottkydiode": {},
        "diode": {},
    }
    for path in source_path.glob(pattern):
        part, kind = _normalize_module_source_name(path.name)
        grouped[kind][part] = path
        if pattern == "*.pdf" and kind == "main" and _is_module_datasheet_alias(path.name):
            grouped["bodydiode"].setdefault(part, path)
    return grouped


def _normalize_module_source_name(filename: str) -> tuple[str, str]:
    stem = Path(filename).stem.upper()
    alias_match = re.fullmatch(r"([A-Z0-9]+)_([A-Z0-9]+L)_DATA_?SHEET", stem)
    if alias_match:
        return alias_match.group(1), "main"
    stem = re.sub(r"_DATA_?SHEET$", "", stem)
    stem = re.sub(r"_DATASHEET$", "", stem)
    if stem.endswith("_BODYDIODE"):
        return stem.removesuffix("_BODYDIODE"), "bodydiode"
    if stem.endswith("_SCHOTTKYDIODE"):
        return stem.removesuffix("_SCHOTTKYDIODE"), "schottkydiode"
    if stem.endswith("_DIODE"):
        return stem.removesuffix("_DIODE"), "diode"
    return stem, "main"


def _is_module_datasheet_alias(filename: str) -> bool:
    stem = Path(filename).stem.upper()
    return re.fullmatch(r"([A-Z0-9]+)_([A-Z0-9]+L)_DATA_?SHEET", stem) is not None


__all__ = [
    "WOLFSPEED_LEGACY_MODULE_SOURCE_SUBDIR",
    "WolfspeedModuleFamilyRecord",
    "WolfspeedModuleReadinessInventory",
    "WolfspeedModuleSeedCandidate",
    "classify_wolfspeed_module_section_kind",
    "discover_wolfspeed_module_readiness_inventory",
]
