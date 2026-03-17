from typing import Any

import httpx

from .exceptions import AuthError, NodeNotFoundError, NodeVaultError
from .models import InvokeResponse, NodeResponse


class AsyncNodeVaultClient:
    """NodeVault Python SDK 异步客户端（适用于 FastAPI / asyncio 环境）"""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._headers = {"Authorization": f"Bearer {api_key}"}

    async def invoke(
        self,
        node_name: str,
        input_data: dict[str, Any],
        version: str | None = None,
    ) -> InvokeResponse:
        """异步调用 Node"""
        async with httpx.AsyncClient(headers=self._headers, timeout=self.timeout) as client:
            node = await self._get_node(client, node_name)
            payload: dict[str, Any] = {"input": input_data}
            if version:
                payload["version"] = version
            resp = await client.post(
                f"{self.base_url}/api/v1/nodes/{node.id}/invoke",
                json=payload,
            )
            self._raise_for_status(resp)
            return InvokeResponse(**resp.json())

    async def _get_node(self, client: httpx.AsyncClient, name: str) -> NodeResponse:
        resp = await client.get(f"{self.base_url}/api/v1/nodes", params={"name": name})
        resp.raise_for_status()
        nodes = resp.json()
        if not nodes:
            raise NodeNotFoundError(f"Node '{name}' not found")
        return NodeResponse(**nodes[0])

    def _raise_for_status(self, resp: httpx.Response) -> None:
        if resp.status_code == 401:
            raise AuthError("Unauthorized")
        if resp.status_code == 404:
            raise NodeNotFoundError(resp.json().get("detail", "Not found"))
        if resp.status_code >= 400:
            raise NodeVaultError(f"API Error {resp.status_code}: {resp.text}")
