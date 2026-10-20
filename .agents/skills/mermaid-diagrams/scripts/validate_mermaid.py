#!/usr/bin/env python3
"""
validate_mermaid.py - Syntax & GitHub Compatibility Validator for Mermaid Diagrams

Validates Mermaid diagrams in markdown files against GitHub native rendering constraints
and project clean-technical-content rules.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

SUPPORTED_TYPES = (
    "flowchart",
    "graph",
    "sequenceDiagram",
    "classDiagram",
    "stateDiagram-v2",
    "stateDiagram",
    "erDiagram",
    "gitGraph",
    "gantt",
    "pie",
    "mindmap",
    "timeline",
    "quadrantChart",
)

UNSUPPORTED_GITHUB_TYPES = (
    "C4Context",
    "C4Container",
    "C4Component",
    "C4Dynamic",
    "C4Deployment",
)

RESERVED_SEQUENCE_PARTICIPANTS = {
    "loop",
    "alt",
    "opt",
    "par",
    "critical",
    "break",
    "end",
    "rect",
}

MERMAID_BLOCK_RE = re.compile(r"```mermaid\s*\n(.*?)\n```", re.DOTALL)
UNQUOTED_PAREN_RE = re.compile(r'\[(?!"[^"]*")([^\]]*?\([^\]]*?\)[^\]]*?)\]')


def has_emoji(text: str) -> bool:
    for ch in text:
        cp = ord(ch)
        if (
            (0x1F300 <= cp <= 0x1F9FF)
            or (0x2600 <= cp <= 0x27BF)
            or (0x1F1E6 <= cp <= 0x1F1FF)
            or (0xFE00 <= cp <= 0xFE0F)
        ):
            return True
    return False


def check_unquoted_parens(line: str) -> bool:
    for m in re.finditer(r'\[([^\]]+)\]', line):
        content = m.group(1).strip()
        if content.startswith('("') and content.endswith('")'):
            continue
        if content.startswith('"') and content.endswith('"'):
            continue
        if '(' in content or ')' in content:
            return True
    return False


def validate_diagram(content: str, file_path: Path, block_num: int) -> list[str]:
    errors = []
    lines = [line.strip() for line in content.strip().splitlines() if line.strip()]

    if not lines:
        errors.append(f"Block {block_num}: Empty Mermaid diagram block")
        return errors

    # Check for emojis
    for line_idx, line in enumerate(lines, 1):
        if has_emoji(line):
            errors.append(
                f"Block {block_num}, Line {line_idx}: Contains prohibited emoji character in violation of clean-technical-content"
            )

    # First non-comment, non-frontmatter line should be the diagram type
    first_meaningful_line = None
    in_frontmatter = False

    for line in lines:
        if line.startswith("---"):
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter or line.startswith("%%"):
            continue
        first_meaningful_line = line
        break

    if not first_meaningful_line:
        errors.append(f"Block {block_num}: No diagram type declared")
        return errors

    diag_type = first_meaningful_line.split()[0]

    # Check for unsupported C4 syntax on GitHub
    if diag_type in UNSUPPORTED_GITHUB_TYPES:
        errors.append(
            f"Block {block_num}: Diagram type '{diag_type}' is not supported natively by GitHub Markdown. Use 'flowchart' with subgraphs instead."
        )

    # Check for supported types
    matched_type = any(first_meaningful_line.startswith(t) for t in SUPPORTED_TYPES)
    if not matched_type and diag_type not in UNSUPPORTED_GITHUB_TYPES:
        errors.append(
            f"Block {block_num}: Unrecognized diagram declaration '{first_meaningful_line}'. Must start with one of {SUPPORTED_TYPES}"
        )

    # Check sequence diagram specific quirks
    if first_meaningful_line.startswith("sequenceDiagram"):
        for line_idx, line in enumerate(lines, 1):
            if line.startswith("participant ") or line.startswith("actor "):
                parts = line.split()
                if len(parts) >= 2 and parts[1].lower() in RESERVED_SEQUENCE_PARTICIPANTS:
                    errors.append(
                        f"Block {block_num}, Line {line_idx}: Reserved keyword '{parts[1]}' used as participant ID. Alias it using 'participant ID as Label'."
                    )
            # Check for unescaped semicolon in message labels
            if "->>" in line or "-->>" in line or "->>" in line:
                if ";" in line:
                    errors.append(
                        f"Block {block_num}, Line {line_idx}: Semicolon in message label may truncate text on GitHub. Replace with hyphen or period."
                    )

    # Check flowchart specific quirks (unquoted parentheses inside labels)
    if first_meaningful_line.startswith(("flowchart", "graph")):
        for line_idx, line in enumerate(lines, 1):
            if line.startswith("%%") or line.startswith("subgraph"):
                continue
            if check_unquoted_parens(line):
                errors.append(
                    f"Block {block_num}, Line {line_idx}: Parentheses inside node label must be enclosed in double quotes: e.g. node[\"Label (Info)\"]. Line: {line}"
                )

    return errors


def validate_file(path: Path) -> tuple[int, list[str]]:
    content = path.read_text(encoding="utf-8")
    blocks = MERMAID_BLOCK_RE.findall(content)
    all_errors = []

    for idx, block in enumerate(blocks, 1):
        errs = validate_diagram(block, path, idx)
        for e in errs:
            all_errors.append(f"{path}: {e}")

    return len(blocks), all_errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Mermaid diagrams in markdown files")
    parser.add_argument("paths", nargs="*", default=["."], help="Files or directories to scan")
    args = parser.parse_args()

    total_blocks = 0
    total_errors = []

    for target in args.paths:
        p = Path(target)
        if p.is_file() and p.suffix == ".md":
            count, errs = validate_file(p)
            total_blocks += count
            total_errors.extend(errs)
        elif p.is_dir():
            for md_file in p.rglob("*.md"):
                if ".git" in md_file.parts:
                    continue
                count, errs = validate_file(md_file)
                total_blocks += count
                total_errors.extend(errs)

    print(f"Validated {total_blocks} Mermaid diagram blocks across scanned files.")
    if total_errors:
        print(f"FAILED: Found {len(total_errors)} issue(s):")
        for err in total_errors:
            print(f"  ERROR: {err}")
        return 1

    print("OK - All Mermaid diagrams comply with GitHub rendering guardrails and project rules.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
