import os
import time
from typing import Any

import httpx


class HTTPExecutor:
    """HTTP 类型 Node 执行器"""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    async def execute(
        self,
        runtime_config: dict[str, Any],
        input_data: dict[str, Any],
    ) -> tuple[dict[str, Any], int]:
        endpoint: str = runtime_config["endpoint"]
        method: str = runtime_config.get("method", "POST").upper()
        headers: dict[str, str] = dict(runtime_config.get("headers") or {})
        auth: dict[str, Any] | None = runtime_config.get("auth")

        if auth:
            headers = self._apply_auth(headers, auth)

        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method == "GET":
                    response = await client.get(endpoint, params=input_data, headers=headers)
                else:
                    response = await client.request(
                        method, endpoint, json=input_data, headers=headers
                    )
                response.raise_for_status()
                latency_ms = int((time.monotonic() - start) * 1000)
                return response.json(), latency_ms

        except httpx.TimeoutException as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            raise TimeoutError(
                f"Node invocation timed out after {self.timeout}s"
            ) from exc
        except httpx.HTTPStatusError as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            raise RuntimeError(
                f"Node returned HTTP {exc.response.status_code}: {exc.response.text}"
            ) from exc

    def _apply_auth(self, headers: dict[str, str], auth: dict[str, Any]) -> dict[str, str]:
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
