"""Ruff runner for Python analysis."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from guardian.analysis.violation import Violation
from guardian.configuration import ConfigValidationError, split_command


def run_ruff(files: list[str], *, tool_command: str) -> list[Violation]:
    """Run Ruff with Guardian config."""
    repo_root = Path.cwd()
    config_file = repo_root / ".guardian" / "ruff.toml"

    if not config_file.exists():
        return [
            Violation(
                file=str(config_file),
                line=0,
                column=0,
                rule="ruff-config-missing",
                message="Ruff config file is missing.",
                severity="error",
                suggestion="Run `guardian init` to restore .guardian/ruff.toml.",
            )
        ]

    try:
        base_cmd = split_command(tool_command, field_name="tools.ruff")
    except ConfigValidationError as exc:
        return [
            Violation(
                file=".guardian/config.yaml",
                line=0,
                column=0,
                rule="ruff-command-invalid",
                message=str(exc),
                severity="error",
                suggestion="Fix tools.ruff in .guardian/config.yaml.",
            )
        ]

    cmd = [
        *base_cmd,
        "check",
        "--config",
        str(config_file),
        "--output-format",
        "json",
        "--ignore-noqa",
        *files,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
    except OSError as exc:
        return [
            Violation(
                file=".",
                line=0,
                column=0,
                rule="ruff-execution",
                message=f"Failed to execute Ruff: {exc}",
                severity="error",
                suggestion="Ensure Ruff is installed and available to Guardian.",
            )
        ]

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        stderr_preview = result.stderr.strip().splitlines()
        detail = stderr_preview[0] if stderr_preview else "No stderr output available."
        return [
            Violation(
                file=".",
                line=0,
                column=0,
                rule="ruff-output-parse",
                message=f"Failed to parse Ruff output: {exc}. {detail}",
                severity="error",
                suggestion="Fix Ruff runtime/configuration issues and retry.",
            )
        ]

    violations: list[Violation] = []
    try:
        for item in data:
            violations.append(
                Violation(
                    file=item["filename"],
                    line=item["location"]["row"],
                    column=item["location"]["column"],
                    rule=item["code"],
                    message=item["message"],
                    severity="error",
                )
            )
    except (AttributeError, KeyError, TypeError) as exc:
        return [
            Violation(
                file=".",
                line=0,
                column=0,
                rule="ruff-output-parse",
                message=f"Unexpected Ruff output structure: {exc}",
                severity="error",
                suggestion="Fix Ruff runtime/configuration issues and retry.",
            )
        ]

    return violations
