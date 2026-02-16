"""AST node dataclasses for CPF documents."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Metadata:
    """Document metadata from the M| header line."""
    doc_id: str
    title: str
    source: str
    timestamp: str


@dataclass
class Block:
    """A single CPF block (e.g. @R:mod-first with its content lines)."""
    sigil: str          # Single letter: R, P, N, S, T, X, Z, C, B
    block_id: str       # kebab-case identifier
    lines: list[str] = field(default_factory=list)  # raw content lines
    is_heredoc: bool = False  # True for @B blocks with << >>


@dataclass
class CPFDocument:
    """A complete CPF v1 document."""
    version: str
    metadata: Metadata
    blocks: list[Block] = field(default_factory=list)

    def get_block(self, block_id: str) -> Block | None:
        """Find a block by its ID."""
        for b in self.blocks:
            if b.block_id == block_id:
                return b
        return None

    def get_blocks_by_sigil(self, sigil: str) -> list[Block]:
        """Get all blocks of a given type."""
        return [b for b in self.blocks if b.sigil == sigil]

    def get_constants(self) -> dict[str, str]:
        """Extract all @C block definitions as a flat dict."""
        constants: dict[str, str] = {}
        for block in self.get_blocks_by_sigil("C"):
            for line in block.lines:
                for pair in line.split(";"):
                    pair = pair.strip()
                    if "::" in pair:
                        key, _, val = pair.partition("::")
                        constants[key.strip()] = val.strip()
        return constants
