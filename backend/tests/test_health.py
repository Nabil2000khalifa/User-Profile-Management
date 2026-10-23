import asyncio

import httpx

from app.api.health import get_database_engine
from app.main import app


class HealthyEngine:
    pass


def request_health() -> httpx.Response:
    async def make_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.get("/api/v1/health/database")

    return asyncio.run(make_request())


def test_database_health_endpoint_reports_ok(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.health.check_database_connection",
        lambda engine: True,
    )
    app.dependency_overrides[get_database_engine] = lambda: HealthyEngine()
    try:
        response = request_health()
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_health_endpoint_reports_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.health.check_database_connection",
        lambda engine: False,
    )
    app.dependency_overrides[get_database_engine] = lambda: HealthyEngine()
    try:
        response = request_health()
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
