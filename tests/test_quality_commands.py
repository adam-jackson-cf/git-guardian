"""Tests for deterministic quality command execution."""

from __future__ import annotations

import sys

from guardian.analysis.quality_commands import run_quality_commands


def test_quality_commands_pass() -> None:
    """Passing commands should return no violations."""
    violations = run_quality_commands((f"{sys.executable} -c 'import sys; sys.exit(0)'",))
    assert violations == []


def test_quality_commands_fail() -> None:
    """Non-zero command exit must fail verification."""
    violations = run_quality_commands((f"{sys.executable} -c 'import sys; sys.exit(2)'",))
    assert len(violations) == 1
    assert violations[0].rule == "quality-command-failed"
    assert violations[0].severity == "error"


def test_quality_commands_invalid_syntax() -> None:
    """Invalid shell-like syntax should be reported as config errors."""
    violations = run_quality_commands(("'unterminated",))
    assert len(violations) == 1
    assert violations[0].rule == "quality-command-invalid"
