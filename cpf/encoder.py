"""English markdown -> CPF encoder.

Takes a markdown file with sections (## headers) containing
instruction bullets and produces a CPF v1 document.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from .abbreviations import ENCODE_MAP
from .ast_nodes import Block, CPFDocument, Metadata
from .formatter import format_document
from .patterns import EXACT_MATCH_RE, PATH_REF_RE, classify_section
from .tokenizer import compress_line
from .utils import extract_section_header, slugify


def encode(
    text: str,
    *,
    doc_id: str | None = None,
    title: str | None = None,
    source: str = "",
    custom_abbrevs: dict[str, str] | None = None,
) -> str:
    """Encode an English markdown instruction document into CPF v1 format.

    Args:
        text: Markdown text with ## sections and bullet items.
        doc_id: Document ID (auto-generated from title if not given).
        title: Document title (extracted from # header if not given).
        source: Source file path or URL.
        custom_abbrevs: Additional abbreviation mappings to merge with defaults.

    Returns:
        CPF v1 formatted string.
    """
    abbrevs = {**ENCODE_MAP, **(custom_abbrevs or {})}
    sections = _split_sections(text)

    # Extract title from first H1 if present
    if not title:
        for header, _ in sections:
            if header:
                title = header
                break
        if not title:
            title = "Untitled"

    if not doc_id:
        doc_id = slugify(title)[:40]

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    metadata = Metadata(doc_id=doc_id, title=title, source=source, timestamp=timestamp)

    # Extract path aliases: find repeated long paths and create $VAR references
    path_aliases = _extract_path_aliases(text)

    blocks: list[Block] = []

    # Emit path constants block if we have aliases
    if path_aliases:
        const_lines = [f"${alias}::{path}" for path, alias in path_aliases.items()]
        blocks.append(Block(sigil="C", block_id="paths", lines=const_lines))

    for header, lines in sections:
        if not header or not lines:
            continue

        # Filter to non-empty content lines
        content_lines = [l for l in lines if l.strip()]
        if not content_lines:
            continue

        # Classify section type
        sigil = classify_section(header, content_lines)
        block_id = slugify(header)[:50]

        # Check for exact match requirements -> produce @X block
        exact_matches = _extract_exact_matches(content_lines)
        if exact_matches and sigil == "R":
            # If section has both rules and exact matches, split them
            pass  # Keep as rule block; exact matches embedded in content

        # Check for path-heavy content -> override to @Z
        path_count = sum(1 for l in content_lines if PATH_REF_RE.search(l))
        if path_count > 0 and path_count / len(content_lines) > 0.5:
            sigil = "Z"

        # Compress each line
        compressed_lines = []
        for line in content_lines:
            compressed = compress_line(line, abbrevs)
            # Apply path aliases
            if compressed and path_aliases:
                for path, alias in path_aliases.items():
                    compressed = compressed.replace(path, f"${alias}")
            if compressed:
                compressed_lines.append(compressed)

        if compressed_lines:
            blocks.append(Block(
                sigil=sigil,
                block_id=block_id,
                lines=compressed_lines,
            ))

    doc = CPFDocument(version="v1", metadata=metadata, blocks=blocks)
    return format_document(doc)


def encode_file(
    path: Path,
    *,
    doc_id: str | None = None,
    title: str | None = None,
    custom_abbrevs: dict[str, str] | None = None,
) -> str:
    """Encode a markdown file into CPF v1 format."""
    text = path.read_text(encoding="utf-8")
    return encode(
        text,
        doc_id=doc_id,
        title=title,
        source=str(path),
        custom_abbrevs=custom_abbrevs,
    )


def _split_sections(text: str) -> list[tuple[str | None, list[str]]]:
    """Split markdown text into (header, [content_lines]) tuples.

    Groups content under ## headers. Content before the first header
    gets header=None.
    """
    sections: list[tuple[str | None, list[str]]] = []
    current_header: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines():
        header = extract_section_header(line)
        if header is not None:
            # Save previous section
            if current_header is not None or current_lines:
                sections.append((current_header, current_lines))
            current_header = header
            current_lines = []
        else:
            current_lines.append(line)

    # Save last section
    if current_header is not None or current_lines:
        sections.append((current_header, current_lines))

    return sections


def _extract_exact_matches(lines: list[str]) -> list[str]:
    """Extract exact string requirements from lines."""
    matches = []
    for line in lines:
        m = EXACT_MATCH_RE.search(line)
        if m:
            matches.append(m.group(1))
    return matches


def _extract_path_aliases(text: str) -> dict[str, str]:
    """Find long paths that appear 2+ times and create short aliases.

    Returns {path: alias} mapping.
    """
    # Find all paths (at least 30 chars to be worth aliasing)
    paths = PATH_REF_RE.findall(text)
    path_counts: dict[str, int] = {}
    for p in paths:
        if len(p) >= 30:
            path_counts[p] = path_counts.get(p, 0) + 1

    # Only alias paths that appear 2+ times
    aliases: dict[str, str] = {}
    counter = 0
    for path, count in sorted(path_counts.items(), key=lambda x: -x[1]):
        if count < 2:
            continue
        # Generate short alias from last path component
        parts = path.rstrip("/").split("/")
        alias = parts[-1].lower().replace(".", "-").replace(" ", "-")[:12]
        if alias in aliases.values():
            alias = f"{alias}{counter}"
        aliases[path] = alias
        counter += 1

    return aliases
