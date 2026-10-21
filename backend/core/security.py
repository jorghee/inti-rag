"""Security utilities for password hashing, institutional validation, and JWT handling."""

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import bcrypt
import jwt

from backend.core.config import settings

INSTITUTIONAL_EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+-]+@" + re.escape(settings.ALLOWED_EMAIL_DOMAIN) + r"$",
    re.IGNORECASE,
)

SPECIAL_CHARACTERS = set('!@#$%^&*(),.?":{}|<>-_=+[]~/\\;')


def validate_institutional_email(email: str) -> bool:
    """Validate whether an email belongs to the institutional domain."""
    if not email:
        return False
    return bool(INSTITUTIONAL_EMAIL_REGEX.match(email.strip()))


def validate_password_complexity(password: str) -> Tuple[bool, str]:
    """Verify password fulfills minimum complexity requirements.

    Requirements:
    - Minimum 8 characters.
    - At least one uppercase letter.
    - At least one lowercase letter.
    - At least one digit.
    - At least one special symbol.
    """
    if len(password) < 8:
        return False, "La contrasena debe tener al menos 8 caracteres."
    if not any(c.isupper() for c in password):
        return False, "La contrasena debe incluir al menos una letra mayuscula."
    if not any(c.islower() for c in password):
        return False, "La contrasena debe incluir al menos una letra minuscula."
    if not any(c.isdigit() for c in password):
        return False, "La contrasena debe incluir al menos un numero."
    if not any(c in SPECIAL_CHARACTERS for c in password):
        return False, "La contrasena debe incluir al menos un caracter especial o simbolo."
    return True, ""


def get_password_hash(password: str) -> str:
    """Hash a plaintext password using bcrypt with salt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(
    subject: str,
    claims: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token compatible with Supabase GoTrue claims."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "aud": settings.JWT_AUDIENCE,
        "iss": settings.JWT_ISSUER,
    }

    if claims:
        payload.update(claims)

    encoded_jwt = jwt.encode(
        payload,
        settings.SUPABASE_JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and verify JWT signature and claims."""
    return jwt.decode(
        token,
        settings.SUPABASE_JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
        audience=settings.JWT_AUDIENCE,
    )
