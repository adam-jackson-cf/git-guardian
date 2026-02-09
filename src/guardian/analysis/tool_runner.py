"""Shared subprocess and JSON parsing helpers for analyzer runners."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from guardian.analysis.violation import Violation
from guardian.configuration import ConfigValidationError, split_command


def resolve_tool_command(
    tool_command: str,
    *,
    field_name: str,
    invalid_rule: str,
    invalid_suggestion: str,
) -> tuple[list[str], None] | tuple[None, Violation]:
    """Resolve a configured command into argv form."""
    try:
        return split_command(tool_command, field_name=field_name), None
    except ConfigValidationError as exc:
        return None, Violation(
            file=".guardian/config.yaml",
            line=0,
            column=0,
            rule=invalid_rule,
            message=str(exc),
            severity="error",
            suggestion=invalid_suggestion,
        )


def run_command(
    cmd: list[str],
    *,
    cwd: Path,
    execution_rule: str,
    execution_prefix: str,
    execution_suggestion: str,
    violation_file: str = ".",
) -> tuple[subprocess.CompletedProcess[str], None] | tuple[None, Violation]:
    """Run command and normalize execution failures into violations."""
    try:
        return (
            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
            ),
            None,
        )
    except OSError as exc:
        return None, Violation(
            file=violation_file,
            line=0,
            column=0,
            rule=execution_rule,
            message=f"{execution_prefix}: {exc}",
            severity="error",
            suggestion=execution_suggestion,
        )


def parse_json_stdout(
    result: subprocess.CompletedProcess[str],
    *,
    parse_rule: str,
    parse_prefix: str,
    parse_suggestion: str,
) -> tuple[Any, None] | tuple[None, Violation]:
    """Parse JSON stdout and return first-line stderr context on failure."""
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError as exc:
        stderr_preview = result.stderr.strip().splitlines()
        detail = stderr_preview[0] if stderr_preview else "No stderr output available."
        return None, Violation(
            file=".",
            line=0,
            column=0,
            rule=parse_rule,
            message=f"{parse_prefix}: {exc}. {detail}",
            severity="error",
            suggestion=parse_suggestion,
        )
