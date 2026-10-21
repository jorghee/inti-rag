"""Integration tests for user registration flow and HU-05 acceptance scenarios.

Validates the full HTTP lifecycle of registration, domain filtering, password
enforcement, and duplicate collision handling against FastAPI endpoints.

Scenarios directly mapped from HU-05:
    - Escenario 1: Registro exitoso con @unsa.edu.pe y contrasena segura.
    - Escenario 2: Correo ya registrado retorna HTTP 409 protegiendo la privacidad.

Reference:
    docs/modules/authentication.md - Section 3.1 & 3.2
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


class TestRegistrationEndpointScenarios:
    """Integration test suite for /api/v1/auth/register endpoint."""

    def test_scenario_1_successful_registration_gherkin(self) -> None:
        """Escenario 1: Registro exitoso.

        DADO QUE un estudiante ingresa al formulario de registro,
        CUANDO introduce su correo "@unsa.edu.pe" y una contrasena segura,
        ENTONCES el sistema crea la cuenta y retorna HTTP 201 con los datos del perfil.
        """
        unique_suffix = uuid.uuid4().hex[:8]
        student_email = f"estudiante.{unique_suffix}@unsa.edu.pe"
        payload = {
            "email": student_email,
            "password": "Password123*",
            "full_name": "Juan Perez Quispe",
            "role": "student",
        }

        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert data["email"] == student_email
        assert data["full_name"] == "Juan Perez Quispe"
        assert data["role"] == "student"
        assert "id" in data
        assert "created_at" in data

    def test_scenario_2_duplicate_email_conflict_gherkin(self) -> None:
        """Escenario 2: Correo ya registrado.

        DADO QUE ya existe una cuenta con el correo "estudiante@unsa.edu.pe",
        CUANDO otro usuario intenta registrarse con esa misma direccion,
        ENTONCES el sistema retorna HTTP 409 informando que ya se encuentra registrada.
        """
        unique_suffix = uuid.uuid4().hex[:8]
        registered_email = f"conflict.{unique_suffix}@unsa.edu.pe"
        initial_payload = {
            "email": registered_email,
            "password": "Password123*",
            "full_name": "Alumno Inicial",
            "role": "student",
        }

        # Step 1: Initial successful registration
        first_resp = client.post("/api/v1/auth/register", json=initial_payload)
        assert first_resp.status_code == 201

        # Step 2: Attempt duplicate registration
        duplicate_payload = {
            "email": registered_email,
            "password": "OtherPassword456*",
            "full_name": "Segundo Intento",
            "role": "student",
        }
        second_resp = client.post("/api/v1/auth/register", json=duplicate_payload)
        assert second_resp.status_code == 409

        detail = second_resp.json()["detail"]
        assert "ya se encuentra registrado" in detail.lower()

    def test_registration_rejects_non_institutional_domain(self) -> None:
        """Verify non-institutional emails are rejected at HTTP boundary with status 400."""
        payload = {
            "email": "estudiante@gmail.com",
            "password": "Password123*",
            "full_name": "Estudiante Externo",
            "role": "student",
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 400
        assert "correo institucional" in response.json()["detail"].lower()

    def test_registration_rejects_weak_password_boundaries(self) -> None:
        """Verify weak passwords fail validation with status 400."""
        # 1. Too short
        resp_short = client.post(
            "/api/v1/auth/register",
            json={
                "email": "short.pass@unsa.edu.pe",
                "password": "Pass1*",
                "full_name": "Short Pass",
                "role": "student",
            },
        )
        assert resp_short.status_code == 400
        assert "8 caracteres" in resp_short.json()["detail"].lower()

        # 2. Missing special symbol
        resp_no_sym = client.post(
            "/api/v1/auth/register",
            json={
                "email": "no.sym@unsa.edu.pe",
                "password": "Password123",
                "full_name": "No Symbol",
                "role": "student",
            },
        )
        assert resp_no_sym.status_code == 400
        assert "especial" in resp_no_sym.json()["detail"].lower()

    def test_full_registration_and_immediate_login_cycle(self) -> None:
        """Verify end-to-end cycle: Register -> Login -> Fetch /me with issued JWT."""
        unique_suffix = uuid.uuid4().hex[:8]
        email = f"cycle.{unique_suffix}@unsa.edu.pe"
        password = "CyclePassword2026!"

        # 1. Register
        reg_resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Usuario Ciclo Completo",
                "role": "student",
            },
        )
        assert reg_resp.status_code == 201

        # 2. Login with registered credentials
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        assert token

        # 3. Retrieve /me profile using issued Bearer token
        me_resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 200
        profile = me_resp.json()
        assert profile["email"] == email
        assert profile["full_name"] == "Usuario Ciclo Completo"
        assert profile["role"] == "student"
