"""Unit tests for the vector store adapter and embedding generation."""

import pytest

from ingestion.chunker import LegalChunk
from ingestion.vector_store import (
    EMBEDDING_DIM,
    LegalChunksVectorStore,
    generate_deterministic_embedding,
)


def _sample_chunk(
    article_num: int = 1,
    sub_chunk_index: int = 0,
    raw_content: str = "La persona humana es sujeto de derecho desde su nacimiento.",
) -> LegalChunk:
    return LegalChunk(
        statute_code="CODIGO_CIVIL_1984",
        statutory_hierarchy=(
            "LIBRO I: DERECHO DE LAS PERSONAS > SECCION PRIMERA > TITULO I > Articulo 1"
        ),
        article_number=article_num,
        article_number_raw=str(article_num),
        raw_content=raw_content,
        official_spij_url=f"https://spij.minjus.gob.pe/spij-ext-web/#/detallenorma/H682687#art{article_num}",
        composite_text=f"LIBRO I... Articulo {article_num}. {raw_content}",
        sub_chunk_index=sub_chunk_index,
        total_words=len(raw_content.split()),
    )


def test_deterministic_embedding_properties() -> None:
    """Test that embedding generation produces normalized 1536d vectors."""
    text = (
        "Artículo 1969. Aquel que por dolo o culpa causa un daño a otro "
        "está obligado a indemnizarlo."
    )
    emb1 = generate_deterministic_embedding(text)
    emb2 = generate_deterministic_embedding(text)

    assert len(emb1) == EMBEDDING_DIM
    assert emb1 == emb2  # Deterministic repeatability

    # Check unit norm (length ~ 1.0)
    norm = sum(x * x for x in emb1) ** 0.5
    assert pytest.approx(norm, rel=1e-5) == 1.0


def test_vector_store_empty_upsert() -> None:
    """Test upserting empty chunk list."""
    store = LegalChunksVectorStore()
    count = store.upsert_chunks([])
    assert count == 0
    assert store.count() == 0


def test_vector_store_upsert_and_retrieve() -> None:
    """Test upserting chunks and retrieving by article number."""
    store = LegalChunksVectorStore()
    chunk1 = _sample_chunk(article_num=1)
    chunk2 = _sample_chunk(article_num=2, raw_content="La vida humana comienza con la concepción.")

    upserted = store.upsert_chunks([chunk1, chunk2])
    assert upserted == 2
    assert store.count() == 2

    retrieved1 = store.get_by_article(1)
    assert retrieved1 is not None
    assert retrieved1["article_number"] == 1
    assert "persona humana" in retrieved1["raw_content"]
    assert len(retrieved1["embedding"]) == EMBEDDING_DIM

    retrieved_none = store.get_by_article(9999)
    assert retrieved_none is None


def test_vector_store_idempotency_updates_without_duplicates() -> None:
    """Test that re-upserting an updated chunk updates the record in-place."""
    store = LegalChunksVectorStore()
    chunk = _sample_chunk(article_num=1, raw_content="Version original")
    store.upsert_chunks([chunk])
    assert store.count() == 1
    assert store.get_by_article(1)["raw_content"] == "Version original"

    # Update article content
    updated_chunk = _sample_chunk(article_num=1, raw_content="Version modificada por ley")
    store.upsert_chunks([updated_chunk])

    assert store.count() == 1  # No duplicate
    assert store.get_by_article(1)["raw_content"] == "Version modificada por ley"


def test_vector_store_query_similar() -> None:
    """Test nearest neighbor query based on cosine similarity."""
    store = LegalChunksVectorStore()
    chunk1 = _sample_chunk(
        article_num=1969,
        raw_content="Responsabilidad extracontractual por dolo o culpa.",
    )
    chunk2 = _sample_chunk(
        article_num=1970,
        raw_content="Aquel que mediante un bien riesgoso causa un daño.",
    )
    store.upsert_chunks([chunk1, chunk2])

    query_emb = generate_deterministic_embedding(chunk1.composite_text)
    results = store.query_similar(query_emb, threshold=0.75, top_k=2)

    assert len(results) >= 1
    assert results[0]["article_number"] == 1969
    assert results[0]["similarity"] >= 0.99
