"""Integration tests for Export API (3.8)"""
import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient


def _make_node_payload(unique: str) -> dict:
    return {
        "name": f"export_node_{unique}",
        "version": "1.0.0",
        "display_name": f"Export Test {unique}",
        "description": "Export test node",
        "type": "tool",
        "category": "test",
        "runtime": {
            "type": "http",
            "endpoint": "https://httpbin.org/post",
            "method": "POST",
        },
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {"type": "array", "description": "Input data"},
                "threshold": {"type": "number", "description": "Threshold", "default": 0.5},
            },
            "required": ["data"],
        },
        "output_schema": {
            "type": "object",
            "properties": {"result": {"type": "string"}},
        },
        "tags": ["test", "export"],
        "status": "active",
    }


@pytest.mark.anyio
async def test_export_openai_format(auth_client):
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]
    create = await client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=headers)
    assert create.status_code == 201
    node_id = create.json()["id"]

    # activate node
    await client.patch(f"/api/v1/nodes/{node_id}", json={"status": "active"}, headers=headers)

    resp = await client.get(f"/api/v1/nodes/{node_id}/export/openai", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["type"] == "function"
    assert "function" in data
    fn = data["function"]
    assert "name" in fn
    assert "parameters" in fn


@pytest.mark.anyio
async def test_export_langchain_format(auth_client):
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]
    create = await client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=headers)
    assert create.status_code == 201
    node_id = create.json()["id"]
    await client.patch(f"/api/v1/nodes/{node_id}", json={"status": "active"}, headers=headers)

    resp = await client.get(f"/api/v1/nodes/{node_id}/export/langchain", headers=headers)
    assert resp.status_code == 200
    code = resp.text
    assert "StructuredTool" in code
    assert "BaseModel" in code


@pytest.mark.anyio
async def test_export_skill_zip(auth_client):
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]
    create = await client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=headers)
    assert create.status_code == 201
    node_id = create.json()["id"]
    await client.patch(f"/api/v1/nodes/{node_id}", json={"status": "active"}, headers=headers)

    resp = await client.get(f"/api/v1/nodes/{node_id}/export/skill", headers=headers)
    assert resp.status_code == 200
    assert "application/zip" in resp.headers.get("content-type", "")
    assert ".zip" in resp.headers.get("content-disposition", "")


@pytest.mark.anyio
async def test_export_batch_openai(auth_client):
    client, headers, _ = auth_client
    ids = []
    for _ in range(2):
        unique = uuid.uuid4().hex[:8]
        create = await client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=headers)
        assert create.status_code == 201
        nid = create.json()["id"]
        await client.patch(f"/api/v1/nodes/{nid}", json={"status": "active"}, headers=headers)
        ids.append(nid)

    resp = await client.get(
        f"/api/v1/export/batch?format=openai&ids={','.join(ids)}", headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "tools" in data
    assert len(data["tools"]) == 2


@pytest.mark.anyio
async def test_export_nonexistent_node(auth_client):
    client, headers, _ = auth_client
    fake_id = uuid.uuid4()
    resp = await client.get(f"/api/v1/nodes/{fake_id}/export/openai", headers=headers)
    assert resp.status_code == 404
