"""Asynchronous HTTP client for the official SPIJ portal with adaptive rate limiting and backoff."""

import asyncio
import logging
import random
import time
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger("inti.ingestion.spij_client")


class SpijClient:
    """Async HTTP client adhering to SPIJ rate limits and polite scraping protocols.

    Implements:
    - Minimum request interval (politeness pause >= 1.5s).
    - Exponential backoff for HTTP 429 (Too Many Requests) and 503 (Service Unavailable).
    - Jitter to avoid thundering herd conditions.
    - Institutional User-Agent header.
    """

    DEFAULT_USER_AGENT = "IntiLegalAssistant/1.0 (UNSA Academic Research; contacto@unsa.edu.pe)"

    def __init__(
        self,
        base_url: str = "https://spij.minjus.gob.pe",
        timeout: float = 30.0,
        min_delay_seconds: float = 1.5,
        max_retries: int = 3,
        backoff_base: float = 1.5,
        user_agent: Optional[str] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.min_delay_seconds = min_delay_seconds
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self._last_request_time: float = 0.0

        headers = {
            "User-Agent": self.user_agent,
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "application/json;q=0.8,*/*;q=0.7"
            ),
            "Accept-Language": "es-PE,es;q=0.9,en;q=0.8",
        }

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
            headers=headers,
            follow_redirects=True,
            transport=transport,
        )

    async def __aenter__(self) -> "SpijClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close underlying httpx AsyncClient session."""
        await self._client.aclose()

    async def _enforce_politeness_delay(self) -> float:
        """Ensure minimum delay interval elapsed since previous request."""
        now = time.monotonic()
        elapsed = now - self._last_request_time
        sleep_needed = self.min_delay_seconds - elapsed

        if sleep_needed > 0:
            await asyncio.sleep(sleep_needed)
            actual_delay = sleep_needed
        else:
            actual_delay = 0.0

        self._last_request_time = time.monotonic()
        return actual_delay

    def calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with random jitter:

        delay = base * (2 ** (attempt - 1)) + uniform(0.1, 0.5)
        """
        exponent = max(0, attempt - 1)
        jitter = random.uniform(0.1, 0.5)
        return (self.backoff_base * (2**exponent)) + jitter

    async def get(
        self,
        endpoint_or_url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Execute async GET request with rate limiting and retry backoff.

        Raises:
            httpx.HTTPStatusError: On unrecoverable 4xx or 5xx HTTP response.
            httpx.RequestError: When network or connection retries are exhausted.
        """
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 2):
            # Enforce sequential request spacing
            await self._enforce_politeness_delay()

            try:
                response = await self._client.get(
                    endpoint_or_url,
                    params=params,
                    headers=headers,
                )

                # Retry on rate limiting (429) or temporary server unavailability (503)
                if response.status_code in (429, 503):
                    if attempt <= self.max_retries:
                        backoff = self.calculate_backoff_delay(attempt)
                        logger.warning(
                            "SPIJ server responded with HTTP %d. Attempt %d/%d. Waiting %.2fs...",
                            response.status_code,
                            attempt,
                            self.max_retries,
                            backoff,
                        )
                        await asyncio.sleep(backoff)
                        continue
                    response.raise_for_status()

                # Raise for any other 4xx/5xx status
                response.raise_for_status()
                return response

            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as exc:
                last_error = exc
                if attempt <= self.max_retries:
                    backoff = self.calculate_backoff_delay(attempt)
                    logger.warning(
                        "Network transient error (%s). Attempt %d/%d. Waiting %.2fs...",
                        type(exc).__name__,
                        attempt,
                        self.max_retries,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    continue
                break

        if last_error:
            raise last_error

        raise httpx.RequestError(
            f"Exhausted maximum retries ({self.max_retries}) accessing {endpoint_or_url}"
        )
