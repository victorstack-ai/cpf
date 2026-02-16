"""Validate CPF v1 documents for correctness."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .spec import (
    BLOCK_RE_PATTERN,
    FORMAT_HEADER,
    HEREDOC_CLOSE,
    HEREDOC_OPEN,
    METADATA_PREFIX,
    SECTION_SEPARATOR,
    SIGILS,
)


@dataclass
class ValidationError:
    """A single validation issue."""
    line: int
    message: str
    severity: str = "error"  # "error" or "warning"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] Line {self.line}: {self.message}"


_BLOCK_RE = re.compile(BLOCK_RE_PATTERN)


def validate(text: str) -> list[ValidationError]:
    """Validate a CPF v1 document. Returns list of errors (empty = valid)."""
    errors: list[ValidationError] = []
    lines = text.splitlines()

    if not lines:
        errors.append(ValidationError(1, "Empty document"))
        return errors

    # Line 1: format header
    if lines[0].strip() != FORMAT_HEADER:
        errors.append(ValidationError(1, f"Expected '{FORMAT_HEADER}', got '{lines[0].strip()}'"))
        return errors  # Can't continue without valid header

    # Line 2: metadata
    if len(lines) < 2:
        errors.append(ValidationError(2, "Missing metadata line"))
        return errors

    meta_line = lines[1].strip()
    if not meta_line.startswith(METADATA_PREFIX):
        errors.append(ValidationError(2, f"Expected metadata starting with '{METADATA_PREFIX}'"))
    else:
        fields = meta_line[len(METADATA_PREFIX):].split("|")
        if len(fields) < 4:
            errors.append(ValidationError(
                2, f"Metadata needs 4 pipe-separated fields, got {len(fields)}"
            ))

    # Line 3: separator
    if len(lines) < 3:
        errors.append(ValidationError(3, f"Missing '{SECTION_SEPARATOR}' separator"))
        return errors

    if lines[2].strip() != SECTION_SEPARATOR:
        errors.append(ValidationError(3, f"Expected '{SECTION_SEPARATOR}', got '{lines[2].strip()}'"))

    # Lines 4+: validate blocks
    block_ids: set[str] = set()
    in_heredoc = False
    heredoc_start = 0
    i = 3

    while i < len(lines):
        line = lines[i].strip()

        if in_heredoc:
            if line == HEREDOC_CLOSE:
                in_heredoc = False
            i += 1
            continue

        if not line:
            i += 1
            continue

        m = _BLOCK_RE.match(line)
        if m:
            sigil = m.group(1)
            block_id = m.group(2).strip()

            if sigil not in SIGILS:
                errors.append(ValidationError(
                    i + 1, f"Unknown sigil '{sigil}'. Valid: {', '.join(sorted(SIGILS))}"
                ))

            if not block_id:
                errors.append(ValidationError(i + 1, "Block ID is empty"))
            elif block_id in block_ids:
                errors.append(ValidationError(
                    i + 1, f"Duplicate block ID '{block_id}'",
                    severity="warning",
                ))
            block_ids.add(block_id)

            # Check for heredoc in blob blocks
            if sigil == "B":
                if i + 1 < len(lines) and lines[i + 1].strip() == HEREDOC_OPEN:
                    in_heredoc = True
                    heredoc_start = i + 1
                    i += 2
                    continue
                else:
                    errors.append(ValidationError(
                        i + 1, f"@B block must be followed by '{HEREDOC_OPEN}'"
                    ))

        i += 1

    if in_heredoc:
        errors.append(ValidationError(
            heredoc_start + 1,
            f"Unclosed heredoc block (missing '{HEREDOC_CLOSE}')"
        ))

    return errors


def is_valid(text: str) -> bool:
    """Quick check: is this a valid CPF document?"""
    return not any(e.severity == "error" for e in validate(text))
