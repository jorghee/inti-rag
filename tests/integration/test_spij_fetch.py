"""Integration tests for Civil Code extraction and telemetry logging workflow."""

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from ingestion.fetch_civil_code import (
    OFFICIAL_SPIJ_URL,
    STATUTE_CODE,
    fetch_civil_code,
)
from ingestion.spij_client import SpijClient


def test_fetch_civil_code_force_mirror(tmp_path: Path):
    """Verify downloading civil code via offline mirror fixture generates valid telemetry."""

    async def _test():
        output_html = tmp_path / "codigo_civil.html"
        log_json = tmp_path / "telemetry.json"

        telemetry = await fetch_civil_code(
            output_path=output_html,
            log_path=log_json,
            force_fallback=True,
        )

        # 1. Output file verification
        assert output_html.is_file()
        content = output_html.read_text(encoding="utf-8")
        assert "DECRETO LEGISLATIVO Nº 295" in content
        assert "Articulo 1.- Sujeto de Derecho" in content
        assert "Articulo 1969" in content
        assert "Articulo 2122" in content
        assert len(content) > 100_000

        # 2. Telemetry JSON verification
        assert log_json.is_file()
        saved_log = json.loads(log_json.read_text(encoding="utf-8"))
        assert saved_log["statute_code"] == STATUTE_CODE
        assert saved_log["official_spij_url"] == OFFICIAL_SPIJ_URL
        assert saved_log["source"] == "official_spij_mirror_fallback"
        assert saved_log["http_status"] == 200
        assert saved_log["bytes_extracted"] == len(content.encode("utf-8"))
        assert len(saved_log["sha256"]) == 64
        assert saved_log["status"] == "success"
        assert telemetry["sha256"] == saved_log["sha256"]

    asyncio.run(_test())


def test_fetch_civil_code_mock_live_download(tmp_path: Path):
    """Verify live download path with simulated 200 OK SPIJ response."""

    async def _test():
        fake_html = "<html><body><h1>DECRETO LEGISLATIVO 295</h1><p>Articulo 1</p></body></html>"

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text=fake_html)

        transport = httpx.MockTransport(handler)
        client = SpijClient(
            transport=transport,
            min_delay_seconds=0.01,
        )

        output_html = tmp_path / "mock_civil_code.html"
        log_json = tmp_path / "mock_telemetry.json"

        telemetry = await fetch_civil_code(
            output_path=output_html,
            log_path=log_json,
            client=client,
            allow_fallback=False,
        )

        assert output_html.read_text(encoding="utf-8") == fake_html
        assert telemetry["source"] == "spij_live"
        assert telemetry["http_status"] == 200

    asyncio.run(_test())


def test_fetch_civil_code_remote_failure_without_fallback(tmp_path: Path):
    """Verify exception is raised when remote fails and fallback is prohibited."""

    async def _test():
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="Internal Server Error")

        transport = httpx.MockTransport(handler)
        client = SpijClient(
            transport=transport,
            min_delay_seconds=0.01,
            max_retries=1,
            backoff_base=0.01,
        )

        output_html = tmp_path / "failed.html"
        log_json = tmp_path / "failed_log.json"

        with pytest.raises(httpx.HTTPStatusError):
            await fetch_civil_code(
                output_path=output_html,
                log_path=log_json,
                client=client,
                allow_fallback=False,
            )

    asyncio.run(_test())
