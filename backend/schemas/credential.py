"""Pydantic schemas for credential management."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AuthType(str, Enum):
    BEARER_LOGIN = "bearer_login"
    BEARER_STATIC = "bearer_static"
    API_KEY = "api_key"
    BASIC = "basic"


# ---------- Create ----------


class CredentialCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    base_url: str = Field(..., min_length=1, max_length=2048)
    auth_type: AuthType

    # bearer_login
    login_endpoint: str | None = None
    login_method: str | None = "POST"
    login_body_template: str | None = None
    username: str | None = None
    password: str | None = None
    token_json_path: str | None = None
    token_ttl: int | None = None

    # bearer_static
    static_token: str | None = None

    # api_key
    api_key_header: str | None = "X-API-Key"
    api_key_value: str | None = None

    # basic (username / password reused from above)


# ---------- Response (list / detail) ----------


class CredentialResponse(BaseModel):
    id: uuid.UUID
    name: str
    base_url: str
    auth_type: AuthType
    login_endpoint: str | None = None
    api_key_header: str | None = None
    token_json_path: str | None = None
    token_ttl: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CredentialDetail(CredentialResponse):
    """Same as CredentialResponse — secrets always hidden."""

    pass


# ---------- Update ----------


class CredentialUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128)
    token_ttl: int | None = None

    # bearer_login / basic — overwrite password (leave None to keep existing)
    password: str | None = None

    # bearer_static — overwrite static token (leave None to keep existing)
    static_token: str | None = None

    # api_key — overwrite api key value (leave None to keep existing)
    api_key_value: str | None = None


# ---------- Test ----------


class CredentialTestResult(BaseModel):
    success: bool
    message: str
    latency_ms: int | None = None
