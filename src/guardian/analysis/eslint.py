"""ESLint runner for TypeScript/JavaScript analysis."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from guardian.analysis.violation import Violation
from guardian.configuration import ConfigValidationError, split_command


def run_eslint(files: list[str], *, tool_command: str) -> list[Violation]:
    """Run ESLint with Guardian config."""
    repo_root = Path.cwd()
    config_file = repo_root / ".guardian" / "eslint.config.js"

    if not config_file.exists():
        return [
            Violation(
                file=str(config_file),
                line=0,
                column=0,
                rule="eslint-config-missing",
                message="ESLint config file is missing.",
                severity="error",
                suggestion="Run `guardian init` to restore .guardian/eslint.config.js.",
            )
        ]

    try:
        base_cmd = split_command(tool_command, field_name="tools.eslint")
    except ConfigValidationError as exc:
        return [
            Violation(
                file=".guardian/config.yaml",
                line=0,
                column=0,
                rule="eslint-command-invalid",
                message=str(exc),
                severity="error",
                suggestion="Fix tools.eslint in .guardian/config.yaml.",
            )
        ]

    cmd = [*base_cmd, "--config", str(config_file), "--format", "json", *files]

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
                rule="eslint-execution",
                message=f"Failed to execute ESLint: {exc}",
                severity="error",
                suggestion="Ensure ESLint is installed and available to Guardian.",
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
                rule="eslint-output-parse",
                message=f"Failed to parse ESLint output: {exc}. {detail}",
                severity="error",
                suggestion="Fix ESLint runtime/configuration issues and retry.",
            )
        ]

    violations: list[Violation] = []
    try:
        for file_result in data:
            for msg in file_result.get("messages", []):
                violations.append(
                    Violation(
                        file=file_result["filePath"],
                        line=msg.get("line", 0),
                        column=msg.get("column", 0),
                        rule=msg.get("ruleId", "unknown"),
                        message=msg.get("message", ""),
                        severity="error" if msg.get("severity") == 2 else "warning",
                    )
                )
    except (AttributeError, KeyError, TypeError) as exc:
        return [
            Violation(
                file=".",
                line=0,
                column=0,
                rule="eslint-output-parse",
                message=f"Unexpected ESLint output structure: {exc}",
                severity="error",
                suggestion="Fix ESLint runtime/configuration issues and retry.",
            )
        ]

    return violations
