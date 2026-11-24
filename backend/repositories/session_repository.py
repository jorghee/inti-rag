"""Session, query log, and citation repositories backed by Supabase PostgREST."""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.repositories.exceptions import ForbiddenAccessError, ResourceNotFoundError
from backend.repositories.supabase_client import SupabaseClient, supabase_client


class SessionRepository(ABC):
    """Abstract interface for user query session and log persistence."""

    @abstractmethod
    def resolve_user_id(self, user_id: str, email: str, full_name: str, role: str) -> str:
        """Resolve and ensure the persistence user identifier for an authenticated user."""

    @abstractmethod
    def create_session(self, user_id: str, session_title: str) -> Dict[str, Any]:
        """Create a new query session for a user."""

    @abstractmethod
    def list_sessions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """List all sessions owned by a user ordered by most recent activity."""

    @abstractmethod
    def get_session(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Retrieve a session and its logs with ownership validation."""

    @abstractmethod
    def delete_session(self, session_id: str, user_id: str) -> None:
        """Delete a session owned by the user."""

    @abstractmethod
    def create_query_log(
        self,
        *,
        session_id: str,
        user_query: str,
        assistant_response: str,
        response_latency_ms: float,
        prompt_tokens: int,
        completion_tokens: int,
        model_used: str,
    ) -> Dict[str, Any]:
        """Persist a query/response turn and update session activity timestamp."""

    @abstractmethod
    def create_citations(
        self,
        query_log_id: str,
        citations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Persist grounded citation references for a query log."""


class SupabaseSessionRepository(SessionRepository):
    """Production session repository persisting to Supabase PostgreSQL via PostgREST."""

    def __init__(self, client: Optional[SupabaseClient] = None) -> None:
        self._client = client or supabase_client

    def resolve_user_id(self, user_id: str, email: str, full_name: str, role: str) -> str:
        return self._client.ensure_user_profile(
            user_id=user_id,
            email=email,
            full_name=full_name,
            role=role,
        )

    def create_session(self, user_id: str, session_title: str) -> Dict[str, Any]:
        payload = {
            "user_id": user_id,
            "session_title": session_title,
        }
        rows = self._client.request(
            "POST",
            "/rest/v1/query_sessions",
            json_body=payload,
            extra_headers={"Prefer": "return=representation"},
        )
        session = rows[0] if isinstance(rows, list) and rows else rows
        session["query_count"] = 0
        return session

    def list_sessions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        rows = self._client.request(
            "GET",
            "/rest/v1/query_sessions",
            params={
                "select": "id,user_id,session_title,started_at,last_active_at,query_logs(count)",
                "user_id": f"eq.{user_id}",
                "order": "last_active_at.desc",
                "limit": str(limit),
            },
        )
        sessions: List[Dict[str, Any]] = []
        for row in rows or []:
            log_meta = row.pop("query_logs", [])
            count = log_meta[0].get("count", 0) if isinstance(log_meta, list) and log_meta else 0
            row["query_count"] = int(count)
            sessions.append(row)
        return sessions

    def get_session(self, session_id: str, user_id: str) -> Dict[str, Any]:
        rows = self._client.request(
            "GET",
            "/rest/v1/query_sessions",
            params={
                "select": "id,user_id,session_title,started_at,last_active_at",
                "id": f"eq.{session_id}",
                "limit": "1",
            },
        )
        if not rows:
            raise ResourceNotFoundError("La sesion solicitada no existe.")

        session = rows[0]
        if str(session["user_id"]) != str(user_id):
            raise ForbiddenAccessError("No tiene permisos para acceder a esta sesion.")

        log_rows = self._client.request(
            "GET",
            "/rest/v1/query_logs",
            params={
                "select": (
                    "id,session_id,user_query,assistant_response,response_latency_ms,"
                    "prompt_tokens,completion_tokens,model_used,created_at,"
                    "citation_refs(id,chunk_id,similarity_score,inline_citation_index,"
                    "legal_chunks(article_number,article_number_raw,statutory_hierarchy,"
                    "official_spij_url))"
                ),
                "session_id": f"eq.{session_id}",
                "order": "created_at.asc",
            },
        )

        formatted_logs: List[Dict[str, Any]] = []
        for log in log_rows or []:
            raw_citations = log.pop("citation_refs", []) or []
            citations: List[Dict[str, Any]] = []
            for cit in raw_citations:
                chunk_info = cit.get("legal_chunks") or {}
                citations.append(
                    {
                        "id": cit["id"],
                        "chunk_id": cit["chunk_id"],
                        "article_number": chunk_info.get("article_number"),
                        "article_number_raw": chunk_info.get("article_number_raw"),
                        "statutory_hierarchy": chunk_info.get("statutory_hierarchy"),
                        "official_spij_url": chunk_info.get("official_spij_url"),
                        "similarity_score": float(cit.get("similarity_score", 0.0)),
                        "inline_citation_index": int(cit.get("inline_citation_index", 1)),
                    }
                )
            citations.sort(key=lambda item: item["inline_citation_index"])
            log["citations"] = citations
            formatted_logs.append(log)

        session["logs"] = formatted_logs
        return session

    def delete_session(self, session_id: str, user_id: str) -> None:
        # Verify ownership before deletion to preserve explicit 404 vs 403 semantics
        self.get_session(session_id, user_id)
        self._client.request(
            "DELETE",
            "/rest/v1/query_sessions",
            params={"id": f"eq.{session_id}", "user_id": f"eq.{user_id}"},
        )

    def create_query_log(
        self,
        *,
        session_id: str,
        user_query: str,
        assistant_response: str,
        response_latency_ms: float,
        prompt_tokens: int,
        completion_tokens: int,
        model_used: str,
    ) -> Dict[str, Any]:
        payload = {
            "session_id": session_id,
            "user_query": user_query,
            "assistant_response": assistant_response,
            "response_latency_ms": round(response_latency_ms, 2),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "model_used": model_used,
        }
        rows = self._client.request(
            "POST",
            "/rest/v1/query_logs",
            json_body=payload,
            extra_headers={"Prefer": "return=representation"},
        )
        log = rows[0] if isinstance(rows, list) and rows else rows

        # Touch parent session last_active_at
        self._client.request(
            "PATCH",
            "/rest/v1/query_sessions",
            params={"id": f"eq.{session_id}"},
            json_body={"last_active_at": datetime.now(timezone.utc).isoformat()},
        )
        log["citations"] = []
        return log

    def create_citations(
        self,
        query_log_id: str,
        citations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if not citations:
            return []
        payload = [
            {
                "query_log_id": query_log_id,
                "chunk_id": cit["chunk_id"],
                "similarity_score": round(float(cit.get("similarity_score", 0.0)), 4),
                "inline_citation_index": int(cit.get("inline_citation_index", idx + 1)),
            }
            for idx, cit in enumerate(citations)
        ]
        rows = self._client.request(
            "POST",
            "/rest/v1/citation_refs",
            json_body=payload,
            extra_headers={"Prefer": "return=representation"},
        )
        return rows if isinstance(rows, list) else []


class InMemorySessionRepository(SessionRepository):
    """In-memory session repository intended strictly for automated tests."""

    def __init__(self) -> None:
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._logs: Dict[str, List[Dict[str, Any]]] = {}

    def resolve_user_id(self, user_id: str, email: str, full_name: str, role: str) -> str:
        return user_id

    def create_session(self, user_id: str, session_title: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        sid = str(uuid.uuid4())
        session = {
            "id": sid,
            "user_id": user_id,
            "session_title": session_title,
            "started_at": now,
            "last_active_at": now,
            "query_count": 0,
        }
        self._sessions[sid] = session
        self._logs[sid] = []
        return dict(session)

    def list_sessions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        owned = [
            {**s, "query_count": len(self._logs.get(s["id"], []))}
            for s in self._sessions.values()
            if s["user_id"] == user_id
        ]
        owned.sort(key=lambda item: item["last_active_at"], reverse=True)
        return owned[:limit]

    def get_session(self, session_id: str, user_id: str) -> Dict[str, Any]:
        session = self._sessions.get(session_id)
        if not session:
            raise ResourceNotFoundError("La sesion solicitada no existe.")
        if session["user_id"] != user_id:
            raise ForbiddenAccessError("No tiene permisos para acceder a esta sesion.")
        return {**session, "logs": list(self._logs.get(session_id, []))}

    def delete_session(self, session_id: str, user_id: str) -> None:
        self.get_session(session_id, user_id)
        self._sessions.pop(session_id, None)
        self._logs.pop(session_id, None)

    def create_query_log(
        self,
        *,
        session_id: str,
        user_query: str,
        assistant_response: str,
        response_latency_ms: float,
        prompt_tokens: int,
        completion_tokens: int,
        model_used: str,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        log = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "user_query": user_query,
            "assistant_response": assistant_response,
            "response_latency_ms": round(response_latency_ms, 2),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "model_used": model_used,
            "created_at": now,
            "citations": [],
        }
        self._logs.setdefault(session_id, []).append(log)
        if session_id in self._sessions:
            self._sessions[session_id]["last_active_at"] = now
        return dict(log)

    def create_citations(
        self,
        query_log_id: str,
        citations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        saved: List[Dict[str, Any]] = []
        for idx, cit in enumerate(citations):
            entry = {
                "id": str(uuid.uuid4()),
                "chunk_id": cit["chunk_id"],
                "article_number": cit.get("article_number"),
                "article_number_raw": cit.get("article_number_raw"),
                "statutory_hierarchy": cit.get("statutory_hierarchy"),
                "official_spij_url": cit.get("official_spij_url"),
                "similarity_score": round(float(cit.get("similarity_score", 0.0)), 4),
                "inline_citation_index": int(cit.get("inline_citation_index", idx + 1)),
            }
            saved.append(entry)
        for logs in self._logs.values():
            for log in logs:
                if log["id"] == query_log_id:
                    log["citations"] = saved
        return saved
