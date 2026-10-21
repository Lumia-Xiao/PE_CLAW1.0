from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from .design import API_SCHEMA_VERSION, WebContractModel


class LoginRequest(WebContractModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class RegisterRequest(WebContractModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=12, max_length=256)


class PasswordChangeRequest(WebContractModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=12, max_length=256)


class UserSummary(WebContractModel):
    user_id: str = Field(pattern=r"^[A-Za-z0-9_-]{3,64}$")
    username: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,63}$")
    role: Literal["user", "admin"]


class AdminUserSummary(UserSummary):
    active: bool
    created_at: datetime


class AdminUserUpdate(WebContractModel):
    role: Literal["user", "admin"] | None = None
    active: bool | None = None

    @model_validator(mode="after")
    def require_change(self) -> "AdminUserUpdate":
        if self.role is None and self.active is None:
            raise ValueError("At least one user property must be supplied")
        return self


class AdminPasswordReset(WebContractModel):
    new_password: str = Field(min_length=12, max_length=256)


class SessionResponse(WebContractModel):
    schema_version: Literal["1.0"] = API_SCHEMA_VERSION
    access_token: str = Field(min_length=32, max_length=256)
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime
    user: UserSummary


class SessionInfo(WebContractModel):
    schema_version: Literal["1.0"] = API_SCHEMA_VERSION
    expires_at: datetime
    user: UserSummary


class AdminUserCreate(WebContractModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=12, max_length=256)
    role: Literal["user", "admin"] = "user"


class AuditEventResponse(WebContractModel):
    schema_version: Literal["1.0"] = API_SCHEMA_VERSION
    event_id: str
    occurred_at: datetime
    actor_user_id: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    outcome: str
    details: dict[str, str | int | bool | None] = Field(default_factory=dict)
