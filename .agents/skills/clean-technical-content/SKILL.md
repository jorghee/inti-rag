---
name: clean-technical-content
description: >-
  Applies clean technical formatting, enforces zero-emoji policy, removes decorative visual ornaments,
  and verifies standard Spanish orthography (tildes, ñ, diéresis, opening marks) across technical documentation,
  code comments, issues, and PRs. Use when writing, editing, or auditing technical documentation, code comments,
  issue descriptions, or pull request bodies.
---

# Clean Technical Content Skill

## 1. Overview & Core Principle

All written artifacts in this repository must maintain professional, clear, and strictly functional formatting. Every character used must serve a technical, syntactic, structural, or semantic purpose.

> **Core Principle:** Use only characters that provide semantic, structural, syntactic, or technical value. Avoid decorative characters, visual ornaments, and emojis.

This policy does **not** restrict standard Spanish grammar. On the contrary, all content authoring in Spanish must strictly adhere to formal Spanish orthography. Diacritical marks (tildes) and proper punctuation carry essential linguistic, semantic, and phonological value and are strictly mandatory.

---

## 2. Prohibited Elements & Concrete Boundaries

1. **Emojis & Pictorial Glyphs:**
   - Never include Unicode emojis or pictorial symbols in any project file, commit message, PR title, or issue body.
   - Prohibited examples: checkmarks (`U+2705`), warning signs (`U+26A0`), rockets (`U+1F680`), celebration icons (`U+1F389`), books (`U+1F4DA`), tools (`U+1F527`), or any colored glyph.
2. **Decorative Ornaments and Banners:**
   - Visual ASCII banners, divider lines (such as `*~*~*`, `=+=+=+`, `----~----`), or decorative box drawings.
   - Decorative bullet alternatives when standard Markdown hyphens (`-`) or numbers (`1.`) suffice.
3. **Ornamental Punctuation:**
   - Repeated punctuation for emphasis (such as `!!!`, `???`, `....`).
   - Trailing ornamental dashes or tildes at the end of sentences.
4. **List Nesting Threshold:**
   - **Maximum 2 Levels of Nesting:** Standard Markdown lists are permitted up to 2 levels of indentation:
     ```markdown
     - Primary concept
       - Secondary detail or attribute
     ```
   - **Deeper Hierarchies ($\ge 3$ levels):** If information requires 3 or more hierarchical levels, do not nest lists further. Organize the content using structured subheadings (`###`), definition lists, or concise Markdown tables.

---

## 3. Permitted and Functional Characters

The policy does not restrict standard technical, syntactic, or structural characters:

1. **GitHub Native Structural Syntax:**
   - GitHub Flavored Markdown alerts (`> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]`) are functional structural syntax and are **fully permitted**.
   - GitHub task list syntax (`- [ ]`, `- [x]`) is standard functional syntax and is **fully permitted**.
   - Standard headers (`#`, `##`, `###`), table pipes (`|`), inline code (`` `code` ``), and fenced code blocks.
2. **Programming Language & Configuration Syntax:**
   - All standard programming language operators, delimiters, brackets, and structural syntax in Python, SQL, HTML, CSS, JavaScript, JSON, and YAML.
   - Conventional commit prefixes (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`) and technical scopes in parentheses.
   - Issue and Pull Request classification tags (such as `[HU-01]`, `[TASK-05.2]`, `[ADR-001]`).
3. **Spanish Language Orthography (Mandatory for Prose):**
   - When writing content in Spanish (documentation in `docs/`, Issues, Pull Requests, review reports, and discussions), the following are strictly mandatory:
     - The letter "ñ" and "Ñ".
     - Vowels with acute accents (tildes): á, é, í, ó, ú (and uppercase: Á, É, Í, Ó, Ú).
     - The diaeresis: ü, Ü (e.g., "antigüedad", "lingüística").
     - Spanish opening punctuation marks: "¿" and "¡".
   - Accents, diacritics, and Spanish opening punctuation provide indispensable phonological, semantic, and syntactic value. They are **never** considered decorative characters or visual ornaments.
4. **Code & Technical Identifiers Boundary:**
   - Programming language identifiers (class names, variable names, function names, package paths), directory names, file names (kebab-case), git branch names, and git commit messages must remain in English or unaccented ASCII characters to maintain compatibility with compilers, shell scripts, and Linux filesystem standards.

---

## 4. Execution & Verification Procedure

When writing or reviewing any document, follow this 3-step verification:

1. **Step 1 (Emoji & Ornament Scrub):** Search the text for Unicode emojis or decorative dividers. Strip them or replace them with standard Markdown headers or GitHub alerts.
2. **Step 2 (Spanish Orthography Check):** If the text is in Spanish, verify that all accent-bearing words are properly accented (e.g. *análisis*, *código*, *información*, *está*, *metodología*) and questions open with `¿`.
3. **Step 3 (Nesting Audit):** Inspect bulleted lists. If any list item contains sub-sub-bullets (3+ levels), refactor that section into a Markdown table or distinct subheadings.
