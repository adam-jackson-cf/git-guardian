"""Tests for deterministic quality command execution."""

from __future__ import annotations

import sys

from guardian.analysis.quality_commands import run_quality_commands
from guardian.configuration import QualityCommand


def test_quality_commands_pass() -> None:
    """Passing commands should return no violations."""
    violations = run_quality_commands(
        (
            QualityCommand(
                name="ok",
                run=f"{sys.executable} -c 'import sys; sys.exit(0)'",
                run_on="always",
                include=(),
            ),
        ),
        changed_files=("src/example.py",),
        scope="changed",
    )
    assert violations == []


def test_quality_commands_fail() -> None:
    """Non-zero command exit must fail verification."""
    violations = run_quality_commands(
        (
            QualityCommand(
                name="failing",
                run=f"{sys.executable} -c 'import sys; sys.exit(2)'",
                run_on="always",
                include=(),
            ),
        ),
        changed_files=("src/example.py",),
        scope="changed",
    )
    assert len(violations) == 1
    assert violations[0].rule == "quality-command-failed"
    assert violations[0].severity == "error"


def test_quality_commands_invalid_syntax() -> None:
    """Invalid shell-like syntax should be reported as config errors."""
    violations = run_quality_commands(
        (
            QualityCommand(
                name="invalid",
                run="'unterminated",
                run_on="always",
                include=(),
            ),
        ),
        changed_files=("src/example.py",),
        scope="changed",
    )
    assert len(violations) == 1
    assert violations[0].rule == "quality-command-invalid"


def test_quality_commands_skip_changed_when_include_does_not_match() -> None:
    """Changed-scope commands should skip when include globs do not match diff."""
    violations = run_quality_commands(
        (
            QualityCommand(
                name="scoped",
                run=f"{sys.executable} -c 'import sys; sys.exit(2)'",
                run_on="changed",
                include=("src/**/*.py",),
            ),
        ),
        changed_files=("docs/readme.md",),
        scope="changed",
    )
    assert violations == []


def test_quality_commands_skip_full_when_run_on_changed() -> None:
    """Full-scope execution should skip changed-only commands."""
    violations = run_quality_commands(
        (
            QualityCommand(
                name="changed-only",
                run=f"{sys.executable} -c 'import sys; sys.exit(2)'",
                run_on="changed",
                include=(),
            ),
        ),
        changed_files=("src/example.py",),
        scope="full",
    )
    assert violations == []
