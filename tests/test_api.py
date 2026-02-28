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
    """GET /health returns status ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_solve_returns_route_and_distance(client: AsyncClient) -> None:
    """POST /solve returns route and distance."""
    payload = {
        "nodes": [
            {"x": 0.0, "y": 0.0},
            {"x": 3.0, "y": 4.0},
        ]
    }
    response = await client.post("/solve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "route" in data
    assert "distance" in data
    assert data["route"] == [0, 1]
    assert data["distance"] == pytest.approx(10.0)  # closed tour


@pytest.mark.asyncio
async def test_solve_rejects_single_node(client: AsyncClient) -> None:
    """POST /solve with one node returns 422."""
    payload = {"nodes": [{"x": 0.0, "y": 0.0}]}
    response = await client.post("/solve", json=payload)
    assert response.status_code == 422
