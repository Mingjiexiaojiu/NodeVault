import re
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.schemas.enums import (
    HttpMethod,
    NodeStatus,
    NodeType,
    NodeVisibility,
    RuntimeType,
)

NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


class RuntimeAuthConfig(BaseModel):
    type: str = "none"  # none | bearer | api_key | basic
    token_env: str | None = None


class RuntimeConfig(BaseModel):
    type: RuntimeType
    endpoint: str | None = None
    method: HttpMethod | None = None
    headers: dict[str, str] | None = None
    auth: RuntimeAuthConfig | None = None


class RetryConfig(BaseModel):
    max_attempts: int = 3
    backoff: str = "exponential"  # fixed | exponential
    initial_delay: str = "1s"


class RateLimitConfig(BaseModel):
    max_calls_per_minute: int = 100


class NodeDependency(BaseModel):
    name: str
    version: str = ">=0.0.0"


class NodeSchemaBase(BaseModel):
    # Basic info
    name: str = Field(..., min_length=3, max_length=64)
    version: str
    display_name: str | None = None
    description: str | None = None

    # Classification
    type: NodeType
    tags: list[str] = Field(default_factory=list)
    category: str | None = None
    keywords: list[str] = Field(default_factory=list)

    # Ownership
    author: str | None = None
    team: str | None = None
    email: str | None = None
    namespace: str | None = None

    # Input/Output contract
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]

    # Runtime
    runtime: RuntimeConfig

    # Execution policy
    timeout: str | None = "30s"
    retry: RetryConfig | None = None
    rate_limit: RateLimitConfig | None = None

    # Dependencies
    dependencies: list[NodeDependency] = Field(default_factory=list)

    # Metadata
    status: NodeStatus = NodeStatus.DRAFT
    visibility: NodeVisibility = NodeVisibility.INTERNAL
    license: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not NAME_PATTERN.match(v):
            raise ValueError(
                "name must be snake_case: lowercase letters, digits and underscores, "
                "starting with a letter, 3-64 characters"
            )
        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        if not SEMVER_PATTERN.match(v):
            raise ValueError(
                "version must follow SemVer format: MAJOR.MINOR.PATCH (e.g. 1.0.0)"
            )
        return v

    @field_validator("input_schema", "output_schema")
    @classmethod
    def validate_json_schema(cls, v: dict[str, Any]) -> dict[str, Any]:
        if v.get("type") != "object":
            raise ValueError("schema type must be 'object'")
        return v

    @model_validator(mode="after")
    def validate_runtime_config(self) -> "NodeSchemaBase":
        if self.runtime.type == RuntimeType.HTTP:
            if not self.runtime.endpoint:
                raise ValueError(
                    "runtime.endpoint is required when runtime.type is 'http'"
                )
            if not self.runtime.method:
                raise ValueError(
                    "runtime.method is required when runtime.type is 'http'"
                )
        return self
