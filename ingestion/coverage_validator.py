"""Validation suite for statutory coverage and consistency of the Peruvian Civil Code."""

import argparse
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Set

from ingestion.chunker import LegalChunk, parse_statute
from ingestion.cleaning import clean_legal_text

logger = logging.getLogger("inti.ingestion.coverage_validator")

TOTAL_CIVIL_CODE_ARTICLES = 2122
EXPECTED_PRELIMINARY_ARTICLES = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X")
MIN_ARTICLE_CONTENT_LENGTH = 15
MIN_ARTICLE_WORD_COUNT = 3


@dataclass
class CoverageAuditReport:
    """Structured audit report for statutory coverage and content integrity."""

    statute_code: str
    total_expected: int
    total_extracted_numeric: int
    total_preliminary: int
    total_chunks: int
    coverage_percentage: float
    missing_articles: List[int] = field(default_factory=list)
    duplicate_articles: List[int] = field(default_factory=list)
    missing_preliminary: List[str] = field(default_factory=list)
    empty_or_truncated_articles: List[str] = field(default_factory=list)
    hierarchy_discrepancies: List[str] = field(default_factory=list)
    is_valid: bool = False
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary format for JSON serialization."""
        return asdict(self)


class CivilCodeCoverageValidator:
    """Audits Peruvian Civil Code extraction to ensure 100% coverage without truncation."""

    def __init__(
        self,
        expected_total: int = TOTAL_CIVIL_CODE_ARTICLES,
        min_content_length: int = MIN_ARTICLE_CONTENT_LENGTH,
        min_word_count: int = MIN_ARTICLE_WORD_COUNT,
    ) -> None:
        self.expected_total = expected_total
        self.min_content_length = min_content_length
        self.min_word_count = min_word_count

    def validate_chunks(self, chunks: List[LegalChunk]) -> CoverageAuditReport:
        """Analyze parsed LegalChunks for complete statutory coverage and integrity.

        Checks:
        1. Range coverage: Articles 1 through 2122 present without numeric gaps.
        2. Título Preliminar: Articles I through X present.
        3. No empty or truncated articles: Exceed minimum length and word count.
        4. Hierarchy assignment: Assigned to identifiable statutory Book or Title.
        """
        if not chunks:
            return CoverageAuditReport(
                statute_code="CODIGO_CIVIL_1984",
                total_expected=self.expected_total,
                total_extracted_numeric=0,
                total_preliminary=0,
                total_chunks=0,
                coverage_percentage=0.0,
                missing_articles=list(range(1, self.expected_total + 1)),
                missing_preliminary=list(EXPECTED_PRELIMINARY_ARTICLES),
                is_valid=False,
                summary="Validation failed: Chunk list is completely empty.",
            )

        numeric_articles_seen: Set[int] = set()
        numeric_counts: Dict[int, int] = {}
        preliminary_seen: Set[str] = set()
        empty_or_truncated: List[str] = []
        hierarchy_discrepancies: List[str] = []

        for chunk in chunks:
            raw_num = chunk.article_number_raw.strip().upper()
            body = chunk.raw_content.strip()

            # 1. Truncation / empty content check
            word_count = len(body.split())
            if len(body) < self.min_content_length or word_count < self.min_word_count:
                empty_or_truncated.append(f"Art. {raw_num} (len={len(body)}, words={word_count})")

            # 2. Hierarchy assignment check
            if not chunk.statutory_hierarchy or chunk.statutory_hierarchy.strip() == "":
                hierarchy_discrepancies.append(f"Art. {raw_num} has empty hierarchy")

            # 3. Categorize numeric vs preliminary
            is_prelim = (
                raw_num in EXPECTED_PRELIMINARY_ARTICLES
                or "PRELIMINAR" in chunk.statutory_hierarchy.upper()
            )
            if is_prelim:
                preliminary_seen.add(raw_num)
            elif chunk.article_number > 0 and raw_num.isdigit():
                num = chunk.article_number
                numeric_articles_seen.add(num)
                numeric_counts[num] = numeric_counts.get(num, 0) + 1

        # Calculate missing articles
        expected_set = set(range(1, self.expected_total + 1))
        missing_numeric = sorted(list(expected_set - numeric_articles_seen))
        missing_prelim = sorted(list(set(EXPECTED_PRELIMINARY_ARTICLES) - preliminary_seen))

        # Check unexpected duplicates (excluding multi-chunk mega-articles)
        primary_chunks_by_num: Dict[int, int] = {}
        for c in chunks:
            if c.sub_chunk_index == 0 and c.article_number > 0 and c.article_number_raw.isdigit():
                current_c = primary_chunks_by_num.get(c.article_number, 0)
                primary_chunks_by_num[c.article_number] = current_c + 1
        duplicates = [num for num, count in primary_chunks_by_num.items() if count > 1]

        coverage_pct = round((len(numeric_articles_seen) / self.expected_total) * 100.0, 2)
        is_valid = (
            coverage_pct == 100.0
            and len(missing_numeric) == 0
            and len(missing_prelim) == 0
            and len(empty_or_truncated) == 0
            and len(hierarchy_discrepancies) == 0
        )

        summary_parts = [
            f"Coverage: {coverage_pct}% ({len(numeric_articles_seen)}/{self.expected_total} arts)",
            f"Preliminary articles: {len(preliminary_seen)}/10",
            f"Missing articles: {len(missing_numeric)}",
            f"Empty/Truncated: {len(empty_or_truncated)}",
            f"Hierarchy issues: {len(hierarchy_discrepancies)}",
            f"Status: {'VALID' if is_valid else 'INVALID'}",
        ]
        summary = " | ".join(summary_parts)

        return CoverageAuditReport(
            statute_code=chunks[0].statute_code if chunks else "CODIGO_CIVIL_1984",
            total_expected=self.expected_total,
            total_extracted_numeric=len(numeric_articles_seen),
            total_preliminary=len(preliminary_seen),
            total_chunks=len(chunks),
            coverage_percentage=coverage_pct,
            missing_articles=missing_numeric,
            duplicate_articles=duplicates,
            missing_preliminary=missing_prelim,
            empty_or_truncated_articles=empty_or_truncated,
            hierarchy_discrepancies=hierarchy_discrepancies,
            is_valid=is_valid,
            summary=summary,
        )

    def validate_html(self, raw_html: str) -> CoverageAuditReport:
        """Clean raw HTML, parse into hierarchical chunks, and run audit."""
        clean_text = clean_legal_text(raw_html)
        chunks = parse_statute(clean_text)
        return self.validate_chunks(chunks)

    def validate_file(self, file_path: Path) -> CoverageAuditReport:
        """Validate an HTML or text file on disk."""
        if not file_path.is_file():
            raise FileNotFoundError(f"Target file does not exist: {file_path}")
        content = file_path.read_text(encoding="utf-8")
        if file_path.suffix.lower() in (".html", ".htm"):
            return self.validate_html(content)
        chunks = parse_statute(content)
        return self.validate_chunks(chunks)


def main() -> None:
    """CLI execution entrypoint for coverage auditing."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(
        description="Audit statutory coverage and integrity of the Peruvian Civil Code.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw/codigo_civil_1984.html"),
        help="Input HTML file to validate.",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=None,
        help="Optional path to output JSON coverage report.",
    )

    args = parser.parse_args()
    validator = CivilCodeCoverageValidator()
    report = validator.validate_file(args.input)

    logger.info("Validation Result: %s", report.summary)
    if not report.is_valid:
        if report.missing_articles:
            logger.error("Missing articles (first 20): %s", report.missing_articles[:20])
        if report.empty_or_truncated_articles:
            logger.error(
                "Truncated articles (first 20): %s",
                report.empty_or_truncated_articles[:20],
            )

    if args.report_json:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        args.report_json.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
        logger.info("Saved coverage report to %s", args.report_json)

    if not report.is_valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
