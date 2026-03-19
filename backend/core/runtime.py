import json
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.credential_vault import decrypt_value
from backend.models.credential import CredentialTokenCache, ServiceCredential

# Safety margin: refresh token 60s before expiry
_TOKEN_EXPIRY_MARGIN = timedelta(seconds=60)


class HTTPExecutor:
    """HTTP 类型 Node 执行器"""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    async def execute(
        self,
        runtime_config: dict[str, Any],
        input_data: dict[str, Any],
        db: AsyncSession | None = None,
    ) -> tuple[dict[str, Any], int]:
        endpoint: str = runtime_config["endpoint"]
        method: str = runtime_config.get("method", "POST").upper()
        headers: dict[str, str] = dict(runtime_config.get("headers") or {})

        credential_id = runtime_config.get("credential_id")
        credential: ServiceCredential | None = None

        if credential_id and db:
            credential = await self._get_credential(db, uuid.UUID(credential_id))
            if credential:
                headers = await self._apply_credential_auth(
                    headers, credential, db
                )
        else:
            # Legacy auth path
            auth: dict[str, Any] | None = runtime_config.get("auth")
            if auth:
                headers = self._apply_legacy_auth(headers, auth)

        start = time.monotonic()
        result, latency_ms = await self._do_request(
            method, endpoint, input_data, headers
        )

        # 401 retry: force-refresh token once and retry
        if result is None and credential and db:
            headers = dict(runtime_config.get("headers") or {})
            headers = await self._apply_credential_auth(
                headers, credential, db, force_refresh=True
            )
            result, latency_ms = await self._do_request(
                method, endpoint, input_data, headers
            )

        if result is None:
            raise RuntimeError("Request failed after retry")

        return result, latency_ms

    async def _do_request(
        self,
        method: str,
        endpoint: str,
        input_data: dict[str, Any],
        headers: dict[str, str],
    ) -> tuple[dict[str, Any] | None, int]:
        """Execute a single HTTP request. Returns (None, latency) on 401."""
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method == "GET":
                    response = await client.get(
                        endpoint, params=input_data, headers=headers
                    )
                else:
                    response = await client.request(
                        method, endpoint, json=input_data, headers=headers
                    )

                latency_ms = int((time.monotonic() - start) * 1000)

                if response.status_code == 401:
                    return None, latency_ms

                response.raise_for_status()
                return response.json(), latency_ms

        except httpx.TimeoutException as exc:
            raise TimeoutError(
                f"Node invocation timed out after {self.timeout}s"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Node returned HTTP {exc.response.status_code}: {exc.response.text}"
            ) from exc

    # ---- Credential-based auth ----

    async def _get_credential(
        self, db: AsyncSession, credential_id: uuid.UUID
    ) -> ServiceCredential | None:
        result = await db.execute(
            select(ServiceCredential).where(ServiceCredential.id == credential_id)
        )
        return result.scalar_one_or_none()

    async def _apply_credential_auth(
        self,
        headers: dict[str, str],
        credential: ServiceCredential,
        db: AsyncSession,
        force_refresh: bool = False,
    ) -> dict[str, str]:
        headers = headers.copy()
        auth_type = credential.auth_type

        if auth_type == "bearer_login":
            token = await self._get_bearer_login_token(
                credential, db, force_refresh=force_refresh
            )
            headers["Authorization"] = f"Bearer {token}"

        elif auth_type == "bearer_static":
            token = decrypt_value(
                credential.static_token_encrypted, credential.static_token_nonce
            )
            headers["Authorization"] = f"Bearer {token}"

        elif auth_type == "api_key":
            api_key = decrypt_value(
                credential.api_key_encrypted, credential.api_key_nonce
            )
            header_name = credential.api_key_header or "X-API-Key"
            headers[header_name] = api_key

        elif auth_type == "basic":
            cred_json = decrypt_value(
                credential.credential_encrypted, credential.credential_nonce
            )
            cred_data = json.loads(cred_json)
            import base64

            b64 = base64.b64encode(
                f"{cred_data['username']}:{cred_data['password']}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {b64}"

        return headers

    async def _get_bearer_login_token(
        self,
        credential: ServiceCredential,
        db: AsyncSession,
        force_refresh: bool = False,
    ) -> str:
        if not force_refresh:
            # Try cached token
            result = await db.execute(
                select(CredentialTokenCache).where(
                    CredentialTokenCache.credential_id == credential.id
                )
            )
            cache = result.scalar_one_or_none()
            if cache and cache.expires_at:
                if datetime.utcnow() + _TOKEN_EXPIRY_MARGIN < cache.expires_at:
                    return cache.access_token
            elif cache:
                # No expiry set — use cached token
                return cache.access_token

        # Refresh: decrypt login body template, perform login
        cred_json = decrypt_value(
            credential.credential_encrypted, credential.credential_nonce
        )
        cred_data = json.loads(cred_json)

        body_template = credential.login_body_template or "{}"
        login_body = json.loads(body_template)
        # Substitute placeholders
        for key, val in login_body.items():
            if isinstance(val, str) and val.startswith("{{") and val.endswith("}}"):
                placeholder = val[2:-2].strip()
                if placeholder in cred_data:
                    login_body[key] = cred_data[placeholder]

        login_method = (credential.login_method or "POST").upper()
        login_url = credential.login_endpoint

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.request(login_method, login_url, json=login_body)
            resp.raise_for_status()
            resp_data = resp.json()

        # Extract token
        token = self._extract_token(resp_data, credential.token_json_path)
        if not token:
            raise RuntimeError("Failed to extract token from login response")

        # Upsert cache
        expires_at = None
        if credential.token_ttl:
            expires_at = datetime.utcnow() + timedelta(seconds=credential.token_ttl)

        result = await db.execute(
            select(CredentialTokenCache).where(
                CredentialTokenCache.credential_id == credential.id
            )
        )
        cache = result.scalar_one_or_none()
        if cache:
            cache.access_token = token
            cache.expires_at = expires_at
            cache.created_at = datetime.utcnow()
        else:
            db.add(
                CredentialTokenCache(
                    credential_id=credential.id,
                    access_token=token,
                    expires_at=expires_at,
                )
            )
        await db.flush()

        return token

    @staticmethod
    def _extract_token(data: Any, json_path: str | None = None) -> str | None:
        """Extract a token from login response data."""
        if json_path:
            parts = json_path.strip(".").split(".")
            current = data
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
            if isinstance(current, str):
                return current
            return None

        # Fallback: search common keys
        if isinstance(data, dict):
            for key in ("access_token", "token", "jwt", "accessToken"):
                if key in data and isinstance(data[key], str):
                    return data[key]
            # Nested search: look for "data" wrapper
            if "data" in data and isinstance(data["data"], dict):
                return HTTPExecutor._extract_token(data["data"])
        return None

    # ---- Legacy auth (backward compatible) ----

    def _apply_legacy_auth(
        self, headers: dict[str, str], auth: dict[str, Any]
    ) -> dict[str, str]:
        headers = headers.copy()
        auth_type = auth.get("type", "none")
        if auth_type == "bearer":
            token = os.environ.get(auth.get("token_env", ""), auth.get("token", ""))
            headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "api_key":
            key = os.environ.get(auth.get("key_env", ""), auth.get("key", ""))
            headers[auth.get("header", "X-API-Key")] = key
        return headers


class RuntimeDispatcher:
    _executors: dict[str, type] = {
        "http": HTTPExecutor,
    }

    @classmethod
    def get_executor(cls, runtime_type: str) -> HTTPExecutor:
        executor_class = cls._executors.get(runtime_type)
        if not executor_class:
            raise ValueError(
                f"Unsupported runtime type: {runtime_type!r}. "
                f"Supported: {list(cls._executors.keys())}"
            )
        return executor_class()
