"""Repository for hybrid legal chunk retrieval against Supabase pgvector RPC."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from backend.repositories.supabase_client import SupabaseClient, supabase_client


class LegalChunksRepository(ABC):
    """Abstract interface for statutory chunk retrieval."""

    @abstractmethod
    def search_hybrid(
        self,
        query_text: str,
        query_embedding: List[float],
        match_count: int = 5,
    ) -> List[Dict[str, Any]]:
        """Retrieve ranked statutory chunks combining semantic and lexical scores."""


class SupabaseLegalChunksRepository(LegalChunksRepository):
    """Production retriever delegating hybrid RRF search directly to PostgreSQL RPC."""

    def __init__(self, client: Optional[SupabaseClient] = None) -> None:
        self._client = client or supabase_client

    def search_hybrid(
        self,
        query_text: str,
        query_embedding: List[float],
        match_count: int = 5,
    ) -> List[Dict[str, Any]]:
        rows = self._client.rpc(
            "match_legal_chunks_hybrid",
            {
                "query_text": query_text,
                "query_embedding": query_embedding,
                "match_count": match_count,
                "full_text_weight": 1.0,
                "vector_weight": 1.0,
                "rrf_k": 60,
            },
        )
        normalized: List[Dict[str, Any]] = []
        for row in rows:
            metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
            normalized.append(
                {
                    "chunk_id": str(row["id"]),
                    "statute_code": row.get("statute_code", "CODIGO_CIVIL_1984"),
                    "statutory_hierarchy": row.get("statutory_hierarchy", ""),
                    "article_number": int(row.get("article_number", 0)),
                    "article_number_raw": str(
                        row.get("article_number_raw") or row.get("article_number", "")
                    ),
                    "raw_content": row.get("raw_content", ""),
                    "official_spij_url": row.get("official_spij_url") or "",
                    "semantic_similarity": float(row.get("semantic_similarity", 0.0)),
                    "combined_score": float(row.get("combined_score", 0.0)),
                    "is_synthetic_template": bool(metadata.get("is_synthetic_template", False)),
                }
            )
        return normalized
