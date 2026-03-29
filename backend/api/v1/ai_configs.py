"""用户 AI 配置管理 API。

支持用户配置多个 AI 提供商（openai / claude / custom），
在生成 SKILL.md 时按需选用。
"""
import time
import uuid

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user
from backend.core.credential_vault import decrypt_value, encrypt_value
from backend.database.session import get_db
from backend.models.ai_config import UserAIConfig
from backend.models.user import User
from backend.schemas.ai_config import (
    AIConfigCreate,
    AIConfigResponse,
    AIConfigTest,
    AIConfigTestResult,
    AIConfigUpdate,
)
from backend.schemas.response import ApiResponse

logger = structlog.get_logger()
router = APIRouter(prefix="/ai-configs", tags=["AI Config"])


def _to_response(cfg: UserAIConfig) -> AIConfigResponse:
    try:
        plaintext = decrypt_value(bytes(cfg.api_key_encrypted), bytes(cfg.api_key_nonce))
    except Exception:
        plaintext = ""
    if len(plaintext) >= 8:
        masked = plaintext[:4] + "****" + plaintext[-4:]
    elif plaintext:
        masked = plaintext[:2] + "****"
    else:
        masked = "****"
    return AIConfigResponse(
        id=cfg.id,
        name=cfg.name,
        provider=cfg.provider,
        model=cfg.model,
        api_key_masked=masked,
        base_url=cfg.base_url,
        is_default=cfg.is_default,
        created_at=cfg.created_at,
        updated_at=cfg.updated_at,
    )


@router.get("", response_model=ApiResponse)
async def list_ai_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    result = await db.execute(
        select(UserAIConfig)
        .where(UserAIConfig.user_id == current_user.id)
        .order_by(UserAIConfig.is_default.desc(), UserAIConfig.created_at.asc())
    )
    configs = list(result.scalars().all())
    return ApiResponse(data=[_to_response(c) for c in configs])


@router.post("/test", response_model=ApiResponse)
async def test_ai_config(
    payload: AIConfigTest,
    _current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """用提供的凭据向 AI 提供商发送一次最小请求，验证连通性。"""
    start = time.monotonic()

    async def _elapsed() -> int:
        return int((time.monotonic() - start) * 1000)

    try:
        if payload.provider in ("openai", "custom"):
            base_url = (payload.base_url or "https://api.openai.com/v1").rstrip("/")
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {payload.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": payload.model,
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 1,
                    },
                )
        elif payload.provider == "claude":
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": payload.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": payload.model,
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 1,
                    },
                )
        else:
            return ApiResponse(data=AIConfigTestResult(ok=False, message="不支持的提供商类型").model_dump())

        latency_ms = await _elapsed()
        if resp.status_code == 200:
            return ApiResponse(data=AIConfigTestResult(ok=True, latency_ms=latency_ms).model_dump())

        # 提取错误信息
        try:
            body = resp.json()
            msg = (
                body.get("error", {}).get("message")
                or body.get("message")
                or f"HTTP {resp.status_code}"
            )
        except Exception:
            msg = f"HTTP {resp.status_code}"
        return ApiResponse(data=AIConfigTestResult(ok=False, message=msg, latency_ms=latency_ms).model_dump())

    except httpx.TimeoutException:
        return ApiResponse(data=AIConfigTestResult(
            ok=False, message="连接超时，请检查 Base URL 是否可达", latency_ms=await _elapsed()
        ).model_dump())
    except httpx.ConnectError:
        return ApiResponse(data=AIConfigTestResult(
            ok=False, message="无法连接到服务器，请检查 Base URL", latency_ms=await _elapsed()
        ).model_dump())
    except Exception as exc:
        logger.warning("ai_config_test_error", error=str(exc))
        return ApiResponse(data=AIConfigTestResult(
            ok=False, message=str(exc), latency_ms=await _elapsed()
        ).model_dump())


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_config(
    payload: AIConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    # 如果新建时设为默认，先取消其他默认
    if payload.is_default:
        await db.execute(
            update(UserAIConfig)
            .where(UserAIConfig.user_id == current_user.id)
            .values(is_default=False)
        )

    ciphertext, nonce = encrypt_value(payload.api_key)
    cfg = UserAIConfig(
        user_id=current_user.id,
        name=payload.name,
        provider=payload.provider,
        model=payload.model,
        api_key_encrypted=ciphertext,
        api_key_nonce=nonce,
        base_url=payload.base_url,
        is_default=payload.is_default,
    )
    db.add(cfg)
    await db.commit()
    await db.refresh(cfg)
    return ApiResponse(data=_to_response(cfg))


@router.patch("/{config_id}", response_model=ApiResponse)
async def update_ai_config(
    config_id: uuid.UUID,
    payload: AIConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    result = await db.execute(
        select(UserAIConfig).where(
            UserAIConfig.id == config_id,
            UserAIConfig.user_id == current_user.id,
        )
    )
    cfg = result.scalar_one_or_none()
    if cfg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="配置不存在")

    if payload.name is not None:
        cfg.name = payload.name
    if payload.model is not None:
        cfg.model = payload.model
    if payload.api_key is not None:
        ciphertext, nonce = encrypt_value(payload.api_key)
        cfg.api_key_encrypted = ciphertext
        cfg.api_key_nonce = nonce
    if payload.base_url is not None:
        cfg.base_url = payload.base_url
    if payload.is_default is not None:
        if payload.is_default:
            await db.execute(
                update(UserAIConfig)
                .where(UserAIConfig.user_id == current_user.id)
                .values(is_default=False)
            )
        cfg.is_default = payload.is_default

    await db.commit()
    await db.refresh(cfg)
    return ApiResponse(data=_to_response(cfg))


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_config(
    config_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    result = await db.execute(
        select(UserAIConfig).where(
            UserAIConfig.id == config_id,
            UserAIConfig.user_id == current_user.id,
        )
    )
    cfg = result.scalar_one_or_none()
    if cfg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="配置不存在")
    await db.delete(cfg)
    await db.commit()
