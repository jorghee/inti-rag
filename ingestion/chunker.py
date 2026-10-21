"""Hierarchical chunking parser for Peruvian codified legal norms.

This module implements the domain-aware structural parser that segments
cleaned legal text into atomic article-level chunks preserving the
full statutory hierarchy (Libro > Seccion > Titulo > Capitulo > Articulo).

It avoids fixed token chunking, slicing text strictly along canonical
statutory boundaries as specified in ADR-002 and docs/modules/legal-ingestion.md.

Key features:
    - Regex-based detection of structural boundaries (Books, Titles, etc.)
    - Atomic article extraction with parent hierarchy tracking
    - Mega-article safeguard: sub-chunking articles exceeding 500 words
    - Composite text assembly for embedding (hierarchy + article body)
    - Structured output conforming to the legal_chunks table schema

Reference:
    docs/modules/legal-ingestion.md - Section 3: Hierarchical Chunking Algorithm
    docs/architecture/decisions.md  - ADR-002: Hierarchical Chunking Pipeline
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Final

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Word count threshold for mega-article sub-chunking (docs/modules/legal-ingestion.md 3.1)
MEGA_ARTICLE_WORD_THRESHOLD: Final[int] = 500

# Default statute code for the Peruvian Civil Code
DEFAULT_STATUTE_CODE: Final[str] = "CODIGO_CIVIL_1984"

# Default norm display name for composite text assembly
DEFAULT_NORM_NAME: Final[str] = "Código Civil de 1984"

# Base URL template for SPIJ article deep links
SPIJ_BASE_URL: Final[str] = "https://spij.minjus.gob.pe/spij-ext-web/#/detallenorma/H682695"

# ---------------------------------------------------------------------------
# Structural boundary regexes
# ---------------------------------------------------------------------------

# Matches: LIBRO I, LIBRO VII, LIBRO PRIMERO, etc.
_RE_LIBRO = re.compile(
    r"^LIBRO\s+([IVXLCDM]+|\w+)\s*[:\.]?\s*(.*)",
    re.IGNORECASE,
)

# Matches: SECCION PRIMERA, SECCION SEGUNDA, etc.
_RE_SECCION = re.compile(
    r"^SECCI[OÓ]N\s+(\w+)\s*[:\.]?\s*(.*)",
    re.IGNORECASE,
)

# Matches: TITULO I, TITULO PRELIMINAR, TITULO FINAL, etc.
_RE_TITULO = re.compile(
    r"^T[IÍ]TULO\s+(PRELIMINAR|FINAL|[IVXLCDM]+|\w+)\s*[:\.]?\s*(.*)",
    re.IGNORECASE,
)

# Matches: CAPITULO PRIMERO, CAPITULO I, etc.
_RE_CAPITULO = re.compile(
    r"^CAP[IÍ]TULO\s+(\w+)\s*[:\.]?\s*(.*)",
    re.IGNORECASE,
)

# Matches: Articulo 1529.- <body text> or Articulo IV.- <body text>
_RE_ARTICULO = re.compile(
    r"^Artículo\s+(\d+[A-Za-z]?|[IVXLCDM]+)\.\-\s*(.*)",
)

# Matches inciso/numeral markers for mega-article sub-chunking
# Examples: "1.", "2)", "a)", "a.", "i)", "1.-"
_RE_INCISO = re.compile(
    r"^(\d+[\.\)\-]|[a-z][\.\)])\s+",
)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class LegalChunk:
    """A single statutory chunk ready for embedding and database storage.

    Attributes:
        statute_code: Norm identifier (e.g. CODIGO_CIVIL_1984).
        statutory_hierarchy: Full hierarchy path separated by " > ".
        article_number: Numeric article identifier.
        article_number_raw: Original article string (e.g. "1529", "2A").
        raw_content: The article text body.
        official_spij_url: Permanent SPIJ URL for this article.
        composite_text: Pre-assembled text for embedding generation.
        sub_chunk_index: 0 for primary chunk, 1+ for mega-article sub-chunks.
        total_words: Word count of raw_content.
    """

    statute_code: str
    statutory_hierarchy: str
    article_number: int
    article_number_raw: str
    raw_content: str
    official_spij_url: str
    composite_text: str
    sub_chunk_index: int = 0
    total_words: int = 0
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class _HierarchyState:
    """Mutable state tracker for current position in the statutory hierarchy."""

    libro: str = ""
    seccion: str = ""
    titulo: str = ""
    capitulo: str = ""

    def build_hierarchy(self) -> str:
        """Assemble the current hierarchy path as a ' > ' separated string."""
        parts = []
        if self.libro:
            parts.append(self.libro)
        if self.seccion:
            parts.append(self.seccion)
        if self.titulo:
            parts.append(self.titulo)
        if self.capitulo:
            parts.append(self.capitulo)
        return " > ".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_statute(
    clean_text: str,
    statute_code: str = DEFAULT_STATUTE_CODE,
    norm_name: str = DEFAULT_NORM_NAME,
    base_url: str = SPIJ_BASE_URL,
) -> list[LegalChunk]:
    """Parse cleaned statutory text into hierarchical article-level chunks.

    Scans the text line by line detecting structural boundaries (Libro,
    Seccion, Titulo, Capitulo) and extracting article blocks. Each article
    becomes a LegalChunk with its full hierarchy path preserved.

    Articles exceeding the mega-article word threshold are sub-chunked
    along inciso/numeral boundaries.

    Args:
        clean_text: Normalized plain text (output of ``clean_legal_text``).
        statute_code: Identifier for the statute being parsed.
        norm_name: Human-readable name for composite text headers.
        base_url: Base SPIJ URL for article deep links.

    Returns:
        List of LegalChunk instances ordered by article number.

    Raises:
        ValueError: If the input text is empty.
    """
    if not clean_text or not clean_text.strip():
        raise ValueError("Input text is empty")

    lines = clean_text.splitlines()
    state = _HierarchyState()
    chunks: list[LegalChunk] = []

    # Buffer for accumulating multi-line article content
    current_article_num: str | None = None
    current_article_body: list[str] = []
    current_hierarchy: str = ""

    for line in lines:
        stripped = line.strip()
        if not stripped:
            # Blank lines within an article body are preserved
            if current_article_num is not None:
                current_article_body.append("")
            continue

        # Check for structural headings (in priority order)
        heading_matched = False

        match = _RE_LIBRO.match(stripped)
        if match:
            # Flush any pending article
            if current_article_num is not None:
                _flush_article(
                    chunks,
                    current_article_num,
                    current_article_body,
                    current_hierarchy,
                    statute_code,
                    norm_name,
                    base_url,
                )
                current_article_num = None
                current_article_body = []

            num, desc = match.group(1), match.group(2).strip()
            label = f"Libro {num}"
            if desc:
                label += f": {desc}"
            state.libro = label
            state.seccion = ""
            state.titulo = ""
            state.capitulo = ""
            heading_matched = True

        if not heading_matched:
            match = _RE_SECCION.match(stripped)
            if match:
                if current_article_num is not None:
                    _flush_article(
                        chunks,
                        current_article_num,
                        current_article_body,
                        current_hierarchy,
                        statute_code,
                        norm_name,
                        base_url,
                    )
                    current_article_num = None
                    current_article_body = []

                num, desc = match.group(1), match.group(2).strip()
                label = f"Sección {num}"
                if desc:
                    label += f": {desc}"
                state.seccion = label
                state.titulo = ""
                state.capitulo = ""
                heading_matched = True

        if not heading_matched:
            match = _RE_TITULO.match(stripped)
            if match:
                if current_article_num is not None:
                    _flush_article(
                        chunks,
                        current_article_num,
                        current_article_body,
                        current_hierarchy,
                        statute_code,
                        norm_name,
                        base_url,
                    )
                    current_article_num = None
                    current_article_body = []

                num, desc = match.group(1), match.group(2).strip()
                label = f"Título {num}"
                if desc:
                    label += f": {desc}"
                state.titulo = label
                state.capitulo = ""
                heading_matched = True

        if not heading_matched:
            match = _RE_CAPITULO.match(stripped)
            if match:
                if current_article_num is not None:
                    _flush_article(
                        chunks,
                        current_article_num,
                        current_article_body,
                        current_hierarchy,
                        statute_code,
                        norm_name,
                        base_url,
                    )
                    current_article_num = None
                    current_article_body = []

                num, desc = match.group(1), match.group(2).strip()
                label = f"Capítulo {num}"
                if desc:
                    label += f": {desc}"
                state.capitulo = label
                heading_matched = True

        if not heading_matched:
            match = _RE_ARTICULO.match(stripped)
            if match:
                # Flush previous article
                if current_article_num is not None:
                    _flush_article(
                        chunks,
                        current_article_num,
                        current_article_body,
                        current_hierarchy,
                        statute_code,
                        norm_name,
                        base_url,
                    )

                current_article_num = match.group(1)
                body_start = match.group(2).strip()
                current_article_body = [body_start] if body_start else []
                current_hierarchy = state.build_hierarchy()
            elif current_article_num is not None:
                # Continuation line of current article
                current_article_body.append(stripped)

    # Flush the last article
    if current_article_num is not None:
        _flush_article(
            chunks,
            current_article_num,
            current_article_body,
            current_hierarchy,
            statute_code,
            norm_name,
            base_url,
        )

    return chunks


def build_composite_text(
    norm_name: str,
    hierarchy: str,
    article_number_raw: str,
    content: str,
) -> str:
    """Assemble the composite text string used for embedding generation.

    Format (from docs/modules/legal-ingestion.md Section 3):
        Norm: Codigo Civil de 1984
        Hierarchy: Libro VII: ... > Titulo I: ...
        Article 1529: <article body text>

    Args:
        norm_name: Human-readable norm name.
        hierarchy: Full statutory hierarchy path.
        article_number_raw: Article number as string.
        content: The article text body.

    Returns:
        Formatted composite text string.
    """
    parts = [f"Norm: {norm_name}"]
    if hierarchy:
        parts.append(f"Hierarchy: {hierarchy}")
    parts.append(f"Article {article_number_raw}: {content}")
    return "\n".join(parts)


def split_mega_article(
    content: str,
    intro_clause: str,
    threshold: int = MEGA_ARTICLE_WORD_THRESHOLD,
) -> list[str]:
    """Split a mega-article into sub-chunks along inciso boundaries.

    Articles exceeding the word threshold are partitioned at structural
    sub-boundaries (numbered incisos, lettered clauses). Each sub-chunk
    retains the introductory clause for context preservation.

    Args:
        content: Full article body text.
        intro_clause: The opening sentence/clause of the article that
            provides context for all sub-chunks.
        threshold: Word count threshold for triggering sub-chunking.

    Returns:
        List of sub-chunk text strings. Returns a single-element list
        containing the original content if below threshold or no
        inciso boundaries are found.
    """
    word_count = len(content.split())
    if word_count <= threshold:
        return [content]

    lines = content.splitlines()
    sub_chunks: list[str] = []
    current_chunk_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        # Detect inciso boundary
        if _RE_INCISO.match(stripped) and current_chunk_lines:
            chunk_text = "\n".join(current_chunk_lines).strip()
            if chunk_text:
                sub_chunks.append(chunk_text)
            current_chunk_lines = [stripped]
        else:
            current_chunk_lines.append(stripped if stripped else "")

    # Flush remaining
    if current_chunk_lines:
        chunk_text = "\n".join(current_chunk_lines).strip()
        if chunk_text:
            sub_chunks.append(chunk_text)

    # If no meaningful splits were made, return original
    if len(sub_chunks) <= 1:
        return [content]

    # Prepend intro clause to each sub-chunk for context retention
    result: list[str] = []
    for chunk in sub_chunks:
        # Avoid duplicating the intro if it's already the first chunk
        if chunk.startswith(intro_clause.strip()):
            result.append(chunk)
        else:
            result.append(f"{intro_clause.strip()}\n{chunk}")

    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _roman_to_int(s: str) -> int:
    """Convert a Roman numeral string to integer.

    Supports standard Roman numerals up to 3999 (I through MMMCMXCIX).
    Returns 0 if the string is not a valid Roman numeral.
    """
    roman_values = {
        "I": 1,
        "V": 5,
        "X": 10,
        "L": 50,
        "C": 100,
        "D": 500,
        "M": 1000,
    }
    s = s.strip().upper()
    if not s or not all(c in roman_values for c in s):
        return 0

    total = 0
    prev = 0
    for char in reversed(s):
        value = roman_values[char]
        if value < prev:
            total -= value
        else:
            total += value
        prev = value
    return total


def _extract_article_number(raw: str) -> int:
    """Extract the numeric portion of an article number string.

    Handles suffixed articles like '2A' by extracting only digits.
    Handles Roman numeral articles by converting to integer.
    """
    digits = re.match(r"(\d+)", raw)
    if digits:
        return int(digits.group(1))
    # Try Roman numeral conversion
    return _roman_to_int(raw)


def _extract_intro_clause(body: str) -> str:
    """Extract the introductory clause (first sentence) of an article."""
    # Find the first period followed by whitespace or end of string
    match = re.search(r"^(.+?\.)\s", body)
    if match:
        return match.group(1)
    # If no period found, use the first line
    first_line = body.split("\n")[0].strip()
    return first_line if first_line else body[:100]


def _flush_article(
    chunks: list[LegalChunk],
    article_num_raw: str,
    body_lines: list[str],
    hierarchy: str,
    statute_code: str,
    norm_name: str,
    base_url: str,
) -> None:
    """Finalize an article and append its chunk(s) to the result list."""
    body = "\n".join(body_lines).strip()
    if not body:
        return

    article_number = _extract_article_number(article_num_raw)
    word_count = len(body.split())

    # Check for mega-article
    if word_count > MEGA_ARTICLE_WORD_THRESHOLD:
        intro = _extract_intro_clause(body)
        sub_chunks = split_mega_article(body, intro)

        if len(sub_chunks) > 1:
            for idx, sub_content in enumerate(sub_chunks):
                sub_words = len(sub_content.split())
                composite = build_composite_text(
                    norm_name,
                    hierarchy,
                    article_num_raw,
                    sub_content,
                )
                chunks.append(
                    LegalChunk(
                        statute_code=statute_code,
                        statutory_hierarchy=hierarchy,
                        article_number=article_number,
                        article_number_raw=article_num_raw,
                        raw_content=sub_content,
                        official_spij_url=base_url,
                        composite_text=composite,
                        sub_chunk_index=idx,
                        total_words=sub_words,
                        metadata={"has_modifications": False, "last_amendment": None},
                    )
                )
            return

    # Standard article (or mega-article that couldn't be split)
    composite = build_composite_text(norm_name, hierarchy, article_num_raw, body)
    chunks.append(
        LegalChunk(
            statute_code=statute_code,
            statutory_hierarchy=hierarchy,
            article_number=article_number,
            article_number_raw=article_num_raw,
            raw_content=body,
            official_spij_url=base_url,
            composite_text=composite,
            sub_chunk_index=0,
            total_words=word_count,
            metadata={"has_modifications": False, "last_amendment": None},
        )
    )
