"""Tests for the CPF -> English decoder."""

from cpf.decoder import decode, expand_line


def test_decode_produces_markdown(sample_cpf):
    result = decode(sample_cpf)
    assert result.startswith("#")
    assert "##" in result


def test_decode_expands_conditionals(sample_cpf):
    result = decode(sample_cpf)
    # Should have "If" statements
    assert "If " in result


def test_decode_expands_negations(sample_cpf):
    result = decode(sample_cpf)
    assert "NOT" in result or "not" in result.lower()


def test_decode_expands_priorities(sample_cpf):
    result = decode(sample_cpf)
    assert "1." in result
    assert "2." in result


def test_expand_conditional_line():
    result = expand_line("?mnt mod exists->recommend+link", {})
    assert "If" in result
    assert "and" in result


def test_expand_negation_line():
    result = expand_line("!!commit secrets", {})
    assert "NOT" in result


def test_expand_emphasis_line():
    result = expand_line("*chk existing solutions", {"chk": "check"})
    assert "check" in result.lower()


def test_expand_priority_line():
    result = expand_line("#1 stab+sec", {"stab": "stability", "sec": "security"})
    assert "1." in result
    assert "stability" in result.lower()


def test_expand_definition_line():
    result = expand_line("key::value here", {})
    assert "Key" in result
    assert "value" in result


def test_expand_prefer_line():
    result = expand_line("prefer(hooks)>core edits", {})
    assert "Prefer" in result
    assert "over" in result


def test_decode_heredoc_passthrough():
    cpf = """CPF|v1
M|test|Test|test|2026-01-01T00:00:00Z
---

@B:example-code
<<
function foo() { return 42; }
>>
"""
    result = decode(cpf)
    assert "function foo()" in result
