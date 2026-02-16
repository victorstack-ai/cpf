"""Tests for the CPF validator."""

from cpf.validator import is_valid, validate


def test_valid_document(sample_cpf):
    errors = validate(sample_cpf)
    assert not any(e.severity == "error" for e in errors)
    assert is_valid(sample_cpf)


def test_empty_document():
    errors = validate("")
    assert len(errors) == 1
    assert "Empty" in errors[0].message


def test_wrong_header():
    errors = validate("WRONG|v1\nM|a|b|c|d\n---\n")
    assert len(errors) >= 1
    assert "CPF|v1" in errors[0].message


def test_missing_metadata():
    errors = validate("CPF|v1\n")
    assert any("metadata" in e.message.lower() or "Missing" in e.message for e in errors)


def test_bad_metadata_fields():
    errors = validate("CPF|v1\nM|only-two-fields|title\n---\n")
    assert any("4 pipe-separated" in e.message for e in errors)


def test_unknown_sigil():
    text = "CPF|v1\nM|t|t|t|t\n---\n\n@Q:bad\nstuff\n"
    errors = validate(text)
    assert any("Unknown sigil" in e.message for e in errors)


def test_duplicate_block_id():
    text = "CPF|v1\nM|t|t|t|t\n---\n\n@R:same\nline1\n\n@R:same\nline2\n"
    errors = validate(text)
    assert any("Duplicate" in e.message for e in errors)


def test_unclosed_heredoc():
    text = "CPF|v1\nM|t|t|t|t\n---\n\n@B:blob\n<<\nstuff\n"
    errors = validate(text)
    assert any("Unclosed" in e.message for e in errors)


def test_valid_heredoc():
    text = "CPF|v1\nM|t|t|t|t\n---\n\n@B:blob\n<<\nstuff here\n>>\n"
    assert is_valid(text)
