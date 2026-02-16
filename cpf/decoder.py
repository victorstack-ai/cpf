"""CPF -> English markdown decoder.

Takes a CPF v1 document (string or AST) and produces readable
English markdown that preserves the semantic meaning.
"""

from __future__ import annotations

import re

from .abbreviations import DECODE_MAP
from .ast_nodes import Block, CPFDocument
from .parser import parse
from .spec import SIGILS


# Maps sigil to a readable section title prefix
_SIGIL_TITLES: dict[str, str] = {
    "R": "",          # Rules get their block_id as title
    "P": "Priorities",
    "N": "Restrictions",
    "S": "Steps",
    "T": "",          # Tone/persona get block_id as title
    "X": "Exact Requirements",
    "Z": "Scope",
    "C": "",          # Constants not rendered
    "B": "",          # Blobs get block_id as title
}


def decode(text: str, custom_decode: dict[str, str] | None = None) -> str:
    """Decode a CPF v1 string into English markdown.

    Args:
        text: CPF v1 formatted string.
        custom_decode: Additional abbreviation decode mappings.

    Returns:
        English markdown string.
    """
    doc = parse(text)
    return decode_ast(doc, custom_decode=custom_decode)


def decode_ast(doc: CPFDocument, custom_decode: dict[str, str] | None = None) -> str:
    """Decode a CPFDocument AST into English markdown."""
    abbrevs = {**DECODE_MAP, **(custom_decode or {})}

    # Collect constants from @C blocks for inline expansion
    constants = doc.get_constants()
    if constants:
        abbrevs.update(constants)

    lines: list[str] = []
    lines.append(f"# {doc.metadata.title}")
    lines.append("")

    for block in doc.blocks:
        # Skip constant blocks (consumed for abbreviation expansion)
        if block.sigil == "C":
            continue

        # Section header
        header = _block_header(block)
        lines.append(f"## {header}")
        lines.append("")

        if block.is_heredoc:
            # Blob: pass through as-is in a code block or plain text
            for content_line in block.lines:
                lines.append(content_line)
            lines.append("")
            continue

        # Decode each line based on block type
        for content_line in block.lines:
            expanded = expand_line(content_line, abbrevs, block.sigil)
            if expanded:
                lines.append(expanded)

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def expand_line(line: str, abbrevs: dict[str, str], sigil: str = "R") -> str:
    """Expand a single CPF line into English.

    Handles operators, abbreviations, and formatting based on block type.
    """
    if not line.strip():
        return ""

    text = line.strip()

    # Conditional: "?condition->action" or "?!condition->action"
    if text.startswith("?!"):
        text = _expand_conditional(text[2:], negated=True, abbrevs=abbrevs)
        return f"- Unless {text}"
    if text.startswith("?"):
        text = _expand_conditional(text[1:], negated=False, abbrevs=abbrevs)
        return f"- If {text}"

    # Negation: "!!something"
    if text.startswith("!!"):
        content = _expand_fragment(text[2:], abbrevs)
        return f"- Do NOT {content}."

    # Emphasis/must: "*something"
    if text.startswith("*"):
        content = _expand_fragment(text[1:], abbrevs)
        return f"- **{_capitalize(content)}.**"

    # Priority: "#1 something"
    m = re.match(r"^#(\d+)\s+(.+)$", text)
    if m:
        num = m.group(1)
        content = _expand_fragment(m.group(2), abbrevs)
        return f"{num}. {_capitalize(content)}"

    # Prefer: "prefer(X)>Y"
    m = re.match(r"^prefer\((.+?)\)>(.+)$", text)
    if m:
        preferred = _expand_fragment(m.group(1), abbrevs)
        over = _expand_fragment(m.group(2), abbrevs)
        return f"- Prefer {preferred} over {over}."

    # Definition: "key::value"
    if "::" in text and not text.startswith("@>"):
        parts = text.split("::", 1)
        key = _expand_fragment(parts[0], abbrevs)
        val = _expand_fragment(parts[1], abbrevs)
        return f"- **{_capitalize(key)}:** {val}."

    # Delegate: "@>reference"
    if text.startswith("@>"):
        ref = _expand_fragment(text[2:], abbrevs)
        return f"- See {ref}."

    # Default: expand as a bullet
    content = _expand_fragment(text, abbrevs)
    return f"- {_capitalize(content)}."


def _expand_conditional(text: str, negated: bool, abbrevs: dict[str, str]) -> str:
    """Expand a conditional expression."""
    # Split on -> for condition -> action
    if "->" in text:
        parts = text.split("->", 1)
        condition = _expand_fragment(parts[0], abbrevs)
        action_part = parts[1]

        # Handle else: "action;else_action"
        if ";" in action_part:
            action_parts = action_part.split(";", 1)
            action = _expand_fragment(action_parts[0], abbrevs)
            else_part = action_parts[1].strip()

            # Check if else part is a negation
            if else_part.startswith("!!"):
                else_text = _expand_fragment(else_part[2:], abbrevs)
                return f"{condition}: {action}. Do NOT {else_text}."
            else:
                else_text = _expand_fragment(else_part, abbrevs)
                return f"{condition}: {action}. Otherwise, {else_text}."
        else:
            action = _expand_fragment(action_part, abbrevs)
            prefix = "not " if negated else ""
            return f"{prefix}{condition}: {action}."
    else:
        content = _expand_fragment(text, abbrevs)
        prefix = "not " if negated else ""
        return f"{prefix}{content}."


def _expand_fragment(text: str, abbrevs: dict[str, str]) -> str:
    """Expand abbreviations and operators in a text fragment."""
    # Replace operators with English words
    text = text.replace("=>", " results in ")
    text = text.replace("->", " then ")
    text = re.sub(r"@>", "see ", text)

    # Replace + with " and " (but not inside parentheses for grouped items)
    text = _replace_outside_parens(text, "+", " and ")

    # Replace | with " or "
    text = _replace_outside_parens(text, "|", " or ")

    # Expand abbreviations (reverse: short -> full)
    text = _apply_expansions(text, abbrevs)

    # Clean up spacing
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _replace_outside_parens(text: str, old: str, new: str) -> str:
    """Replace `old` with `new` but only outside parentheses."""
    depth = 0
    result = []
    i = 0
    while i < len(text):
        if text[i] == "(":
            depth += 1
            result.append(text[i])
        elif text[i] == ")":
            depth = max(0, depth - 1)
            result.append(text[i])
        elif depth == 0 and text[i:i + len(old)] == old:
            result.append(new)
            i += len(old)
            continue
        else:
            result.append(text[i])
        i += 1
    return "".join(result)


def _apply_expansions(text: str, abbrevs: dict[str, str]) -> str:
    """Replace abbreviations with full words."""
    # Sort by length descending to avoid partial matches
    sorted_entries = sorted(abbrevs.items(), key=lambda x: len(x[0]), reverse=True)

    for abbr, full in sorted_entries:
        # Only match as whole tokens (word boundaries or adjacent to operators)
        pattern = r"(?<![a-zA-Z])" + re.escape(abbr) + r"(?![a-zA-Z])"
        text = re.sub(pattern, full, text)

    return text


def _capitalize(text: str) -> str:
    """Capitalize first letter if it's lowercase."""
    if text and text[0].islower():
        return text[0].upper() + text[1:]
    return text


def _block_header(block: Block) -> str:
    """Generate a readable section header from block sigil and ID."""
    base_title = _SIGIL_TITLES.get(block.sigil, "")
    # Convert block_id from kebab-case to Title Case
    id_title = block.block_id.replace("-", " ").title()

    if base_title:
        return f"{base_title}: {id_title}"
    return id_title
