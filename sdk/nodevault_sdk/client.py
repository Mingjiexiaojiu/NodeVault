import inspect
import typing
from typing import Any, Callable

import httpx

from .exceptions import AuthError, NodeNotFoundError, NodeVaultError
from .models import InvokeResponse, NodeResponse


class NodeVaultClient:
    """NodeVault Python SDK 同步客户端"""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        email: str | None = None,
        password: str | None = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._token: str | None = None

        if api_key:
            self._token = api_key
        elif email and password:
            self._login(email, password)

    def _login(self, email: str, password: str) -> None:
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"email": email, "password": password},
            )
            if resp.status_code == 401:
                raise AuthError("Invalid credentials")
            resp.raise_for_status()
            self._token = resp.json()["access_token"]

    @property
    def _headers(self) -> dict[str, str]:
        if not self._token:
            raise AuthError("Not authenticated. Provide api_key or email/password.")
        return {"Authorization": f"Bearer {self._token}"}

    # ===== Node 管理 =====

    def register(
        self,
        name: str,
        type: str,
        input_schema: dict,
        output_schema: dict,
        endpoint: str,
        description: str = "",
        tags: list[str] | None = None,
        version: str = "1.0.0",
        **kwargs: Any,
    ) -> NodeResponse:
        """注册一个新 Node"""
        payload = {
            "name": name,
            "type": type,
            "description": description,
            "tags": tags or [],
            "version": version,
            "input_schema": input_schema,
            "output_schema": output_schema,
            "runtime": {"type": "http", "endpoint": endpoint},
            **kwargs,
        }
        with httpx.Client(headers=self._headers, timeout=self.timeout) as client:
            resp = client.post(f"{self.base_url}/api/v1/nodes", json=payload)
            self._raise_for_status(resp)
            return NodeResponse(**resp.json())

    def get(self, node_name: str) -> NodeResponse:
        """通过名称获取 Node"""
        with httpx.Client(headers=self._headers, timeout=self.timeout) as client:
            resp = client.get(f"{self.base_url}/api/v1/nodes", params={"name": node_name})
            resp.raise_for_status()
            nodes = resp.json()
            if not nodes:
                raise NodeNotFoundError(f"Node '{node_name}' not found")
            return NodeResponse(**nodes[0])

    def search(self, query: str, **filters: Any) -> list[NodeResponse]:
        """搜索 Node"""
        params = {"q": query, **filters}
        with httpx.Client(headers=self._headers, timeout=self.timeout) as client:
            resp = client.get(f"{self.base_url}/api/v1/search/nodes", params=params)
            resp.raise_for_status()
            return [NodeResponse(**n) for n in resp.json().get("results", [])]

    def list_nodes(self, **filters: Any) -> list[NodeResponse]:
        """列出 Node"""
        with httpx.Client(headers=self._headers, timeout=self.timeout) as client:
            resp = client.get(f"{self.base_url}/api/v1/nodes", params=filters)
            resp.raise_for_status()
            return [NodeResponse(**n) for n in resp.json()]

    def invoke(
        self,
        node_name: str,
        input_data: dict[str, Any],
        version: str | None = None,
    ) -> InvokeResponse:
        """调用 Node"""
        node = self.get(node_name)
        payload: dict[str, Any] = {"input": input_data}
        if version:
            payload["version"] = version

        with httpx.Client(headers=self._headers, timeout=self.timeout) as client:
            resp = client.post(
                f"{self.base_url}/api/v1/nodes/{node.id}/invoke",
                json=payload,
            )
            self._raise_for_status(resp)
            return InvokeResponse(**resp.json())

    # ===== 装饰器支持 =====

    def node(
        self,
        name: str,
        type: str,
        description: str = "",
        tags: list[str] | None = None,
        endpoint: str | None = None,
        auto_register: bool = True,
    ) -> Callable:
        """
        @vault.node 装饰器：从函数类型注解自动生成 schema 并注册 Node。

        用法::

            @vault.node(
                name="my_analysis",
                type="analysis",
                description="分析数据",
                endpoint="http://my-service/api/analyze"
            )
            def my_analysis(data: list) -> dict:
                pass
        """

        def decorator(func: Callable) -> Callable:
            if auto_register:
                hints = typing.get_type_hints(func)
                sig = inspect.signature(func)
                input_schema = self._schema_from_hints(
                    {k: v for k, v in hints.items() if k != "return"}, sig
                )
                output_type = hints.get("return", dict)
                output_schema = self._type_to_schema(output_type)

                try:
                    self.register(
                        name=name,
                        type=type,
                        description=description,
                        tags=tags or [],
                        input_schema=input_schema,
                        output_schema=output_schema,
                        endpoint=endpoint or f"__local__/{name}",
                    )
                except NodeVaultError:
                    pass  # Already exists — skip silently

            func._nodevault_name = name  # type: ignore[attr-defined]
            func._nodevault_registered = True  # type: ignore[attr-defined]
            return func

        return decorator

    def _schema_from_hints(self, hints: dict, sig: inspect.Signature) -> dict:
        properties: dict[str, dict] = {}
        required: list[str] = []
        for param_name, hint in hints.items():
            properties[param_name] = self._type_to_schema(hint)
            param = sig.parameters.get(param_name)
            if param and param.default is inspect.Parameter.empty:
                required.append(param_name)
        return {"type": "object", "properties": properties, "required": required}

    def _type_to_schema(self, python_type: Any) -> dict:
        type_map: dict[Any, dict] = {
            int: {"type": "integer"},
            float: {"type": "number"},
            str: {"type": "string"},
            bool: {"type": "boolean"},
            list: {"type": "array"},
            dict: {"type": "object"},
        }
        return type_map.get(python_type, {"type": "object"})

    def _raise_for_status(self, resp: httpx.Response) -> None:
        if resp.status_code == 401:
            raise AuthError("Unauthorized")
        if resp.status_code == 404:
            detail = resp.json().get("detail", "Not found")
            raise NodeNotFoundError(detail)
        if resp.status_code >= 400:
            raise NodeVaultError(f"API Error {resp.status_code}: {resp.text}")
