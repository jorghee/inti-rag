"""FastAPI router for grounded legal queries (HU-01 partial)."""

from fastapi import APIRouter, Depends, status

from backend.api.dependencies import get_current_user
from backend.schemas.auth import UserProfileResponse
from backend.schemas.queries import LegalQueryRequest, LegalQueryResponse
from backend.services.rag_service import RagService, get_rag_service

router = APIRouter(prefix="/queries", tags=["Legal Queries"])


@router.post(
    "",
    response_model=LegalQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute a hybrid RAG legal query and persist it to session history",
)
def execute_legal_query(
    payload: LegalQueryRequest,
    current_user: UserProfileResponse = Depends(get_current_user),
    service: RagService = Depends(get_rag_service),
) -> LegalQueryResponse:
    """Run hybrid statutory retrieval, grounded synthesis, and persist the turn."""
    return service.execute_query(user=current_user, payload=payload)
