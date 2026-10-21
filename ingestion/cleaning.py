"""HTML sanitization and text normalization for Peruvian legal documents.

This module implements the cleaning and preprocessing pipeline for raw
HTML content extracted from SPIJ (Sistema Peruano de Informacion Juridica).
It produces clean, normalized plain text preserving the statutory structure
required by the downstream hierarchical chunker.

Pipeline steps:
    1. HTML tag removal (scripts, styles, navigation, UI chrome)
    2. Boilerplate stripping (SPIJ headers, footers, toolbar elements)
    3. UTF-8 normalization (curly quotes, special dashes, non-breaking spaces)
    4. Whitespace consolidation (collapse runs, normalize line breaks)
    5. Legal text formatting normalization (consistent article markers)

Reference:
    docs/modules/legal-ingestion.md - Section 2: Ingestion Pipeline Flow
"""

from __future__ import annotations

import re
import unicodedata

from bs4 import BeautifulSoup, Comment, Tag

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# HTML elements that carry no textual legal content
_STRIP_TAGS: set[str] = {
    "script",
    "style",
    "noscript",
    "iframe",
    "svg",
    "canvas",
    "meta",
    "link",
    "head",
}

# CSS class prefixes identifying SPIJ chrome / non-content containers
_BOILERPLATE_CLASS_PREFIXES: tuple[str, ...] = (
    "header-spij",
    "footer-spij",
    "nav-menu",
    "sidebar-filters",
    "toolbar-actions",
    "contextual-sidebar",
    "search-box",
    "logo-minjus",
    "modifications-history",
    "norm-index-tree",
    "btn-",
)

# CSS classes for concordances and cross-reference blocks
_CONCORDANCE_CLASSES: tuple[str, ...] = (
    "concordances-section",
    "concordance-label",
    "concordancias",
)

# Unicode normalization mappings for typographic characters
_UNICODE_REPLACEMENTS: dict[str, str] = {
    "\u2018": "'",  # left single curly quote
    "\u2019": "'",  # right single curly quote
    "\u201c": '"',  # left double curly quote
    "\u201d": '"',  # right double curly quote
    "\u2013": "-",  # en dash
    "\u2014": "-",  # em dash
    "\u2015": "-",  # horizontal bar
    "\u00a0": " ",  # non-breaking space
    "\u200b": "",  # zero-width space
    "\u200c": "",  # zero-width non-joiner
    "\u200d": "",  # zero-width joiner
    "\ufeff": "",  # byte order mark / zero-width no-break space
    "\u2026": "...",  # horizontal ellipsis
    "\u00ad": "",  # soft hyphen
}

# Pre-compiled regex for collapsing multiple blank lines
_MULTI_BLANK_LINES = re.compile(r"\n{3,}")

# Pre-compiled regex for collapsing horizontal whitespace (spaces/tabs)
_HORIZONTAL_WHITESPACE = re.compile(r"[^\S\n]+")

# Pre-compiled regex for normalizing article markers to a consistent format.
# Matches patterns like "Artículo  1 .-", "Articulo 1.-", "ARTÍCULO 1.-", "Articulo I.-"
_ARTICLE_MARKER = re.compile(
    r"(?i)(art[ií]culo)\s+(\d+[A-Za-z]?|[IVXLCDM]+)\s*[\.\-]+\s*",
)

