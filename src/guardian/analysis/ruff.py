"""Ruff runner for Python analysis."""

from __future__ import annotations

from pathlib import Path

from guardian.analysis.tool_runner import parse_json_stdout, resolve_tool_command, run_command
from guardian.analysis.violation import Violation


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

    base_cmd, command_violation = resolve_tool_command(
        tool_command,
        field_name="tools.ruff",
        invalid_rule="ruff-command-invalid",
        invalid_suggestion="Fix tools.ruff in .guardian/config.yaml.",
    )
    if command_violation is not None:
        return [command_violation]
    assert base_cmd is not None

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

    result, execution_violation = run_command(
        cmd,
        cwd=repo_root,
        execution_rule="ruff-execution",
        execution_prefix="Failed to execute Ruff",
        execution_suggestion="Ensure Ruff is installed and available to Guardian.",
    )
    if execution_violation is not None:
        return [execution_violation]
    assert result is not None

    data, parse_violation = parse_json_stdout(
        result,
        parse_rule="ruff-output-parse",
        parse_prefix="Failed to parse Ruff output",
        parse_suggestion="Fix Ruff runtime/configuration issues and retry.",
    )
    if parse_violation is not None:
        return [parse_violation]
    assert data is not None

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
