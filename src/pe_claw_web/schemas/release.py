from __future__ import annotations

from pydantic import Field

from .design import API_SCHEMA_VERSION, WebContractModel


class ReleaseInfo(WebContractModel):
    schema_version: str = API_SCHEMA_VERSION
    application_version: str
    frontend_version: str
    migration_revision: str
    pipeline_version: str = Field(min_length=64, max_length=64)
    release_revision: str
    python_version: str
    dependencies: dict[str, str]
    built_at: str | None = None
