"""Semgrep runner for custom pattern detection."""

from __future__ import annotations

from pathlib import Path

from guardian.analysis.tool_runner import parse_json_stdout, resolve_tool_command, run_command
from guardian.analysis.violation import Violation


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

    base_cmd, command_violation = resolve_tool_command(
        tool_command,
        field_name="tools.semgrep",
        invalid_rule="semgrep-command-invalid",
        invalid_suggestion="Fix tools.semgrep in .guardian/config.yaml.",
    )
    if command_violation is not None:
        return [command_violation]
    assert base_cmd is not None

    cmd = [*base_cmd, "--config", str(rules_file), "--json", *files]

    result, execution_violation = run_command(
        cmd,
        cwd=repo_root,
        execution_rule="semgrep-execution",
        execution_prefix="Failed to execute Semgrep",
        execution_suggestion="Ensure Semgrep is installed and available to Guardian.",
    )
    if execution_violation is not None:
        return [execution_violation]
    assert result is not None

    data, parse_violation = parse_json_stdout(
        result,
        parse_rule="semgrep-output-parse",
        parse_prefix="Failed to parse Semgrep output",
        parse_suggestion="Fix Semgrep runtime/configuration issues and retry.",
    )
    if parse_violation is not None:
        return [parse_violation]
    assert data is not None

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
