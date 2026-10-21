"""Unit tests for institutional user registration and password validation.

This module provides exhaustive unit test coverage for [TASK-05.5] (parent [HU-05]):
- Rejection of weak passwords and edge-case boundary validations.
- Rejection of non-institutional and spoofed email domains.
- Rejection of duplicate institutional registrations with case insensitivity.
- Service-level registration flow and persistence guarantees.

Reference:
    docs/modules/authentication.md
    docs/architecture/decisions.md (ADR-004)
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from backend.core.security import (
    SPECIAL_CHARACTERS,
    validate_institutional_email,
    validate_password_complexity,
    verify_password,
)
from backend.schemas.auth import UserRegisterRequest
from backend.services.auth_service import AuthService, UserRecord

# ===========================================================================
# Password Complexity Unit Tests
# ===========================================================================


class TestPasswordComplexityValidation:
    """Exhaustive test suite for password complexity validation rules."""

    @pytest.mark.parametrize(
        "valid_password",
        [
            "Password123*",
            "A1!bcdef",  # Exact 8-char boundary
            "Val1d#Passw0rdLonger",
            "Derecho#2026UNSA",
            "C0mplex_P@ss!2026",
            "Abcdefg8!",
            "1234567Aa!",
        ],
    )
    def test_accepts_valid_complex_passwords(self, valid_password: str) -> None:
        """Verify that passwords fulfilling all criteria are accepted."""
        is_valid, err_msg = validate_password_complexity(valid_password)
        assert is_valid is True
        assert err_msg == ""

    @pytest.mark.parametrize(
        "short_password",
        [
            "",  # Length 0
            "A1!",  # Length 3
            "Abc1!",  # Length 5
            "Abcd1!",  # Length 6
            "Abcde1!",  # Exact 7-char boundary
        ],
    )
    def test_rejects_passwords_shorter_than_eight_chars(self, short_password: str) -> None:
        """Verify that passwords with fewer than 8 characters are rejected."""
        is_valid, err_msg = validate_password_complexity(short_password)
        assert is_valid is False
        assert "8 caracteres" in err_msg.lower()

    @pytest.mark.parametrize(
        "no_upper_password",
        [
            "password123*",
            "abcdefg1!",
            "unsa_student_2026!",
            "lowercaseonly1#",
        ],
    )
    def test_rejects_passwords_without_uppercase(self, no_upper_password: str) -> None:
        """Verify that passwords missing an uppercase letter are rejected."""
        is_valid, err_msg = validate_password_complexity(no_upper_password)
        assert is_valid is False
        assert "mayuscula" in err_msg.lower()

    @pytest.mark.parametrize(
        "no_lower_password",
        [
            "PASSWORD123*",
            "ABCDEFG1!",
            "UNSA_FACULTY_2026#",
            "UPPERCASEONLY1!",
        ],
    )
    def test_rejects_passwords_without_lowercase(self, no_lower_password: str) -> None:
        """Verify that passwords missing a lowercase letter are rejected."""
        is_valid, err_msg = validate_password_complexity(no_lower_password)
        assert is_valid is False
        assert "minuscula" in err_msg.lower()

    @pytest.mark.parametrize(
        "no_digit_password",
        [
            "Password!*",
            "Abcdefgh!",
            "UNSAstudent#",
            "NoDigitsAtAll*",
        ],
    )
    def test_rejects_passwords_without_digits(self, no_digit_password: str) -> None:
        """Verify that passwords missing numeric digits are rejected."""
        is_valid, err_msg = validate_password_complexity(no_digit_password)
        assert is_valid is False
        assert "numero" in err_msg.lower()

    @pytest.mark.parametrize(
        "no_special_password",
        [
            "Password123",
            "Abcdefg12",
            "UNSA2026student",
            "OnlyLettersAndDigits1",
        ],
    )
    def test_rejects_passwords_without_special_characters(self, no_special_password: str) -> None:
        """Verify that passwords missing special characters are rejected."""
        is_valid, err_msg = validate_password_complexity(no_special_password)
        assert is_valid is False
        assert "especial" in err_msg.lower() or "simbolo" in err_msg.lower()

    def test_accepts_all_defined_special_characters(self) -> None:
        """Verify each character in SPECIAL_CHARACTERS fulfills the symbol criterion."""
        for char in SPECIAL_CHARACTERS:
            pwd = f"Pass123{char}"
            is_valid, _ = validate_password_complexity(pwd)
            assert is_valid is True, f"Failed for special character: {char!r}"


# ===========================================================================
# Institutional Email Domain Unit Tests
# ===========================================================================


class TestInstitutionalEmailValidation:
    """Exhaustive test suite for @unsa.edu.pe institutional domain validation."""

    @pytest.mark.parametrize(
        "valid_email",
        [
            "estudiante@unsa.edu.pe",
            "jariasq@unsa.edu.pe",
            "docente.derecho@unsa.edu.pe",
            "maria_quispe@unsa.edu.pe",
            "alumno-2026@unsa.edu.pe",
            "investigador+lab@unsa.edu.pe",
            "ALUMNO@UNSA.EDU.PE",
            "Profesor.UNSA@Unsa.Edu.Pe",
            "u19991234@unsa.edu.pe",
        ],
    )
    def test_accepts_valid_institutional_emails(self, valid_email: str) -> None:
        """Verify that valid addresses under @unsa.edu.pe are accepted."""
        assert validate_institutional_email(valid_email) is True

    @pytest.mark.parametrize(
        "external_domain_email",
        [
            "estudiante@gmail.com",
            "abogado@hotmail.com",
            "docente@yahoo.es",
            "investigador@outlook.com",
            "alumno@pucp.edu.pe",
            "estudiante@uni.edu.pe",
            "usuario@unmsm.edu.pe",
            "admin@gob.pe",
        ],
    )
    def test_rejects_external_commercial_and_academic_domains(
        self, external_domain_email: str
    ) -> None:
        """Verify rejection of external commercial and non-UNSA university domains."""
        assert validate_institutional_email(external_domain_email) is False

    @pytest.mark.parametrize(
        "spoofed_or_subdomain_email",
        [
            "estudiante@cs.unsa.edu.pe",  # Subdomain rejected
            "docente@derecho.unsa.edu.pe",  # Subdomain rejected
            "user@unsa.edu.pe.attacker.com",  # Suffix attack
            "user@unsa.edu.pe.org",  # Extra TLD
            "user@fakeunsa.edu.pe",  # Prefix attack
            "user@unsa.edu",  # Missing .pe
            "user@unsa.pe",  # Missing .edu
            "user@unsa-edu.pe",  # Hyphen variation
        ],
    )
    def test_rejects_spoofed_and_subdomain_variations(
        self, spoofed_or_subdomain_email: str
    ) -> None:
        """Verify strict domain boundary matching against spoofed variants."""
        assert validate_institutional_email(spoofed_or_subdomain_email) is False

    @pytest.mark.parametrize(
        "malformed_email",
        [
            "",
            "   ",
            "not-an-email",
            "@unsa.edu.pe",
            "estudiante@",
            "estudiante@@unsa.edu.pe",
            "estudiante @unsa.edu.pe",
            "estudiante@ unsa.edu.pe",
            "estudiante<script>@unsa.edu.pe",
            "estudiante' OR '1'='1@unsa.edu.pe",
        ],
    )
    def test_rejects_malformed_email_syntaxes(self, malformed_email: str) -> None:
        """Verify rejection of malformed and injection-attempt syntaxes."""
        assert validate_institutional_email(malformed_email) is False


# ===========================================================================
# Duplicate Institutional Email & AuthService Unit Tests
# ===========================================================================


class TestAuthServiceRegistrationAndDuplicates:
    """Test suite for user registration logic and duplicate conflict detection."""

    @pytest.fixture
    def fresh_service(self) -> AuthService:
        """Instantiate an isolated AuthService instance for test isolation."""
        return AuthService()

    def test_register_new_student_success(self, fresh_service: AuthService) -> None:
        """Verify standard successful registration creates complete profile metadata."""
        payload = UserRegisterRequest(
            email="nuevo.alumno@unsa.edu.pe",
            password="SecurePassword2026*",
            full_name="Nuevo Alumno UNSA",
            role="student",
        )
        profile = fresh_service.register_user(payload)

        assert profile.email == "nuevo.alumno@unsa.edu.pe"
        assert profile.full_name == "Nuevo Alumno UNSA"
        assert profile.role == "student"
        assert profile.id.startswith("usr-")

        # Verify retrievable by email and id
        by_id = fresh_service.get_user_by_id(profile.id)
        assert by_id is not None
        assert by_id.email == "nuevo.alumno@unsa.edu.pe"

        by_email = fresh_service.get_user_by_email("nuevo.alumno@unsa.edu.pe")
        assert by_email is not None
        assert by_email.id == profile.id

    def test_register_duplicate_email_raises_conflict_409(self, fresh_service: AuthService) -> None:
        """Verify registering an already existing email raises HTTP 409 Conflict."""
        payload = UserRegisterRequest(
            email="estudiante.dup@unsa.edu.pe",
            password="Password123*",
            full_name="Estudiante Original",
            role="student",
        )
        fresh_service.register_user(payload)

        # Attempt second registration with same email
        duplicate_payload = UserRegisterRequest(
            email="estudiante.dup@unsa.edu.pe",
            password="OtherPassword456#",
            full_name="Estudiante Duplicado",
            role="student",
        )
        with pytest.raises(HTTPException) as exc_info:
            fresh_service.register_user(duplicate_payload)

        assert exc_info.value.status_code == 409
        assert "ya se encuentra registrado" in exc_info.value.detail.lower()

    def test_register_duplicate_email_case_insensitive(self, fresh_service: AuthService) -> None:
        """Verify duplicate detection is strictly case-insensitive."""
        payload = UserRegisterRequest(
            email="lowercase.user@unsa.edu.pe",
            password="Password123*",
            full_name="User Lower",
            role="student",
        )
        fresh_service.register_user(payload)

        # Duplicate attempt with uppercase characters
        upper_payload = UserRegisterRequest(
            email="LOWERCASE.USER@UNSA.EDU.PE",
            password="Password123*",
            full_name="User Upper",
            role="student",
        )
        with pytest.raises(HTTPException) as exc_info:
            fresh_service.register_user(upper_payload)

        assert exc_info.value.status_code == 409

    def test_register_conflict_with_seeded_default_users(self, fresh_service: AuthService) -> None:
        """Verify attempting to register seeded default users triggers HTTP 409."""
        payload = UserRegisterRequest(
            email="jariasq@unsa.edu.pe",
            password="Password123*",
            full_name="Impostor Arias",
            role="student",
        )
        with pytest.raises(HTTPException) as exc_info:
            fresh_service.register_user(payload)

        assert exc_info.value.status_code == 409

    def test_register_rejects_invalid_domain_service_layer(
        self, fresh_service: AuthService
    ) -> None:
        """Verify service layer rejects non-institutional emails with HTTP 400."""
        payload = UserRegisterRequest(
            email="externo@gmail.com",
            password="Password123*",
            full_name="Usuario Externo",
            role="student",
        )
        with pytest.raises(HTTPException) as exc_info:
            fresh_service.register_user(payload)

        assert exc_info.value.status_code == 400
        assert "dominio @unsa.edu.pe" in exc_info.value.detail

    def test_register_rejects_weak_password_service_layer(self, fresh_service: AuthService) -> None:
        """Verify service layer rejects weak passwords with HTTP 400 and clear error."""
        payload = UserRegisterRequest(
            email="valido@unsa.edu.pe",
            password="simple",
            full_name="Alumno Debil",
            role="student",
        )
        with pytest.raises(HTTPException) as exc_info:
            fresh_service.register_user(payload)

        assert exc_info.value.status_code == 400
        assert "8 caracteres" in exc_info.value.detail

    def test_password_is_properly_hashed_upon_registration(
        self, fresh_service: AuthService
    ) -> None:
        """Verify user password hash uses bcrypt and plaintext is never stored."""
        raw_password = "SecretPassword123#"
        payload = UserRegisterRequest(
            email="verif.hash@unsa.edu.pe",
            password=raw_password,
            full_name="Verif Hash",
            role="student",
        )
        profile = fresh_service.register_user(payload)

        # Retrieve internal record
        internal_user: UserRecord = fresh_service._users_by_id[profile.id]
        assert internal_user.hashed_password != raw_password
        assert internal_user.hashed_password.startswith("$2b$")
        assert verify_password(raw_password, internal_user.hashed_password) is True
        assert verify_password("WrongPassword123*", internal_user.hashed_password) is False
