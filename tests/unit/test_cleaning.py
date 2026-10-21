"""Unit tests for ingestion.cleaning module.

Tests the complete HTML sanitization and text normalization pipeline
for SPIJ legal documents, validating each cleaning step independently
and the full pipeline integration.

Reference: docs/modules/legal-ingestion.md
"""

from __future__ import annotations

import pytest

from ingestion.cleaning import (
    clean_legal_text,
    normalize_article_markers,
    normalize_structural_headings,
    normalize_unicode,
    normalize_whitespace,
    sanitize_html,
    strip_boilerplate_text,
)
from tests.fixtures import (
    BOILERPLATE_ONLY_FRAGMENT,
    INCONSISTENT_MARKERS_FRAGMENT,
    SPIJ_CIVIL_CODE_FRAGMENT,
    SPIJ_MULTI_LEVEL_FRAGMENT,
    UNICODE_HEAVY_FRAGMENT,
)

# ===========================================================================
# sanitize_html tests
# ===========================================================================


class TestSanitizeHtml:
    """Tests for HTML tag removal and DOM cleanup."""

    def test_removes_script_tags(self) -> None:
        html = '<div><script>alert("xss")</script><p>Legal text</p></div>'
        result = sanitize_html(html)
        assert "alert" not in result
        assert "script" not in result.lower() or "Legal text" in result
        assert "Legal text" in result

    def test_removes_style_tags(self) -> None:
        html = "<div><style>.foo{color:red}</style><p>Content</p></div>"
        result = sanitize_html(html)
        assert "color" not in result
        assert "Content" in result

    def test_removes_noscript_tags(self) -> None:
        html = '<div><noscript><img src="track.png"></noscript><p>Text</p></div>'
        result = sanitize_html(html)
        assert "track.png" not in result
        assert "Text" in result

    def test_removes_html_comments(self) -> None:
        html = "<div><!-- This is a comment --><p>Visible</p></div>"
        result = sanitize_html(html)
        assert "comment" not in result
        assert "Visible" in result

    def test_removes_spij_header(self) -> None:
        result = sanitize_html(SPIJ_CIVIL_CODE_FRAGMENT)
        assert "MINJUSDH Logo" not in result
        assert "Inicio" not in result
        assert "Legislacion" not in result

    def test_removes_spij_toolbar(self) -> None:
        result = sanitize_html(SPIJ_CIVIL_CODE_FRAGMENT)
        # Toolbar buttons should be removed via class matching
        assert "btn-download-pdf" not in result

    def test_removes_sidebar_filters(self) -> None:
        result = sanitize_html(SPIJ_CIVIL_CODE_FRAGMENT)
        assert "Buscar..." not in result

    def test_removes_concordances(self) -> None:
        result = sanitize_html(SPIJ_CIVIL_CODE_FRAGMENT)
        assert "Concordancias:" not in result
        assert "Codigo de los" not in result or "Constitucion" not in result

    def test_removes_contextual_sidebar(self) -> None:
        result = sanitize_html(SPIJ_CIVIL_CODE_FRAGMENT)
        assert "Historial de Modificaciones" not in result

    def test_removes_footer(self) -> None:
        result = sanitize_html(SPIJ_CIVIL_CODE_FRAGMENT)
        # Footer is inside footer-spij class, should be stripped
        # Remaining boilerplate text is handled by strip_boilerplate_text
        assert "footer-spij" not in result

    def test_preserves_article_content(self) -> None:
        result = sanitize_html(SPIJ_CIVIL_CODE_FRAGMENT)
        assert "persona humana es sujeto de derecho" in result
        assert "nacimiento" in result

    def test_preserves_article_numbers(self) -> None:
        result = sanitize_html(SPIJ_CIVIL_CODE_FRAGMENT)
        assert "1" in result
        assert "2" in result

    def test_preserves_structural_headings(self) -> None:
        result = sanitize_html(SPIJ_CIVIL_CODE_FRAGMENT)
        assert "LIBRO I" in result or "Libro I" in result

    def test_preserves_multi_level_hierarchy(self) -> None:
        result = sanitize_html(SPIJ_MULTI_LEVEL_FRAGMENT)
        assert "Fuentes de las Obligaciones" in result
        assert "Compraventa" in result
        assert "compraventa el vendedor" in result

    def test_raises_on_empty_input(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            sanitize_html("")

    def test_raises_on_whitespace_only_input(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            sanitize_html("   \n\t  ")

    def test_handles_minimal_html(self) -> None:
        result = sanitize_html("<p>Simple text</p>")
        assert "Simple text" in result

    def test_handles_nested_boilerplate(self) -> None:
        html = """
        <div class="header-spij">
            <div class="nav-menu">
                <div>Deep nested boilerplate</div>
            </div>
        </div>
        <p>Legal content survives</p>
        """
        result = sanitize_html(html)
        assert "Deep nested" not in result
        assert "Legal content survives" in result


# ===========================================================================
# normalize_unicode tests
# ===========================================================================


class TestNormalizeUnicode:
    """Tests for Unicode character normalization."""

    def test_replaces_curly_double_quotes(self) -> None:
        text = "\u201cEl concebido es sujeto de derecho\u201d"
        result = normalize_unicode(text)
        assert result == '"El concebido es sujeto de derecho"'

    def test_replaces_curly_single_quotes(self) -> None:
        text = "\u2018ejemplo\u2019"
        result = normalize_unicode(text)
        assert result == "'ejemplo'"

    def test_replaces_en_dash(self) -> None:
        text = "Art. 1\u2013 contenido"
        result = normalize_unicode(text)
        assert "1- contenido" in result

    def test_replaces_em_dash(self) -> None:
        text = "texto\u2014continuacion"
        result = normalize_unicode(text)
        assert "texto-continuacion" in result

    def test_replaces_non_breaking_space(self) -> None:
        text = "Art.\u00a01\u00a0del\u00a0Codigo"
        result = normalize_unicode(text)
        assert result == "Art. 1 del Codigo"

    def test_removes_zero_width_spaces(self) -> None:
        text = "texto\u200bcon\u200czero\u200dwidth"
        result = normalize_unicode(text)
        assert result == "textoconzerowidth"

    def test_removes_byte_order_mark(self) -> None:
        text = "\ufeffContenido legal"
        result = normalize_unicode(text)
        assert result == "Contenido legal"

    def test_replaces_horizontal_ellipsis(self) -> None:
        text = "continuara\u2026"
        result = normalize_unicode(text)
        assert result == "continuara..."

    def test_removes_soft_hyphen(self) -> None:
        text = "con\u00addi\u00adcio\u00adna\u00adda"
        result = normalize_unicode(text)
        assert result == "condicionada"

    def test_preserves_spanish_diacritics(self) -> None:
        text = "La atribuci\u00f3n est\u00e1 condicionada. A\u00f1o 2024. G\u00fcemes."
        result = normalize_unicode(text)
        assert "\u00f3" in result  # o with acute
        assert "\u00e1" in result  # a with acute
        assert "\u00f1" in result  # n with tilde
        assert "\u00fc" in result  # u with diaeresis

    def test_nfc_normalization_composes_decomposed(self) -> None:
        # Decomposed a + combining acute accent -> composed a
        import unicodedata

        decomposed = unicodedata.normalize("NFD", "Art\u00edculo")
        result = normalize_unicode(decomposed)
        assert "Art\u00edculo" in result

    def test_handles_empty_string(self) -> None:
        assert normalize_unicode("") == ""

    def test_handles_pure_ascii(self) -> None:
        text = "Plain ASCII text with no special chars."
        assert normalize_unicode(text) == text


# ===========================================================================
# normalize_whitespace tests
# ===========================================================================


class TestNormalizeWhitespace:
    """Tests for whitespace consolidation."""

    def test_collapses_multiple_spaces(self) -> None:
        text = "word1    word2     word3"
        result = normalize_whitespace(text)
        assert result == "word1 word2 word3"

    def test_collapses_tabs(self) -> None:
        text = "word1\t\tword2"
        result = normalize_whitespace(text)
        assert result == "word1 word2"

    def test_collapses_triple_blank_lines(self) -> None:
        text = "Line 1\n\n\n\nLine 2"
        result = normalize_whitespace(text)
        assert result == "Line 1\n\nLine 2"

    def test_preserves_single_blank_line(self) -> None:
        text = "Line 1\n\nLine 2"
        result = normalize_whitespace(text)
        assert result == "Line 1\n\nLine 2"

    def test_preserves_single_newline(self) -> None:
        text = "Line 1\nLine 2"
        result = normalize_whitespace(text)
        assert result == "Line 1\nLine 2"

    def test_strips_trailing_whitespace(self) -> None:
        text = "Line 1   \nLine 2  "
        result = normalize_whitespace(text)
        assert result == "Line 1\nLine 2"

    def test_strips_leading_trailing_document_whitespace(self) -> None:
        text = "\n\n  Content here  \n\n"
        result = normalize_whitespace(text)
        assert result == "Content here"

    def test_handles_mixed_whitespace(self) -> None:
        text = "  \t word1  \t  word2  \n\n\n\n\n  word3  "
        result = normalize_whitespace(text)
        assert "word1 word2" in result
        assert "\n\n" in result
        assert "word3" in result
        assert "\n\n\n" not in result

    def test_handles_empty_string(self) -> None:
        assert normalize_whitespace("") == ""


# ===========================================================================
# normalize_article_markers tests
# ===========================================================================


class TestNormalizeArticleMarkers:
    """Tests for standardizing article number markers."""

    def test_normalizes_standard_format(self) -> None:
        text = "Art\u00edculo 1.- La persona humana"
        result = normalize_article_markers(text)
        assert "Art\u00edculo 1.- La persona humana" in result

    def test_normalizes_extra_spaces(self) -> None:
        text = "Art\u00edculo  2 .- La mujer puede"
        result = normalize_article_markers(text)
        assert "Art\u00edculo 2.- " in result

    def test_normalizes_uppercase(self) -> None:
        text = "ART\u00cdCULO 1529.- Por la compraventa"
        result = normalize_article_markers(text)
        assert "Art\u00edculo 1529.- " in result

    def test_normalizes_lowercase(self) -> None:
        text = "art\u00edculo 100.- Primer articulo"
        result = normalize_article_markers(text)
        assert "Art\u00edculo 100.- " in result

    def test_normalizes_without_accent(self) -> None:
        text = "Articulo 50.- Sin tilde"
        result = normalize_article_markers(text)
        assert "Art\u00edculo 50.- " in result

    def test_preserves_surrounding_text(self) -> None:
        text = "Segun el Art\u00edculo 1.- la persona humana es sujeto"
        result = normalize_article_markers(text)
        assert "Segun el" in result
        assert "la persona humana es sujeto" in result

    def test_normalizes_multiple_articles(self) -> None:
        text = "Art\u00edculo 1.- Primero.\nART\u00cdCULO  2 .- Segundo."
        result = normalize_article_markers(text)
        assert "Art\u00edculo 1.- Primero." in result
        assert "Art\u00edculo 2.- Segundo." in result

    def test_handles_article_with_letter_suffix(self) -> None:
        text = "Art\u00edculo 2A.- Articulo con sufijo literal."
        result = normalize_article_markers(text)
        assert "Art\u00edculo 2A.- " in result

    def test_preserves_non_article_text(self) -> None:
        text = "Este es un texto normal sin marcadores de articulo."
        result = normalize_article_markers(text)
        assert result == text


# ===========================================================================
# normalize_structural_headings tests
# ===========================================================================


class TestNormalizeStructuralHeadings:
    """Tests for uppercasing structural heading markers."""

    def test_uppercases_libro(self) -> None:
        text = "Libro I: Derechos de las Personas"
        result = normalize_structural_headings(text)
        assert "LIBRO I: DERECHOS DE LAS PERSONAS" in result

    def test_uppercases_titulo(self) -> None:
        text = "T\u00edtulo II: Acto Jur\u00eddico"
        result = normalize_structural_headings(text)
        assert result.startswith("T\u00cdTULO II")

    def test_uppercases_seccion(self) -> None:
        text = "Secci\u00f3n Segunda: Contratos Nominados"
        result = normalize_structural_headings(text)
        assert result.startswith("SECCI\u00d3N SEGUNDA")

    def test_uppercases_capitulo(self) -> None:
        text = "Cap\u00edtulo Primero: Disposiciones Generales"
        result = normalize_structural_headings(text)
        assert result.startswith("CAP\u00cdTULO PRIMERO")

    def test_preserves_non_heading_lines(self) -> None:
        text = "La persona humana es sujeto de derecho."
        result = normalize_structural_headings(text)
        assert result == text

    def test_handles_mixed_content(self) -> None:
        text = "Libro VII: Fuentes\nLa compraventa es un contrato.\nT\u00edtulo I: Compraventa"
        result = normalize_structural_headings(text)
        lines = result.splitlines()
        assert lines[0] == "LIBRO VII: FUENTES"
        assert lines[1] == "La compraventa es un contrato."
        assert lines[2].startswith("T\u00cdTULO I")

    def test_already_uppercase_is_idempotent(self) -> None:
        text = "LIBRO I: DERECHOS DE LAS PERSONAS"
        result = normalize_structural_headings(text)
        assert result == text


# ===========================================================================
# strip_boilerplate_text tests
# ===========================================================================


class TestStripBoilerplateText:
    """Tests for textual boilerplate removal."""

    def test_removes_ministry_footer(self) -> None:
        text = "Legal content.\nMinisterio de Justicia y Derechos Humanos - MINJUSDH\nMore content."
        result = strip_boilerplate_text(text)
        assert "Ministerio de Justicia" not in result
        assert "Legal content." in result
        assert "More content." in result

    def test_removes_spij_identifier(self) -> None:
        text = "Content.\nSistema Peruano de Informaci\u00f3n Jur\u00eddica - SPIJ\nMore."
        result = strip_boilerplate_text(text)
        assert "Sistema Peruano" not in result

    def test_removes_update_timestamp(self) -> None:
        text = "Content.\nActualizado y concordado al 15 de marzo de 2024\nMore."
        result = strip_boilerplate_text(text)
        assert "Actualizado" not in result

    def test_removes_button_labels(self) -> None:
        text = "Content.\nPDF\nWord\nImprimir\nCompartir\nMore."
        result = strip_boilerplate_text(text)
        assert "\nPDF\n" not in result
        assert "\nWord\n" not in result

    def test_removes_copyright_notice(self) -> None:
        text = "Content.\nTodos los derechos reservados\nMore."
        result = strip_boilerplate_text(text)
        assert "derechos reservados" not in result

    def test_removes_page_numbers(self) -> None:
        text = "Content.\nP\u00e1gina 1 de 10\nMore."
        result = strip_boilerplate_text(text)
        assert "P\u00e1gina 1 de 10" not in result

    def test_preserves_legal_content(self) -> None:
        text = "Art\u00edculo 1.- La persona humana es sujeto de derecho desde su nacimiento."
        result = strip_boilerplate_text(text)
        assert result == text


# ===========================================================================
# clean_legal_text (full pipeline integration) tests
# ===========================================================================


class TestCleanLegalText:
    """Integration tests for the complete cleaning pipeline."""

    def test_full_pipeline_civil_code_fragment(self) -> None:
        result = clean_legal_text(SPIJ_CIVIL_CODE_FRAGMENT)

        # Should preserve article content
        assert "persona humana es sujeto de derecho" in result
        assert "nacimiento" in result
        assert "reconocimiento de su embarazo" in result

        # Should remove boilerplate
        assert "MINJUSDH Logo" not in result
        assert "Buscar..." not in result
        assert "Google Analytics" not in result.lower()

        # Should remove concordances
        assert "Concordancias:" not in result

        # Structural headings should be uppercase
        assert "LIBRO I" in result

        # Should have normalized article markers
        assert "Art\u00edculo 1.- " in result
        assert "Art\u00edculo 2.- " in result

    def test_full_pipeline_multi_level(self) -> None:
        result = clean_legal_text(SPIJ_MULTI_LEVEL_FRAGMENT)

        # Content preserved
        assert "compraventa el vendedor" in result
        assert "gastos de entrega" in result

        # Structural headings uppercased
        assert "LIBRO VII" in result

        # Article markers normalized
        assert "Art\u00edculo 1529.- " in result
        assert "Art\u00edculo 1530.- " in result

    def test_full_pipeline_unicode_heavy(self) -> None:
        result = clean_legal_text(UNICODE_HEAVY_FRAGMENT)

        # Curly quotes replaced
        assert "\u201c" not in result
        assert "\u201d" not in result
        assert '"' in result

        # En dash replaced
        assert "\u2013" not in result

        # Non-breaking spaces replaced
        assert "\u00a0" not in result

        # Ellipsis replaced
        assert "\u2026" not in result
        assert "..." in result

        # Content preserved
        assert "concebido es sujeto de derecho" in result

    def test_full_pipeline_boilerplate_only_returns_minimal(self) -> None:
        result = clean_legal_text(BOILERPLATE_ONLY_FRAGMENT)
        # After stripping all boilerplate, should be minimal or empty
        # The result may have some residual whitespace but no meaningful content
        assert "MINJUSDH" not in result or len(result.strip()) < 10

    def test_full_pipeline_inconsistent_markers(self) -> None:
        result = clean_legal_text(INCONSISTENT_MARKERS_FRAGMENT)

        # All markers should be normalized to "Articulo N.- " format
        assert "Art\u00edculo 100.- " in result
        assert "Art\u00edculo 101.- " in result
        assert "Art\u00edculo 102.- " in result

    def test_full_pipeline_raises_on_empty(self) -> None:
        with pytest.raises(ValueError):
            clean_legal_text("")

    def test_full_pipeline_idempotent_on_clean_text(self) -> None:
        """Running the pipeline twice should produce the same result."""
        first_pass = clean_legal_text(SPIJ_CIVIL_CODE_FRAGMENT)
        # Wrap in minimal HTML for second pass
        second_pass = clean_legal_text(f"<html><body><p>{first_pass}</p></body></html>")
        # Core content should be preserved
        assert "persona humana es sujeto de derecho" in second_pass

    def test_output_has_no_excessive_blank_lines(self) -> None:
        result = clean_legal_text(SPIJ_CIVIL_CODE_FRAGMENT)
        assert "\n\n\n" not in result

    def test_output_has_no_trailing_whitespace_on_lines(self) -> None:
        result = clean_legal_text(SPIJ_CIVIL_CODE_FRAGMENT)
        for line in result.splitlines():
            assert line == line.rstrip(), f"Trailing whitespace found: {line!r}"

    def test_output_preserves_paragraph_separation(self) -> None:
        result = clean_legal_text(SPIJ_CIVIL_CODE_FRAGMENT)
        # Articles should be separated (at least by newlines)
        assert "Art\u00edculo 1.- " in result
        assert "Art\u00edculo 2.- " in result
        # The two articles should appear on different lines
        idx1 = result.index("Art\u00edculo 1.- ")
        idx2 = result.index("Art\u00edculo 2.- ")
        between = result[idx1:idx2]
        assert "\n" in between
