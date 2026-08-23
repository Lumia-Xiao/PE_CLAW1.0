"""Static Sendust Fe-Si-Al Steinmetz coefficients for AC-DC low-frequency chokes."""

from __future__ import annotations

from dataclasses import dataclass


STEINMETZ_POWER_UNIT = "mW_per_cm3"
STEINMETZ_FREQUENCY_UNIT = "Hz"
STEINMETZ_FLUX_SWING_UNIT = "T_delta_b"
SENDUST_STEINMETZ_SOURCE = "Micrometals Steinmetz coefficients supplement, MS Sendust 60 Hz fit"


@dataclass(frozen=True)
class SendustSteinmetzMaterial:
    """One Sendust Fe-Si-Al low-frequency Steinmetz material record."""

    material_id: str
    display_name: str
    relative_permeability: float
    steinmetz_k: float
    steinmetz_alpha: float
    steinmetz_beta: float
    frequency_reference_hz: float = 60.0
    power_unit: str = STEINMETZ_POWER_UNIT
    frequency_unit: str = STEINMETZ_FREQUENCY_UNIT
    flux_swing_unit: str = STEINMETZ_FLUX_SWING_UNIT
    source: str = SENDUST_STEINMETZ_SOURCE


SENDUST_STEINMETZ_MATERIALS_60HZ: tuple[SendustSteinmetzMaterial, ...] = (
    SendustSteinmetzMaterial("ms_14", "MS-14 Sendust", 14.0, 1.0451, 1.0001, 1.7544),
    SendustSteinmetzMaterial("ms_26", "MS-26 Sendust", 26.0, 0.76487, 1.0002, 1.8394),
    SendustSteinmetzMaterial("ms_40", "MS-40 Sendust", 40.0, 0.55875, 1.0004, 1.8365),
    SendustSteinmetzMaterial("ms_60", "MS-60 Sendust", 60.0, 0.36886, 1.0004, 1.7766),
    SendustSteinmetzMaterial("ms_75", "MS-75 Sendust", 75.0, 0.36886, 1.0004, 1.7766),
    SendustSteinmetzMaterial("ms_90", "MS-90 Sendust", 90.0, 0.36886, 1.0004, 1.7766),
    SendustSteinmetzMaterial("ms_125", "MS-125 Sendust", 125.0, 0.26412, 1.0009, 1.7759),
    SendustSteinmetzMaterial("ms_147", "MS-147 Sendust", 147.0, 0.31891, 1.0005, 1.7983),
    SendustSteinmetzMaterial("ms_160", "MS-160 Sendust", 160.0, 0.30532, 1.0005, 1.8248),
)

DEFAULT_SENDUST_STEINMETZ_MATERIAL_ID = "ms_60"
CONSERVATIVE_SENDUST_STEINMETZ_MATERIAL_ID = "ms_26"


def list_sendust_steinmetz_materials() -> tuple[SendustSteinmetzMaterial, ...]:
    """Return the fixed Sendust Steinmetz material table."""

    return SENDUST_STEINMETZ_MATERIALS_60HZ


def get_sendust_steinmetz_material(material_id: str) -> SendustSteinmetzMaterial:
    """Return one Sendust Steinmetz material by stable material id."""

    normalized_id = material_id.strip().casefold()
    for material in SENDUST_STEINMETZ_MATERIALS_60HZ:
        if material.material_id == normalized_id:
            return material
    raise KeyError(f"Unknown Sendust Steinmetz material id: {material_id}")


def estimate_sendust_core_loss_mw_per_cm3(
    material: SendustSteinmetzMaterial,
    *,
    frequency_hz: float,
    delta_b_t: float,
) -> float:
    """Estimate core loss density using P = k * f^alpha * deltaB^beta."""

    if frequency_hz < 0.0:
        raise ValueError("frequency_hz must be non-negative")
    if delta_b_t < 0.0:
        raise ValueError("delta_b_t must be non-negative")
    return material.steinmetz_k * (frequency_hz ** material.steinmetz_alpha) * (delta_b_t ** material.steinmetz_beta)
