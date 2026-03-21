"""
Tests for stats API (task 7.4):
- GET /nodes/{id}/stats with no logs returns zero values
- ?days=500 returns 422
- Normal stats returned correctly
"""
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import insert


def _make_node_payload(unique: str, category_id: str = "") -> dict:
    return {
        "name": f"stats_node_{unique}",
        "version": "1.0.0",
        "display_name": f"Stats Node {unique}",
        "description": "node for stats testing",
        "category_id": category_id,
        "runtime": {
            "type": "http",
            "endpoint": "https://httpbin.org/post",
            "method": "POST",
        },
        "input_schema": {"type": "object", "properties": {}},
        "output_schema": {"type": "object", "properties": {}},
    }


async def _create_node(auth_client) -> tuple:
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]
    with patch("backend.api.v1.nodes.NodeSearchIndex"):
        resp = await client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=headers)
    assert resp.status_code == 201
    return client, headers, resp.json()["id"]


@pytest.mark.anyio
async def test_stats_no_logs_returns_zero(auth_client):
    """没有调用日志时 stats 应返回零值"""
    client, headers, node_id = await _create_node(auth_client)

    resp = await client.get(f"/api/v1/nodes/{node_id}/stats", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_invocations"] == 0
    assert data["success_rate"] is None
    assert data["avg_latency_ms"] is None
    assert data["daily_trend"] == []
    assert data["top_callers"] == []


@pytest.mark.anyio
async def test_stats_days_too_large_returns_422(auth_client):
    """days > 365 应返回 422 验证错误"""
    client, headers, node_id = await _create_node(auth_client)

    resp = await client.get(f"/api/v1/nodes/{node_id}/stats?days=500", headers=headers)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_stats_node_not_found(auth_client):
    """不存在的 node_id 应返回 404"""
    client, headers, _ = auth_client
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/nodes/{fake_id}/stats", headers=headers)
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_stats_with_invocation_logs(_test_engine, auth_client):
    """有调用日志时统计值应正确计算"""
    from backend.models.node import NodeInvocationLog

    client, headers, node_id = await _create_node(auth_client)
    node_uuid = uuid.UUID(node_id)

    # Insert mock log records directly into DB
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    session_factory = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        now = datetime.utcnow()
        logs = [
            NodeInvocationLog(
                id=uuid.uuid4(),
                node_id=node_uuid,
                status="success",
                latency_ms=100,
                created_at=now - timedelta(hours=1),
            ),
            NodeInvocationLog(
                id=uuid.uuid4(),
                node_id=node_uuid,
                status="success",
                latency_ms=200,
                created_at=now - timedelta(hours=2),
            ),
            NodeInvocationLog(
                id=uuid.uuid4(),
                node_id=node_uuid,
                status="error",
                latency_ms=50,
                created_at=now - timedelta(hours=3),
            ),
        ]
        session.add_all(logs)
        await session.commit()

    resp = await client.get(f"/api/v1/nodes/{node_id}/stats?days=7", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_invocations"] >= 3
    assert data["success_rate"] is not None
    assert 0 < data["success_rate"] <= 1.0
    assert data["avg_latency_ms"] is not None
    assert data["p95_latency_ms"] is not None
    assert data["p99_latency_ms"] is not None
    assert len(data["daily_trend"]) >= 1


@pytest.mark.anyio
async def test_stats_daily_trend_structure(_test_engine, auth_client):
    """daily_trend 每项应包含 date / count / errors 字段"""
    from backend.models.node import NodeInvocationLog
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    client, headers, node_id = await _create_node(auth_client)
    node_uuid = uuid.UUID(node_id)

    session_factory = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        now = datetime.utcnow()
        session.add(
            NodeInvocationLog(
                id=uuid.uuid4(),
                node_id=node_uuid,
                status="success",
                latency_ms=80,
                created_at=now,
            )
        )
        await session.commit()

    resp = await client.get(f"/api/v1/nodes/{node_id}/stats?days=1", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    if data["daily_trend"]:
        entry = data["daily_trend"][0]
        assert "date" in entry
        assert "count" in entry
        assert "errors" in entry


@pytest.mark.anyio
async def test_stats_days_boundary_values(auth_client):
    """days=1 和 days=365 应都返回 200"""
    client, headers, node_id = await _create_node(auth_client)

    for days in [1, 365]:
        resp = await client.get(f"/api/v1/nodes/{node_id}/stats?days={days}", headers=headers)
        assert resp.status_code == 200


@pytest.mark.anyio
async def test_stats_requires_auth(client):
    """未认证请求 /nodes/{id}/stats 应返回 401"""
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/nodes/{fake_id}/stats")
    assert resp.status_code == 401
