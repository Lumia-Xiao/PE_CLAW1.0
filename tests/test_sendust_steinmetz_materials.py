from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from pe_claw_gui.libraries.magnetics.sendust_steinmetz import (
    CONSERVATIVE_SENDUST_STEINMETZ_MATERIAL_ID,
    DEFAULT_SENDUST_STEINMETZ_MATERIAL_ID,
    STEINMETZ_FLUX_SWING_UNIT,
    STEINMETZ_FREQUENCY_UNIT,
    STEINMETZ_POWER_UNIT,
    estimate_sendust_core_loss_mw_per_cm3,
    get_sendust_steinmetz_material,
    list_sendust_steinmetz_materials,
)


def test_sendust_steinmetz_table_contains_fixed_60hz_materials() -> None:
    materials = list_sendust_steinmetz_materials()
    ids = [material.material_id for material in materials]

    assert ids == ["ms_14", "ms_26", "ms_40", "ms_60", "ms_75", "ms_90", "ms_125", "ms_147", "ms_160"]
    assert all(material.frequency_reference_hz == 60.0 for material in materials)
    assert all(material.power_unit == STEINMETZ_POWER_UNIT for material in materials)
    assert all(material.frequency_unit == STEINMETZ_FREQUENCY_UNIT for material in materials)
    assert all(material.flux_swing_unit == STEINMETZ_FLUX_SWING_UNIT for material in materials)


def test_default_and_conservative_sendust_material_parameters_are_locked() -> None:
    default = get_sendust_steinmetz_material(DEFAULT_SENDUST_STEINMETZ_MATERIAL_ID)
    conservative = get_sendust_steinmetz_material(CONSERVATIVE_SENDUST_STEINMETZ_MATERIAL_ID)

    assert default.display_name == "MS-60 Sendust"
    assert default.relative_permeability == pytest.approx(60.0)
    assert default.steinmetz_k == pytest.approx(0.36886)
    assert default.steinmetz_alpha == pytest.approx(1.0004)
    assert default.steinmetz_beta == pytest.approx(1.7766)
    assert conservative.display_name == "MS-26 Sendust"
    assert conservative.steinmetz_k == pytest.approx(0.76487)
    assert conservative.steinmetz_alpha == pytest.approx(1.0002)
    assert conservative.steinmetz_beta == pytest.approx(1.8394)


def test_sendust_core_loss_density_uses_delta_b_tesla() -> None:
    material = get_sendust_steinmetz_material("ms_60")

    loss = estimate_sendust_core_loss_mw_per_cm3(material, frequency_hz=50.0, delta_b_t=0.2)

    expected = material.steinmetz_k * (50.0 ** material.steinmetz_alpha) * (0.2 ** material.steinmetz_beta)
    assert loss == pytest.approx(expected)
    assert loss > 0.0


def test_sendust_core_loss_density_rejects_negative_inputs() -> None:
    material = get_sendust_steinmetz_material("ms_60")

    with pytest.raises(ValueError):
        estimate_sendust_core_loss_mw_per_cm3(material, frequency_hz=-1.0, delta_b_t=0.2)
    with pytest.raises(ValueError):
        estimate_sendust_core_loss_mw_per_cm3(material, frequency_hz=50.0, delta_b_t=-0.2)
    with pytest.raises(KeyError):
        get_sendust_steinmetz_material("missing")
