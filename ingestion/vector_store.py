"""Vector store adapter for storing and querying statutory chunks in Supabase pgvector."""

import hashlib
import logging
import math
import uuid
from typing import Any, Dict, List, Optional

import httpx

from backend.core.config import settings
from ingestion.chunker import LegalChunk

logger = logging.getLogger("inti.ingestion.vector_store")

EMBEDDING_DIM = 1536


def generate_deterministic_embedding(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """Generate a deterministic 1536-dimensional normalized vector for offline testing."""
    hasher = hashlib.sha256()
    raw_vec: List[float] = []

    for i in range(dim):
        hasher.update(f"{text}:{i}".encode("utf-8"))
        digest = hasher.digest()
        val = (int.from_bytes(digest[:4], "big") / (2**32)) - 0.5
        raw_vec.append(val)

    # Normalize to unit length for cosine similarity
    norm = math.sqrt(sum(x * x for x in raw_vec))
    if norm > 0:
        return [x / norm for x in raw_vec]
    return raw_vec


class LegalChunksVectorStore:
    """Vector store repository managing statutory chunks and pgvector embeddings."""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        service_role_key: Optional[str] = None,
        use_remote: bool = False,
    ) -> None:
        self.supabase_url = (supabase_url or settings.SUPABASE_URL).rstrip("/")
        self.service_role_key = service_role_key or settings.SUPABASE_SERVICE_ROLE_KEY
        self.use_remote = use_remote
        # In-memory storage for offline execution, testing, and CI
        self._local_chunks: Dict[str, Dict[str, Any]] = {}

    def upsert_chunks(
        self,
        chunks: List[LegalChunk],
        embeddings: Optional[List[List[float]]] = None,
    ) -> int:
        """Idempotently insert or update statutory chunks with their embeddings.

        Matches database constraint UNIQUE(statute_code, article_number).
        """
        if not chunks:
            return 0

        upserted_count = 0
        for idx, chunk in enumerate(chunks):
            embedding = (
                embeddings[idx]
                if embeddings and idx < len(embeddings)
                else generate_deterministic_embedding(chunk.composite_text)
            )

            record_key = f"{chunk.statute_code}:{chunk.article_number_raw}:{chunk.sub_chunk_index}"
            record: Dict[str, Any] = {
                "id": str(uuid.uuid4()),
                "statute_code": chunk.statute_code,
                "statutory_hierarchy": chunk.statutory_hierarchy,
                "article_number": chunk.article_number,
                "article_number_raw": chunk.article_number_raw,
                "raw_content": chunk.raw_content,
                "official_spij_url": chunk.official_spij_url,
                "composite_text": chunk.composite_text,
                "sub_chunk_index": chunk.sub_chunk_index,
                "total_words": chunk.total_words,
                "embedding": embedding,
            }

            self._local_chunks[record_key] = record
            upserted_count += 1

        if self.use_remote and not settings.SUPABASE_URL.startswith("https://xyzcompany"):
            self._sync_remote(list(self._local_chunks.values()))

        return upserted_count

    def _sync_remote(self, records: List[Dict[str, Any]]) -> None:
        """Sync records to Supabase PostgREST endpoint."""
        url = f"{self.supabase_url}/rest/v1/legal_chunks"
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates",
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, headers=headers, json=records[:100])
                resp.raise_for_status()
        except Exception as exc:
            logger.warning("Remote Supabase synchronization skipped: %s", exc)

    def count(self, statute_code: str = "CODIGO_CIVIL_1984") -> int:
        """Count stored chunks for a given statute."""
        return sum(1 for r in self._local_chunks.values() if r["statute_code"] == statute_code)

    def get_by_article(
        self, article_number: int, article_number_raw: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve chunk by numeric article identifier, prioritizing exact numeric string match."""
        if article_number_raw is not None:
            for r in self._local_chunks.values():
                if r["article_number_raw"] == article_number_raw and r["sub_chunk_index"] == 0:
                    return r
            return None

        for r in self._local_chunks.values():
            if (
                r["article_number"] == article_number
                and r["article_number_raw"] == str(article_number)
                and r["sub_chunk_index"] == 0
            ):
                return r

        for r in self._local_chunks.values():
            if r["article_number"] == article_number and r["sub_chunk_index"] == 0:
                return r
        return None

    def get_by_raw_article(self, article_number_raw: str) -> Optional[Dict[str, Any]]:
        """Retrieve chunk by raw article identifier (e.g., '1', 'I', '2A')."""
        for r in self._local_chunks.values():
            if r["article_number_raw"] == article_number_raw and r["sub_chunk_index"] == 0:
                return r
        return None

    def query_similar(
        self,
        query_embedding: List[float],
        threshold: float = 0.75,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Query nearest neighbor statutory chunks using cosine similarity."""
        results: List[Dict[str, Any]] = []

        for record in self._local_chunks.values():
            vec = record["embedding"]
            similarity = sum(a * b for a, b in zip(query_embedding, vec))
            if similarity >= threshold:
                results.append({**record, "similarity": round(similarity, 4)})

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]


# Global instance for shared access
vector_store = LegalChunksVectorStore()
