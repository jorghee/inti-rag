"""Pydantic schemas for user query sessions and history (HU-06)."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    """Payload for creating a new legal query session."""

    session_title: str = Field(
        default="Nueva consulta jurídica",
        min_length=1,
        max_length=255,
        description="Short descriptive title for the legal research session.",
    )


class CitationItemResponse(BaseModel):
    """Persisted statutory citation linked to a query response."""

    id: str = Field(..., description="Unique citation reference identifier.")
    chunk_id: str = Field(..., description="Referenced legal_chunks UUID.")
    article_number: Optional[int] = Field(default=None, description="Numeric article identifier.")
    article_number_raw: Optional[str] = Field(
        default=None, description="Canonical article label (e.g. '1529', 'I')."
    )
    statutory_hierarchy: Optional[str] = Field(
        default=None, description="Full statutory hierarchy path."
    )
    official_spij_url: Optional[str] = Field(
        default=None, description="Official SPIJ link for verification."
    )
    similarity_score: float = Field(..., description="Cosine similarity score of the chunk.")
    inline_citation_index: int = Field(..., description="Order of citation in the response.")


class QueryLogItemResponse(BaseModel):
    """Single user query and assistant response turn inside a session."""

    id: str = Field(..., description="Unique query log UUID.")
    session_id: str = Field(..., description="Parent session UUID.")
    user_query: str = Field(..., description="Question submitted by the user.")
    assistant_response: str = Field(..., description="Synthesized legal answer.")
    response_latency_ms: float = Field(..., description="End-to-end response latency in ms.")
    prompt_tokens: int = Field(default=0, description="Input tokens consumed.")
    completion_tokens: int = Field(default=0, description="Output tokens generated.")
    model_used: str = Field(..., description="LLM identifier used for synthesis.")
    created_at: datetime = Field(..., description="UTC timestamp of the interaction.")
    citations: List[CitationItemResponse] = Field(
        default_factory=list, description="Verified citations attached to this response."
    )


class SessionSummaryResponse(BaseModel):
    """Summary item for listing a user's historical sessions."""

    id: str = Field(..., description="Unique session UUID.")
    user_id: str = Field(..., description="Owner user UUID.")
    session_title: str = Field(..., description="Session title.")
    started_at: datetime = Field(..., description="Session creation timestamp.")
    last_active_at: datetime = Field(..., description="Timestamp of the latest activity.")
    query_count: int = Field(default=0, description="Number of recorded queries in this session.")


class SessionDetailResponse(BaseModel):
    """Detailed view of a single session including all ordered query logs."""

    id: str = Field(..., description="Unique session UUID.")
    user_id: str = Field(..., description="Owner user UUID.")
    session_title: str = Field(..., description="Session title.")
    started_at: datetime = Field(..., description="Session creation timestamp.")
    last_active_at: datetime = Field(..., description="Timestamp of the latest activity.")
    logs: List[QueryLogItemResponse] = Field(
        default_factory=list, description="Chronological list of query/response turns."
    )
