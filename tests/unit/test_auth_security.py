"""Unit tests for security utilities, email domain validation, and JWT handling."""

from datetime import timedelta

import jwt
import pytest

from backend.core.config import settings
from backend.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    validate_institutional_email,
    validate_password_complexity,
    verify_password,
)


def test_validate_institutional_email_valid():
    """Verify valid @unsa.edu.pe institutional addresses are accepted."""
    assert validate_institutional_email("student@unsa.edu.pe") is True
    assert validate_institutional_email("docente.derecho@unsa.edu.pe") is True
    assert validate_institutional_email("jariasq@unsa.edu.pe") is True
    assert validate_institutional_email("ALUMNO123@UNSA.EDU.PE") is True


def test_validate_institutional_email_invalid():
    """Verify non-institutional or malformed domains are rejected."""
    assert validate_institutional_email("user@gmail.com") is False
    assert validate_institutional_email("user@unsa.pe") is False
    assert validate_institutional_email("user@unsa.edu") is False
    assert validate_institutional_email("user@fakeunsa.edu.pe.org") is False
    assert validate_institutional_email("") is False
    assert validate_institutional_email("not-an-email") is False


def test_validate_password_complexity():
    """Verify password strength validation rules."""
    # Valid passwords
    valid, _ = validate_password_complexity("Password123*")
    assert valid is True
    valid, _ = validate_password_complexity("Derecho#2026")
    assert valid is True

    # Too short (< 8 chars)
    valid, msg = validate_password_complexity("Pass1*")
    assert valid is False
    assert "8 caracteres" in msg

    # Missing uppercase
    valid, msg = validate_password_complexity("password123*")
    assert valid is False
    assert "mayuscula" in msg

    # Missing lowercase
    valid, msg = validate_password_complexity("PASSWORD123*")
    assert valid is False
    assert "minuscula" in msg

    # Missing digit
    valid, msg = validate_password_complexity("Password*!")
    assert valid is False
    assert "numero" in msg

    # Missing special character
    valid, msg = validate_password_complexity("Password123")
    assert valid is False
    assert "especial" in msg


def test_password_hashing_and_verification():
    """Verify bcrypt password hashing and verification consistency."""
    plain = "SecurePassword2026!"
    hashed = get_password_hash(plain)

    assert hashed != plain
    assert hashed.startswith("$2b$")
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword123*", hashed) is False


def test_jwt_create_and_decode_valid():
    """Verify standard JWT creation and claim decoding."""
    subject = "usr-test-123"
    claims = {
        "email": "test@unsa.edu.pe",
        "full_name": "Test User",
        "role": "student",
    }
    token = create_access_token(subject=subject, claims=claims)
    decoded = decode_access_token(token)

    assert decoded["sub"] == subject
    assert decoded["email"] == "test@unsa.edu.pe"
    assert decoded["full_name"] == "Test User"
    assert decoded["role"] == "student"
    assert decoded["aud"] == settings.JWT_AUDIENCE
    assert decoded["iss"] == settings.JWT_ISSUER


def test_jwt_expired_token():
    """Verify expired JWT tokens raise ExpiredSignatureError."""
    subject = "usr-expired"
    token = create_access_token(
        subject=subject,
        claims={"email": "expired@unsa.edu.pe"},
        expires_delta=timedelta(seconds=-10),
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_jwt_invalid_signature():
    """Verify tampering with signature raises InvalidTokenError."""
    token = create_access_token(subject="usr-tamper")
    tampered_token = token[:-5] + "aaaaa"
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(tampered_token)
