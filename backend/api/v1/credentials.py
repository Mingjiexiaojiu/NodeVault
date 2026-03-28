"""Credential management API endpoints."""

from __future__ import annotations

import json
import time
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user
from backend.core.credential_vault import decrypt_value, encrypt_value
from backend.database.session import get_db
from backend.models.credential import CredentialTokenCache, ServiceCredential
from backend.models.node import NodeVersion
from backend.models.user import User
from backend.schemas.credential import (
    CredentialCreate,
    CredentialDetail,
    CredentialResponse,
    CredentialTestResult,
    CredentialUpdate,
)

router = APIRouter(prefix="/credentials", tags=["credentials"])


@router.post("", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(
    body: CredentialCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an encrypted credential for a target service."""
    cred = ServiceCredential(
        owner_id=user.id,
        name=body.name,
        base_url=body.base_url.rstrip("/"),
        auth_type=body.auth_type.value,
        login_endpoint=body.login_endpoint,
        login_method=body.login_method,
        login_body_template=body.login_body_template,
        token_json_path=body.token_json_path,
        token_ttl=body.token_ttl,
        api_key_header=body.api_key_header,
    )

    if body.auth_type.value == "bearer_login":
        if not body.username or not body.password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="username and password required for bearer_login",
            )
        secret = json.dumps({"username": body.username, "password": body.password})
        ct, nonce = encrypt_value(secret)
        cred.credential_encrypted = ct
        cred.credential_nonce = nonce

    elif body.auth_type.value == "bearer_static":
        if not body.static_token:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="static_token required for bearer_static",
            )
        ct, nonce = encrypt_value(body.static_token)
        cred.static_token_encrypted = ct
        cred.static_token_nonce = nonce

    elif body.auth_type.value == "api_key":
        if not body.api_key_value:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="api_key_value required for api_key",
            )
        ct, nonce = encrypt_value(body.api_key_value)
        cred.api_key_encrypted = ct
        cred.api_key_nonce = nonce

    elif body.auth_type.value == "basic":
        if not body.username or not body.password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="username and password required for basic",
            )
        secret = json.dumps({"username": body.username, "password": body.password})
        ct, nonce = encrypt_value(secret)
        cred.credential_encrypted = ct
        cred.credential_nonce = nonce

    db.add(cred)
    await db.commit()
    await db.refresh(cred)
    return cred


@router.get("", response_model=list[CredentialResponse])
async def list_credentials(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all credentials owned by the current user (secrets hidden)."""
    result = await db.execute(
        select(ServiceCredential)
        .where(ServiceCredential.owner_id == user.id)
        .order_by(ServiceCredential.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{credential_id}", response_model=CredentialDetail)
async def get_credential(
    credential_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single credential's metadata (secrets hidden)."""
    cred = await db.get(ServiceCredential, credential_id)
    if not cred or cred.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")
    return cred


@router.patch("/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    credential_id: uuid.UUID,
    body: CredentialUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update credential metadata and/or rotate secret values.

    auth_type and base_url cannot be changed — delete and recreate to change those.
    Leaving a secret field as None keeps the existing encrypted value.
    If any secret is rotated, the token cache is cleared.
    """
    cred = await db.get(ServiceCredential, credential_id)
    if not cred or cred.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")

    secret_rotated = False

    if body.name is not None:
        cred.name = body.name
    if body.token_ttl is not None:
        cred.token_ttl = body.token_ttl

    # Rotate password (bearer_login / basic)
    if body.password is not None:
        if cred.auth_type in ("bearer_login", "basic"):
            existing_json = decrypt_value(cred.credential_encrypted, cred.credential_nonce)
            existing = json.loads(existing_json)
            existing["password"] = body.password
            ct, nonce = encrypt_value(json.dumps(existing))
            cred.credential_encrypted = ct
            cred.credential_nonce = nonce
            secret_rotated = True

    # Rotate static token (bearer_static)
    if body.static_token is not None:
        if cred.auth_type == "bearer_static":
            ct, nonce = encrypt_value(body.static_token)
            cred.static_token_encrypted = ct
            cred.static_token_nonce = nonce
            secret_rotated = True

    # Rotate API key (api_key)
    if body.api_key_value is not None:
        if cred.auth_type == "api_key":
            ct, nonce = encrypt_value(body.api_key_value)
            cred.api_key_encrypted = ct
            cred.api_key_nonce = nonce
            secret_rotated = True

    if secret_rotated:
        await db.execute(
            delete(CredentialTokenCache).where(
                CredentialTokenCache.credential_id == credential_id
            )
        )

    await db.commit()
    await db.refresh(cred)
    return cred


@router.post("/{credential_id}/test", response_model=CredentialTestResult)
async def test_credential(
    credential_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Test whether a credential can successfully authenticate against the target service.

    Does NOT update the token cache — purely a validation check.
    Always returns HTTP 200; check the `success` field for the result.
    """
    cred = await db.get(ServiceCredential, credential_id)
    if not cred or cred.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")

    start = time.monotonic()

    try:
        if cred.auth_type == "bearer_login":
            cred_json = decrypt_value(cred.credential_encrypted, cred.credential_nonce)
            cred_data = json.loads(cred_json)
            body_template = cred.login_body_template or "{}"
            login_body = json.loads(body_template)
            for key, val in login_body.items():
                if isinstance(val, str) and val.startswith("{{") and val.endswith("}}"):
                    placeholder = val[2:-2].strip()
                    if placeholder in cred_data:
                        login_body[key] = cred_data[placeholder]

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.request(
                    (cred.login_method or "POST").upper(),
                    cred.login_endpoint,
                    json=login_body,
                )

            latency_ms = int((time.monotonic() - start) * 1000)
            if resp.status_code == 401:
                return CredentialTestResult(success=False, message="鉴权失败：服务返回 401", latency_ms=latency_ms)
            if resp.status_code >= 400:
                return CredentialTestResult(
                    success=False,
                    message=f"请求失败：服务返回 {resp.status_code}",
                    latency_ms=latency_ms,
                )
            return CredentialTestResult(success=True, message="连接成功", latency_ms=latency_ms)

        elif cred.auth_type == "bearer_static":
            token = decrypt_value(cred.static_token_encrypted, cred.static_token_nonce)
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    cred.base_url,
                    headers={"Authorization": f"Bearer {token}"},
                )
            latency_ms = int((time.monotonic() - start) * 1000)
            if resp.status_code == 401:
                return CredentialTestResult(success=False, message="Token 无效：服务返回 401", latency_ms=latency_ms)
            return CredentialTestResult(success=True, message="连接成功（Token 有效）", latency_ms=latency_ms)

        elif cred.auth_type == "api_key":
            api_key = decrypt_value(cred.api_key_encrypted, cred.api_key_nonce)
            header_name = cred.api_key_header or "X-API-Key"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    cred.base_url,
                    headers={header_name: api_key},
                )
            latency_ms = int((time.monotonic() - start) * 1000)
            if resp.status_code == 401:
                return CredentialTestResult(success=False, message="API Key 无效：服务返回 401", latency_ms=latency_ms)
            return CredentialTestResult(success=True, message="连接成功（API Key 有效）", latency_ms=latency_ms)

        elif cred.auth_type == "basic":
            import base64
            cred_json = decrypt_value(cred.credential_encrypted, cred.credential_nonce)
            cred_data = json.loads(cred_json)
            b64 = base64.b64encode(
                f"{cred_data['username']}:{cred_data['password']}".encode()
            ).decode()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    cred.base_url,
                    headers={"Authorization": f"Basic {b64}"},
                )
            latency_ms = int((time.monotonic() - start) * 1000)
            if resp.status_code == 401:
                return CredentialTestResult(success=False, message="Basic 认证失败：服务返回 401", latency_ms=latency_ms)
            return CredentialTestResult(success=True, message="连接成功", latency_ms=latency_ms)

        else:
            return CredentialTestResult(success=False, message=f"不支持的 auth_type: {cred.auth_type}")

    except httpx.TimeoutException:
        latency_ms = int((time.monotonic() - start) * 1000)
        return CredentialTestResult(
            success=False,
            message=f"连接超时：{cred.base_url}",
            latency_ms=latency_ms,
        )
    except Exception as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        return CredentialTestResult(
            success=False,
            message=f"连接失败：{exc}",
            latency_ms=latency_ms,
        )


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    credential_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a credential. Nodes referencing it via credential_id in runtime_config will have it cleared."""
    cred = await db.get(ServiceCredential, credential_id)
    if not cred or cred.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")

    # Clear credential_id from all NodeVersions' runtime_config that reference this credential
    versions_result = await db.execute(select(NodeVersion))
    for version in versions_result.scalars():
        rc = version.runtime_config or {}
        if rc.get("credential_id") == str(credential_id):
            rc.pop("credential_id", None)
            version.runtime_config = rc

    # Explicitly delete token cache (cascade also handles this, belt-and-suspenders)
    await db.execute(
        delete(CredentialTokenCache).where(
            CredentialTokenCache.credential_id == credential_id
        )
    )

    await db.delete(cred)
    await db.commit()
