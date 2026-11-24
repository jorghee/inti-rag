"""Pydantic schemas for natural language legal queries (HU-01 partial)."""

from typing import List, Optional

from pydantic import BaseModel, Field


class LegalQueryRequest(BaseModel):
    """Payload for executing a RAG legal query."""

    query: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Legal question in Spanish.",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Existing session UUID to append this turn; creates a new session if omitted.",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of statutory chunks to retrieve.",
    )


class RetrievedArticleResponse(BaseModel):
    """Statutory chunk retrieved from pgvector hybrid search."""

    chunk_id: str = Field(..., description="legal_chunks UUID.")
    statute_code: str = Field(..., description="Statute identifier (e.g. CODIGO_CIVIL_1984).")
    article_number: int = Field(..., description="Numeric article identifier.")
    article_number_raw: str = Field(..., description="Canonical article string.")
    statutory_hierarchy: str = Field(..., description="Book > Section > Title > Chapter path.")
    raw_content: str = Field(..., description="Statutory text body.")
    official_spij_url: str = Field(..., description="Official SPIJ URL.")
    semantic_similarity: float = Field(..., description="Cosine similarity score.")
    combined_score: float = Field(..., description="Reciprocal Rank Fusion combined score.")
    is_synthetic_template: bool = Field(
        default=False,
        description="True when chunk comes from a fixture placeholder instead of full text.",
    )


class LegalQueryResponse(BaseModel):
    """Structured RAG response with grounding metadata and citations."""

    session_id: str = Field(..., description="Session UUID where this turn was persisted.")
    query_log_id: str = Field(..., description="Persisted query_logs UUID.")
    query: str = Field(..., description="Original user question.")
    answer: str = Field(..., description="Synthesized legal answer or deterministic refusal.")
    grounded: bool = Field(..., description="True when supported by verified statutory text.")
    out_of_scope: bool = Field(..., description="True when no chunk met relevance thresholds.")
    contains_synthetic_chunks: bool = Field(
        default=False,
        description="True if retrieved candidates included fixture template placeholders.",
    )
    response_latency_ms: float = Field(..., description="Total execution latency in milliseconds.")
    model_used: str = Field(..., description="LLM identifier used (or 'refusal-guardrail').")
    citations: List[RetrievedArticleResponse] = Field(
        default_factory=list,
        description="Verified statutory chunks cited in the generated answer.",
    )
    retrieved_chunks: List[RetrievedArticleResponse] = Field(
        default_factory=list,
        description="Top-K candidate chunks returned by hybrid search.",
    )
