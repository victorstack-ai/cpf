"""Tests for the abbreviation dictionary."""

from cpf.abbreviations import abbreviate, expand, ENCODE_MAP, DECODE_MAP


def test_abbreviate_known_word():
    assert abbreviate("module") == "mod"
    assert abbreviate("plugin") == "plg"
    assert abbreviate("maintained") == "mnt"
    assert abbreviate("WordPress") == "wp"
    assert abbreviate("Drupal") == "dp"


def test_abbreviate_case_insensitive():
    assert abbreviate("Module") == "mod"
    assert abbreviate("PLUGIN") == "plg"


def test_abbreviate_unknown_word():
    assert abbreviate("foobar") == "foobar"


def test_expand_known_abbr():
    assert expand("mod") == "module"
    assert expand("plg") == "plugin"
    assert expand("wp") == "WordPress"


def test_expand_unknown_abbr():
    assert expand("xyz") == "xyz"


def test_encode_decode_roundtrip():
    """Every encoded word should decode back to a known full form."""
    for full, abbr in ENCODE_MAP.items():
        # The decode map might map to a different form (e.g. "updates" encodes to "upds"
        # but "upds" decodes to "updates" — the first entry wins)
        assert abbr in DECODE_MAP, f"Abbreviation '{abbr}' for '{full}' not in DECODE_MAP"


def test_multi_word_abbreviations():
    assert abbreviate("dependency injection") == "di"
    assert abbreviate("pull request") == "pr"
    assert abbreviate("developer experience") == "dx"
