"""Credential management API endpoints."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user
from backend.core.credential_vault import encrypt_value
from backend.database.session import get_db
from backend.models.credential import CredentialTokenCache, ServiceCredential
from backend.models.node import NodeVersion
from backend.models.user import User
from backend.schemas.credential import (
    CredentialCreate,
    CredentialDetail,
    CredentialResponse,
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

    # Encrypt secrets based on auth_type
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

    # Delete token cache
    await db.execute(
        select(CredentialTokenCache).where(
            CredentialTokenCache.credential_id == credential_id
        )
    )

    await db.delete(cred)
    await db.commit()
