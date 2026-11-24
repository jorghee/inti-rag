"""FastAPI router for user query sessions and history (HU-06)."""

from typing import List

from fastapi import APIRouter, Depends, Query, Response, status

from backend.api.dependencies import get_current_user
from backend.schemas.auth import UserProfileResponse
from backend.schemas.sessions import (
    SessionCreateRequest,
    SessionDetailResponse,
    SessionSummaryResponse,
)
from backend.services.session_service import SessionService, get_session_service

router = APIRouter(prefix="/sessions", tags=["Query History"])


@router.get(
    "",
    response_model=List[SessionSummaryResponse],
    summary="List authenticated user query sessions",
)
def list_user_sessions(
    limit: int = Query(default=50, ge=1, le=100),
    current_user: UserProfileResponse = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
) -> List[SessionSummaryResponse]:
    """Return sessions owned by the authenticated user ordered by latest activity."""
    return service.list_sessions(user=current_user, limit=limit)


@router.post(
    "",
    response_model=SessionSummaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new query session",
)
def create_user_session(
    payload: SessionCreateRequest,
    current_user: UserProfileResponse = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
) -> SessionSummaryResponse:
    """Create a new legal research session for the authenticated user."""
    return service.create_session(user=current_user, payload=payload)


@router.get(
    "/{session_id}",
    response_model=SessionDetailResponse,
    summary="Retrieve a session with full query history and citations",
)
def get_user_session(
    session_id: str,
    current_user: UserProfileResponse = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
) -> SessionDetailResponse:
    """Return a single owned session along with its chronological query logs."""
    return service.get_session(user=current_user, session_id=session_id)


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an owned query session",
)
def delete_user_session(
    session_id: str,
    current_user: UserProfileResponse = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
) -> Response:
    """Delete a session and its associated query logs owned by the authenticated user."""
    service.delete_session(user=current_user, session_id=session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
