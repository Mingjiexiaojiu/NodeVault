import uuid

import httpx
import pytest
import respx
from httpx import AsyncClient


async def _get_default_category_id(client: AsyncClient, headers: dict) -> str:
    resp = await client.get("/api/v1/categories", headers=headers)
    return resp.json()[0]["id"]


async def _create_active_node(client: AsyncClient, headers: dict, category_id: str | None = None) -> tuple[str, str]:
    """Helper: create a node and activate it; returns (node_id, version)."""
    if category_id is None:
        category_id = await _get_default_category_id(client, headers)
    unique = uuid.uuid4().hex[:8]
    r = await client.post(
        "/api/v1/nodes",
        json={
            "name": f"invoke_node_{unique}",
            "version": "1.0.0",
            "display_name": f"Invoke Node {unique}",
            "category_id": category_id,
            "runtime": {
                "type": "http",
                "endpoint": "https://mock-target.example/api",
                "method": "POST",
            },
            "input_schema": {"type": "object", "properties": {}},
            "output_schema": {"type": "object", "properties": {}},
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    node_id = r.json()["id"]

    # Activate node
    act = await client.patch(
        f"/api/v1/nodes/{node_id}",
        json={"status": "active"},
        headers=headers,
    )
    assert act.status_code == 200, act.text
    return node_id, "1.0.0"


@pytest.mark.anyio
@respx.mock
async def test_invoke_success(auth_client):
    client, headers, _ = auth_client
    node_id, version = await _create_active_node(client, headers)

    respx.post("https://mock-target.example/api").mock(
        return_value=httpx.Response(200, json={"result": "ok"})
    )

    resp = await client.post(
        f"/api/v1/nodes/{node_id}/invoke",
        json={"input": {"key": "value"}},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["output"] == {"result": "ok"}
    assert data["version"] == version
    assert "invocation_id" in data
    assert data["latency_ms"] >= 0


@pytest.mark.anyio
@respx.mock
async def test_invoke_timeout(auth_client):
    client, headers, _ = auth_client
    node_id, _ = await _create_active_node(client, headers)

    respx.post("https://mock-target.example/api").mock(
        side_effect=httpx.TimeoutException("timed out")
    )

    resp = await client.post(
        f"/api/v1/nodes/{node_id}/invoke",
        json={"input": {}},
        headers=headers,
    )
    assert resp.status_code == 502


@pytest.mark.anyio
@respx.mock
async def test_invoke_upstream_error(auth_client):
    client, headers, _ = auth_client
    node_id, _ = await _create_active_node(client, headers)

    respx.post("https://mock-target.example/api").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    resp = await client.post(
        f"/api/v1/nodes/{node_id}/invoke",
        json={"input": {}},
        headers=headers,
    )
    assert resp.status_code == 502


@pytest.mark.anyio
async def test_invoke_node_not_found(auth_client):
    client, headers, _ = auth_client
    fake_id = str(uuid.uuid4())
    resp = await client.post(
        f"/api/v1/nodes/{fake_id}/invoke",
        json={"input": {}},
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.anyio
@respx.mock
async def test_invoke_log_written(auth_client):
    """After a successful invocation, a log entry should exist."""
    client, headers, _ = auth_client
    node_id, _ = await _create_active_node(client, headers)

    respx.post("https://mock-target.example/api").mock(
        return_value=httpx.Response(200, json={"answer": 42})
    )

    await client.post(
        f"/api/v1/nodes/{node_id}/invoke",
        json={"input": {}},
        headers=headers,
    )

    logs_resp = await client.get(f"/api/v1/nodes/{node_id}/logs", headers=headers)
    assert logs_resp.status_code == 200
    logs = logs_resp.json()
    assert len(logs) >= 1
    assert logs[0]["status"] == "success"


@pytest.mark.anyio
@respx.mock
async def test_invoke_failure_log_written(auth_client):
    """After a failed invocation, failure is logged."""
    client, headers, _ = auth_client
    node_id, _ = await _create_active_node(client, headers)

    respx.post("https://mock-target.example/api").mock(
        return_value=httpx.Response(500, text="err")
    )

    await client.post(
        f"/api/v1/nodes/{node_id}/invoke",
        json={"input": {}},
        headers=headers,
    )

    logs_resp = await client.get(f"/api/v1/nodes/{node_id}/logs", headers=headers)
    assert logs_resp.status_code == 200
    logs = logs_resp.json()
    assert len(logs) >= 1
    assert logs[0]["status"] == "failure"
