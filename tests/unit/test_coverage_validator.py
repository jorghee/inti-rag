"""Unit tests for CivilCodeCoverageValidator verifying gaps and truncation detection."""

from ingestion.chunker import LegalChunk
from ingestion.coverage_validator import CivilCodeCoverageValidator


def _make_mock_chunk(
    article_number: int,
    article_number_raw: str,
    raw_content: str = "Disposicion legal completa y suficiente del articulo correspondiente.",
    hierarchy: str = "Libro I > Titulo I",
    sub_chunk_index: int = 0,
) -> LegalChunk:
    """Helper to instantiate a mock LegalChunk."""
    return LegalChunk(
        statute_code="CODIGO_CIVIL_1984",
        statutory_hierarchy=hierarchy,
        article_number=article_number,
        article_number_raw=article_number_raw,
        raw_content=raw_content,
        official_spij_url="https://spij.minjus.gob.pe",
        composite_text=f"{hierarchy} - Art. {article_number_raw}: {raw_content}",
        sub_chunk_index=sub_chunk_index,
        total_words=len(raw_content.split()),
    )


def test_validator_empty_chunks():
    """Verify validator handles empty chunk input gracefully and reports 0% coverage."""
    validator = CivilCodeCoverageValidator(expected_total=10)
    report = validator.validate_chunks([])

    assert report.is_valid is False
    assert report.coverage_percentage == 0.0
    assert report.total_extracted_numeric == 0
    assert len(report.missing_articles) == 10


def test_validator_detects_missing_numeric_articles():
    """Verify missing articles in sequence are correctly identified in report."""
    validator = CivilCodeCoverageValidator(expected_total=5)
    # Provide articles 1, 2, 4, 5 (missing 3) plus all 10 preliminary
    chunks = [_make_mock_chunk(n, str(n)) for n in [1, 2, 4, 5]]
    for rom in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]:
        chunks.append(_make_mock_chunk(0, rom, hierarchy="Título PRELIMINAR"))

    report = validator.validate_chunks(chunks)

    assert report.is_valid is False
    assert report.missing_articles == [3]
    assert report.coverage_percentage == 80.0
    assert len(report.missing_preliminary) == 0


def test_validator_detects_empty_or_truncated_article():
    """Verify articles with insufficient length or word count are flagged as truncated."""
    validator = CivilCodeCoverageValidator(expected_total=3)
    chunks = [
        _make_mock_chunk(1, "1", raw_content="Texto valido y suficiente para el articulo primero."),
        _make_mock_chunk(2, "2", raw_content="Corto"),  # Truncated (< 15 chars)
        _make_mock_chunk(3, "3", raw_content="Texto valido y suficiente para el articulo tercero."),
    ]
    for rom in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]:
        chunks.append(_make_mock_chunk(0, rom, hierarchy="Título PRELIMINAR"))

    report = validator.validate_chunks(chunks)

    assert report.is_valid is False
    assert len(report.empty_or_truncated_articles) == 1
    assert "Art. 2" in report.empty_or_truncated_articles[0]


def test_validator_detects_missing_preliminary_articles():
    """Verify missing Roman numeral preliminary articles are identified."""
    validator = CivilCodeCoverageValidator(expected_total=2)
    chunks = [
        _make_mock_chunk(1, "1"),
        _make_mock_chunk(2, "2"),
    ]
    # Only supply preliminary I and II (missing III through X)
    chunks.append(_make_mock_chunk(0, "I", hierarchy="Título PRELIMINAR"))
    chunks.append(_make_mock_chunk(0, "II", hierarchy="Título PRELIMINAR"))

    report = validator.validate_chunks(chunks)

    assert report.is_valid is False
    assert "III" in report.missing_preliminary
    assert "X" in report.missing_preliminary
    assert len(report.missing_preliminary) == 8


def test_validator_detects_empty_hierarchy():
    """Verify articles with missing or blank statutory hierarchy are flagged."""
    validator = CivilCodeCoverageValidator(expected_total=2)
    chunks = [
        _make_mock_chunk(1, "1", hierarchy="   "),  # Empty hierarchy
        _make_mock_chunk(2, "2", hierarchy="Libro I > Titulo I"),
    ]
    for rom in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]:
        chunks.append(_make_mock_chunk(0, rom, hierarchy="Título PRELIMINAR"))

    report = validator.validate_chunks(chunks)

    assert report.is_valid is False
    assert len(report.hierarchy_discrepancies) == 1
    assert "Art. 1" in report.hierarchy_discrepancies[0]


def test_validator_success_on_complete_mock_norm():
    """Verify 100% complete and consistent mock norm passes validation."""
    validator = CivilCodeCoverageValidator(expected_total=3)
    chunks = [
        _make_mock_chunk(1, "1"),
        _make_mock_chunk(2, "2"),
        _make_mock_chunk(3, "3"),
    ]
    for rom in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]:
        chunks.append(_make_mock_chunk(0, rom, hierarchy="Título PRELIMINAR"))

    report = validator.validate_chunks(chunks)

    assert report.is_valid is True
    assert report.coverage_percentage == 100.0
    assert len(report.missing_articles) == 0
    assert len(report.missing_preliminary) == 0
    assert len(report.empty_or_truncated_articles) == 0
    assert len(report.hierarchy_discrepancies) == 0
    assert "VALID" in report.summary
