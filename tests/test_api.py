from __future__ import annotations

import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from starlette.testclient import TestClient

from morning.app import create_app
from morning.config import Settings
from morning.db import create_database_engine


def _config() -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", os.environ["MORNING_DATABASE_URL"])
    return config


@pytest.fixture(scope="module", autouse=True)
def schema() -> None:
    if "MORNING_DATABASE_URL" not in os.environ:
        pytest.skip("MORNING_DATABASE_URL is required for API tests")
    command.upgrade(_config(), "head")


@pytest.fixture()
def client() -> TestClient:
    database_url = os.environ["MORNING_DATABASE_URL"]
    engine = create_database_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE morning_principals, morning_crews, morning_machines CASCADE"))
        connection.execute(text("DELETE FROM morning_shift_policy"))
    engine.dispose()
    app = create_app(
        Settings(
            environment="test",
            database_url=database_url,
            session_secret="test-morning-session-secret-with-enough-entropy",
        )
    )
    app.state.morning_store.set_shift_policy(
        timezone="Africa/Johannesburg",
        day_shift_start="06:00",
        night_shift_start="18:00",
    )
    return TestClient(app)


def _login(client: TestClient, username: str, password: str) -> dict:
    response = client.post("/api/morning/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def _admin(client: TestClient) -> dict:
    client.app.state.morning_accounts.create_admin(
        username="admin",
        password="correct-horse",
        display_name="Morning Admin",
    )
    return _login(client, "admin", "correct-horse")


def _supervisor(client: TestClient, admin_headers: dict[str, str]) -> dict:
    registered = client.post(
        "/api/morning/auth/register",
        json={"username": "jurie", "password": "correct-horse", "display_name": "Jurie Venter"},
    )
    assert registered.status_code == 201
    principal_id = registered.json()["principal"]["principal_id"]
    approved = client.post(
        f"/api/morning/admin/accounts/{principal_id}/approve",
        headers=admin_headers,
    )
    assert approved.status_code == 200, approved.text
    return _login(client, "jurie", "correct-horse")


def test_registration_requires_admin_approval(client: TestClient) -> None:
    registered = client.post(
        "/api/morning/auth/register",
        json={"username": "jurie", "password": "correct-horse", "display_name": "Jurie Venter"},
    )
    assert registered.status_code == 201
    assert registered.json()["principal"]["role"] == "supervisor"
    pending = client.post("/api/morning/auth/login", json={"username": "jurie", "password": "correct-horse"})
    assert pending.status_code == 403
    assert pending.json()["pending_approval"] is True


def test_admin_authorization_matrix(client: TestClient) -> None:
    assert client.get("/api/morning/admin/machines").status_code == 401
    admin = _admin(client)
    admin_headers = {"X-CSRF-Token": admin["csrf_token"]}
    _supervisor(client, admin_headers)
    supervisor_client = TestClient(client.app)
    login = supervisor_client.post(
        "/api/morning/auth/login",
        json={"username": "jurie", "password": "correct-horse"},
    )
    assert login.status_code == 200
    assert supervisor_client.get("/api/morning/admin/machines").status_code == 403
    assert client.get("/api/morning/admin/machines").status_code == 200
    assert client.post("/api/morning/admin/machines", json={"machine_id": "RLH1"}).status_code == 403
    created = client.post(
        "/api/morning/admin/machines",
        json={"machine_id": "RLH1", "machine_type": "LHD"},
        headers=admin_headers,
    )
    assert created.status_code == 201


def test_supervisor_full_capture_and_explicit_machine_state(client: TestClient) -> None:
    admin = _admin(client)
    admin_headers = {"X-CSRF-Token": admin["csrf_token"]}
    crew = client.post("/api/morning/admin/crews", json={"name": "Crew A"}, headers=admin_headers).json()
    person = client.post(
        "/api/morning/admin/persons",
        json={"name": "Jurie Venter", "role": "Supervisor", "crew_id": crew["id"]},
        headers=admin_headers,
    ).json()
    machine = client.post(
        "/api/morning/admin/machines",
        json={"machine_id": "RLH1", "machine_type": "LHD"},
        headers=admin_headers,
    ).json()
    supervisor = _supervisor(client, admin_headers)
    principal_id = supervisor["principal"]["principal_id"]
    linked = client.post(
        f"/api/morning/admin/accounts/{principal_id}/link",
        json={"person_id": person["id"]},
        headers=admin_headers,
    )
    assert linked.status_code == 200

    supervisor_client = TestClient(client.app)
    login = supervisor_client.post(
        "/api/morning/auth/login",
        json={"username": "jurie", "password": "correct-horse"},
    ).json()
    headers = {"X-CSRF-Token": login["csrf_token"]}
    report = supervisor_client.post(
        "/api/morning/draft",
        json={"shift_date": "2026-08-28", "shift_kind": "day"},
        headers=headers,
    )
    assert report.status_code == 201, report.text
    report_id = report.json()["id"]

    attendance = supervisor_client.post(
        f"/api/morning/reports/{report_id}/attendance",
        json={"entries": [{"person_id": person["id"], "present": True}]},
        headers=headers,
    )
    assert attendance.status_code == 200

    safety = supervisor_client.post(
        f"/api/morning/reports/{report_id}/stop-fix",
        json={
            "number": "SF-001",
            "issued_at": "1999-01-01T00:00",
            "area_of_concern": "Support",
            "location": "17L",
            "reason": "Loose rock",
            "instruction": "Make safe",
        },
        headers=headers,
    )
    assert safety.status_code == 201
    assert not safety.json()["stop_fix"][0]["issued_at"].startswith("1999-")

    event = supervisor_client.post(
        f"/api/morning/reports/{report_id}/machine-events",
        json={
            "machine_id": machine["id"],
            "start_hhmm": "10:00",
            "end_hhmm": "10:40",
            "issue": "hydraulic hose",
        },
        headers=headers,
    )
    assert event.status_code == 201, event.text

    state = supervisor_client.post(
        f"/api/morning/reports/{report_id}/machine-states",
        json={"machine_id": machine["id"], "declared_hhmm": "10:40", "state": "not_tested"},
        headers=headers,
    )
    assert state.status_code == 201, state.text
    assert state.json()["state"] == "not_tested"

    submitted = supervisor_client.post(f"/api/morning/reports/{report_id}/submit", headers=headers)
    assert submitted.status_code == 200
    whatsapp = supervisor_client.get(f"/api/morning/reports/{report_id}/whatsapp")
    assert "Not tested" in whatsapp.json()["text"]


def test_supervisor_cannot_read_another_supervisors_report(client: TestClient) -> None:
    admin = _admin(client)
    admin_headers = {"X-CSRF-Token": admin["csrf_token"]}
    _supervisor(client, admin_headers)
    first_client = TestClient(client.app)
    first_login = first_client.post(
        "/api/morning/auth/login",
        json={"username": "jurie", "password": "correct-horse"},
    ).json()
    first_report = first_client.post(
        "/api/morning/draft",
        json={"shift_date": "2026-08-28", "shift_kind": "day"},
        headers={"X-CSRF-Token": first_login["csrf_token"]},
    ).json()

    registered = client.post(
        "/api/morning/auth/register",
        json={"username": "lyle", "password": "correct-horse", "display_name": "Lyle"},
    ).json()
    client.post(
        f"/api/morning/admin/accounts/{registered['principal']['principal_id']}/approve",
        headers=admin_headers,
    )
    other = TestClient(client.app)
    other.post("/api/morning/auth/login", json={"username": "lyle", "password": "correct-horse"})
    assert other.get(f"/api/morning/reports/{first_report['id']}").status_code == 404
