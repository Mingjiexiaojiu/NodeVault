from datetime import datetime
from typing import Literal
import uuid

from pydantic import BaseModel, field_validator


ProviderType = Literal["openai", "claude", "custom"]


class AIConfigTest(BaseModel):
    provider: ProviderType
    model: str
    api_key: str
    base_url: str | None = None


class AIConfigTestResult(BaseModel):
    ok: bool
    message: str | None = None
    latency_ms: int | None = None


class AIConfigCreate(BaseModel):
    name: str
    provider: ProviderType = "openai"
    model: str
    api_key: str
    base_url: str | None = None
    is_default: bool = False

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("配置名称不能为空")
        return v.strip()

    @field_validator("model")
    @classmethod
    def model_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("模型名称不能为空")
        return v.strip()


class AIConfigUpdate(BaseModel):
    name: str | None = None
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    is_default: bool | None = None


class AIConfigResponse(BaseModel):
    id: uuid.UUID
    name: str
    provider: str
    model: str
    # API Key 脱敏：前4位 + **** + 后4位，不返回明文
    api_key_masked: str
    base_url: str | None
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
