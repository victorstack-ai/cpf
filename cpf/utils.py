"""Shared utilities for CPF encoding/decoding."""

from __future__ import annotations

import re


def slugify(text: str) -> str:
    """Convert a section header to a kebab-case block ID.

    'Module / Plugin first approach' -> 'mod-plg-first-approach'
    '## Git and PR standards' -> 'git-pr-standards'
    """
    # Strip markdown heading markers
    text = re.sub(r"^#+\s*", "", text)
    # Strip bold markers
    text = text.replace("**", "")
    # Lowercase
    text = text.lower().strip()
    # Replace non-alphanum with hyphens
    text = re.sub(r"[^a-z0-9]+", "-", text)
    # Collapse multiple hyphens
    text = re.sub(r"-+", "-", text)
    # Strip leading/trailing hyphens
    return text.strip("-")


def strip_markdown_formatting(text: str) -> str:
    """Remove markdown bold/italic markers from text."""
    text = text.replace("**", "")
    text = text.replace("__", "")
    # Single * or _ for italic — only strip pairs
    text = re.sub(r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", r"\1", text)
    text = re.sub(r"(?<!_)_(?!_)(.*?)(?<!_)_(?!_)", r"\1", text)
    return text


def strip_articles(text: str) -> str:
    """Remove English articles (a, an, the) that add no semantic value for LLMs."""
    return re.sub(r"\b(a|an|the)\b\s*", "", text, flags=re.IGNORECASE)


def collapse_whitespace(text: str) -> str:
    """Collapse multiple spaces/tabs into single space."""
    return re.sub(r"[ \t]+", " ", text).strip()


def strip_bullet_prefix(line: str) -> str:
    """Remove leading '- ' or '* ' bullet markers."""
    stripped = line.strip()
    if stripped.startswith("- "):
        return stripped[2:]
    if stripped.startswith("* "):
        return stripped[2:]
    return stripped


def is_numbered_item(line: str) -> tuple[bool, int, str]:
    """Check if line is a numbered list item. Returns (is_numbered, number, content)."""
    match = re.match(r"^\s*(\d+)\.\s+(.+)$", line)
    if match:
        return True, int(match.group(1)), match.group(2)
    return False, 0, line


def extract_section_header(line: str) -> str | None:
    """Extract section name from markdown header line (## Header)."""
    match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
    if match:
        return match.group(2).strip()
    return None


def count_tokens_estimate(text: str) -> int:
    """Rough token count estimate (~4 chars per token for English, ~3 for CPF).

    This is a rough heuristic, not an exact tokenizer.
    """
    # Split on whitespace and punctuation boundaries
    words = re.findall(r"\S+", text)
    # Rough estimate: each word is ~1.3 tokens on average
    return max(1, int(len(words) * 1.3))
