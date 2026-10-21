"""Centralized v1 API router."""

from fastapi import APIRouter

from backend.api.v1.endpoints import auth

api_router = APIRouter()

api_router.include_router(auth.router)


@api_router.get("/health", tags=["System"])
def health_check() -> dict:
    """Service health and readiness check."""
    return {
        "status": "healthy",
        "service": "inti-rag-api",
        "version": "1.0.0",
    }
