"""Unit tests for ingestion.chunker module.

Tests the hierarchical statutory parser including hierarchy tracking,
article extraction, mega-article sub-chunking, and composite text assembly.

Reference: docs/modules/legal-ingestion.md - Section 3
"""

from __future__ import annotations

import pytest

from ingestion.chunker import (
    MEGA_ARTICLE_WORD_THRESHOLD,
    build_composite_text,
    parse_statute,
    split_mega_article,
)

# ===========================================================================
# Fixtures: Synthetic clean text representing normalized legal content
# ===========================================================================

SIMPLE_TWO_ARTICLES = """\
LIBRO I: DERECHOS DE LAS PERSONAS

TITULO I: PRINCIPIO DE LA PERSONA

CAPITULO PRIMERO: DISPOSICIONES GENERALES

Artículo 1.- La persona humana es sujeto de derecho desde su nacimiento.

Artículo 2.- La mujer puede solicitar judicialmente el reconocimiento de su embarazo o del parto, con citación de las personas que tengan interés en el nacimiento.
"""

MULTI_LEVEL_HIERARCHY = """\
LIBRO VII: FUENTES DE LAS OBLIGACIONES

SECCIÓN SEGUNDA: CONTRATOS NOMINADOS

TÍTULO I: COMPRAVENTA

CAPÍTULO PRIMERO: DISPOSICIONES GENERALES

Artículo 1529.- Por la compraventa el vendedor se obliga a transferir la propiedad de un bien al comprador y este a pagar su precio en dinero.

Artículo 1530.- Los gastos de entrega son de cargo del vendedor y los gastos de transporte a un lugar diferente del de cumplimiento son de cargo del comprador, salvo pacto diverso.
"""

TWO_BOOKS_MULTIPLE_TITLES = """\
LIBRO I: DERECHOS DE LAS PERSONAS

TITULO I: PRINCIPIO DE LA PERSONA

Artículo 1.- Primera disposicion.

TITULO II: DERECHOS DE LA PERSONA

Artículo 3.- Contenido del Titulo II.

LIBRO II: ACTO JURIDICO

TITULO I: DISPOSICIONES GENERALES

Artículo 140.- Definicion del acto juridico.
"""

MULTILINE_ARTICLE = """\
LIBRO I: DERECHOS DE LAS PERSONAS

TITULO I: PRINCIPIO DE LA PERSONA

Artículo 1.- La persona humana es sujeto de derecho desde su nacimiento.
La vida humana comienza con la concepcion. El concebido es sujeto de
derecho para todo cuanto le favorece. La atribucion de derechos
patrimoniales esta condicionada a que nazca vivo.
"""

TITULO_PRELIMINAR = """\
TÍTULO PRELIMINAR

Artículo I.- La ley se deroga solo por otra ley.

Artículo II.- La ley no ampara el ejercicio ni la omision abusivos de un derecho.
"""

ARTICLE_WITH_LETTER_SUFFIX = """\
LIBRO I: DERECHOS DE LAS PERSONAS

TITULO I: PRINCIPIO DE LA PERSONA

Artículo 2A.- Disposicion especial con sufijo literal.
"""


