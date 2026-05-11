"""Centralized semiconductor package templates and normalization helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SemiconductorPackageTemplate:
    """First-pass package metadata and renderer geometry inputs."""

    canonical_name: str
    aliases: tuple[str, ...]
    package_family: str
    body_width_mm: float
    body_height_mm: float
    body_thickness_mm: float
    lead_count: int
    mounting_style: str
    lead_style: str
    tab_cue: str | None
    renderer_template_id: str
    tab_width_mm: float
    tab_height_mm: float
    hole_diameter_mm: float
    lead_pitch_mm: float
    lead_width_mm: float
    lead_length_mm: float
    datasheet_basis: str

    @property
    def canonical_key(self) -> str:
        return normalize_package_name(self.canonical_name)


@dataclass(frozen=True)
class ResolvedSemiconductorPackage:
    """Resolved package lookup result used by the geometry pipeline."""

    raw_package: str
    normalized_package: str
    canonical_package: str
    canonical_key: str
    package_family: str
    renderer_template_id: str
    template: SemiconductorPackageTemplate
    fallback_warning: str | None = None


def normalize_package_name(package_name: str) -> str:
    """Normalize a raw package string into a stable comparison key."""

    if not package_name:
        return ""
    tokens = re.findall(r"[a-z0-9]+", package_name.casefold())
    return "-".join(tokens)


_GENERIC_FALLBACK_TEMPLATE = SemiconductorPackageTemplate(
    canonical_name="GENERIC-UNSUPPORTED-PACKAGE",
    aliases=(),
    package_family="generic",
    body_width_mm=10.0,
    body_height_mm=12.0,
    body_thickness_mm=3.0,
    lead_count=0,
    mounting_style="unknown",
    lead_style="generic",
    tab_cue=None,
    renderer_template_id="generic_power_package",
    tab_width_mm=0.0,
    tab_height_mm=0.0,
    hole_diameter_mm=0.0,
    lead_pitch_mm=2.54,
    lead_width_mm=0.8,
    lead_length_mm=5.0,
    datasheet_basis="Fallback only for unsupported device package strings.",
)


_PACKAGE_LIBRARY: tuple[SemiconductorPackageTemplate, ...] = (
    SemiconductorPackageTemplate(
        canonical_name="PG-TO252-3",
        aliases=("TO252-3", "TO-252-3", "DPAK", "D-PAK", "PG-TO252-3-1"),
        package_family="to252",
        body_width_mm=6.54,
        body_height_mm=6.10,
        body_thickness_mm=2.29,
        lead_count=3,
        mounting_style="surface-mount",
        lead_style="gullwing-bottom",
        tab_cue="drain tab",
        renderer_template_id="to252_3_dpak",
        tab_width_mm=5.22,
        tab_height_mm=2.55,
        hole_diameter_mm=0.0,
        lead_pitch_mm=2.29,
        lead_width_mm=0.77,
        lead_length_mm=3.84,
        datasheet_basis="Infineon PG-TO252-3 / DPAK outline used by IPD60RxxxCM8 datasheets.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="PG-TO263-7",
        aliases=("TO263-7", "TO-263-7", "D2PAK-7", "D2PAK7", "PG-TO263-7-1"),
        package_family="to263",
        body_width_mm=10.0,
        body_height_mm=9.25,
        body_thickness_mm=4.4,
        lead_count=7,
        mounting_style="surface-mount",
        lead_style="gullwing-bottom",
        tab_cue="drain tab",
        renderer_template_id="to263_7_d2pak",
        tab_width_mm=8.5,
        tab_height_mm=6.0,
        hole_diameter_mm=0.0,
        lead_pitch_mm=1.27,
        lead_width_mm=0.60,
        lead_length_mm=4.70,
        datasheet_basis="First-pass PG-TO263-7 / D2PAK-7 outline from Infineon CoolSiC MOSFET G2 750 V package rows.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="PG-TO220-3",
        aliases=("TO220-3", "TO-220-3", "PG-TO220-3-1", "TO220 FullPAK narrow leads"),
        package_family="to220",
        body_width_mm=10.2,
        body_height_mm=15.4,
        body_thickness_mm=4.7,
        lead_count=3,
        mounting_style="through-hole",
        lead_style="vertical",
        tab_cue="mounting tab",
        renderer_template_id="to220_3_tht",
        tab_width_mm=10.2,
        tab_height_mm=4.8,
        hole_diameter_mm=3.6,
        lead_pitch_mm=2.54,
        lead_width_mm=0.9,
        lead_length_mm=13.5,
        datasheet_basis="First-pass TO-220 front-view dimensions used by the CoolMOS 8 TO-220 package family.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="PG-TO220-2",
        aliases=("TO220-2", "TO-220-2", "TO-220AC-2L", "TO-220FM-2L"),
        package_family="to220",
        body_width_mm=10.2,
        body_height_mm=15.4,
        body_thickness_mm=4.7,
        lead_count=2,
        mounting_style="through-hole",
        lead_style="vertical",
        tab_cue="mounting tab",
        renderer_template_id="to220_3_tht",
        tab_width_mm=10.2,
        tab_height_mm=4.8,
        hole_diameter_mm=3.6,
        lead_pitch_mm=2.54,
        lead_width_mm=0.9,
        lead_length_mm=13.5,
        datasheet_basis="First-pass TO-220 2-lead envelope for ROHM SiC diode packages using the existing TO-220 renderer.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="PG-TO247-3",
        aliases=("TO247-3", "TO-247-3", "TO-247-3L", "TO247-3L", "TO-247N-3L", "TO247N-3L", "TO-247N family", "TO247N family"),
        package_family="to247",
        body_width_mm=15.9,
        body_height_mm=20.9,
        body_thickness_mm=5.0,
        lead_count=3,
        mounting_style="through-hole",
        lead_style="vertical",
        tab_cue="mounting tab",
        renderer_template_id="to247_3_tht",
        tab_width_mm=15.9,
        tab_height_mm=6.0,
        hole_diameter_mm=3.6,
        lead_pitch_mm=5.45,
        lead_width_mm=1.2,
        lead_length_mm=18.5,
        datasheet_basis="First-pass PG-TO247-3 outline based on Infineon TO-247 package family dimensions.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="PG-TO247-4",
        aliases=(
            "TO247-4",
            "TO-247-4",
            "TO-247-4L",
            "TO247-4L",
            "TO-247-7L Kelvin",
            "TO247-7L Kelvin",
            "DOT-247-7L",
            "DOT247-7L",
            "TO-247-4L / 7L Kelvin",
            "TO247-4L / 7L Kelvin",
            "TO-247N-4L Kelvin",
            "TO-247N-4L",
            "TO247N-4L Kelvin",
            "TO247N-4L",
        ),
        package_family="to247",
        body_width_mm=15.9,
        body_height_mm=20.9,
        body_thickness_mm=5.0,
        lead_count=4,
        mounting_style="through-hole",
        lead_style="vertical",
        tab_cue="mounting tab",
        renderer_template_id="to247_4_tht",
        tab_width_mm=15.9,
        tab_height_mm=6.0,
        hole_diameter_mm=3.6,
        lead_pitch_mm=3.55,
        lead_width_mm=1.0,
        lead_length_mm=18.5,
        datasheet_basis="First-pass PG-TO247-4 outline based on Infineon CoolMOS 8 TO-247-4 package rows.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="PG-TO247-2",
        aliases=("TO247-2", "TO-247-2", "TO-247-2L", "TO247-2L"),
        package_family="to247",
        body_width_mm=15.9,
        body_height_mm=20.9,
        body_thickness_mm=5.0,
        lead_count=2,
        mounting_style="through-hole",
        lead_style="vertical",
        tab_cue="mounting tab",
        renderer_template_id="to247_2_tht",
        tab_width_mm=15.9,
        tab_height_mm=6.0,
        hole_diameter_mm=3.6,
        lead_pitch_mm=5.45,
        lead_width_mm=1.2,
        lead_length_mm=18.5,
        datasheet_basis="First-pass TO-247 2-lead envelope for ROHM SiC diode packages using the existing TO-247 renderer.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="PG-TO263-2",
        aliases=("TO263-2", "TO-263-2", "D2PAK-2", "D2PAK2", "TO-263-2L"),
        package_family="to263",
        body_width_mm=10.0,
        body_height_mm=9.25,
        body_thickness_mm=4.4,
        lead_count=2,
        mounting_style="surface-mount",
        lead_style="gullwing-bottom",
        tab_cue="drain tab",
        renderer_template_id="to263_7_d2pak",
        tab_width_mm=8.5,
        tab_height_mm=6.0,
        hole_diameter_mm=0.0,
        lead_pitch_mm=2.29,
        lead_width_mm=0.77,
        lead_length_mm=4.70,
        datasheet_basis="First-pass TO-263 2-lead envelope for ROHM SiC diode packages using the existing D2PAK renderer.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="PG-HDSOP-10",
        aliases=("HDSOP-10", "PG-HDSOP-10-1", "D-DPAK", "DDPAK"),
        package_family="hdsop",
        body_width_mm=10.3,
        body_height_mm=9.7,
        body_thickness_mm=2.3,
        lead_count=10,
        mounting_style="surface-mount",
        lead_style="gullwing-dual-row",
        tab_cue="drain pad",
        renderer_template_id="hdsop_10_top",
        tab_width_mm=7.6,
        tab_height_mm=3.6,
        hole_diameter_mm=0.0,
        lead_pitch_mm=1.27,
        lead_width_mm=0.55,
        lead_length_mm=1.15,
        datasheet_basis="First-pass PG-HDSOP-10 top-view geometry from Infineon D-DPAK family proportions.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="PG-HDSOP-16",
        aliases=("HDSOP-16", "PGHDSOP16", "PG-HDSOP16", "TOLT"),
        package_family="hdsop",
        body_width_mm=10.6,
        body_height_mm=14.0,
        body_thickness_mm=1.2,
        lead_count=16,
        mounting_style="surface-mount",
        lead_style="leadless-dual-row",
        tab_cue="source pad",
        renderer_template_id="hdsop_16_top",
        tab_width_mm=7.8,
        tab_height_mm=5.0,
        hole_diameter_mm=0.0,
        lead_pitch_mm=0.8,
        lead_width_mm=0.45,
        lead_length_mm=0.95,
        datasheet_basis="First-pass PG-HDSOP-16 / TOLT top-view geometry for Infineon CoolGaN 650 V packages.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="PG-HDSOP-22",
        aliases=("HDSOP-22", "Q-DPAK", "QDPAK"),
        package_family="hdsop",
        body_width_mm=10.3,
        body_height_mm=10.0,
        body_thickness_mm=1.1,
        lead_count=22,
        mounting_style="surface-mount",
        lead_style="gullwing-dual-row",
        tab_cue="drain pad",
        renderer_template_id="hdsop_22_top",
        tab_width_mm=7.2,
        tab_height_mm=3.8,
        hole_diameter_mm=0.0,
        lead_pitch_mm=0.65,
        lead_width_mm=0.32,
        lead_length_mm=0.95,
        datasheet_basis="First-pass PG-HDSOP-22 top-view geometry from Infineon Q-DPAK package rows.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="PG-HSOF-8",
        aliases=("HSOF-8", "TOLL", "PG-HSOF-8-1", "PGHSOF8", "PG-HSOF8"),
        package_family="hsof",
        body_width_mm=9.9,
        body_height_mm=11.7,
        body_thickness_mm=2.3,
        lead_count=8,
        mounting_style="surface-mount",
        lead_style="gullwing-bottom",
        tab_cue="drain tab",
        renderer_template_id="hsof_8_top",
        tab_width_mm=7.2,
        tab_height_mm=4.6,
        hole_diameter_mm=0.0,
        lead_pitch_mm=1.27,
        lead_width_mm=0.60,
        lead_length_mm=1.50,
        datasheet_basis="First-pass PG-HSOF-8 / TOLL top-view geometry from CoolMOS 8 package rows.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="PG-DSO-20",
        aliases=("DSO-20", "PGDSO20", "PG-DSO20"),
        package_family="dso",
        body_width_mm=12.8,
        body_height_mm=10.3,
        body_thickness_mm=1.2,
        lead_count=20,
        mounting_style="surface-mount",
        lead_style="leadless-dual-row",
        tab_cue="source pad",
        renderer_template_id="dso_20_top",
        tab_width_mm=8.6,
        tab_height_mm=4.2,
        hole_diameter_mm=0.0,
        lead_pitch_mm=0.65,
        lead_width_mm=0.30,
        lead_length_mm=0.90,
        datasheet_basis="First-pass PG-DSO-20 top-view geometry for Infineon CoolGaN 650 V packages.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="PG-LHSOF-4",
        aliases=("LHSOF-4", "Thin-TOLL", "Thin TOLL", "Thin-TOLL 8x8"),
        package_family="lhsof",
        body_width_mm=10.0,
        body_height_mm=8.0,
        body_thickness_mm=1.0,
        lead_count=4,
        mounting_style="surface-mount",
        lead_style="gullwing-bottom",
        tab_cue="drain tab",
        renderer_template_id="lhsof_4_top",
        tab_width_mm=7.5,
        tab_height_mm=3.6,
        hole_diameter_mm=0.0,
        lead_pitch_mm=1.8,
        lead_width_mm=0.70,
        lead_length_mm=1.30,
        datasheet_basis="First-pass PG-LHSOF-4 / Thin-TOLL top-view geometry from CoolMOS 8 package rows.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="PG-TSON-8",
        aliases=("TSON-8", "PGTSON8", "PG-TSON8"),
        package_family="tson",
        body_width_mm=5.3,
        body_height_mm=6.1,
        body_thickness_mm=1.0,
        lead_count=8,
        mounting_style="surface-mount",
        lead_style="leadless-bottom",
        tab_cue="source pad",
        renderer_template_id="tson_8_top",
        tab_width_mm=3.8,
        tab_height_mm=2.6,
        hole_diameter_mm=0.0,
        lead_pitch_mm=0.8,
        lead_width_mm=0.35,
        lead_length_mm=0.65,
        datasheet_basis="First-pass PG-TSON-8 top-view geometry for Infineon CoolGaN 650 V packages.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="PG-LSON-8",
        aliases=("LSON-8", "PGLSON8", "PG-LSON8"),
        package_family="lson",
        body_width_mm=5.3,
        body_height_mm=6.1,
        body_thickness_mm=1.0,
        lead_count=8,
        mounting_style="surface-mount",
        lead_style="leadless-bottom",
        tab_cue="source pad",
        renderer_template_id="lson_8_top",
        tab_width_mm=3.8,
        tab_height_mm=2.6,
        hole_diameter_mm=0.0,
        lead_pitch_mm=0.8,
        lead_width_mm=0.35,
        lead_length_mm=0.65,
        datasheet_basis="First-pass PG-LSON-8 top-view geometry for Infineon CoolGaN 650 V packages.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="ThinPAK 8x8",
        aliases=("Thin-PAK 8x8", "ThinPAK8x8", "ThinPAK-8x8"),
        package_family="thinpak",
        body_width_mm=8.0,
        body_height_mm=8.0,
        body_thickness_mm=1.0,
        lead_count=8,
        mounting_style="surface-mount",
        lead_style="leadless-bottom",
        tab_cue="drain pad",
        renderer_template_id="thinpak_8x8_top",
        tab_width_mm=6.2,
        tab_height_mm=3.2,
        hole_diameter_mm=0.0,
        lead_pitch_mm=0.90,
        lead_width_mm=0.45,
        lead_length_mm=0.85,
        datasheet_basis="First-pass ThinPAK 8x8 top-view geometry based on Infineon ThinPAK 8x8 package overview dimensions.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="rohm_bsm_sic_module",
        aliases=("ROHM BSM SiC module", "ROHM-BSM-SiC-module"),
        package_family="power-module",
        body_width_mm=152.0,
        body_height_mm=75.0,
        body_thickness_mm=35.0,
        lead_count=6,
        mounting_style="module",
        lead_style="terminal-blocks",
        tab_cue="baseplate",
        renderer_template_id="module_half_bridge",
        tab_width_mm=18.0,
        tab_height_mm=9.0,
        hole_diameter_mm=6.0,
        lead_pitch_mm=18.0,
        lead_width_mm=6.0,
        lead_length_mm=8.0,
        datasheet_basis="First-pass ROHM BSM SiC module outline; runtime module dimensions override this template when available.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="DOT-247-7L half-bridge module",
        aliases=("DOT247-7L half-bridge module",),
        package_family="power-module",
        body_width_mm=26.45,
        body_height_mm=31.50,
        body_thickness_mm=5.25,
        lead_count=7,
        mounting_style="module",
        lead_style="leadframe-module",
        tab_cue="molded base",
        renderer_template_id="module_half_bridge",
        tab_width_mm=8.0,
        tab_height_mm=4.0,
        hole_diameter_mm=0.0,
        lead_pitch_mm=4.0,
        lead_width_mm=1.2,
        lead_length_mm=6.0,
        datasheet_basis="First-pass ROHM SCZ DOT-247 molded half-bridge module outline.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="dual_switch_half_bridge_module",
        aliases=(),
        package_family="power-module",
        body_width_mm=108.0,
        body_height_mm=62.0,
        body_thickness_mm=30.0,
        lead_count=6,
        mounting_style="module",
        lead_style="terminal-blocks",
        tab_cue="baseplate",
        renderer_template_id="module_half_bridge",
        tab_width_mm=18.0,
        tab_height_mm=9.0,
        hole_diameter_mm=6.0,
        lead_pitch_mm=18.0,
        lead_width_mm=6.0,
        lead_length_mm=8.0,
        datasheet_basis="First-pass Mitsubishi dual-switch half-bridge module outline; runtime module dimensions override this template when available.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="dual_switch_hvigbt_module",
        aliases=(),
        package_family="power-module",
        body_width_mm=140.0,
        body_height_mm=110.0,
        body_thickness_mm=40.0,
        lead_count=6,
        mounting_style="module",
        lead_style="terminal-blocks",
        tab_cue="baseplate",
        renderer_template_id="module_half_bridge",
        tab_width_mm=22.0,
        tab_height_mm=10.0,
        hole_diameter_mm=6.0,
        lead_pitch_mm=24.0,
        lead_width_mm=7.0,
        lead_length_mm=10.0,
        datasheet_basis="First-pass Mitsubishi HVIGBT half-bridge module outline; runtime module dimensions override this template when available.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="dual_switch_hvigbt_flat_baseplate_module",
        aliases=(),
        package_family="power-module",
        body_width_mm=140.0,
        body_height_mm=130.0,
        body_thickness_mm=38.0,
        lead_count=6,
        mounting_style="module",
        lead_style="terminal-blocks",
        tab_cue="flat baseplate",
        renderer_template_id="module_flat_baseplate",
        tab_width_mm=22.0,
        tab_height_mm=10.0,
        hole_diameter_mm=6.0,
        lead_pitch_mm=24.0,
        lead_width_mm=7.0,
        lead_length_mm=10.0,
        datasheet_basis="First-pass Mitsubishi HVIGBT flat-baseplate module outline; runtime module dimensions override this template when available.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="dual_switch_half_bridge_copper_baseplate_module",
        aliases=(),
        package_family="power-module",
        body_width_mm=140.0,
        body_height_mm=130.0,
        body_thickness_mm=34.0,
        lead_count=6,
        mounting_style="module",
        lead_style="terminal-blocks",
        tab_cue="copper baseplate",
        renderer_template_id="module_half_bridge",
        tab_width_mm=22.0,
        tab_height_mm=10.0,
        hole_diameter_mm=6.0,
        lead_pitch_mm=24.0,
        lead_width_mm=7.0,
        lead_length_mm=10.0,
        datasheet_basis="First-pass Mitsubishi copper-baseplate half-bridge module outline; runtime module dimensions override this template when available.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="single_switch_hvigbt_module",
        aliases=(),
        package_family="power-module",
        body_width_mm=190.0,
        body_height_mm=140.0,
        body_thickness_mm=45.0,
        lead_count=4,
        mounting_style="module",
        lead_style="terminal-blocks",
        tab_cue="baseplate",
        renderer_template_id="module_single_switch",
        tab_width_mm=28.0,
        tab_height_mm=12.0,
        hole_diameter_mm=7.0,
        lead_pitch_mm=36.0,
        lead_width_mm=8.0,
        lead_length_mm=10.0,
        datasheet_basis="First-pass Mitsubishi single-switch HVIGBT module outline; runtime module dimensions override this template when available.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="hybrid_hvigbt_flat_baseplate_module",
        aliases=(),
        package_family="power-module",
        body_width_mm=140.0,
        body_height_mm=130.0,
        body_thickness_mm=38.0,
        lead_count=6,
        mounting_style="module",
        lead_style="terminal-blocks",
        tab_cue="flat baseplate",
        renderer_template_id="module_flat_baseplate",
        tab_width_mm=22.0,
        tab_height_mm=10.0,
        hole_diameter_mm=6.0,
        lead_pitch_mm=24.0,
        lead_width_mm=7.0,
        lead_length_mm=10.0,
        datasheet_basis="First-pass Mitsubishi hybrid HVIGBT flat-baseplate module outline; runtime module dimensions override this template when available.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="six_in_one_direct_cooling_module",
        aliases=(),
        package_family="power-module",
        body_width_mm=154.0,
        body_height_mm=115.0,
        body_thickness_mm=32.0,
        lead_count=12,
        mounting_style="module",
        lead_style="terminal-blocks",
        tab_cue="direct cooling base",
        renderer_template_id="module_six_pack",
        tab_width_mm=18.0,
        tab_height_mm=8.0,
        hole_diameter_mm=6.0,
        lead_pitch_mm=11.0,
        lead_width_mm=5.0,
        lead_length_mm=8.0,
        datasheet_basis="First-pass Mitsubishi six-in-one direct-cooling module outline; runtime module dimensions override this template when available.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="hvmosfet_dual_module",
        aliases=(),
        package_family="power-module",
        body_width_mm=140.0,
        body_height_mm=110.0,
        body_thickness_mm=40.0,
        lead_count=6,
        mounting_style="module",
        lead_style="terminal-blocks",
        tab_cue="baseplate",
        renderer_template_id="module_half_bridge",
        tab_width_mm=22.0,
        tab_height_mm=10.0,
        hole_diameter_mm=6.0,
        lead_pitch_mm=24.0,
        lead_width_mm=7.0,
        lead_length_mm=10.0,
        datasheet_basis="First-pass Mitsubishi high-voltage dual MOSFET module outline; runtime module dimensions override this template when available.",
    ),
    SemiconductorPackageTemplate(
        canonical_name="sic_mosfet_module",
        aliases=(),
        package_family="power-module",
        body_width_mm=108.0,
        body_height_mm=62.0,
        body_thickness_mm=30.0,
        lead_count=6,
        mounting_style="module",
        lead_style="terminal-blocks",
        tab_cue="baseplate",
        renderer_template_id="module_half_bridge",
        tab_width_mm=18.0,
        tab_height_mm=9.0,
        hole_diameter_mm=6.0,
        lead_pitch_mm=18.0,
        lead_width_mm=6.0,
        lead_length_mm=8.0,
        datasheet_basis="First-pass Mitsubishi SiC MOSFET module outline; runtime module dimensions override this template when available.",
    ),
)


def get_package_templates() -> tuple[SemiconductorPackageTemplate, ...]:
    """Return the centralized package-template library."""

    return _PACKAGE_LIBRARY


def get_package_template(package_name: str) -> SemiconductorPackageTemplate | None:
    """Look up a package template by raw or canonical package string."""

    return _PACKAGE_ALIAS_MAP.get(normalize_package_name(package_name))


def resolve_package_template(package_name: str) -> ResolvedSemiconductorPackage:
    """Resolve a raw package string into a canonical package template."""

    normalized = normalize_package_name(package_name)
    template = _PACKAGE_ALIAS_MAP.get(normalized)
    if template is not None:
        return ResolvedSemiconductorPackage(
            raw_package=package_name,
            normalized_package=normalized,
            canonical_package=template.canonical_name,
            canonical_key=template.canonical_key,
            package_family=template.package_family,
            renderer_template_id=template.renderer_template_id,
            template=template,
        )

    warning = (
        f"Unsupported package '{package_name}' normalized as '{normalized or 'unknown'}'; "
        f"falling back to generic renderer '{_GENERIC_FALLBACK_TEMPLATE.renderer_template_id}'."
    )
    return ResolvedSemiconductorPackage(
        raw_package=package_name,
        normalized_package=normalized,
        canonical_package=_GENERIC_FALLBACK_TEMPLATE.canonical_name,
        canonical_key=_GENERIC_FALLBACK_TEMPLATE.canonical_key,
        package_family=_GENERIC_FALLBACK_TEMPLATE.package_family,
        renderer_template_id=_GENERIC_FALLBACK_TEMPLATE.renderer_template_id,
        template=_GENERIC_FALLBACK_TEMPLATE,
        fallback_warning=warning,
    )


def validate_registered_packages(
    package_names: Iterable[str],
    *,
    require_supported: bool = False,
) -> tuple[ResolvedSemiconductorPackage, ...]:
    """Resolve a package list and optionally fail if any package is unsupported."""

    resolved = tuple(resolve_package_template(package_name) for package_name in package_names)
    if require_supported:
        unsupported = [
            f"{item.raw_package!r} -> {item.normalized_package or 'unknown'}"
            for item in resolved
            if item.fallback_warning is not None
        ]
        if unsupported:
            raise ValueError("Unsupported semiconductor packages: " + ", ".join(sorted(unsupported)))
    return resolved


def _build_package_alias_map() -> dict[str, SemiconductorPackageTemplate]:
    alias_map: dict[str, SemiconductorPackageTemplate] = {}
    for template in _PACKAGE_LIBRARY:
        for raw_name in (template.canonical_name, *template.aliases):
            normalized = normalize_package_name(raw_name)
            existing = alias_map.get(normalized)
            if existing is not None and existing.canonical_name != template.canonical_name:
                raise ValueError(
                    f"Package alias collision for '{raw_name}' between "
                    f"{existing.canonical_name} and {template.canonical_name}."
                )
            alias_map[normalized] = template
    return alias_map


_PACKAGE_ALIAS_MAP = _build_package_alias_map()


__all__ = [
    "ResolvedSemiconductorPackage",
    "SemiconductorPackageTemplate",
    "get_package_template",
    "get_package_templates",
    "normalize_package_name",
    "resolve_package_template",
    "validate_registered_packages",
]
