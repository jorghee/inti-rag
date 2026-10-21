"""End-to-end automated statutory ingestion pipeline for the Peruvian Civil Code."""

import argparse
import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from ingestion.chunker import LegalChunk, parse_statute
from ingestion.cleaning import clean_legal_text
from ingestion.coverage_validator import CivilCodeCoverageValidator
from ingestion.fetch_civil_code import fetch_civil_code
from ingestion.vector_store import LegalChunksVectorStore, vector_store

logger = logging.getLogger("inti.ingestion.pipeline")

DEFAULT_LOG_PATH = Path("data/raw/ingestion_pipeline_summary.json")


@dataclass
class IngestionPipelineSummary:
    """Summary metrics of an end-to-end statutory ingestion run."""

    statute_code: str
    total_chunks_extracted: int
    numeric_articles_count: int
    preliminary_articles_count: int
    coverage_percentage: float
    vector_store_upserted: int
    duration_seconds: float
    status: str
    errors_count: int
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert summary dataclass to dictionary."""
        return asdict(self)


async def run_statutory_ingestion(
    force_mirror: bool = True,
    allow_network: bool = False,
    store: Optional[LegalChunksVectorStore] = None,
    log_output_path: Optional[Path] = None,
) -> IngestionPipelineSummary:
    """Execute end-to-end statutory ingestion pipeline:

    1. Download / fetch raw HTML from SPIJ.
    2. Sanitize and normalize statutory legal text.
    3. Hierarchical segmentation into atomic chunks with statutory hierarchy.
    4. Comprehensive coverage validation (100% of articles 1..2122 + preliminary).
    5. Generate dense 1536d embeddings and idempotent upsert into vector store.
    6. Record telemetry log.
    """
    t0 = time.monotonic()
    logger.info("Starting statutory ingestion pipeline for CODIGO_CIVIL_1984...")

    target_store = store or vector_store
    target_log = log_output_path or DEFAULT_LOG_PATH

    # Step 1: Extraction / Download
    telemetry = await fetch_civil_code(
        force_fallback=force_mirror or not allow_network,
        allow_fallback=True,
    )
    raw_html_path = Path(telemetry["output_file"])
    raw_html = raw_html_path.read_text(encoding="utf-8")

    # Step 2: Sanitization and Normalization
    logger.info("Sanitizing and normalizing raw statutory HTML...")
    cleaned_text = clean_legal_text(raw_html)

    # Step 3: Hierarchical Chunking
    logger.info("Parsing statutory hierarchy (Libro > Seccion > Titulo > Capitulo > Articulo)...")
    chunks: list[LegalChunk] = parse_statute(cleaned_text)
    logger.info("Generated %d statutory chunks", len(chunks))

    # Step 4: Coverage and Integrity Validation
    logger.info("Executing statutory coverage and consistency audit...")
    validator = CivilCodeCoverageValidator()
    coverage_report = validator.validate_chunks(chunks)

    if not coverage_report.is_valid:
        logger.warning("Coverage audit warning: %s", coverage_report.summary)

    # Step 5: Vector Store Idempotent Upsert
    logger.info("Generating 1536d embeddings and upserting into pgvector store...")
    upserted_count = target_store.upsert_chunks(chunks)
    logger.info("Successfully upserted %d chunks into vector store", upserted_count)

    duration = time.monotonic() - t0
    status = "success" if coverage_report.is_valid else "warning_discrepancy"
    errors_count = len(coverage_report.missing_articles) + len(
        coverage_report.empty_or_truncated_articles
    )

    summary = IngestionPipelineSummary(
        statute_code="CODIGO_CIVIL_1984",
        total_chunks_extracted=len(chunks),
        numeric_articles_count=coverage_report.total_extracted_numeric,
        preliminary_articles_count=coverage_report.total_preliminary,
        coverage_percentage=coverage_report.coverage_percentage,
        vector_store_upserted=upserted_count,
        duration_seconds=round(duration, 3),
        status=status,
        errors_count=errors_count,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    # Step 6: Telemetry Log Persistence
    target_log.parent.mkdir(parents=True, exist_ok=True)
    target_log.write_text(json.dumps(summary.to_dict(), indent=2), encoding="utf-8")
    logger.info(
        "Ingestion pipeline completed in %.2fs. Total articles: %d (%.1f%% coverage)",
        duration,
        summary.total_chunks_extracted,
        summary.coverage_percentage,
    )

    return summary


def main() -> None:
    """CLI execution entrypoint for statutory ingestion pipeline."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(
        description="Run end-to-end statutory ingestion for Peruvian Civil Code.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Attempt live SPIJ download before falling back to mirror fixture.",
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=DEFAULT_LOG_PATH,
        help="Destination path for pipeline summary JSON.",
    )

    args = parser.parse_args()

    asyncio.run(
        run_statutory_ingestion(
            force_mirror=not args.live,
            allow_network=args.live,
            log_output_path=args.log,
        )
    )


if __name__ == "__main__":
    main()
