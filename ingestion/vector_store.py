"""Vector store adapter for storing and querying statutory chunks in Supabase pgvector."""

import hashlib
import json
import logging
import math
import uuid
from pathlib import Path
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


EMBEDDINGS_CACHE_FILE = Path("data/processed/civil_code_embeddings.json")


def generate_openrouter_embeddings(
    texts: List[str],
    batch_size: int = 50,
    model: str = "openai/text-embedding-3-small",
) -> List[List[float]]:
    """Generate 1536d semantic embeddings via OpenRouter API with local disk caching."""
    api_key = settings.OPENROUTER_API_KEY
    if not api_key or "dummy" in api_key.lower():
        logger.info("Using deterministic fallback embeddings (dummy OpenRouter key)")
        return [generate_deterministic_embedding(t) for t in texts]

    all_embeddings: List[List[float]] = []

    # Check local cache first to resume or return complete embeddings
    if EMBEDDINGS_CACHE_FILE.is_file():
        try:
            cached_data = json.loads(EMBEDDINGS_CACHE_FILE.read_text(encoding="utf-8"))
            if isinstance(cached_data, list):
                if len(cached_data) == len(texts):
                    logger.info(
                        "Loaded all %d semantic embeddings from cache: %s",
                        len(cached_data),
                        EMBEDDINGS_CACHE_FILE,
                    )
                    return cached_data
                elif len(cached_data) < len(texts):
                    all_embeddings = cached_data
                    logger.info(
                        "Resuming embedding generation from chunk %d of %d",
                        len(all_embeddings),
                        len(texts),
                    )
        except Exception as exc:
            logger.warning("Failed reading embeddings cache (%s). Will re-fetch.", exc)
            all_embeddings = []

    url = "https://openrouter.ai/api/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    start_idx = len(all_embeddings)
    with httpx.Client(timeout=45.0) as client:
        for i in range(start_idx, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            payload = {"model": model, "input": batch}
            batch_embeddings: Optional[List[List[float]]] = None

            for attempt in range(1, 4):
                try:
                    resp = client.post(url, headers=headers, json=payload)
                    resp.raise_for_status()
                    data = resp.json()["data"]
                    batch_embeddings = [item["embedding"] for item in data]
                    break
                except Exception as exc:
                    logger.warning(
                        "OpenRouter attempt %d/3 failed for batch %d..%d: %s",
                        attempt,
                        i + 1,
                        min(i + batch_size, len(texts)),
                        exc,
                    )
                    import time
                    time.sleep(2.0 * attempt)

            if batch_embeddings is None:
                logger.error(
                    "Using deterministic fallback for batch %d..%d",
                    i + 1,
                    min(i + batch_size, len(texts)),
                )
                batch_embeddings = [generate_deterministic_embedding(t) for t in batch]

            all_embeddings.extend(batch_embeddings)
            logger.info(
                "Progress: %d / %d embeddings generated (%.1f%%)",
                len(all_embeddings),
                len(texts),
                (len(all_embeddings) / len(texts)) * 100.0,
            )

            # Incrementally persist cache
            try:
                EMBEDDINGS_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
                EMBEDDINGS_CACHE_FILE.write_text(json.dumps(all_embeddings), encoding="utf-8")
            except Exception as cache_exc:
                logger.debug("Incremental cache write error: %s", cache_exc)

    return all_embeddings


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

        if (
            embeddings is None
            and self.use_remote
            and not settings.OPENROUTER_API_KEY.startswith("sk-or-dummy")
        ):
            logger.info(
                "Generating real 1536d semantic embeddings via OpenRouter for %d chunks...",
                len(chunks),
            )
            texts = [c.composite_text for c in chunks]
            embeddings = generate_openrouter_embeddings(texts)

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
                "metadata": chunk.metadata,
                "embedding": embedding,
            }

            self._local_chunks[record_key] = record
            upserted_count += 1

        if self.use_remote and not settings.SUPABASE_URL.startswith("https://xyzcompany"):
            self._sync_remote(list(self._local_chunks.values()))

        return upserted_count

    def _sync_remote(self, records: List[Dict[str, Any]], batch_size: int = 100) -> None:
        """Sync records to Supabase PostgREST endpoint in batches with idempotent merge."""
        url = (
            f"{self.supabase_url}/rest/v1/legal_chunks"
            "?on_conflict=statute_code,article_number_raw,sub_chunk_index"
        )
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates",
        }
        total = len(records)
        synced = 0
        try:
            with httpx.Client(timeout=45.0) as client:
                for i in range(0, total, batch_size):
                    batch = records[i : i + batch_size]
                    resp = client.post(url, headers=headers, json=batch)
                    resp.raise_for_status()
                    synced += len(batch)
                    logger.info("Synced %d / %d chunks to Supabase Cloud", synced, total)
        except Exception as exc:
            logger.warning("Remote Supabase synchronization skipped: %s", exc)
            raise

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
