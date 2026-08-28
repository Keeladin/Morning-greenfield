from __future__ import annotations

from starlette.testclient import TestClient

from morning.app import create_app
from morning.config import Settings


def test_healthz_does_not_require_a_database_in_development() -> None:
    client = TestClient(create_app(Settings(environment="development", database_url=None, session_secret=None)))
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "morning",
        "environment": "development",
        "application_ready": False,
    }
