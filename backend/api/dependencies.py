"""Security dependencies for FastAPI routes."""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.config import settings
from backend.core.security import decode_access_token
from backend.schemas.auth import UserProfileResponse
from backend.services.auth_service import auth_service

security = HTTPBearer(auto_error=True)


async def get_current_user_claims(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Validate bearer token signature, audience, and institutional domain."""
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        email = payload.get("email", "")

        if not email.endswith(f"@{settings.ALLOWED_EMAIL_DOMAIN}"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso restringido a cuentas institucionales @unsa.edu.pe",
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token de acceso ha expirado",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acceso invalido",
        )


async def get_current_user(
    claims: dict = Depends(get_current_user_claims),
) -> UserProfileResponse:
    """Retrieve verified profile of the currently authenticated user."""
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identificador de usuario ausente en el token",
        )

    user = auth_service.get_user_by_id(user_id)
    if user:
        return user

    # Fallback to claims in token if user was created in external session
    return UserProfileResponse(
        id=user_id,
        email=claims.get("email", ""),
        full_name=claims.get("full_name", ""),
        role=claims.get("role", "student"),
    )
