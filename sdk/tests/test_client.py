"""
SDK unit tests (task 8.8):
Test NodeVaultClient and AsyncNodeVaultClient with mocked HTTP calls.
Coverage target: ≥80%
"""
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import httpx
import pytest
import respx

from nodevault_sdk import AsyncNodeVaultClient, NodeVaultClient
from nodevault_sdk.exceptions import AuthError, NodeNotFoundError, NodeVaultError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE = "http://testvault"


def _node_json(name: str = "my_node") -> dict:
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "display_name": "My Node",
        "description": "test",
        "type": "tool",
        "category": "test",
        "status": "active",
        "visibility": "public",
        "namespace_id": str(uuid.uuid4()),
        "owner_id": str(uuid.uuid4()),
        "tags": [],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


def _invoke_json(name: str = "my_node") -> dict:
    return {
        "node_name": name,
        "version": "1.0.0",
        "output": {"result": 42},
        "latency_ms": 120,
        "invocation_id": str(uuid.uuid4()),
    }


# ---------------------------------------------------------------------------
# NodeVaultClient — authentication tests
# ---------------------------------------------------------------------------


@respx.mock
def test_login_success():
    """api_key 方式不进行 login 请求"""
    client = NodeVaultClient(base_url=_BASE, api_key="tok_test")
    assert client._token == "tok_test"


@respx.mock
def test_login_email_password_success():
    """email+password 方式应发送 login 请求获取 token"""
    respx.post(f"{_BASE}/api/v1/auth/login").mock(
        return_value=httpx.Response(200, json={"access_token": "tok_xyz"})
    )
    client = NodeVaultClient(base_url=_BASE, email="a@b.com", password="secret")
    assert client._token == "tok_xyz"


@respx.mock
def test_login_email_password_invalid_credentials():
    """登录失败（401）应抛出 AuthError"""
    respx.post(f"{_BASE}/api/v1/auth/login").mock(
        return_value=httpx.Response(401, json={"detail": "wrong"})
    )
    with pytest.raises(AuthError):
        NodeVaultClient(base_url=_BASE, email="a@b.com", password="bad")


def test_headers_require_auth():
    """未设置 token 时访问 _headers 应抛出 AuthError"""
    client = NodeVaultClient.__new__(NodeVaultClient)
    client.base_url = _BASE
    client.timeout = 30
    client._token = None
    with pytest.raises(AuthError):
        _ = client._headers


# ---------------------------------------------------------------------------
# NodeVaultClient — register / get / list
# ---------------------------------------------------------------------------


@respx.mock
def test_register_node():
    """register 应发 POST /api/v1/nodes 并返回 NodeResponse"""
    node_data = _node_json("new_tool")
    respx.post(f"{_BASE}/api/v1/nodes").mock(
        return_value=httpx.Response(201, json=node_data)
    )
    client = NodeVaultClient(base_url=_BASE, api_key="tok")
    result = client.register(
        name="new_tool",
        type="tool",
        input_schema={"type": "object", "properties": {}},
        output_schema={"type": "object", "properties": {}},
        endpoint="http://myservice/call",
        display_name="New Tool",
        category="test",
    )
    assert result.name == "new_tool"


@respx.mock
def test_register_node_conflict_raises_nodevaulterror():
    """注册冲突（409）应抛出 NodeVaultError"""
    respx.post(f"{_BASE}/api/v1/nodes").mock(
        return_value=httpx.Response(409, json={"detail": "already exists"})
    )
    client = NodeVaultClient(base_url=_BASE, api_key="tok")
    with pytest.raises(NodeVaultError):
        client.register(
            name="dup",
            type="tool",
            input_schema={},
            output_schema={},
            endpoint="http://x/y",
        )


@respx.mock
def test_get_node_found():
    """get 应通过名称查询并返回第一个节点"""
    respx.get(f"{_BASE}/api/v1/nodes").mock(
        return_value=httpx.Response(200, json=[_node_json("my_node")])
    )
    client = NodeVaultClient(base_url=_BASE, api_key="tok")
    node = client.get("my_node")
    assert node.name == "my_node"


@respx.mock
def test_get_node_not_found():
    """不存在的 Node 应抛出 NodeNotFoundError"""
    respx.get(f"{_BASE}/api/v1/nodes").mock(
        return_value=httpx.Response(200, json=[])
    )
    client = NodeVaultClient(base_url=_BASE, api_key="tok")
    with pytest.raises(NodeNotFoundError):
        client.get("ghost_node")


@respx.mock
def test_list_nodes():
    """list_nodes 应返回 NodeResponse 列表"""
    nodes = [_node_json("a"), _node_json("b")]
    respx.get(f"{_BASE}/api/v1/nodes").mock(
        return_value=httpx.Response(200, json=nodes)
    )
    client = NodeVaultClient(base_url=_BASE, api_key="tok")
    result = client.list_nodes()
    assert len(result) == 2
    assert result[0].name == "a"


# ---------------------------------------------------------------------------
# NodeVaultClient — search
# ---------------------------------------------------------------------------


@respx.mock
def test_search_nodes():
    """search 应调用 /api/v1/search/nodes 并返回结果列表"""
    results = [_node_json("found_node")]
    respx.get(f"{_BASE}/api/v1/search/nodes").mock(
        return_value=httpx.Response(200, json={"results": results, "total": 1})
    )
    client = NodeVaultClient(base_url=_BASE, api_key="tok")
    found = client.search("tool")
    assert len(found) == 1
    assert found[0].name == "found_node"


