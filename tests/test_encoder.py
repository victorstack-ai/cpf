"""Tests for the English -> CPF encoder."""

from cpf.encoder import encode
from cpf.validator import is_valid


def test_encode_produces_valid_cpf(sample_english):
    result = encode(sample_english, doc_id="test", title="Test")
    assert result.startswith("CPF|v1")
    assert is_valid(result)


def test_encode_includes_metadata(sample_english):
    result = encode(sample_english, doc_id="my-doc", title="My Document")
    assert "M|my-doc|My Document|" in result


def test_encode_creates_blocks(sample_english):
    result = encode(sample_english)
    # Should have blocks for each section
    assert "@R:" in result or "@P:" in result or "@N:" in result


def test_encode_priorities_detected(sample_english):
    result = encode(sample_english)
    # The priorities section should be detected
    assert "@P:" in result


def test_encode_abbreviations_applied(sample_english):
    result = encode(sample_english)
    # "WordPress" should become "wp" somewhere
    assert "wp" in result.lower()


def test_encode_conditionals_compressed():
    text = """# Rules

## Module Check

- If a maintained module exists: recommend it.
- If no module exists: code from scratch.
"""
    result = encode(text)
    # Should contain conditional operator
    assert "?" in result
    assert "->" in result


def test_encode_negations_compressed():
    text = """# Rules

## Restrictions

- Do NOT commit secrets.
- Never leave debug code.
- Avoid broad upgrades.
"""
    result = encode(text)
    assert "!!" in result


def test_encode_empty_sections_skipped():
    text = """# Title

## Empty Section

## Has Content

- Something here.
"""
    result = encode(text)
    assert "empty-section" not in result


def test_encode_custom_abbreviations():
    text = """# Rules

## Custom

- Check the frobnicator.
"""
    result = encode(text, custom_abbrevs={"frobnicator": "frob"})
    assert "frob" in result
