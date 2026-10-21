"""Authentication schemas and data transfer objects."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserRegisterRequest(BaseModel):
    """Payload for institutional user registration."""

    email: str = Field(..., description="Institutional email address ending in @unsa.edu.pe")
    password: str = Field(..., description="Strong password fulfilling complexity rules")
    full_name: str = Field(..., description="Student or faculty full name")
    role: str = Field(
        default="student",
        description="Institutional role (student, faculty, docent, admin)",
    )


class UserLoginRequest(BaseModel):
    """Payload for user login."""

    email: str = Field(..., description="Institutional email address ending in @unsa.edu.pe")
    password: str = Field(..., description="User plaintext password")


class UserProfileResponse(BaseModel):
    """Institutional user profile response."""

    id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="Institutional email address")
    full_name: str = Field(..., description="User full name")
    role: str = Field(..., description="User role")
    created_at: Optional[datetime] = Field(default=None, description="Account creation timestamp")


class LoginResponse(BaseModel):
    """JWT authentication response payload."""

    access_token: str = Field(..., description="Signed JWT Bearer access token")
    token_type: str = Field(default="bearer", description="Token authorization type")
    expires_in: int = Field(default=3600, description="Token validity duration in seconds")
    user: UserProfileResponse = Field(..., description="Authenticated user profile")