# ---------------------------------------------------------------------------
# NodeVaultClient — invoke
# ---------------------------------------------------------------------------


@respx.mock
def test_invoke_node_success():
    """invoke 应先 get 节点，再 POST /invoke，返回 InvokeResponse"""
    node_data = _node_json("calc_node")
    respx.get(f"{_BASE}/api/v1/nodes").mock(
        return_value=httpx.Response(200, json=[node_data])
    )
    respx.post(f"{_BASE}/api/v1/nodes/{node_data['id']}/invoke").mock(
        return_value=httpx.Response(200, json=_invoke_json("calc_node"))
    )
    client = NodeVaultClient(base_url=_BASE, api_key="tok")
    result = client.invoke("calc_node", input_data={"x": 1})
    assert result.node_name == "calc_node"
    assert result.output == {"result": 42}
    assert result.latency_ms == 120


@respx.mock
def test_invoke_node_not_found_raises():
    """节点不存在时 invoke 应抛出 NodeNotFoundError"""
    respx.get(f"{_BASE}/api/v1/nodes").mock(
        return_value=httpx.Response(200, json=[])
    )
    client = NodeVaultClient(base_url=_BASE, api_key="tok")
    with pytest.raises(NodeNotFoundError):
        client.invoke("missing_node", input_data={})


# ---------------------------------------------------------------------------
# NodeVaultClient — @node() decorator
# ---------------------------------------------------------------------------


@respx.mock
def test_node_decorator_registers_and_marks_function():
    """@vault.node 应自动注册并在函数上设置 _nodevault_name"""
    node_data = _node_json("my_func")
    respx.post(f"{_BASE}/api/v1/nodes").mock(
        return_value=httpx.Response(201, json=node_data)
    )
    vault = NodeVaultClient(base_url=_BASE, api_key="tok")

    @vault.node(name="my_func", type="tool", endpoint="http://svc/func")
    def my_func(text: str) -> dict:
        return {}

    assert my_func._nodevault_name == "my_func"
    assert my_func._nodevault_registered is True


@respx.mock
def test_node_decorator_silently_skips_conflict():
    """@vault.node 注册冲突时不抛出异常（幂等）"""
    respx.post(f"{_BASE}/api/v1/nodes").mock(
        return_value=httpx.Response(409, json={"detail": "already exists"})
    )
    vault = NodeVaultClient(base_url=_BASE, api_key="tok")

    @vault.node(name="dup_func", type="tool", endpoint="http://svc/func")
    def dup_func(x: int) -> dict:
        return {}

    assert dup_func._nodevault_name == "dup_func"


# ---------------------------------------------------------------------------
# _raise_for_status tests
# ---------------------------------------------------------------------------


def test_raise_for_status_unauthorized():
    client = NodeVaultClient(base_url=_BASE, api_key="tok")
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 401
    with pytest.raises(AuthError):
        client._raise_for_status(resp)


def test_raise_for_status_not_found():
    client = NodeVaultClient(base_url=_BASE, api_key="tok")
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 404
    resp.json.return_value = {"detail": "not found"}
    with pytest.raises(NodeNotFoundError):
        client._raise_for_status(resp)


def test_raise_for_status_generic_error():
    client = NodeVaultClient(base_url=_BASE, api_key="tok")
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 500
    resp.text = "internal error"
    with pytest.raises(NodeVaultError):
        client._raise_for_status(resp)


def test_raise_for_status_ok():
    client = NodeVaultClient(base_url=_BASE, api_key="tok")
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    client._raise_for_status(resp)  # should not raise


# ---------------------------------------------------------------------------
# AsyncNodeVaultClient tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
@respx.mock
async def test_async_invoke_success():
    """AsyncNodeVaultClient.invoke 应异步调用 Node"""
    node_data = _node_json("async_node")
    respx.get(f"{_BASE}/api/v1/nodes").mock(
        return_value=httpx.Response(200, json=[node_data])
    )
    respx.post(f"{_BASE}/api/v1/nodes/{node_data['id']}/invoke").mock(
        return_value=httpx.Response(200, json=_invoke_json("async_node"))
    )
    async_client = AsyncNodeVaultClient(base_url=_BASE, api_key="tok")
    result = await async_client.invoke("async_node", input_data={"val": 1})
    assert result.node_name == "async_node"


@pytest.mark.anyio
@respx.mock
async def test_async_invoke_node_not_found():
    """异步客户端节点不存在时抛出 NodeNotFoundError"""
    respx.get(f"{_BASE}/api/v1/nodes").mock(
        return_value=httpx.Response(200, json=[])
    )
    async_client = AsyncNodeVaultClient(base_url=_BASE, api_key="tok")
    with pytest.raises(NodeNotFoundError):
        await async_client.invoke("ghost", input_data={})


@pytest.mark.anyio
@respx.mock
async def test_async_invoke_auth_error():
    """异步客户端遇到 401 时抛出 AuthError"""
    node_data = _node_json("locked_node")
    respx.get(f"{_BASE}/api/v1/nodes").mock(
        return_value=httpx.Response(200, json=[node_data])
    )
    respx.post(f"{_BASE}/api/v1/nodes/{node_data['id']}/invoke").mock(
        return_value=httpx.Response(401, json={"detail": "unauthorized"})
    )
    async_client = AsyncNodeVaultClient(base_url=_BASE, api_key="bad_key")
    with pytest.raises(AuthError):
        await async_client.invoke("locked_node", input_data={})
