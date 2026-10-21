"""Authentication router providing registration, login, and profile introspection."""

from fastapi import APIRouter, Depends, status

from backend.api.dependencies import get_current_user
from backend.schemas.auth import (
    LoginResponse,
    UserLoginRequest,
    UserProfileResponse,
    UserRegisterRequest,
)
from backend.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new institutional user",
    description="Registers a new user verifying the @unsa.edu.pe domain and password complexity.",
)
def register(payload: UserRegisterRequest) -> UserProfileResponse:
    """Register an institutional user account."""
    return auth_service.register_user(payload)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Institutional user login",
    description="Authenticates institutional credentials and issues a signed JWT access token.",
)
def login(payload: UserLoginRequest) -> LoginResponse:
    """Authenticate and issue JWT session token."""
    return auth_service.authenticate_user(payload.email, payload.password)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Returns the profile data of the currently authenticated institutional user.",
)
def get_me(current_user: UserProfileResponse = Depends(get_current_user)) -> UserProfileResponse:
    """Retrieve profile for the authenticated bearer token."""
    return current_user