def _generate_mega_article(word_count: int) -> str:
    """Generate a synthetic mega-article with inciso boundaries."""
    lines = [
        "LIBRO I: DERECHOS DE LAS PERSONAS",
        "",
        "TITULO I: PRINCIPIO DE LA PERSONA",
        "",
        "Artículo 999.- Disposicion introductoria del articulo largo.",
    ]

    # Generate incisos to exceed threshold
    words_per_inciso = 50
    num_incisos = (word_count // words_per_inciso) + 1

    for i in range(1, num_incisos + 1):
        filler = " ".join(f"palabra{j}" for j in range(words_per_inciso))
        lines.append(f"{i}. Inciso {i} del articulo: {filler}")

    return "\n".join(lines)


# ===========================================================================
# parse_statute tests
# ===========================================================================


class TestParseStatute:
    """Tests for the main hierarchical parser."""

    def test_extracts_two_articles(self) -> None:
        chunks = parse_statute(SIMPLE_TWO_ARTICLES)
        assert len(chunks) == 2

    def test_article_numbers_are_correct(self) -> None:
        chunks = parse_statute(SIMPLE_TWO_ARTICLES)
        assert chunks[0].article_number == 1
        assert chunks[1].article_number == 2

    def test_article_raw_numbers_preserved(self) -> None:
        chunks = parse_statute(SIMPLE_TWO_ARTICLES)
        assert chunks[0].article_number_raw == "1"
        assert chunks[1].article_number_raw == "2"

    def test_hierarchy_includes_all_levels(self) -> None:
        chunks = parse_statute(MULTI_LEVEL_HIERARCHY)
        hierarchy = chunks[0].statutory_hierarchy
        assert "Libro VII" in hierarchy
        assert "Sección Segunda" in hierarchy or "Sección SEGUNDA" in hierarchy
        assert "Título I" in hierarchy or "Título I" in hierarchy
        assert "Capítulo" in hierarchy

    def test_hierarchy_uses_separator(self) -> None:
        chunks = parse_statute(MULTI_LEVEL_HIERARCHY)
        assert " > " in chunks[0].statutory_hierarchy

    def test_preserves_article_content(self) -> None:
        chunks = parse_statute(SIMPLE_TWO_ARTICLES)
        assert "persona humana es sujeto de derecho" in chunks[0].raw_content
        assert "reconocimiento de su embarazo" in chunks[1].raw_content

    def test_default_statute_code(self) -> None:
        chunks = parse_statute(SIMPLE_TWO_ARTICLES)
        assert all(c.statute_code == "CODIGO_CIVIL_1984" for c in chunks)

    def test_custom_statute_code(self) -> None:
        chunks = parse_statute(SIMPLE_TWO_ARTICLES, statute_code="CODIGO_PENAL_1991")
        assert all(c.statute_code == "CODIGO_PENAL_1991" for c in chunks)

    def test_spij_url_assigned(self) -> None:
        chunks = parse_statute(SIMPLE_TWO_ARTICLES)
        assert all(c.official_spij_url.startswith("https://spij.minjus.gob.pe") for c in chunks)

    def test_word_count_populated(self) -> None:
        chunks = parse_statute(SIMPLE_TWO_ARTICLES)
        assert all(c.total_words > 0 for c in chunks)

    def test_sub_chunk_index_zero_for_normal(self) -> None:
        chunks = parse_statute(SIMPLE_TWO_ARTICLES)
        assert all(c.sub_chunk_index == 0 for c in chunks)

    def test_multiline_article_concatenated(self) -> None:
        chunks = parse_statute(MULTILINE_ARTICLE)
        assert len(chunks) == 1
        content = chunks[0].raw_content
        assert "persona humana es sujeto de derecho" in content
        assert "condicionada a que nazca vivo" in content

    def test_hierarchy_resets_on_new_book(self) -> None:
        chunks = parse_statute(TWO_BOOKS_MULTIPLE_TITLES)
        assert len(chunks) == 3

        # Article 1 in Libro I, Titulo I
        assert "Libro I" in chunks[0].statutory_hierarchy
        assert "Título I" in chunks[0].statutory_hierarchy

        # Article 3 in Libro I, Titulo II
        assert "Libro I" in chunks[1].statutory_hierarchy
        assert "Título II" in chunks[1].statutory_hierarchy

        # Article 140 in Libro II, Titulo I
        assert "Libro II" in chunks[2].statutory_hierarchy
        assert "Título I" in chunks[2].statutory_hierarchy
        # Should NOT contain Titulo II from previous book
        assert "Título II" not in chunks[2].statutory_hierarchy

    def test_titulo_resets_capitulo(self) -> None:
        text = """\
LIBRO I: TEST

TITULO I: FIRST

CAPITULO PRIMERO: INITIAL

Artículo 1.- First article.

TITULO II: SECOND

Artículo 2.- Second article without capitulo.
"""
        chunks = parse_statute(text)
        # Article 2 should not inherit Capitulo from Titulo I
        assert "Capítulo" not in chunks[1].statutory_hierarchy

    def test_raises_on_empty_input(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            parse_statute("")

    def test_raises_on_whitespace_only(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            parse_statute("   \n\n  ")

    def test_handles_titulo_preliminar(self) -> None:
        chunks = parse_statute(TITULO_PRELIMINAR)
        assert len(chunks) >= 1
        # Titulo Preliminar should appear in hierarchy
        assert (
            "Título PRELIMINAR" in chunks[0].statutory_hierarchy
            or "Título Preliminar" in chunks[0].statutory_hierarchy
        )

    def test_handles_article_with_letter_suffix(self) -> None:
        chunks = parse_statute(ARTICLE_WITH_LETTER_SUFFIX)
        assert len(chunks) == 1
        assert chunks[0].article_number == 2
        assert chunks[0].article_number_raw == "2A"

    def test_no_articles_returns_empty_list(self) -> None:
        text = "LIBRO I: DERECHOS DE LAS PERSONAS\n\nSome preamble without articles."
        chunks = parse_statute(text)
        assert len(chunks) == 0

    def test_metadata_has_required_fields(self) -> None:
        chunks = parse_statute(SIMPLE_TWO_ARTICLES)
        for chunk in chunks:
            assert "has_modifications" in chunk.metadata
            assert "last_amendment" in chunk.metadata


# ===========================================================================
# build_composite_text tests
# ===========================================================================


class TestBuildCompositeText:
    """Tests for composite text assembly."""

    def test_includes_norm_name(self) -> None:
        result = build_composite_text(
            "Código Civil de 1984",
            "Libro I > Título I",
            "1",
            "La persona humana es sujeto de derecho.",
        )
        assert "Norm: Código Civil de 1984" in result

    def test_includes_hierarchy(self) -> None:
        result = build_composite_text(
            "Código Civil de 1984",
            "Libro VII: Fuentes > Título I: Compraventa",
            "1529",
            "Body text.",
        )
        assert "Hierarchy: Libro VII: Fuentes > Título I: Compraventa" in result

    def test_includes_article_number_and_body(self) -> None:
        result = build_composite_text(
            "Test Norm",
            "Libro I",
            "42",
            "Content of article forty-two.",
        )
        assert "Article 42: Content of article forty-two." in result

    def test_omits_hierarchy_when_empty(self) -> None:
        result = build_composite_text("Test", "", "1", "Body.")
        assert "Hierarchy" not in result

    def test_multiline_format(self) -> None:
        result = build_composite_text(
            "Norm",
            "Libro I",
            "1",
            "Body.",
        )
        lines = result.splitlines()
        assert len(lines) == 3
        assert lines[0].startswith("Norm:")
        assert lines[1].startswith("Hierarchy:")
        assert lines[2].startswith("Article 1:")

    def test_composite_text_in_parsed_chunks(self) -> None:
        chunks = parse_statute(SIMPLE_TWO_ARTICLES)
        for chunk in chunks:
            assert chunk.composite_text
            assert "Norm:" in chunk.composite_text
            assert "Article" in chunk.composite_text
            assert chunk.raw_content in chunk.composite_text


# ===========================================================================
# split_mega_article tests
# ===========================================================================


class TestSplitMegaArticle:
    """Tests for mega-article sub-chunking."""

    def test_short_article_not_split(self) -> None:
        content = "This is a short article with only a few words."
        result = split_mega_article(content, "This is a short article.")
        assert len(result) == 1
        assert result[0] == content

    def test_long_article_with_incisos_is_split(self) -> None:
        # Create content exceeding threshold with inciso markers
        filler = " ".join(["word"] * 200)
        content = (
            f"Introductory clause of the article.\n"
            f"1. First inciso with content: {filler}\n"
            f"2. Second inciso with content: {filler}\n"
            f"3. Third inciso with content: {filler}\n"
        )
        result = split_mega_article(content, "Introductory clause of the article.")
        assert len(result) > 1

    def test_sub_chunks_preserve_intro(self) -> None:
        filler = " ".join(["word"] * 200)
        intro = "Introductory clause."
        content = (
            f"{intro}\n"
            f"1. First inciso: {filler}\n"
            f"2. Second inciso: {filler}\n"
            f"3. Third inciso: {filler}\n"
        )
        result = split_mega_article(content, intro)
        # All sub-chunks after the first should start with the intro
        for sub in result[1:]:
            assert sub.startswith(intro)

    def test_long_article_without_incisos_not_split(self) -> None:
        # A long article without inciso markers should not be split
        filler = " ".join(["word"] * (MEGA_ARTICLE_WORD_THRESHOLD + 100))
        content = f"Single continuous paragraph: {filler}"
        result = split_mega_article(content, "Single continuous paragraph:")
        assert len(result) == 1

    def test_threshold_boundary(self) -> None:
        # Exactly at threshold should not trigger split
        words = " ".join(["word"] * MEGA_ARTICLE_WORD_THRESHOLD)
        result = split_mega_article(words, "word")
        assert len(result) == 1

    def test_just_above_threshold_with_incisos(self) -> None:
        filler = " ".join(["word"] * 260)
        content = f"Intro.\n1. First: {filler}\n2. Second: {filler}\n"
        result = split_mega_article(content, "Intro.")
        assert len(result) > 1


# ===========================================================================
# Mega-article integration via parse_statute
# ===========================================================================


class TestMegaArticleIntegration:
    """Integration tests for mega-article detection during parsing."""

    def test_mega_article_produces_sub_chunks(self) -> None:
        text = _generate_mega_article(MEGA_ARTICLE_WORD_THRESHOLD + 200)
        chunks = parse_statute(text)

        # Should produce multiple chunks for the same article
        article_999_chunks = [c for c in chunks if c.article_number == 999]
        assert len(article_999_chunks) > 1

    def test_mega_sub_chunks_share_article_number(self) -> None:
        text = _generate_mega_article(MEGA_ARTICLE_WORD_THRESHOLD + 200)
        chunks = parse_statute(text)

        article_999_chunks = [c for c in chunks if c.article_number == 999]
        article_numbers = {c.article_number for c in article_999_chunks}
        assert len(article_numbers) == 1

    def test_mega_sub_chunks_share_url(self) -> None:
        text = _generate_mega_article(MEGA_ARTICLE_WORD_THRESHOLD + 200)
        chunks = parse_statute(text)

        article_999_chunks = [c for c in chunks if c.article_number == 999]
        urls = {c.official_spij_url for c in article_999_chunks}
        assert len(urls) == 1

    def test_mega_sub_chunks_have_sequential_indices(self) -> None:
        text = _generate_mega_article(MEGA_ARTICLE_WORD_THRESHOLD + 200)
        chunks = parse_statute(text)

        article_999_chunks = [c for c in chunks if c.article_number == 999]
        indices = [c.sub_chunk_index for c in article_999_chunks]
        assert indices == list(range(len(indices)))

    def test_mega_sub_chunks_all_have_composite_text(self) -> None:
        text = _generate_mega_article(MEGA_ARTICLE_WORD_THRESHOLD + 200)
        chunks = parse_statute(text)

        article_999_chunks = [c for c in chunks if c.article_number == 999]
        for chunk in article_999_chunks:
            assert chunk.composite_text
            assert "Norm:" in chunk.composite_text

    def test_normal_article_not_sub_chunked(self) -> None:
        chunks = parse_statute(SIMPLE_TWO_ARTICLES)
        for chunk in chunks:
            assert chunk.sub_chunk_index == 0


# ===========================================================================
# End-to-end: cleaning + chunking pipeline
# ===========================================================================


class TestEndToEndPipeline:
    """Integration tests chaining cleaning and chunking."""

    def test_clean_then_chunk(self) -> None:
        from ingestion.cleaning import clean_legal_text
        from tests.fixtures import SPIJ_CIVIL_CODE_FRAGMENT

        clean_text = clean_legal_text(SPIJ_CIVIL_CODE_FRAGMENT)
        chunks = parse_statute(clean_text)

        assert len(chunks) >= 2
        assert any("persona humana" in c.raw_content for c in chunks)
        assert any("embarazo" in c.raw_content for c in chunks)

    def test_clean_then_chunk_multi_level(self) -> None:
        from ingestion.cleaning import clean_legal_text
        from tests.fixtures import SPIJ_MULTI_LEVEL_FRAGMENT

        clean_text = clean_legal_text(SPIJ_MULTI_LEVEL_FRAGMENT)
        chunks = parse_statute(clean_text)

        assert len(chunks) >= 2
        assert any(c.article_number == 1529 for c in chunks)
        assert any("compraventa" in c.raw_content for c in chunks)

        # Verify hierarchy
        chunk_1529 = next(c for c in chunks if c.article_number == 1529)
        assert "Libro VII" in chunk_1529.statutory_hierarchy
