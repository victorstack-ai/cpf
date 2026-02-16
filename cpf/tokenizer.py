"""Line-level tokenizer: compress a single English line into CPF notation.

This is the core compression engine. It applies operator substitution,
abbreviation mapping, and aggressive filler/grammar removal to produce
compact CPF lines optimized for LLM consumption.
"""

from __future__ import annotations

import re

from .abbreviations import ENCODE_MAP
from .patterns import (
    AND_CONNECTOR_RE,
    ARTICLES_RE,
    BOLD_KV_RE,
    CONDITIONAL_RE,
    FILLER_WORDS,
    IMPERATIVE_RE,
    NEGATION_LINE_RE,
    NUMBERED_RE,
    OR_CONNECTOR_RE,
    PREFER_RE,
)
from .utils import collapse_whitespace, strip_bullet_prefix, strip_markdown_formatting


# Additional filler/grammar to strip for aggressive compression
_PRONOUNS_RE = re.compile(
    r"\b(you|your|yours|we|our|they|their|them|it|its|this|that|these|those|"
    r"which|who|whom|whose)\b\s*",
    re.I,
)

# Verbose phrases to collapse
_VERBOSE_PHRASES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bfor example\b", re.I), "e.g."),
    (re.compile(r"\bfor instance\b", re.I), "e.g."),
    (re.compile(r"\bsuch as\b", re.I), "e.g."),
    (re.compile(r"\bin order to\b", re.I), "to"),
    (re.compile(r"\bso that\b", re.I), "so"),
    (re.compile(r"\bas well as\b", re.I), "+"),
    (re.compile(r"\balong with\b", re.I), "+"),
    (re.compile(r"\bin addition to\b", re.I), "+"),
    (re.compile(r"\bwith respect to\b", re.I), "re:"),
    (re.compile(r"\bwith regard to\b", re.I), "re:"),
    (re.compile(r"\bregarding\b", re.I), "re:"),
    (re.compile(r"\bis required\b", re.I), "req"),
    (re.compile(r"\bare required\b", re.I), "req"),
    (re.compile(r"\bis not\b", re.I), "!"),
    (re.compile(r"\bare not\b", re.I), "!"),
    (re.compile(r"\bdo not\b", re.I), "!!"),
    (re.compile(r"\bshould not\b", re.I), "!!"),
    (re.compile(r"\bmust not\b", re.I), "!!"),
    (re.compile(r"\bcan not\b", re.I), "!!"),
    (re.compile(r"\bcannot\b", re.I), "!!"),
    (re.compile(r"\bshould be\b", re.I), "=>"),
    (re.compile(r"\bneeds to be\b", re.I), "=>"),
    (re.compile(r"\bhas to be\b", re.I), "=>"),
    (re.compile(r"\bwhen possible\b", re.I), "[possible]"),
    (re.compile(r"\bwhere appropriate\b", re.I), "[appropriate]"),
    (re.compile(r"\bwhere needed\b", re.I), "[needed]"),
    (re.compile(r"\bif needed\b", re.I), "[needed]"),
    (re.compile(r"\bif applicable\b", re.I), "[applicable]"),
    (re.compile(r"\bwhen relevant\b", re.I), "[relevant]"),
    (re.compile(r"\bif relevant\b", re.I), "[relevant]"),
    (re.compile(r"\bat least\b", re.I), ">="),
    (re.compile(r"\bat minimum\b", re.I), ">="),
    (re.compile(r"\bat most\b", re.I), "<="),
    (re.compile(r"\bmore than\b", re.I), ">"),
    (re.compile(r"\bless than\b", re.I), "<"),
    (re.compile(r"\bgreater than\b", re.I), ">"),
    (re.compile(r"\bresults? in\b", re.I), "=>"),
    (re.compile(r"\bleads? to\b", re.I), "=>"),
    (re.compile(r"\bsee\s+", re.I), "@>"),
    (re.compile(r"\brefer to\b", re.I), "@>"),
    (re.compile(r"\bmake sure\b", re.I), "ensure"),
    (re.compile(r"\bbe sure to\b", re.I), "ensure"),
]

# Sentence-ending fluff to strip
_TRAILING_FLUFF = re.compile(
    r"\s*[.;,]+\s*$"
)

# Multiple consecutive punctuation/operators
_MULTI_OPERATORS = re.compile(r"([+|;])\1+")


