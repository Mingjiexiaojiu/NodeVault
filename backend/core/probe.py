"""OpenAPI spec probe engine — discover service specs by trying known paths."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
import yaml

from backend.core.url_validator import SSRFError, validate_url

# Built-in probe paths, ordered by popularity
DEFAULT_PROBE_PATHS = [
    "/openapi.json",
    "/swagger.json",
    "/openapi.yaml",
    "/v3/api-docs",
    "/v2/api-docs",
    "/api/schema/",
    "/swagger/v1/swagger.json",
    "/swagger/doc.json",
    "/api-docs",
    "/docs/openapi.json",
]

_PER_PATH_TIMEOUT = 5.0  # seconds
_TOTAL_TIMEOUT = 30.0  # seconds
_USER_AGENT = "NodeVault/1.0 ServiceProbe"


@dataclass
class ProbeAttempt:
    path: str
    status: int | None = None
    success: bool = False
    error: str | None = None


@dataclass
class ProbeResult:
    base_url: str
    found: bool = False
    spec_url: str | None = None
    spec_dict: dict[str, Any] | None = None
    attempts: list[ProbeAttempt] = field(default_factory=list)
    needs_auth: bool = False
    error: str | None = None


def _is_valid_spec(data: dict[str, Any]) -> bool:
    """Check if data looks like a valid OpenAPI / Swagger spec."""
    return (
        isinstance(data, dict)
        and ("openapi" in data or "swagger" in data)
        and "paths" in data
    )


def _parse_spec(text: str) -> dict[str, Any] | None:
    """Try parsing text as JSON, then YAML. Return spec dict or None."""
    # Try JSON first (faster)
    import json

    try:
        data = json.loads(text)
        if _is_valid_spec(data):
            return data
    except (json.JSONDecodeError, ValueError):
        pass

    # Try YAML
    try:
        data = yaml.safe_load(text)
        if isinstance(data, dict) and _is_valid_spec(data):
            return data
    except yaml.YAMLError:
        pass

    return None


def _extract_token_from_response(resp_json: Any, token_json_path: str | None = None) -> str | None:
    """Extract token from a login response body.

    Strategy:
    1. If token_json_path provided, follow dot-separated path
    2. Search recursively for keys containing 'token'/'jwt'/'access' with 'eyJ' prefix
    """
    if not isinstance(resp_json, dict):
        return None

    # Strategy 1: explicit path
    if token_json_path:
        obj = resp_json
        for part in token_json_path.split("."):
            if isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                obj = None
                break
        if isinstance(obj, str) and obj:
            return obj

    # Strategy 2: recursive search
    candidates: list[str] = []

    def _search(d: Any) -> None:
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, str) and v.startswith("eyJ"):
                    candidates.append(v)
                elif isinstance(v, str) and any(
                    kw in k.lower() for kw in ("token", "jwt", "access")
                ):
                    candidates.append(v)
                else:
                    _search(v)
        elif isinstance(d, list):
            for item in d:
                _search(item)

    _search(resp_json)
    return candidates[0] if candidates else None


async def probe_spec(
    base_url: str,
    auth_token: str | None = None,
    probe_paths: list[str] | None = None,
) -> ProbeResult:
    """Probe *base_url* for an OpenAPI spec.

    Tries each path in order with SSRF validation. Returns on first success.
    """
    base_url = base_url.rstrip("/")
    paths = probe_paths or DEFAULT_PROBE_PATHS
    result = ProbeResult(base_url=base_url)

    # SSRF check on base URL
    try:
        validate_url(base_url)
    except SSRFError as e:
        result.error = str(e)
        return result

    headers: dict[str, str] = {"User-Agent": _USER_AGENT}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    deadline = time.monotonic() + _TOTAL_TIMEOUT
    all_401 = True

    async with httpx.AsyncClient(timeout=_PER_PATH_TIMEOUT) as client:
        for path in paths:
            if time.monotonic() > deadline:
                result.error = "Total probe timeout exceeded"
                break

            attempt = ProbeAttempt(path=path)
            url = f"{base_url}{path}"

            try:
                resp = await client.get(url, headers=headers, follow_redirects=True)
                attempt.status = resp.status_code

                if resp.status_code == 200:
                    all_401 = False
                    spec = _parse_spec(resp.text)
                    if spec:
                        attempt.success = True
                        result.found = True
                        result.spec_url = url
                        result.spec_dict = spec
                        result.attempts.append(attempt)
                        return result
                elif resp.status_code not in (401, 403):
                    all_401 = False

            except httpx.TimeoutException:
                attempt.error = "timeout"
            except httpx.RequestError as e:
                attempt.error = str(e)
                all_401 = False

            result.attempts.append(attempt)

    if all_401 and result.attempts:
        result.needs_auth = True

    return result


async def probe_with_auth(
    base_url: str,
    login_endpoint: str,
    login_method: str,
    login_body: dict[str, Any],
    token_json_path: str | None = None,
    probe_paths: list[str] | None = None,
) -> ProbeResult:
    """Probe after authenticating via a login endpoint.

    1. POST/GET login_endpoint with login_body → extract token
    2. Use token to probe spec paths
    """
    base_url = base_url.rstrip("/")

    # SSRF check
    try:
        validate_url(base_url)
    except SSRFError as e:
        return ProbeResult(base_url=base_url, error=str(e))

    headers = {"User-Agent": _USER_AGENT}
    login_url = f"{base_url}{login_endpoint}"

    async with httpx.AsyncClient(timeout=_PER_PATH_TIMEOUT) as client:
        try:
            if login_method.upper() == "GET":
                resp = await client.get(login_url, params=login_body, headers=headers)
            else:
                resp = await client.request(
                    login_method.upper(), login_url, json=login_body, headers=headers
                )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            return ProbeResult(
                base_url=base_url,
                error=f"Login failed: HTTP {e.response.status_code}",
            )
        except httpx.RequestError as e:
            return ProbeResult(base_url=base_url, error=f"Login request failed: {e}")

        try:
            body = resp.json()
        except Exception:
            return ProbeResult(base_url=base_url, error="Login response is not JSON")

        token = _extract_token_from_response(body, token_json_path)
        if not token:
            return ProbeResult(
                base_url=base_url,
                error="Could not extract token from login response",
            )

    return await probe_spec(base_url, auth_token=token, probe_paths=probe_paths)
