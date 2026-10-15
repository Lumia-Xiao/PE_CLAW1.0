"""Versioned Pydantic contracts for the public design API.

Only JSON-safe values cross this boundary. Filesystem paths, Python module
names, callables, and internal pipeline objects are deliberately absent from
the request models.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator


API_SCHEMA_VERSION = "1.0"
BUCK_TOPOLOGY_ID = "buck_diode_rectified_unidirectional"


class WebContractModel(BaseModel):
    """Common closed-schema behavior for public Web contracts."""

    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
        str_strip_whitespace=True,
        use_enum_values=True,
    )


class DesignRequest(WebContractModel):
    """Versioned base contract for currently supported design requests."""

    schema_version: Literal["1.0"] = API_SCHEMA_VERSION
    topology: Literal["buck_diode_rectified_unidirectional"] = BUCK_TOPOLOGY_ID


class SemiconductorManufacturer(StrEnum):
    any = "Any"
    infineon = "Infineon"
    navitas = "Navitas"
    mitsubishi = "Mitsubishi"
    rohm = "ROHM"
    wolfspeed = "Wolfspeed"


class BuckMainSwitchCategory(StrEnum):
    any = "Any active switch"
    discrete_mosfet = "Discrete MOSFET"
    discrete_silicon_mosfet = "Discrete Silicon MOSFET"
    discrete_sic_mosfet = "Discrete SiC MOSFET"
    gan_switch = "GaN switch"
    discrete_igbt = "Discrete IGBT"
    mosfet_module = "MOSFET module"
    igbt_module = "IGBT module"
    mosfet_sbd_module = "MOSFET + SBD module"
    igbt_fwd_module = "IGBT + FWD module"
    half_bridge_module = "Half-bridge module section"
    chopper_module = "Chopper module section"


class BuckRectifierCategory(StrEnum):
    any = "Any diode"
    discrete_sic_sbd = "Discrete SiC SBD"
    discrete_schottky = "Discrete Schottky diode"
    frd_fwd = "FRD / FWD"
    jbs = "JBS diode"
    diode_module = "Diode module"
    internal_module = "Internal diode section from selected switch module"


class BuckDesignOptions(WebContractModel):
    """Allowlisted GUI options that affect the Buck pipeline."""

    main_switch_category: BuckMainSwitchCategory = BuckMainSwitchCategory.any
    rectifier_diode_category: BuckRectifierCategory = BuckRectifierCategory.any
    semiconductor_manufacturer: SemiconductorManufacturer = SemiconductorManufacturer.any
    ambient_temp_c: float = Field(
        default=25.0,
        ge=-40.0,
        le=150.0,
        description="Ambient temperature in degrees Celsius.",
        json_schema_extra={"unit": "degC"},
    )
    target_junction_temp_c: float = Field(
        default=100.0,
        ge=25.0,
        le=175.0,
        description="Target semiconductor junction temperature in degrees Celsius.",
        json_schema_extra={"unit": "degC"},
    )


class BuckDesignRequest(DesignRequest):
    """Buck design-point inputs with explicit engineering units."""

    vin_min: float = Field(
        gt=0,
        description="Minimum input voltage in volts.",
        json_schema_extra={"unit": "V"},
    )
    vin_max: float = Field(
        gt=0,
        description="Maximum input voltage in volts.",
        json_schema_extra={"unit": "V"},
    )
    vout: float = Field(
        gt=0,
        description="Regulated output voltage in volts.",
        json_schema_extra={"unit": "V"},
    )
    pout: float = Field(
        gt=0,
        description="Rated output power in watts.",
        json_schema_extra={"unit": "W"},
    )
    fs_khz: float = Field(
        gt=0,
        description="Switching frequency in kilohertz.",
        json_schema_extra={"unit": "kHz"},
    )
    ripple_current_ratio: float = Field(
        gt=0,
        description="Peak-to-peak inductor-current ripple divided by output current.",
        json_schema_extra={"unit": "ratio"},
    )
    ripple_voltage_ratio_percent: float = Field(
        gt=0,
        description="Allowed output-voltage ripple in percent.",
        json_schema_extra={"unit": "%"},
    )
    options: BuckDesignOptions = Field(default_factory=BuckDesignOptions)

    @model_validator(mode="after")
    def validate_voltage_relationships(self) -> "BuckDesignRequest":
        if self.vin_max < self.vin_min:
            raise ValueError("vin_max must be greater than or equal to vin_min")
        if self.vout >= self.vin_min:
            raise ValueError("vout must be less than vin_min for the Buck topology")
        return self

    def pipeline_input(self) -> dict[str, float | str]:
        """Return only allowlisted raw fields consumed by the core pipeline."""

        electrical = self.model_dump(
            mode="json",
            exclude={"schema_version", "topology", "options"},
        )
        return {**electrical, **self.options.model_dump(mode="json")}


class OperatingPointRequest(WebContractModel):
    """Fixed-hardware operating point used by complete design jobs."""

    vin_v: float = Field(
        gt=0,
        description="Operating input voltage in volts.",
        json_schema_extra={"unit": "V"},
    )
    load_ratio: float = Field(
        ge=0,
        description="Requested load relative to rated load.",
        json_schema_extra={"unit": "ratio"},
    )


class DesignJobCreate(WebContractModel):
    schema_version: Literal["1.0"] = API_SCHEMA_VERSION
    request: BuckDesignRequest
    client_request_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9_-]+$",
    )
    execution_profile: Literal["complete"] = "complete"
    operating_point: OperatingPointRequest | None = None

    @model_validator(mode="after")
    def validate_operating_point(self) -> "DesignJobCreate":
        if self.operating_point is None:
            return self
        if not self.request.vin_min <= self.operating_point.vin_v <= self.request.vin_max:
            raise ValueError("operating_point.vin_v must be within the design Vin range")
        return self


class DesignJobStatus(StrEnum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"
    expired = "expired"


class DesignError(WebContractModel):
    schema_version: Literal["1.0"] = API_SCHEMA_VERSION
    code: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z][A-Za-z0-9_]*$")
    message: str = Field(min_length=1, max_length=500)
    correlation_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9_-]+$",
    )


class ArtifactManifestEntry(WebContractModel):
    schema_version: Literal["1.0"] = API_SCHEMA_VERSION
    id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    name: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
        description="Download filename only; paths are forbidden.",
    )
    media_type: str = Field(min_length=3, max_length=100, pattern=r"^[a-z0-9.+-]+/[a-z0-9.+-]+$")
    size: int = Field(ge=0, description="Artifact size in bytes", json_schema_extra={"unit": "byte"})
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stage: str = Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    download_url: str = Field(
        min_length=1,
        max_length=512,
        pattern=r"^/api/v1/design-jobs/[A-Za-z0-9_-]+(?:/actions/[A-Za-z0-9_-]+)?/artifacts/[A-Za-z0-9_-]+$",
    )


class DesignJobResponse(WebContractModel):
    schema_version: Literal["1.0"] = API_SCHEMA_VERSION
    job_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    topology: Literal["buck_diode_rectified_unidirectional"]
    status: DesignJobStatus
    progress: int = Field(
        ge=0,
        le=100,
        description="Job completion in percent.",
        json_schema_extra={"unit": "%"},
    )
    stage: str | None = Field(default=None, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: DesignError | None = None
    result_url: str | None = Field(default=None, pattern=r"^/api/v1/design-jobs/[A-Za-z0-9_-]+/result$")
    artifacts_url: str | None = Field(default=None, pattern=r"^/api/v1/design-jobs/[A-Za-z0-9_-]+/artifacts$")
    attempt: int = Field(default=0, ge=0)
    stages: dict[str, str] = Field(default_factory=dict)
    retryable: bool = False


class DesignResultResponse(WebContractModel):
    schema_version: Literal["1.0"] = API_SCHEMA_VERSION
    job_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    topology: Literal["buck_diode_rectified_unidirectional"]
    summary: dict[str, JsonValue]
    warnings: list[str] = Field(default_factory=list)
    artifacts: list[ArtifactManifestEntry] = Field(default_factory=list)
