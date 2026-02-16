"""Tests for the CPF parser."""

import pytest

from cpf.parser import ParseError, parse


def test_parse_valid_document(sample_cpf):
    doc = parse(sample_cpf)
    assert doc.version == "v1"
    assert doc.metadata.doc_id == "test-rules"
    assert doc.metadata.title == "Test Rules"
    assert len(doc.blocks) == 3


def test_parse_metadata():
    text = """CPF|v1
M|my-id|My Title|source.md|2026-01-01T00:00:00Z
---
"""
    doc = parse(text)
    assert doc.metadata.doc_id == "my-id"
    assert doc.metadata.title == "My Title"
    assert doc.metadata.source == "source.md"
    assert doc.metadata.timestamp == "2026-01-01T00:00:00Z"


def test_parse_blocks(sample_cpf):
    doc = parse(sample_cpf)
    assert doc.blocks[0].sigil == "R"
    assert doc.blocks[0].block_id == "decision-rules"
    assert doc.blocks[1].sigil == "P"
    assert doc.blocks[1].block_id == "default-priorities"
    assert doc.blocks[2].sigil == "R"
    assert doc.blocks[2].block_id == "coding-standards"


def test_parse_block_content(sample_cpf):
    doc = parse(sample_cpf)
    rule_block = doc.blocks[0]
    assert any("?mnt" in line for line in rule_block.lines)
    assert any("!!" in line for line in rule_block.lines)


def test_parse_heredoc():
    text = """CPF|v1
M|test|Test|test|2026-01-01T00:00:00Z
---

@B:example
<<
This is raw content.
It can have multiple lines.
>>
"""
    doc = parse(text)
    assert len(doc.blocks) == 1
    blob = doc.blocks[0]
    assert blob.sigil == "B"
    assert blob.is_heredoc
    assert len(blob.lines) == 2
    assert "raw content" in blob.lines[0]


def test_parse_empty_raises():
    with pytest.raises(ParseError):
        parse("")


def test_parse_bad_header_raises():
    with pytest.raises(ParseError):
        parse("WRONG|v1\nM|a|b|c|d\n---\n")


def test_parse_missing_metadata_raises():
    with pytest.raises(ParseError):
        parse("CPF|v1\n")


def test_parse_constants():
    text = """CPF|v1
M|test|Test|test|2026-01-01T00:00:00Z
---

@C:abbr
wp::WordPress;dp::Drupal
"""
    doc = parse(text)
    constants = doc.get_constants()
    assert constants["wp"] == "WordPress"
    assert constants["dp"] == "Drupal"
