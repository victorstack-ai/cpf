"""CLI entry point for CPF: encode, decode, validate, stats."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__


def _cmd_encode(args: argparse.Namespace) -> int:
    from .abbreviations import (
        ENCODE_MAP,
        load_custom_abbreviations,
        merge_abbreviations,
    )
    from .encoder import encode

    text = args.input.read_text(encoding="utf-8")
    custom = {}
    if args.abbrev:
        custom_encode, _ = load_custom_abbreviations(args.abbrev)
        custom = custom_encode

    result = encode(
        text,
        doc_id=args.id,
        title=args.title,
        source=str(args.input),
        custom_abbrevs=custom,
    )

    if args.output:
        args.output.write_text(result, encoding="utf-8")
        print(f"Encoded {args.input} -> {args.output}")
    else:
        print(result, end="")

    return 0


def _cmd_decode(args: argparse.Namespace) -> int:
    from .abbreviations import DECODE_MAP, load_custom_abbreviations
    from .decoder import decode

    text = args.input.read_text(encoding="utf-8")
    custom = {}
    if args.abbrev:
        _, custom_decode = load_custom_abbreviations(args.abbrev)
        custom = custom_decode

    result = decode(text, custom_decode=custom)

    if args.output:
        args.output.write_text(result, encoding="utf-8")
        print(f"Decoded {args.input} -> {args.output}")
    else:
        print(result, end="")

    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    from .validator import validate

    text = args.input.read_text(encoding="utf-8")
    errors = validate(text)

    if not errors:
        print(f"OK: {args.input} is valid CPF v1")
        return 0

    for err in errors:
        print(err, file=sys.stderr)

    error_count = sum(1 for e in errors if e.severity == "error")
    warn_count = sum(1 for e in errors if e.severity == "warning")
    print(f"\n{error_count} error(s), {warn_count} warning(s)", file=sys.stderr)
    return 1 if error_count > 0 else 0


def _cmd_stats(args: argparse.Namespace) -> int:
    from .utils import count_tokens_estimate

    cpf_text = args.input.read_text(encoding="utf-8")
    cpf_tokens = count_tokens_estimate(cpf_text)
    cpf_chars = len(cpf_text)
    cpf_lines = len(cpf_text.splitlines())

    print(f"CPF file: {args.input}")
    print(f"  Lines:  {cpf_lines}")
    print(f"  Chars:  {cpf_chars}")
    print(f"  Tokens: ~{cpf_tokens} (estimate)")

    if args.original:
        orig_text = args.original.read_text(encoding="utf-8")
        orig_tokens = count_tokens_estimate(orig_text)
        orig_chars = len(orig_text)
        orig_lines = len(orig_text.splitlines())

        reduction_tokens = (1 - cpf_tokens / orig_tokens) * 100 if orig_tokens > 0 else 0
        reduction_chars = (1 - cpf_chars / orig_chars) * 100 if orig_chars > 0 else 0

        print(f"\nOriginal: {args.original}")
        print(f"  Lines:  {orig_lines}")
        print(f"  Chars:  {orig_chars}")
        print(f"  Tokens: ~{orig_tokens} (estimate)")
        print(f"\nReduction:")
        print(f"  Tokens: ~{reduction_tokens:.1f}%")
        print(f"  Chars:  ~{reduction_chars:.1f}%")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cpf",
        description="CPF — Compact Prompt Format: token-efficient instruction encoding for LLMs",
    )
    parser.add_argument("--version", action="version", version=f"cpf {__version__}")
    sub = parser.add_subparsers(dest="command")

    # encode
    enc = sub.add_parser("encode", help="Convert English markdown to CPF")
    enc.add_argument("input", type=Path, help="Input markdown file")
    enc.add_argument("-o", "--output", type=Path, help="Output CPF file")
    enc.add_argument("--abbrev", type=Path, help="Custom abbreviation JSON file")
    enc.add_argument("--id", type=str, help="Document ID (auto-generated if not given)")
    enc.add_argument("--title", type=str, help="Document title (extracted from input if not given)")

    # decode
    dec = sub.add_parser("decode", help="Convert CPF back to English markdown")
    dec.add_argument("input", type=Path, help="Input CPF file")
    dec.add_argument("-o", "--output", type=Path, help="Output markdown file")
    dec.add_argument("--abbrev", type=Path, help="Custom abbreviation JSON file")

    # validate
    val = sub.add_parser("validate", help="Validate a CPF document")
    val.add_argument("input", type=Path, help="CPF file to validate")

    # stats
    st = sub.add_parser("stats", help="Show compression statistics")
    st.add_argument("input", type=Path, help="CPF file")
    st.add_argument("--original", type=Path, help="Original English file for comparison")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "encode": _cmd_encode,
        "decode": _cmd_decode,
        "validate": _cmd_validate,
        "stats": _cmd_stats,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
