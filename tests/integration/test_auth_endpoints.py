"""Integration tests for FastAPI authentication endpoints."""

from fastapi.testclient import TestClient

from backend.core.security import create_access_token
from backend.main import app

client = TestClient(app)


def test_health_check_endpoint():
    """Verify system health endpoint operates normally."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "inti-rag-api"


def test_register_invalid_domain():
    """Verify registration with non-institutional email returns HTTP 400."""
    payload = {
        "email": "student@gmail.com",
        "password": "Password123*",
        "full_name": "Estudiante Externo",
        "role": "student",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "correo institucional" in response.json()["detail"].lower()


def test_register_weak_password():
    """Verify registration with weak password returns HTTP 400."""
    payload = {
        "email": "estudiante.nuevo@unsa.edu.pe",
        "password": "simple",
        "full_name": "Nuevo Alumno",
        "role": "student",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400


def test_register_success_and_conflict():
    """Verify successful user registration and subsequent duplicate conflict (HTTP 409)."""
    payload = {
        "email": "rodrigo.derecho@unsa.edu.pe",
        "password": "Password123*",
        "full_name": "Rodrigo Alexander",
        "role": "student",
    }
    # Initial registration
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "rodrigo.derecho@unsa.edu.pe"
    assert data["full_name"] == "Rodrigo Alexander"
    assert "id" in data

    # Attempt duplicate registration with same email
    dup_response = client.post("/api/v1/auth/register", json=payload)
    assert dup_response.status_code == 409
    assert "ya se encuentra registrado" in dup_response.json()["detail"].lower()


def test_login_invalid_domain():
    """Verify login with non-institutional domain returns HTTP 400."""
    payload = {
        "email": "intruder@yahoo.com",
        "password": "Password123*",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 400


def test_login_wrong_credentials():
    """Verify login with wrong password returns HTTP 401."""
    payload = {
        "email": "jariasq@unsa.edu.pe",
        "password": "WrongPassword123*",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "invalidas" in response.json()["detail"].lower()


def test_login_success():
    """Verify login with seeded default user returns 200 and signed JWT."""
    payload = {
        "email": "jariasq@unsa.edu.pe",
        "password": "Password123*",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 3600
    assert data["user"]["email"] == "jariasq@unsa.edu.pe"
    assert data["user"]["full_name"] == "Jhonatan David Arias Quispe"


def test_get_current_user_me_flow():
    """Verify complete authentication and /me profile inspection flow."""
    # 1. Login to obtain access token
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "docente@unsa.edu.pe", "password": "Password123*"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # 2. Query /api/v1/auth/me with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "docente@unsa.edu.pe"
    assert me_data["full_name"] == "Dr. Jorge Huarsaya"
    assert me_data["role"] == "docent"


def test_get_current_user_unauthorized():
    """Verify accessing /me without token or with invalid token is rejected."""
    # Without token
    no_token_resp = client.get("/api/v1/auth/me")
    assert no_token_resp.status_code in (401, 403)

    # Tampered token
    bad_headers = {"Authorization": "Bearer bad.token.here"}
    bad_token_resp = client.get("/api/v1/auth/me", headers=bad_headers)
    assert bad_token_resp.status_code == 401


def test_get_current_user_non_institutional_token():
    """Verify valid token with non-UNSA domain is rejected with HTTP 403."""
    external_token = create_access_token(
        subject="usr-external",
        claims={"email": "hacker@gmail.com", "full_name": "External", "role": "student"},
    )
    headers = {"Authorization": f"Bearer {external_token}"}
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 403
    assert "acceso restringido" in resp.json()["detail"].lower()
