"""Integration test suite ensuring 100% coverage and integrity of the Civil Code corpus."""

from pathlib import Path

from ingestion.coverage_validator import (
    TOTAL_CIVIL_CODE_ARTICLES,
    CivilCodeCoverageValidator,
)


def test_civil_code_complete_100_percent_coverage():
    """Verify that the extracted Peruvian Civil Code achieves 100.0% coverage without gaps."""
    fixture_path = Path("ingestion/fixtures/spij_civil_code_mirror.html")
    assert fixture_path.is_file(), f"Expected fixture mirror not found at {fixture_path}"

    validator = CivilCodeCoverageValidator()
    report = validator.validate_file(fixture_path)

    # 1. Total article count and coverage checks
    assert report.total_expected == TOTAL_CIVIL_CODE_ARTICLES
    assert report.total_extracted_numeric == TOTAL_CIVIL_CODE_ARTICLES
    assert report.coverage_percentage == 100.0

    # 2. Sequential integrity (no gaps between 1 and 2122)
    assert len(report.missing_articles) == 0, f"Missing: {report.missing_articles}"

    # 3. Preliminary title integrity (Articles I through X)
    assert report.total_preliminary == 10
    assert len(report.missing_preliminary) == 0

    # 4. Truncation and emptiness checks
    assert len(report.empty_or_truncated_articles) == 0, (
        f"Truncated articles: {report.empty_or_truncated_articles[:10]}"
    )

    # 5. Hierarchy mapping check
    assert len(report.hierarchy_discrepancies) == 0

    # 6. Overall validity
    assert report.is_valid is True
    assert "VALID" in report.summary


def test_civil_code_landmark_articles_content():
    """Verify landmark articles of Peruvian civil law contain substantive legal content."""
    fixture_path = Path("ingestion/fixtures/spij_civil_code_mirror.html")
    validator = CivilCodeCoverageValidator()
    report = validator.validate_file(fixture_path)
    assert report.is_valid is True

    # Re-validate with direct text checks on key milestones
    content = fixture_path.read_text(encoding="utf-8")

    landmark_provisions = [
        "Articulo 1.- Sujeto de Derecho",
        "Articulo 140.- Nocion de Acto Juridico",
        "Articulo 219.- Causales de nulidad",
        "Articulo 923.- Definicion del derecho de propiedad",
        "Articulo 949.- Transferencia de propiedad de bien inmueble",
        "Articulo 1351.- Nocion de contrato",
        "Articulo 1529.- Definicion de compraventa",
        "Articulo 1969.- Indemnizacion por dolo o culpa",
        "Articulo 1970.- Responsabilidad por riesgo",
        "Articulo 2001.- Plazos de prescripcion",
        "Articulo 2122.- Vigencia del Codigo",
    ]

    for provision in landmark_provisions:
        assert provision in content, f"Missing landmark provision: {provision}"
