"""Regex patterns for detecting compressible English structures.

Each detector returns structured data that the tokenizer uses
to apply the appropriate compression.
"""

from __future__ import annotations

import re

# --- Section classification patterns ---

# Headings that signal priority/ordering content
PRIORITY_HEADERS = re.compile(
    r"(priorit|order|hierarchy|ranking|precedence)", re.I
)

# Headings that signal negation/prohibition content
NEGATION_HEADERS = re.compile(
    r"(restriction|prohibited|forbidden|don.t|avoid|never|quality.gate|checklist)", re.I
)

# Headings that signal tone/persona/style
TONE_HEADERS = re.compile(
    r"(tone|personality|style|voice|character|persona|communication|approach)", re.I
)

# Headings that signal sequence/steps
SEQUENCE_HEADERS = re.compile(
    r"(step|sequence|workflow|procedure|process|after|before|how.to)", re.I
)

# Headings that signal scope/zone/boundary
ZONE_HEADERS = re.compile(
    r"(boundar|scope|zone|path|workspace|directory|folder)", re.I
)

# --- Line-level patterns ---

# Conditional: "If X", "When X", "If a maintained..."
CONDITIONAL_RE = re.compile(
    r"^(?:\*\*)?(?:If|When|Unless)\b\s*(.+?)(?:\*\*)?(?:[:,]\s*|\s*[-—]\s*)(.*)",
    re.I,
)

# Negation: "Do NOT X", "Never X", "Avoid X"
NEGATION_LINE_RE = re.compile(
    r"^(?:\*\*)?(?:Do\s+NOT|do\s+not|Don't|dont|Never|Avoid|NEVER)\b\s*(.+?)(?:\*\*)?\.?\s*$",
    re.I,
)

# Exact match requirement: "MUST be `X`", "must equal `X`"
EXACT_MATCH_RE = re.compile(
    r"(?:MUST|must|shall)\s+(?:be|equal|match|use)\s+[`\"']([^`\"']+)[`\"']",
    re.I,
)

# Priority/numbered items: "1. Something", "2. Something"
NUMBERED_RE = re.compile(r"^\s*(\d+)\.\s+(.+)$")

# Path reference: /path/to/something
PATH_REF_RE = re.compile(r"(/[\w./-]+(?:/[\w./-]+)+)")

# Bold key-value: "**Key:** value" or "**Key** — value"
BOLD_KV_RE = re.compile(
    r"^\*\*(.+?)\*\*\s*(?:[:—-]+)\s*(.+)$"
)

# Definition: "X means Y", "X is defined as Y"
DEFINITION_RE = re.compile(
    r"^(.+?)\s+(?:means|is defined as|is|are)\s+(.+)$", re.I
)

# "Prefer X over Y" / "Prefer X > Y"
PREFER_RE = re.compile(
    r"(?:Prefer|prefer)\s+(.+?)\s+(?:over|>|instead of|rather than)\s+(.+)", re.I
)

# Imperative with strong emphasis: "Always X", "Must X"
IMPERATIVE_RE = re.compile(
    r"^(?:\*\*)?(?:Always|Must|Ensure|Make sure|Required|Important)\b[:\s]*(.+?)(?:\*\*)?\.?\s*$",
    re.I,
)

# "X and Y" connector
AND_CONNECTOR_RE = re.compile(r"\b(?:and|also|as well as|along with|plus)\b", re.I)

# "X or Y" connector
OR_CONNECTOR_RE = re.compile(r"\b(?:\bor\b|alternatively)\b", re.I)

# Filler words that can be dropped without semantic loss
FILLER_WORDS = re.compile(
    r"\b(please|basically|essentially|simply|just|that is|in order to|"
    r"make sure to|be sure to|it is important to|you should|you must|"
    r"we need to|we should|there is|there are|this is|that are|which is|"
    r"which are|in this case|at this point|for this purpose)\b",
    re.I,
)

# Articles
ARTICLES_RE = re.compile(r"\b(a|an|the)\b\s*", re.I)


def classify_section(header: str, lines: list[str]) -> str:
    """Classify a markdown section into a CPF sigil based on header and content.

    Returns the sigil letter (R, P, N, S, T, Z, etc.).
    """
    header_lower = header.lower()

    # Check header keywords first
    if ZONE_HEADERS.search(header_lower):
        return "Z"
    if TONE_HEADERS.search(header_lower):
        return "T"
    if PRIORITY_HEADERS.search(header_lower):
        return "P"
    if SEQUENCE_HEADERS.search(header_lower):
        return "S"
    if NEGATION_HEADERS.search(header_lower):
        return "N"

    # Content analysis: count dominant patterns
    negation_count = sum(1 for l in lines if NEGATION_LINE_RE.match(l.strip()))
    conditional_count = sum(1 for l in lines if CONDITIONAL_RE.match(l.strip()))
    numbered_count = sum(1 for l in lines if NUMBERED_RE.match(l.strip()))

    total = len([l for l in lines if l.strip()])
    if total == 0:
        return "R"

    # If >60% negation lines, it's a negation block
    if negation_count > 0 and negation_count / total > 0.6:
        return "N"

    # If mostly numbered and looks like priorities
    if numbered_count > 0 and numbered_count / total > 0.6:
        return "P"

    # If mostly numbered and looks like steps (imperative verbs)
    if numbered_count > 0 and numbered_count / total > 0.4:
        return "S"

    # Default: rule block
    return "R"
