"""Shared fixtures for CPF tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_english() -> str:
    """A simple English instruction document for testing."""
    return """# Test Rules

## Decision Rules

- If a maintained module exists: recommend it and link to it.
- If a module exists but is abandoned: code a custom solution and explain why.
- If no module exists: code the solution from scratch.
- Do NOT reinvent the wheel.
- Always check for existing solutions first.

## Default Priorities

1. Stability and security
2. Performance and caching
3. Maintainability
4. Developer experience

## Coding Standards

- Follow WordPress coding standards.
- Prefer hooks and filters over core edits.
- Avoid expensive queries in loops.
- Never commit secrets or credentials.
"""


@pytest.fixture
def sample_cpf() -> str:
    """A valid CPF v1 document for testing."""
    return """CPF|v1
M|test-rules|Test Rules|test.md|2026-01-01T00:00:00Z
---

@R:decision-rules
?mnt mod exists->recommend+link
?mod exists+abd->code custom solution+explain why
?!mod exists->code solution from scratch
!!reinvent wheel
*chk for existing solutions first

@P:default-priorities
#1 stab+sec
#2 perf+cch
#3 maintainability
#4 dx

@R:coding-standards
Follow wp coding standards
prefer(hooks+filters)>core edits
!!expensive queries in loops
!!commit secrets|credentials
"""


@pytest.fixture
def sample_negation_section() -> str:
    """English section heavy on negation."""
    return """## Quality Gate

- Do NOT commit secrets or credentials.
- Never leave debug code behind.
- Avoid broad dependency upgrades.
- Do not skip the test runner.
"""


@pytest.fixture
def sample_sequence_section() -> str:
    """English section with numbered steps."""
    return """## After Completing

1. Remove this item from the backlog.
2. Commit and push all changes.
3. Append narrative to pending posts.
4. Write a short summary of what was done.
"""
