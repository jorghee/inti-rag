"""Integration tests for HU-06 user query session history and isolation."""

from typing import Dict

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.repositories.session_repository import InMemorySessionRepository
from backend.services.session_service import SessionService, get_session_service


def _login_headers(
    client: TestClient, email: str, password: str = "Password123*"
) -> Dict[str, str]:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def isolated_session_service():
    """Provide an isolated in-memory SessionService per test."""
    session_repo = InMemorySessionRepository()
    sess_svc = SessionService(repository=session_repo)
    app.dependency_overrides[get_session_service] = lambda: sess_svc
    yield sess_svc
    app.dependency_overrides.clear()


def test_session_crud_and_cross_user_isolation(
    isolated_session_service: SessionService,
) -> None:
    """Verify users can create/list/delete their own sessions and cannot read others' sessions."""
    client = TestClient(app)
    student_headers = _login_headers(client, "jariasq@unsa.edu.pe")
    docent_headers = _login_headers(client, "docente@unsa.edu.pe")

    created = client.post(
        "/api/v1/sessions",
        headers=student_headers,
        json={"session_title": "Investigación sobre compraventa"},
    )
    assert created.status_code == 201
    session_id = created.json()["id"]

    # Owner can list and inspect
    listed = client.get("/api/v1/sessions", headers=student_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["id"] == session_id

    # Another authenticated UNSA user is forbidden (403)
    forbidden = client.get(f"/api/v1/sessions/{session_id}", headers=docent_headers)
    assert forbidden.status_code == 403

    # Owner can delete
    deleted = client.delete(f"/api/v1/sessions/{session_id}", headers=student_headers)
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/sessions/{session_id}", headers=student_headers).status_code == 404
