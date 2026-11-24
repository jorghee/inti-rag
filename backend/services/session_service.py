"""Business logic for user query sessions and history (HU-06)."""

from typing import List, Optional

from fastapi import HTTPException, status

from backend.repositories.exceptions import (
    ForbiddenAccessError,
    RepositoryError,
    ResourceNotFoundError,
    StorageUnavailableError,
)
from backend.repositories.session_repository import SessionRepository, SupabaseSessionRepository
from backend.schemas.auth import UserProfileResponse
from backend.schemas.sessions import (
    QueryLogItemResponse,
    SessionCreateRequest,
    SessionDetailResponse,
    SessionSummaryResponse,
)


def _derive_session_title(query_text: str, max_length: int = 80) -> str:
    cleaned = " ".join(query_text.strip().split())
    if len(cleaned) <= max_length:
        return cleaned or "Nueva consulta jurídica"
    return f"{cleaned[: max_length - 3].rstrip()}..."


class SessionService:
    """Coordinates user-scoped legal research sessions and query history."""

    def __init__(self, repository: Optional[SessionRepository] = None) -> None:
        self._repo: SessionRepository = repository or SupabaseSessionRepository()

    def ensure_user_ready(self, user: UserProfileResponse) -> str:
        """Validate/provision the user profile in persistence before downstream work."""
        return self._resolve_owner_id(user)

    def _resolve_owner_id(self, user: UserProfileResponse) -> str:
        try:
            return self._repo.resolve_user_id(
                user_id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
            )
        except StorageUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        except RepositoryError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

    def create_session(
        self,
        user: UserProfileResponse,
        payload: SessionCreateRequest,
    ) -> SessionSummaryResponse:
        owner_id = self._resolve_owner_id(user)
        try:
            record = self._repo.create_session(
                user_id=owner_id,
                session_title=payload.session_title.strip(),
            )
            return SessionSummaryResponse(**record)
        except StorageUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        except RepositoryError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

    def list_sessions(
        self,
        user: UserProfileResponse,
        limit: int = 50,
    ) -> List[SessionSummaryResponse]:
        owner_id = self._resolve_owner_id(user)
        try:
            rows = self._repo.list_sessions(user_id=owner_id, limit=limit)
            return [SessionSummaryResponse(**row) for row in rows]
        except StorageUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        except RepositoryError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

    def get_session(
        self,
        user: UserProfileResponse,
        session_id: str,
    ) -> SessionDetailResponse:
        owner_id = self._resolve_owner_id(user)
        try:
            record = self._repo.get_session(session_id=session_id, user_id=owner_id)
            return SessionDetailResponse(**record)
        except ResourceNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except ForbiddenAccessError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        except StorageUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        except RepositoryError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

    def delete_session(self, user: UserProfileResponse, session_id: str) -> None:
        owner_id = self._resolve_owner_id(user)
        try:
            self._repo.delete_session(session_id=session_id, user_id=owner_id)
        except ResourceNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except ForbiddenAccessError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        except StorageUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        except RepositoryError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

    def record_interaction(
        self,
        *,
        user: UserProfileResponse,
        session_id: Optional[str],
        user_query: str,
        assistant_response: str,
        response_latency_ms: float,
        prompt_tokens: int,
        completion_tokens: int,
        model_used: str,
        citations: List[dict],
    ) -> QueryLogItemResponse:
        """Persist a query turn into an existing owned session or create a new one."""
        owner_id = self._resolve_owner_id(user)
        try:
            if session_id:
                self._repo.get_session(session_id=session_id, user_id=owner_id)
                target_session_id = session_id
            else:
                created = self._repo.create_session(
                    user_id=owner_id,
                    session_title=_derive_session_title(user_query),
                )
                target_session_id = str(created["id"])

            log = self._repo.create_query_log(
                session_id=target_session_id,
                user_query=user_query,
                assistant_response=assistant_response,
                response_latency_ms=response_latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                model_used=model_used,
            )
            if citations:
                saved_citations = self._repo.create_citations(
                    query_log_id=str(log["id"]),
                    citations=citations,
                )
                log["citations"] = saved_citations
            return QueryLogItemResponse(**log)
        except ResourceNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except ForbiddenAccessError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        except StorageUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        except RepositoryError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc


session_service = SessionService()


def get_session_service() -> SessionService:
    """FastAPI dependency provider for SessionService."""
    return session_service
