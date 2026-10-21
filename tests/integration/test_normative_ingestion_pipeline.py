"""Integration test suite for the end-to-end statutory ingestion pipeline."""

import asyncio
import json
import tempfile
from pathlib import Path

from ingestion.pipeline import run_statutory_ingestion
from ingestion.vector_store import LegalChunksVectorStore


def test_statutory_ingestion_pipeline_end_to_end() -> None:
    """Test full execution of statutory ingestion pipeline using offline mirror."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_path = Path(tmp_dir) / "test_pipeline_summary.json"
        store = LegalChunksVectorStore()

        summary = asyncio.run(
            run_statutory_ingestion(
                force_mirror=True,
                allow_network=False,
                store=store,
                log_output_path=log_path,
            )
        )

        # Assert status and coverage metrics
        assert summary.status == "success"
        assert summary.statute_code == "CODIGO_CIVIL_1984"
        assert summary.numeric_articles_count == 2122
        assert summary.preliminary_articles_count == 10
        assert summary.coverage_percentage == 100.0
        assert summary.errors_count == 0
        assert summary.vector_store_upserted >= 2132
        assert summary.duration_seconds > 0

        # Assert vector store content
        assert store.count() >= 2132
        article_1 = store.get_by_article(1)
        assert article_1 is not None
        assert "persona humana" in article_1["raw_content"]
        assert len(article_1["embedding"]) == 1536

        article_i = store.get_by_raw_article("I")
        assert article_i is not None
        assert "Abrogacion de la ley" in article_i["raw_content"]

        article_1969 = store.get_by_article(1969)
        assert article_1969 is not None
        assert "dolo o culpa" in article_1969["raw_content"]

        # Assert JSON telemetry output was generated
        assert log_path.exists()
        logged_data = json.loads(log_path.read_text(encoding="utf-8"))
        assert logged_data["statute_code"] == "CODIGO_CIVIL_1984"
        assert logged_data["coverage_percentage"] == 100.0
        assert logged_data["status"] == "success"


def test_statutory_ingestion_idempotency() -> None:
    """Test executing the ingestion pipeline multiple times does not produce duplicate vectors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_path = Path(tmp_dir) / "test_idempotency_summary.json"
        store = LegalChunksVectorStore()

        # First ingestion run
        summary_1 = asyncio.run(
            run_statutory_ingestion(
                force_mirror=True,
                allow_network=False,
                store=store,
                log_output_path=log_path,
            )
        )
        count_first_run = store.count()

        # Second ingestion run (idempotent re-run)
        summary_2 = asyncio.run(
            run_statutory_ingestion(
                force_mirror=True,
                allow_network=False,
                store=store,
                log_output_path=log_path,
            )
        )
        count_second_run = store.count()

        assert count_second_run == count_first_run
        assert summary_1.vector_store_upserted == summary_2.vector_store_upserted
