"""Built-in abbreviation dictionary for CPF encoding/decoding.

Maps common prompt/instruction words to short tokens.
Supports custom overrides via JSON files.
"""

from __future__ import annotations

import json
from pathlib import Path

# Encode map: full word -> abbreviation
# Only whole-word replacements to avoid false positives.
ENCODE_MAP: dict[str, str] = {
    "module": "mod",
    "modules": "mods",
    "plugin": "plg",
    "plugins": "plgs",
    "maintained": "mnt",
    "abandoned": "abd",
    "dependency": "dep",
    "dependencies": "deps",
    "configuration": "cfg",
    "configure": "cfg",
    "security": "sec",
    "performance": "perf",
    "stability": "stab",
    "documentation": "doc",
    "authentication": "auth",
    "permissions": "perm",
    "repository": "repo",
    "repositories": "repos",
    "template": "tpl",
    "templates": "tpls",
    "environment": "env",
    "implementation": "impl",
    "version": "ver",
    "versions": "vers",
    "update": "upd",
    "updates": "upds",
    "breaking": "brk",
    "compatibility": "compat",
    "developer experience": "dx",
    "continuous integration": "ci",
    "pull request": "pr",
    "pull requests": "prs",
    "function": "fn",
    "functions": "fns",
    "class": "cls",
    "classes": "clss",
    "service": "svc",
    "services": "svcs",
    "dependency injection": "di",
    "cache": "cch",
    "caching": "cch",
    "context": "ctx",
    "require": "req",
    "required": "req",
    "requirement": "req",
    "requirements": "reqs",
    "validate": "val",
    "validation": "val",
    "sanitize": "san",
    "sanitization": "san",
    "escape": "esc",
    "escaping": "esc",
    "check": "chk",
    "checks": "chks",
    "WordPress": "wp",
    "Drupal": "dp",
    "deprecated": "depr",
    "deprecation": "depr",
    "deprecations": "deprs",
    "application": "app",
    "applications": "apps",
    "database": "db",
    "databases": "dbs",
    "directory": "dir",
    "directories": "dirs",
    "parameter": "param",
    "parameters": "params",
    "argument": "arg",
    "arguments": "args",
    "response": "resp",
    "request": "req",
    "middleware": "mw",
    "controller": "ctrl",
    "controllers": "ctrls",
    "component": "comp",
    "components": "comps",
    "description": "desc",
    "specification": "spec",
    "infrastructure": "infra",
    "production": "prod",
    "development": "dev",
    "default": "def",
    "maximum": "max",
    "minimum": "min",
    "information": "info",
    "available": "avail",
    "backwards": "bkwd",
    "otherwise": "else",
    "approximately": "~",
    "important": "*",
}

# Decode map: abbreviation -> full word (built from ENCODE_MAP, keeping first match)
DECODE_MAP: dict[str, str] = {}
_seen_abbrs: set[str] = set()
for _full, _abbr in ENCODE_MAP.items():
    if _abbr not in _seen_abbrs:
        DECODE_MAP[_abbr] = _full
        _seen_abbrs.add(_abbr)


def abbreviate(word: str, custom: dict[str, str] | None = None) -> str:
    """Compress a word/phrase using the abbreviation dictionary."""
    lookup = custom if custom else ENCODE_MAP
    # Try exact match first (case-insensitive for common words)
    if word in lookup:
        return lookup[word]
    lower = word.lower()
    for full, abbr in lookup.items():
        if lower == full.lower():
            return abbr
    return word


def expand(abbr: str, custom: dict[str, str] | None = None) -> str:
    """Expand an abbreviation back to full word."""
    lookup = custom if custom else DECODE_MAP
    if abbr in lookup:
        return lookup[abbr]
    return abbr


def load_custom_abbreviations(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Load custom abbreviation JSON file. Returns (encode_map, decode_map)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    encode = dict(data)
    decode = {v: k for k, v in encode.items()}
    return encode, decode


def merge_abbreviations(
    base_encode: dict[str, str],
    base_decode: dict[str, str],
    custom_encode: dict[str, str],
    custom_decode: dict[str, str],
) -> tuple[dict[str, str], dict[str, str]]:
    """Merge custom abbreviations into base, with custom taking precedence."""
    merged_encode = {**base_encode, **custom_encode}
    merged_decode = {**base_decode, **custom_decode}
    return merged_encode, merged_decode