def compress_line(line: str, encode_map: dict[str, str] | None = None) -> str:
    """Compress a single English instruction line into CPF notation.

    Pipeline:
    1. Strip markdown formatting
    2. Detect and replace structural patterns (conditionals, negations, etc.)
    3. Apply aggressive grammar/filler removal
    4. Replace connectors with operators
    5. Apply abbreviation dictionary
    6. Collapse whitespace and clean up
    """
    if not line.strip():
        return ""

    abbrevs = encode_map or ENCODE_MAP
    text = strip_bullet_prefix(line)
    text = strip_markdown_formatting(text)

    # --- Pattern-based structural replacements ---

    # Conditional: "If X: Y" -> "?X->Y"
    m = CONDITIONAL_RE.match(text)
    if m:
        condition = m.group(1).strip().rstrip(":")
        action = m.group(2).strip().rstrip(".")
        condition = _compress_fragment(condition, abbrevs)
        action = _compress_fragment(action, abbrevs)
        return f"?{condition}->{action}"

    # Negation: "Do NOT X" / "Never X" -> "!!X"
    m = NEGATION_LINE_RE.match(text)
    if m:
        content = m.group(1).strip().rstrip(".")
        content = _compress_fragment(content, abbrevs)
        return f"!!{content}"

    # Imperative: "Always X" / "Must X" -> "*X"
    m = IMPERATIVE_RE.match(text)
    if m:
        content = m.group(1).strip().rstrip(".")
        content = _compress_fragment(content, abbrevs)
        return f"*{content}"

    # Prefer: "Prefer X over Y" -> "prefer(X)>Y"
    m = PREFER_RE.match(text)
    if m:
        preferred = _compress_fragment(m.group(1).strip(), abbrevs)
        over = _compress_fragment(m.group(2).strip().rstrip("."), abbrevs)
        return f"prefer({preferred})>{over}"

    # Bold key-value: "**Key:** value" -> "key::value"
    m = BOLD_KV_RE.match(text)
    if m:
        key = _compress_fragment(m.group(1).strip(), abbrevs)
        val = _compress_fragment(m.group(2).strip().rstrip("."), abbrevs)
        return f"{key}::{val}"

    # Numbered: "1. Something" -> "#1 something"
    m = NUMBERED_RE.match(text)
    if m:
        num = m.group(1)
        content = _compress_fragment(m.group(2).strip().rstrip("."), abbrevs)
        return f"#{num} {content}"

    # Default: apply aggressive compression
    return _compress_fragment(text, abbrevs)


def _compress_fragment(text: str, abbrevs: dict[str, str]) -> str:
    """Apply aggressive compression to a text fragment.

    Designed for LLM consumption: strips all grammar that LLMs can infer.
    """
    # Apply verbose phrase replacements first (multi-word -> operator)
    for pattern, replacement in _VERBOSE_PHRASES:
        text = pattern.sub(replacement, text)

    # Remove filler words
    text = FILLER_WORDS.sub("", text)

    # Remove articles
    text = ARTICLES_RE.sub("", text)

    # Remove pronouns (LLMs infer subject from context)
    text = _PRONOUNS_RE.sub("", text)

    # Replace connectors
    text = AND_CONNECTOR_RE.sub("+", text)
    text = OR_CONNECTOR_RE.sub("|", text)

    # Apply abbreviations (whole-word, case-insensitive)
    text = _apply_abbreviations(text, abbrevs)

    # Strip trailing punctuation fluff
    text = _TRAILING_FLUFF.sub("", text)

    # Collapse whitespace
    text = collapse_whitespace(text)

    # Clean up operator spacing
    text = re.sub(r"\s*\+\s*", "+", text)
    text = re.sub(r"\s*\|\s*", "|", text)
    text = re.sub(r"\s*->\s*", "->", text)
    text = re.sub(r"\s*=>\s*", "=>", text)
    text = re.sub(r"\s*::\s*", "::", text)

    # Remove duplicate operators
    text = _MULTI_OPERATORS.sub(r"\1", text)

    # Strip leading/trailing operator artifacts
    text = text.strip(" +|;,.")

    return text


def _apply_abbreviations(text: str, abbrevs: dict[str, str]) -> str:
    """Replace whole words with their abbreviations.

    Handles multi-word phrases first (e.g. 'dependency injection' -> 'di'),
    then single words. Case-insensitive matching.
    """
    # Sort by length descending so multi-word phrases match first
    sorted_entries = sorted(abbrevs.items(), key=lambda x: len(x[0]), reverse=True)

    for full, abbr in sorted_entries:
        pattern = r"\b" + re.escape(full) + r"\b"
        text = re.sub(pattern, abbr, text, flags=re.I)

    return text
