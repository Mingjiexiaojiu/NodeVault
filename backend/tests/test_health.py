import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_root_healthz(client: AsyncClient):
    response = await client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.anyio
async def test_api_v1_healthz(client: AsyncClient):
    response = await client.get("/api/v1/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "ok"
    assert "request_id" in data