# Pre-compiled regex for structural heading markers (LIBRO, TITULO, etc.)
_STRUCTURAL_HEADING = re.compile(
    r"^(LIBRO|SECCI[OÓ]N|T[IÍ]TULO|CAP[IÍ]TULO"
    r"|SUBCAP[IÍ]TULO|T[IÍ]TULO PRELIMINAR|T[IÍ]TULO FINAL)",
    re.IGNORECASE | re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def sanitize_html(raw_html: str) -> str:
    """Remove HTML markup and extract clean text content from SPIJ pages.

    Strips script/style elements, SPIJ navigation chrome, concordance
    annotations, and HTML comments, then extracts the remaining visible
    text content.

    Args:
        raw_html: Raw HTML string from SPIJ portal download.

    Returns:
        Plain text with HTML tags removed but original whitespace
        largely preserved. Further normalization should be applied
        via ``normalize_text``.

    Raises:
        ValueError: If ``raw_html`` is empty or contains no parseable content.
    """
    if not raw_html or not raw_html.strip():
        raise ValueError("Input HTML is empty or contains only whitespace")

    soup = BeautifulSoup(raw_html, "lxml")

    # 1. Remove elements that never contain legal text
    for tag_name in _STRIP_TAGS:
        for element in soup.find_all(tag_name):
            element.decompose()

    # 2. Remove HTML comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # 3. Remove SPIJ boilerplate containers by CSS class
    _remove_boilerplate_elements(soup)

    # 4. Remove concordance / cross-reference blocks
    _remove_concordance_blocks(soup)

    # 5. Extract text from the cleaned DOM
    text = soup.get_text(separator="\n")

    return text


def normalize_unicode(text: str) -> str:
    """Normalize Unicode characters to their ASCII or standard equivalents.

    Applies NFC normalization first to compose decomposed characters
    (ensuring accented Spanish characters like a + combining acute = a),
    then replaces typographic variants (curly quotes, special dashes,
    zero-width characters) with their plain equivalents.

    Args:
        text: Input text potentially containing typographic Unicode.

    Returns:
        Text with normalized Unicode characters. Spanish diacritics
        (a, e, i, o, u, n) are preserved as they are structural
        in legal terminology.
    """
    # NFC normalization: compose decomposed diacritics
    text = unicodedata.normalize("NFC", text)

    # Replace typographic characters
    for original, replacement in _UNICODE_REPLACEMENTS.items():
        text = text.replace(original, replacement)

    return text


def normalize_whitespace(text: str) -> str:
    """Consolidate whitespace into a canonical form.

    Collapses multiple consecutive blank lines into a single blank line
    (double newline), trims trailing whitespace on each line, and
    collapses horizontal whitespace runs (spaces/tabs) into single spaces.

    Args:
        text: Input text with potentially irregular whitespace.

    Returns:
        Text with normalized whitespace suitable for hierarchical parsing.
    """
    # Collapse horizontal whitespace (but preserve newlines)
    text = _HORIZONTAL_WHITESPACE.sub(" ", text)

    # Strip trailing whitespace on each line
    lines = [line.rstrip() for line in text.splitlines()]
    text = "\n".join(lines)

    # Collapse multiple blank lines into a single blank line
    text = _MULTI_BLANK_LINES.sub("\n\n", text)

    # Strip leading/trailing whitespace from the entire document
    return text.strip()


def normalize_article_markers(text: str) -> str:
    """Standardize article number markers to a consistent format.

    Converts varying patterns like ``Articulo 1.-``, ``ARTICULO  1 .-``,
    ``Articulo 1.-`` into the canonical form ``Articulo 1.-``.

    The canonical format uses:
    - Title case ``Articulo`` (matches SPIJ convention)
    - Single space between label and number
    - ``.-`` suffix immediately after the number

    Args:
        text: Legal text with potentially inconsistent article markers.

    Returns:
        Text with standardized article markers.
    """

    def _normalize_match(match: re.Match[str]) -> str:
        article_number = match.group(2)
        return f"Artículo {article_number}.- "

    return _ARTICLE_MARKER.sub(_normalize_match, text)


def normalize_structural_headings(text: str) -> str:
    """Normalize structural heading casing to UPPERCASE.

    Ensures hierarchical markers (LIBRO, SECCION, TITULO, CAPITULO)
    are consistently uppercased, which the downstream chunker relies
    on for structural boundary detection.

    Args:
        text: Legal text with potentially mixed-case headings.

    Returns:
        Text with uppercased structural headings.
    """
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if _STRUCTURAL_HEADING.match(stripped):
            lines.append(stripped.upper())
        else:
            lines.append(line)
    return "\n".join(lines)


def strip_boilerplate_text(text: str) -> str:
    """Remove common SPIJ textual boilerplate that survives HTML stripping.

    Targets recurring footer disclaimers, update timestamps, and
    institutional header text that appear as plain text in the
    extracted content.

    Args:
        text: Plain text that may contain SPIJ boilerplate strings.

    Returns:
        Text with boilerplate strings removed.
    """
    # Common SPIJ boilerplate patterns
    boilerplate_patterns: list[re.Pattern[str]] = [
        # Ministry footer
        re.compile(
            r"Ministerio de Justicia y Derechos Humanos\s*-?\s*MINJUSDH",
            re.IGNORECASE,
        ),
        # SPIJ system identifier
        re.compile(
            r"Sistema Peruano de Informaci[oó]n Jur[ií]dica\s*-?\s*SPIJ",
            re.IGNORECASE,
        ),
        # Update timestamp lines
        re.compile(
            r"(?:Texto\s+)?[Aa]ctualizado\s+(?:al|hasta|y concordado).*?\d{4}",
        ),
        # PDF/Word/Print button labels that leak as text
        re.compile(r"^\s*(?:PDF|Word|Imprimir|Compartir)\s*$", re.MULTILINE),
        # Copyright notices
        re.compile(
            r"(?:Todos\s+los\s+derechos\s+reservados|All\s+rights\s+reserved)",
            re.IGNORECASE,
        ),
        # Page numbers
        re.compile(r"^\s*P[aá]gina\s+\d+\s+de\s+\d+\s*$", re.MULTILINE),
    ]

    for pattern in boilerplate_patterns:
        text = pattern.sub("", text)

    return text


def clean_legal_text(raw_html: str) -> str:
    """Execute the full cleaning pipeline on raw SPIJ HTML.

    This is the primary entry point for the cleaning module. It chains
    all sanitization and normalization steps in the correct order:

        HTML sanitization -> boilerplate stripping -> Unicode normalization
        -> article marker normalization -> heading normalization
        -> whitespace consolidation

    Args:
        raw_html: Raw HTML string downloaded from the SPIJ portal.

    Returns:
        Clean, normalized plain text ready for the hierarchical chunker.

    Raises:
        ValueError: If the input HTML is empty or unparseable.
    """
    # Step 1: Strip HTML and extract text
    text = sanitize_html(raw_html)

    # Step 2: Remove textual boilerplate that survived HTML stripping
    text = strip_boilerplate_text(text)

    # Step 3: Normalize Unicode (curly quotes, special dashes, etc.)
    text = normalize_unicode(text)

    # Step 4: Standardize article number markers
    text = normalize_article_markers(text)

    # Step 5: Normalize structural headings to uppercase
    text = normalize_structural_headings(text)

    # Step 6: Consolidate whitespace
    text = normalize_whitespace(text)

    return text


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _remove_boilerplate_elements(soup: BeautifulSoup) -> None:
    """Remove DOM elements whose CSS classes match SPIJ boilerplate patterns."""
    # Collect elements to remove first to avoid mutation during iteration
    to_remove: list[Tag] = []
    for element in soup.find_all(True):
        if not isinstance(element, Tag) or element.attrs is None:
            continue
        css_classes = element.get("class", [])
        if isinstance(css_classes, str):
            css_classes = [css_classes]
        for cls in css_classes:
            if any(cls.startswith(prefix) for prefix in _BOILERPLATE_CLASS_PREFIXES):
                to_remove.append(element)
                break

    for element in to_remove:
        if element.attrs is not None:
            element.decompose()


def _remove_concordance_blocks(soup: BeautifulSoup) -> None:
    """Remove concordance and cross-reference annotation blocks."""
    for cls_name in _CONCORDANCE_CLASSES:
        for element in soup.find_all(class_=cls_name):
            element.decompose()
