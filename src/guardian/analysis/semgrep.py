"""Semgrep runner for custom pattern detection."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from guardian.analysis.violation import Violation
from guardian.configuration import ConfigValidationError, split_command


def run_semgrep(files: list[str], *, tool_command: str) -> list[Violation]:
    """Run Semgrep with Guardian rules."""
    repo_root = Path.cwd()
    rules_file = repo_root / ".guardian" / "semgrep-rules.yaml"

    if not rules_file.exists():
        return [
            Violation(
                file=str(rules_file),
                line=0,
                column=0,
                rule="semgrep-rules-missing",
                message="Semgrep rules file is missing.",
                severity="error",
                suggestion="Run `guardian init` to restore .guardian/semgrep-rules.yaml.",
            )
        ]

    try:
        base_cmd = split_command(tool_command, field_name="tools.semgrep")
    except ConfigValidationError as exc:
        return [
            Violation(
                file=".guardian/config.yaml",
                line=0,
                column=0,
                rule="semgrep-command-invalid",
                message=str(exc),
                severity="error",
                suggestion="Fix tools.semgrep in .guardian/config.yaml.",
            )
        ]

    cmd = [*base_cmd, "--config", str(rules_file), "--json", *files]

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
                rule="semgrep-execution",
                message=f"Failed to execute Semgrep: {exc}",
                severity="error",
                suggestion="Ensure Semgrep is installed and available to Guardian.",
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
                rule="semgrep-output-parse",
                message=f"Failed to parse Semgrep output: {exc}. {detail}",
                severity="error",
                suggestion="Fix Semgrep runtime/configuration issues and retry.",
            )
        ]

    violations: list[Violation] = []
    try:
        for item in data.get("results", []):
            violations.append(
                Violation(
                    file=item["path"],
                    line=item["start"]["line"],
                    column=item["start"]["col"],
                    rule=item["check_id"],
                    message=item["extra"]["message"],
                    severity=item["extra"]["severity"].lower(),
                )
            )
    except (AttributeError, KeyError, TypeError) as exc:
        return [
            Violation(
                file=".",
                line=0,
                column=0,
                rule="semgrep-output-parse",
                message=f"Unexpected Semgrep output structure: {exc}",
                severity="error",
                suggestion="Fix Semgrep runtime/configuration issues and retry.",
            )
        ]

    return violations
