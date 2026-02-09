"""ESLint runner for TypeScript/JavaScript analysis."""

from __future__ import annotations

from pathlib import Path

from guardian.analysis.tool_runner import parse_json_stdout, resolve_tool_command, run_command
from guardian.analysis.violation import Violation


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

    base_cmd, command_violation = resolve_tool_command(
        tool_command,
        field_name="tools.eslint",
        invalid_rule="eslint-command-invalid",
        invalid_suggestion="Fix tools.eslint in .guardian/config.yaml.",
    )
    if command_violation is not None:
        return [command_violation]
    assert base_cmd is not None

    cmd = [*base_cmd, "--config", str(config_file), "--format", "json", *files]

    result, execution_violation = run_command(
        cmd,
        cwd=repo_root,
        execution_rule="eslint-execution",
        execution_prefix="Failed to execute ESLint",
        execution_suggestion="Ensure ESLint is installed and available to Guardian.",
    )
    if execution_violation is not None:
        return [execution_violation]
    assert result is not None

    data, parse_violation = parse_json_stdout(
        result,
        parse_rule="eslint-output-parse",
        parse_prefix="Failed to parse ESLint output",
        parse_suggestion="Fix ESLint runtime/configuration issues and retry.",
    )
    if parse_violation is not None:
        return [parse_violation]
    assert data is not None

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
