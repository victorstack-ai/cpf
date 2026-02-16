"""Roundtrip tests: encode then decode, verify semantic preservation."""

from cpf.decoder import decode
from cpf.encoder import encode
from cpf.validator import is_valid


def test_roundtrip_basic(sample_english):
    """Encode English -> CPF -> decode back. Output should be valid and meaningful."""
    cpf = encode(sample_english, doc_id="test", title="Test")
    assert is_valid(cpf), f"Encoded CPF is not valid:\n{cpf}"

    # Decode back
    decoded = decode(cpf)
    assert decoded.strip(), "Decoded output is empty"

    # Check key semantic elements survive the roundtrip
    decoded_lower = decoded.lower()
    assert "if" in decoded_lower, "Conditionals should be present in decoded output"


def test_roundtrip_negations():
    text = """# Rules

## Restrictions

- Do NOT commit secrets or credentials.
- Never leave debug code behind.
"""
    cpf = encode(text, doc_id="neg-test", title="Neg Test")
    assert is_valid(cpf)

    decoded = decode(cpf)
    assert "NOT" in decoded or "not" in decoded.lower()


def test_roundtrip_priorities():
    text = """# Config

## Default Priorities

1. Stability and security
2. Performance
3. Maintainability
"""
    cpf = encode(text, doc_id="pri-test", title="Priority Test")
    assert is_valid(cpf)

    decoded = decode(cpf)
    assert "1." in decoded
    assert "2." in decoded


def test_roundtrip_produces_shorter_output(sample_english):
    """CPF should be significantly shorter than the English input."""
    cpf = encode(sample_english, doc_id="test", title="Test")
    # CPF should be shorter in character count
    assert len(cpf) < len(sample_english), (
        f"CPF ({len(cpf)} chars) should be shorter than English ({len(sample_english)} chars)"
    )


def test_roundtrip_preserves_structure(sample_english):
    """Decoded output should have section headers."""
    cpf = encode(sample_english, doc_id="test", title="Test")
    decoded = decode(cpf)
    # Should have markdown headers
    assert "## " in decoded
