"""Tests for FastAPI service endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from service.app import app


@pytest.fixture
def client() -> AsyncClient:
    """Async HTTP client for the app."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    """GET /v1/health returns status and version/uptime."""
    response = await client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "uptime_s" in data


@pytest.mark.asyncio
async def test_solve_returns_cool_solution(client: AsyncClient) -> None:
    """POST /v1/solve returns CoolTsp solution with nodes and pickup_detour_delta."""
    payload = {
        "deliveries": [
            {"x": 0.0, "y": 0.0},
            {"x": 3.0, "y": 4.0},
        ],
        "vehicle_capacity": 100.0,
    }
    response = await client.post("/v1/solve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "solution" in data
    assert len(data["solution"]["route"]) == 3  # start + 2 deliveries
    assert data["solution"]["distance"] == pytest.approx(10.0)  # closed tour
    assert "nodes" in data
    assert "unused_nodes" in data
    assert data["pickup_detour_delta"] == 0.0


@pytest.mark.asyncio
async def test_solve_rejects_empty_deliveries(client: AsyncClient) -> None:
    """POST /v1/solve with no deliveries returns 422."""
    payload = {
        "deliveries": [],
        "vehicle_capacity": 100.0,
    }
    response = await client.post("/v1/solve", json=payload)
    assert response.status_code == 422
