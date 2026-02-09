"""Tests for shared tool runner helpers."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from guardian.analysis.tool_runner import parse_json_stdout, resolve_tool_command, run_command


def test_resolve_tool_command_valid() -> None:
    """Valid command strings should split into argv."""
    argv, violation = resolve_tool_command(
        f"{sys.executable} -V",
        field_name="tools.example",
        invalid_rule="command-invalid",
        invalid_suggestion="Fix tools.example.",
    )
    assert violation is None
    assert argv is not None
    assert argv[0] == sys.executable


def test_resolve_tool_command_invalid() -> None:
    """Invalid command syntax should produce violation."""
    argv, violation = resolve_tool_command(
        "'unterminated",
        field_name="tools.example",
        invalid_rule="command-invalid",
        invalid_suggestion="Fix tools.example.",
    )
    assert argv is None
    assert violation is not None
    assert violation.rule == "command-invalid"


def test_run_command_missing_executable() -> None:
    """Missing executable should return normalized execution violation."""
    result, violation = run_command(
        ["definitely-not-a-real-executable-guardian-test"],
        cwd=Path.cwd(),
        execution_rule="tool-execution",
        execution_prefix="Execution failed",
        execution_suggestion="Install tool.",
        violation_file=".",
    )
    assert result is None
    assert violation is not None
    assert violation.rule == "tool-execution"


def test_parse_json_stdout_invalid() -> None:
    """Invalid JSON stdout should return normalized parse violation."""
    process = subprocess.CompletedProcess(
        args=["tool"],
        returncode=0,
        stdout="not-json",
        stderr="error line",
    )
    data, violation = parse_json_stdout(
        process,
        parse_rule="tool-parse",
        parse_prefix="Parse failed",
        parse_suggestion="Fix tool output.",
    )
    assert data is None
    assert violation is not None
    assert violation.rule == "tool-parse"
