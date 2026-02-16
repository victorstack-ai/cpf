"""CPF v1 format constants: sigils, operators, version."""

VERSION = "v1"
FORMAT_HEADER = f"CPF|{VERSION}"
METADATA_PREFIX = "M|"
SECTION_SEPARATOR = "---"

# Block type sigils — each starts a new block as @SIGIL:block-id
SIGILS: dict[str, str] = {
    "R": "rule",
    "P": "priority",
    "N": "negation",
    "S": "sequence",
    "T": "tone",
    "X": "exact",
    "Z": "zone",
    "C": "constant",
    "B": "blob",
}

# Operators that replace English grammar inside block content.
# Ordered longest-first so multi-char operators match before single-char.
OPERATORS: dict[str, str] = {
    "?!": "if_not",
    "->": "then",
    "!!": "never",
    "::": "definition",
    "@>": "delegate",
    "=>": "produces",
    "?": "if",
    ";": "else",
    "+": "and",
    "|": "or",
    "*": "emphasis",
    "~": "approx",
}

# Reverse map: English meaning -> operator symbol
OPERATORS_REVERSE: dict[str, str] = {v: k for k, v in OPERATORS.items()}

HEREDOC_OPEN = "<<"
HEREDOC_CLOSE = ">>"

BLOCK_RE_PATTERN = r"^@([A-Z]):(.+)$"
