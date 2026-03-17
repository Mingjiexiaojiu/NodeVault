"""Integration tests for Agent API (4.6)"""
import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


def _make_node_payload(unique: str) -> dict:
    return {
        "name": f"agent_node_{unique}",
        "version": "1.0.0",
        "display_name": f"Agent Test {unique}",
        "description": "Agent test node for risk analysis",
        "type": "tool",
        "category": "risk",
        "runtime": {
            "type": "http",
            "endpoint": "https://httpbin.org/post",
            "method": "POST",
        },
        "input_schema": {
            "type": "object",
            "properties": {"data": {"type": "array", "description": "Input"}},
            "required": ["data"],
        },
        "output_schema": {"type": "object", "properties": {"result": {"type": "string"}}},
        "tags": ["risk", "test"],
        "status": "active",
    }


@pytest.mark.anyio
async def test_agent_tools_returns_list(auth_client):
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]
    create = await client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=headers)
    assert create.status_code == 201
    await client.patch(
        f"/api/v1/nodes/{create.json()['id']}",
        json={"status": "active"},
        headers=headers,
    )

    resp = await client.get("/api/v1/agent/tools", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "tools" in data
    assert isinstance(data["tools"], list)


@pytest.mark.anyio
async def test_agent_discover(auth_client):
    client, headers, _ = auth_client
    with patch("backend.api.v1.agent.NodeSearchIndex") as MockSearch:
        instance = MockSearch.return_value
        instance.search.return_value = {"hits": []}
        resp = await client.get(
            "/api/v1/agent/discover?intent=分析风险&format=openai", headers=headers
        )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "tools" in data


@pytest.mark.anyio
async def test_execute_tool_node_not_found(auth_client):
    client, headers, _ = auth_client
    tool_call = {
        "id": "call_test_123",
        "type": "function",
        "function": {
            "name": "nonexistent_node_xyz",
            "arguments": json.dumps({}),
        },
    }
    resp = await client.post("/api/v1/agent/execute-tool", json=tool_call, headers=headers)
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_execute_tool_invalid_arguments_json(auth_client):
    client, headers, _ = auth_client
    tool_call = {
        "id": "call_test_456",
        "type": "function",
        "function": {
            "name": "some_node",
            "arguments": "not valid json {{{",
        },
    }
    resp = await client.post("/api/v1/agent/execute-tool", json=tool_call, headers=headers)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_execute_tool_success(auth_client):
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]
    node_name = f"agent_node_{unique}"
    create = await client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=headers)
    assert create.status_code == 201
    node_id = create.json()["id"]
    await client.patch(f"/api/v1/nodes/{node_id}", json={"status": "active"}, headers=headers)

    tool_call = {
        "id": "call_ok_789",
        "type": "function",
        "function": {
            "name": node_name,
            "arguments": json.dumps({"data": [1, 2, 3]}),
        },
    }

    with patch("backend.core.invocation.RuntimeDispatcher") as MockDispatcher:
        mock_exec = AsyncMock()
        mock_exec.execute = AsyncMock(return_value=({"result": "ok"}, 10))
        MockDispatcher.get_executor.return_value = mock_exec

        resp = await client.post("/api/v1/agent/execute-tool", json=tool_call, headers=headers)

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["role"] == "tool"
    assert data["tool_call_id"] == "call_ok_789"
    assert "content" in data
