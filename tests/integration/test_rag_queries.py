"""Integration tests for HU-01 partial hybrid RAG grounding and guardrails."""

from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.repositories.legal_chunks_repository import LegalChunksRepository
from backend.repositories.session_repository import InMemorySessionRepository
from backend.services.rag_service import (
    OUT_OF_SCOPE_REFUSAL,
    SYNTHETIC_ONLY_REFUSAL,
    RagService,
    get_rag_service,
)
from backend.services.session_service import SessionService, get_session_service


class _StubChunksRepository(LegalChunksRepository):
    """Deterministic stub returning configurable chunk sets for guardrail tests."""

    def __init__(self, rows: List[Dict[str, Any]]) -> None:
        self._rows = rows

    def search_hybrid(
        self,
        query_text: str,
        query_embedding: List[float],
        match_count: int = 5,
    ) -> List[Dict[str, Any]]:
        return self._rows[:match_count]


def _login_headers(
    client: TestClient, email: str, password: str = "Password123*"
) -> Dict[str, str]:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def isolated_env():
    """Provide an isolated in-memory SessionService and reset overrides afterwards."""
    session_repo = InMemorySessionRepository()
    sess_svc = SessionService(repository=session_repo)
    app.dependency_overrides[get_session_service] = lambda: sess_svc
    yield sess_svc
    app.dependency_overrides.clear()


