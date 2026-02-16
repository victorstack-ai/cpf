"""CPF document parser: CPF string -> AST."""

from __future__ import annotations

import re

from .ast_nodes import Block, CPFDocument, Metadata
from .spec import (
    BLOCK_RE_PATTERN,
    FORMAT_HEADER,
    HEREDOC_CLOSE,
    HEREDOC_OPEN,
    METADATA_PREFIX,
    SECTION_SEPARATOR,
    SIGILS,
)


class ParseError(Exception):
    """Raised when CPF document is malformed."""

    def __init__(self, line_num: int, message: str):
        self.line_num = line_num
        super().__init__(f"Line {line_num}: {message}")


_BLOCK_RE = re.compile(BLOCK_RE_PATTERN)


def parse(text: str) -> CPFDocument:
    """Parse a CPF v1 string into a CPFDocument AST.

    Raises ParseError on malformed input.
    """
    lines = text.splitlines()
    if not lines:
        raise ParseError(1, "Empty document")

    # Line 1: format header
    if lines[0].strip() != FORMAT_HEADER:
        raise ParseError(1, f"Expected '{FORMAT_HEADER}', got '{lines[0].strip()}'")

    # Line 2: metadata
    if len(lines) < 2 or not lines[1].strip().startswith(METADATA_PREFIX):
        raise ParseError(2, f"Expected metadata line starting with '{METADATA_PREFIX}'")

    metadata = _parse_metadata(lines[1].strip(), 2)

    # Line 3: separator
    if len(lines) < 3 or lines[2].strip() != SECTION_SEPARATOR:
        raise ParseError(3, f"Expected '{SECTION_SEPARATOR}' separator")

    # Lines 4+: blocks
    blocks: list[Block] = []
    i = 3
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines between blocks
        if not line:
            i += 1
            continue

        # Check for block start
        match = _BLOCK_RE.match(line)
        if match:
            sigil = match.group(1)
            block_id = match.group(2).strip()

            if sigil not in SIGILS:
                raise ParseError(i + 1, f"Unknown sigil '{sigil}'. Valid: {', '.join(SIGILS)}")

            block = Block(sigil=sigil, block_id=block_id)

            # For blob blocks, handle heredoc
            if sigil == "B":
                i += 1
                i, heredoc_lines = _parse_heredoc(lines, i)
                block.lines = heredoc_lines
                block.is_heredoc = True
            else:
                # Read content lines until next block or EOF
                i += 1
                while i < len(lines):
                    content_line = lines[i]
                    # Check if next block starts
                    if _BLOCK_RE.match(content_line.strip()):
                        break
                    # Skip empty lines at start of block
                    if not block.lines and not content_line.strip():
                        i += 1
                        continue
                    block.lines.append(content_line.rstrip())
                    i += 1

                # Strip trailing empty lines from block
                while block.lines and not block.lines[-1].strip():
                    block.lines.pop()

            blocks.append(block)
        else:
            # Orphan line outside a block — skip silently
            i += 1

    return CPFDocument(
        version="v1",
        metadata=metadata,
        blocks=blocks,
    )


def _parse_metadata(line: str, line_num: int) -> Metadata:
    """Parse M|id|title|source|timestamp into Metadata."""
    parts = line[len(METADATA_PREFIX):].split("|")
    if len(parts) < 4:
        raise ParseError(
            line_num,
            f"Metadata needs 4 pipe-separated fields after 'M|', got {len(parts)}"
        )
    return Metadata(
        doc_id=parts[0].strip(),
        title=parts[1].strip(),
        source=parts[2].strip(),
        timestamp=parts[3].strip(),
    )


def _parse_heredoc(lines: list[str], start: int) -> tuple[int, list[str]]:
    """Parse a heredoc block starting at `start`. Returns (next_line_index, content_lines)."""
    if start >= len(lines) or lines[start].strip() != HEREDOC_OPEN:
        raise ParseError(start + 1, f"Expected '{HEREDOC_OPEN}' to start heredoc block")

    content: list[str] = []
    i = start + 1
    while i < len(lines):
        if lines[i].strip() == HEREDOC_CLOSE:
            return i + 1, content
        content.append(lines[i].rstrip())
        i += 1

    raise ParseError(start + 1, f"Unclosed heredoc block (missing '{HEREDOC_CLOSE}')")
