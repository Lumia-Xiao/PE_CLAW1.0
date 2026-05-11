"""Default engineering-allow profiles for magnetic candidate screening."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class MagneticAllowProfile:
    """One resolved engineering-allow profile for a magnetic design frequency band."""

    band_name: str
    fs_min_hz: float
    fs_max_hz: float
    b_allow_ratio_to_bsat_100c: float
    loss_allow_power_ratio: float
    loss_allow_density_w_per_cm3: float
    j_allow_a_per_mm2: float
    fill_allow: float

    def to_dict(self) -> dict[str, float | str]:
        """Return the profile as a serializable dictionary."""
        return asdict(self)


_DEFAULT_ALLOW_PROFILES: tuple[MagneticAllowProfile, ...] = (
    MagneticAllowProfile(
        band_name="10 kHz to < 50 kHz",
        fs_min_hz=10e3,
        fs_max_hz=50e3,
        b_allow_ratio_to_bsat_100c=0.50,
        loss_allow_power_ratio=0.010,
        loss_allow_density_w_per_cm3=0.6,
        j_allow_a_per_mm2=5.0,
        fill_allow=0.40,
    ),
    MagneticAllowProfile(
        band_name="50 kHz to < 300 kHz",
        fs_min_hz=50e3,
        fs_max_hz=300e3,
        b_allow_ratio_to_bsat_100c=0.40,
        loss_allow_power_ratio=0.007,
        loss_allow_density_w_per_cm3=0.35,
        j_allow_a_per_mm2=4.0,
        fill_allow=0.33,
    ),
    MagneticAllowProfile(
        band_name="300 kHz to <= 1 MHz",
        fs_min_hz=300e3,
        fs_max_hz=1e6,
        b_allow_ratio_to_bsat_100c=0.30,
        loss_allow_power_ratio=0.005,
        loss_allow_density_w_per_cm3=0.2,
        j_allow_a_per_mm2=3.0,
        fill_allow=0.25,
    ),
)


def resolve_frequency_band(fs_hz: float) -> str:
    """Resolve the default engineering-allow frequency band for a switching frequency."""
    return get_default_allow_profile(fs_hz).band_name


def get_default_allow_profile(fs_hz: float) -> MagneticAllowProfile:
    """Return the platform default engineering-allow profile for a switching frequency."""
    if fs_hz < _DEFAULT_ALLOW_PROFILES[0].fs_min_hz:
        return _DEFAULT_ALLOW_PROFILES[0]
    for profile in _DEFAULT_ALLOW_PROFILES:
        if profile.fs_min_hz <= fs_hz < profile.fs_max_hz:
            return profile
    return _DEFAULT_ALLOW_PROFILES[-1]
