"""Thin HTTP client for Supabase PostgREST, RPC, and Auth Admin endpoints."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from backend.core.config import settings
from backend.repositories.exceptions import RepositoryError, StorageUnavailableError

logger = logging.getLogger("inti.repositories.supabase")


class SupabaseClient:
    """Low-level client wrapping Supabase REST, RPC, and GoTrue Admin APIs."""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        service_role_key: Optional[str] = None,
        timeout: float = 15.0,
    ) -> None:
        self.base_url = (supabase_url or settings.SUPABASE_URL).rstrip("/")
        self.service_role_key = service_role_key or settings.SUPABASE_SERVICE_ROLE_KEY
        self.timeout = timeout

    def _ensure_configured(self) -> None:
        if (
            not self.base_url
            or "xyzcompany.supabase.co" in self.base_url
            or "dummy" in self.service_role_key.lower()
        ):
            raise StorageUnavailableError(
                "Supabase no esta configurado con credenciales reales en el entorno."
            )

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
        }
        if extra:
            headers.update(extra)
        return headers

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Any] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Execute an HTTP request against Supabase and decode JSON responses."""
        self._ensure_configured()
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=self._headers(extra_headers),
                    params=params,
                    json=json_body,
                )
        except httpx.RequestError as exc:
            logger.error("Supabase network error (%s %s): %s", method, path, exc)
            raise StorageUnavailableError(
                "No se pudo conectar con Supabase Cloud (verifique red o estado del proyecto)."
            ) from exc

        if response.status_code >= 500:
            logger.error("Supabase server error %d: %s", response.status_code, response.text[:300])
            raise StorageUnavailableError(
                f"Supabase devolvio un error interno ({response.status_code})."
            )

        if response.status_code >= 400:
            raise RepositoryError(
                f"Error de Supabase ({response.status_code}): {response.text[:300]}"
            )

        if not response.content:
            return None
        return response.json()

    def rpc(self, function_name: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Invoke a PostgreSQL RPC function via PostgREST."""
        data = self.request("POST", f"/rest/v1/rpc/{function_name}", json_body=payload)
        return data if isinstance(data, list) else []

    def ensure_user_profile(
        self,
        user_id: str,
        email: str,
        full_name: str,
        role: str,
    ) -> str:
        """Ensure the user exists in auth.users and public.profiles, returning the profile UUID.

        If the email already exists in public.profiles under a different UUID, returns that
        existing UUID so foreign key references on query_sessions remain consistent.
        """
        self._ensure_configured()
        existing = self.request(
            "GET",
            "/rest/v1/profiles",
            params={"select": "id,email", "email": f"eq.{email.lower()}", "limit": "1"},
        )
        if isinstance(existing, list) and existing:
            return str(existing[0]["id"])

        # Create user via GoTrue Admin API; the on_auth_user_created trigger populates profiles.
        url = f"{self.base_url}/auth/v1/admin/users"
        admin_payload = {
            "id": user_id,
            "email": email.lower(),
            "email_confirm": True,
            "user_metadata": {
                "full_name": full_name or email.split("@")[0],
                "role": role if role in ("student", "docent", "faculty", "admin") else "student",
            },
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, headers=self._headers(), json=admin_payload)
        except httpx.RequestError as exc:
            raise StorageUnavailableError(
                "No se pudo conectar con Supabase Auth para aprovisionar el perfil."
            ) from exc

        if resp.status_code in (200, 201):
            created = resp.json()
            return str(created.get("id", user_id))

        # Re-check profiles in case of concurrent creation
        recheck = self.request(
            "GET",
            "/rest/v1/profiles",
            params={"select": "id", "email": f"eq.{email.lower()}", "limit": "1"},
        )
        if isinstance(recheck, list) and recheck:
            return str(recheck[0]["id"])

        raise RepositoryError(
            f"No se pudo aprovisionar el perfil en Supabase ({resp.status_code}): {resp.text[:250]}"
        )


supabase_client = SupabaseClient()
