"""Unit tests for SPIJ asynchronous HTTP client, rate limiting, and backoff."""

import asyncio
import time

import httpx
import pytest

from ingestion.spij_client import SpijClient


def test_spij_client_default_headers():
    """Verify default headers include institutional User-Agent."""

    async def _test():
        client = SpijClient()
        try:
            assert "IntiLegalAssistant" in client.user_agent
            assert "@unsa.edu.pe" in client.user_agent
        finally:
            await client.close()

    asyncio.run(_test())


def test_calculate_backoff_delay():
    """Verify exponential backoff calculation increases monotonically."""

    async def _test():
        client = SpijClient(backoff_base=1.5)
        try:
            delay_1 = client.calculate_backoff_delay(1)
            delay_2 = client.calculate_backoff_delay(2)
            delay_3 = client.calculate_backoff_delay(3)

            assert 1.5 <= delay_1 <= 2.2
            assert 3.0 <= delay_2 <= 3.8
            assert 6.0 <= delay_3 <= 6.8
            assert delay_1 < delay_2 < delay_3
        finally:
            await client.close()

    asyncio.run(_test())


def test_enforce_politeness_delay():
    """Verify sequential requests maintain minimum delay spacing."""

    async def _test():
        client = SpijClient(min_delay_seconds=0.1)
        try:
            t0 = time.monotonic()
            await client._enforce_politeness_delay()
            await client._enforce_politeness_delay()
            elapsed = time.monotonic() - t0
            assert elapsed >= 0.09
        finally:
            await client.close()

    asyncio.run(_test())


def test_retry_on_429_rate_limit():
    """Verify client retries when receiving HTTP 429 Too Many Requests and succeeds."""

    async def _test():
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(429, text="Rate limit exceeded")
            return httpx.Response(200, text="<html>Success</html>")

        transport = httpx.MockTransport(handler)
        client = SpijClient(
            transport=transport,
            min_delay_seconds=0.01,
            backoff_base=0.05,
            max_retries=2,
        )
        async with client:
            resp = await client.get("/test-rate-limit")
            assert resp.status_code == 200
            assert resp.text == "<html>Success</html>"
            assert call_count == 2

    asyncio.run(_test())


def test_retry_on_503_service_unavailable():
    """Verify client retries on 503 and recovers."""

    async def _test():
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(503, text="Service Unavailable")
            return httpx.Response(200, text="<html>Recovered</html>")

        transport = httpx.MockTransport(handler)
        client = SpijClient(
            transport=transport,
            min_delay_seconds=0.01,
            backoff_base=0.05,
            max_retries=2,
        )
        async with client:
            resp = await client.get("/test-503")
            assert resp.status_code == 200
            assert resp.text == "<html>Recovered</html>"
            assert call_count == 2

    asyncio.run(_test())


def test_exhausted_retries_raises_http_status_error():
    """Verify client raises error after exceeding max retries on persistent 429."""

    async def _test():
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, text="Persistent Rate Limit")

        transport = httpx.MockTransport(handler)
        client = SpijClient(
            transport=transport,
            min_delay_seconds=0.01,
            backoff_base=0.02,
            max_retries=2,
        )
        async with client:
            with pytest.raises(httpx.HTTPStatusError):
                await client.get("/test-exhausted")

    asyncio.run(_test())
