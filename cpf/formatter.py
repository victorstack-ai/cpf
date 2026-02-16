"""CPF AST -> formatted CPF string output."""

from __future__ import annotations

from .ast_nodes import CPFDocument
from .spec import FORMAT_HEADER, HEREDOC_CLOSE, HEREDOC_OPEN, METADATA_PREFIX, SECTION_SEPARATOR


def format_document(doc: CPFDocument) -> str:
    """Render a CPFDocument AST into a CPF v1 string."""
    lines: list[str] = []

    # Header
    lines.append(FORMAT_HEADER)

    # Metadata
    m = doc.metadata
    lines.append(f"{METADATA_PREFIX}{m.doc_id}|{m.title}|{m.source}|{m.timestamp}")

    # Separator
    lines.append(SECTION_SEPARATOR)

    # Blocks
    for block in doc.blocks:
        lines.append("")  # blank line between blocks
        lines.append(f"@{block.sigil}:{block.block_id}")

        if block.is_heredoc:
            lines.append(HEREDOC_OPEN)
            for content_line in block.lines:
                lines.append(content_line)
            lines.append(HEREDOC_CLOSE)
        else:
            for content_line in block.lines:
                lines.append(content_line)

    return "\n".join(lines) + "\n"