def test_query_grounded_and_persisted_in_history(isolated_env: SessionService) -> None:
    """Verify grounded RAG query persists log and citations into user history."""
    chunks_repo = _StubChunksRepository(
        [
            {
                "chunk_id": "22222222-2222-4222-8222-222222222201",
                "statute_code": "CODIGO_CIVIL_1984",
                "statutory_hierarchy": "Libro VII > Contratos > Compraventa",
                "article_number": 1529,
                "article_number_raw": "1529",
                "raw_content": (
                    "Por la compraventa el vendedor se obliga a transferir la propiedad."
                ),
                "official_spij_url": (
                    "https://spij.minjus.gob.pe/spij-ext-web/#/detallenorma/H682695"
                ),
                "semantic_similarity": 0.86,
                "combined_score": 0.032,
                "is_synthetic_template": False,
            }
        ]
    )
    rag_svc = RagService(
        chunks_repository=chunks_repo,
        sessions=isolated_env,
        embed_fn=lambda _: [0.01] * 1536,
        synthesize_fn=lambda _sys, _usr: (
            "El vendedor se obliga a transferir la propiedad del bien [Código Civil, Art. 1529].",
            120,
            25,
            "deepseek/deepseek-chat",
        ),
    )
    app.dependency_overrides[get_rag_service] = lambda: rag_svc

    client = TestClient(app)
    headers = _login_headers(client, "jariasq@unsa.edu.pe")

    resp = client.post(
        "/api/v1/queries",
        headers=headers,
        json={"query": "¿Qué obliga al vendedor en una compraventa?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["grounded"] is True
    assert body["out_of_scope"] is False
    assert len(body["citations"]) == 1
    assert body["citations"][0]["article_number_raw"] == "1529"

    detail = client.get(f"/api/v1/sessions/{body['session_id']}", headers=headers)
    assert detail.status_code == 200
    assert len(detail.json()["logs"]) == 1
    assert detail.json()["logs"][0]["citations"][0]["article_number"] == 1529


def test_query_refuses_out_of_scope_and_synthetic_only_chunks(
    isolated_env: SessionService,
) -> None:
    """Verify deterministic refusals without calling LLM when chunks are low-score or synthetic."""
    llm_called = False

    def _fail_if_called(_sys: str, _usr: str):
        nonlocal llm_called
        llm_called = True
        return ("should not run", 0, 0, "none")

    client = TestClient(app)
    headers = _login_headers(client, "jariasq@unsa.edu.pe")

    # Case 1: Out of scope (low similarity)
    app.dependency_overrides[get_rag_service] = lambda: RagService(
        chunks_repository=_StubChunksRepository(
            [
                {
                    "chunk_id": "22222222-2222-4222-8222-222222222202",
                    "statute_code": "CODIGO_CIVIL_1984",
                    "statutory_hierarchy": "Libro I",
                    "article_number": 1,
                    "article_number_raw": "1",
                    "raw_content": "La persona humana es sujeto de derecho.",
                    "official_spij_url": "https://spij.minjus.gob.pe",
                    "semantic_similarity": 0.21,
                    "combined_score": 0.004,
                    "is_synthetic_template": False,
                }
            ]
        ),
        sessions=isolated_env,
        embed_fn=lambda _: [0.01] * 1536,
        synthesize_fn=_fail_if_called,
    )
    r_oos = client.post(
        "/api/v1/queries",
        headers=headers,
        json={"query": "¿Cómo funciona el régimen aduanero de importación temporal?"},
    )
    assert r_oos.status_code == 200
    assert r_oos.json()["out_of_scope"] is True
    assert r_oos.json()["answer"] == OUT_OF_SCOPE_REFUSAL
    assert llm_called is False

    # Case 2: Only synthetic template chunks returned
    app.dependency_overrides[get_rag_service] = lambda: RagService(
        chunks_repository=_StubChunksRepository(
            [
                {
                    "chunk_id": "22222222-2222-4222-8222-222222222203",
                    "statute_code": "CODIGO_CIVIL_1984",
                    "statutory_hierarchy": "Libro IV",
                    "article_number": 691,
                    "article_number_raw": "691",
                    "raw_content": "Disposicion legal y normativa correspondiente al articulo 691.",
                    "official_spij_url": "https://spij.minjus.gob.pe",
                    "semantic_similarity": 0.81,
                    "combined_score": 0.025,
                    "is_synthetic_template": True,
                }
            ]
        ),
        sessions=isolated_env,
        embed_fn=lambda _: [0.01] * 1536,
        synthesize_fn=_fail_if_called,
    )
    r_syn = client.post(
        "/api/v1/queries",
        headers=headers,
        json={"query": "¿Qué establece el artículo 691 del Código Civil?"},
    )
    assert r_syn.status_code == 200
    assert r_syn.json()["contains_synthetic_chunks"] is True
    assert r_syn.json()["answer"] == SYNTHETIC_ONLY_REFUSAL
    assert llm_called is False

    # Case 3: Explicit synthetic article requested even when a real chunk is also returned
    app.dependency_overrides[get_rag_service] = lambda: RagService(
        chunks_repository=_StubChunksRepository(
            [
                {
                    "chunk_id": "22222222-2222-4222-8222-222222222204",
                    "statute_code": "CODIGO_CIVIL_1984",
                    "statutory_hierarchy": "Libro I",
                    "article_number": 1,
                    "article_number_raw": "1",
                    "raw_content": "La persona humana es sujeto de derecho.",
                    "official_spij_url": "https://spij.minjus.gob.pe",
                    "semantic_similarity": 0.48,
                    "combined_score": 0.025,
                    "is_synthetic_template": False,
                },
                {
                    "chunk_id": "22222222-2222-4222-8222-222222222203",
                    "statute_code": "CODIGO_CIVIL_1984",
                    "statutory_hierarchy": "Libro IV",
                    "article_number": 691,
                    "article_number_raw": "691",
                    "raw_content": "Disposicion legal y normativa correspondiente al articulo 691.",
                    "official_spij_url": "https://spij.minjus.gob.pe",
                    "semantic_similarity": 0.74,
                    "combined_score": 0.011,
                    "is_synthetic_template": True,
                },
            ]
        ),
        sessions=isolated_env,
        embed_fn=lambda _: [0.01] * 1536,
        synthesize_fn=_fail_if_called,
    )
    r_explicit_syn = client.post(
        "/api/v1/queries",
        headers=headers,
        json={"query": "¿Qué establece el artículo 691 del Código Civil?"},
    )
    assert r_explicit_syn.status_code == 200
    assert r_explicit_syn.json()["answer"] == SYNTHETIC_ONLY_REFUSAL
    assert llm_called is False


def test_query_allows_colloquial_hybrid_match_above_calibrated_floor(
    isolated_env: SessionService,
) -> None:
    """Verify colloquial queries with strong RRF score pass the 0.35 semantic floor."""
    app.dependency_overrides[get_rag_service] = lambda: RagService(
        chunks_repository=_StubChunksRepository(
            [
                {
                    "chunk_id": "22222222-2222-4222-8222-222222222205",
                    "statute_code": "CODIGO_CIVIL_1984",
                    "statutory_hierarchy": "Libro VII > Contratos Nominados > Compraventa",
                    "article_number": 1529,
                    "article_number_raw": "1529",
                    "raw_content": (
                        "Por la compraventa el vendedor se obliga a transferir la propiedad "
                        "de un bien al comprador y este a pagar su precio en dinero."
                    ),
                    "official_spij_url": (
                        "https://spij.minjus.gob.pe/spij-ext-web/#/detallenorma/H682695"
                    ),
                    "semantic_similarity": 0.4091,
                    "combined_score": 0.0325,
                    "is_synthetic_template": False,
                }
            ]
        ),
        sessions=isolated_env,
        embed_fn=lambda _: [0.01] * 1536,
        synthesize_fn=lambda _sys, _usr: (
            "El comprador debe pagar el precio en dinero [Código Civil, Art. 1529].",
            110,
            20,
            "openai/gpt-6-luna",
        ),
    )

    client = TestClient(app)
    headers = _login_headers(client, "jariasq@unsa.edu.pe")
    resp = client.post(
        "/api/v1/queries",
        headers=headers,
        json={"query": "qué consideraciones debería tener como comprador"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["grounded"] is True
    assert body["out_of_scope"] is False
    assert body["citations"][0]["article_number_raw"] == "1529"
