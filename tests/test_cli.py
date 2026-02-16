"""Tests for the CLI interface."""

import tempfile
from pathlib import Path

from cpf.cli import main


def test_cli_encode(sample_english, tmp_path):
    input_file = tmp_path / "input.md"
    output_file = tmp_path / "output.cpf"
    input_file.write_text(sample_english)

    ret = main(["encode", str(input_file), "-o", str(output_file)])
    assert ret == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert content.startswith("CPF|v1")


def test_cli_decode(sample_cpf, tmp_path):
    input_file = tmp_path / "input.cpf"
    output_file = tmp_path / "output.md"
    input_file.write_text(sample_cpf)

    ret = main(["decode", str(input_file), "-o", str(output_file)])
    assert ret == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert content.startswith("#")


def test_cli_validate_valid(sample_cpf, tmp_path):
    input_file = tmp_path / "input.cpf"
    input_file.write_text(sample_cpf)

    ret = main(["validate", str(input_file)])
    assert ret == 0


def test_cli_validate_invalid(tmp_path):
    input_file = tmp_path / "bad.cpf"
    input_file.write_text("NOT VALID CPF")

    ret = main(["validate", str(input_file)])
    assert ret == 1


def test_cli_stats(sample_cpf, sample_english, tmp_path):
    cpf_file = tmp_path / "input.cpf"
    orig_file = tmp_path / "original.md"
    cpf_file.write_text(sample_cpf)
    orig_file.write_text(sample_english)

    ret = main(["stats", str(cpf_file), "--original", str(orig_file)])
    assert ret == 0


def test_cli_no_command(capsys):
    ret = main([])
    assert ret == 1


def test_cli_version(capsys):
    try:
        main(["--version"])
    except SystemExit:
        pass  # --version causes SystemExit(0)
