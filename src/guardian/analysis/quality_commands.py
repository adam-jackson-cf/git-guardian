"""Runner for repository-defined deterministic quality gate commands."""

from __future__ import annotations

from pathlib import Path

from guardian.analysis.tool_runner import resolve_tool_command, run_command
from guardian.analysis.violation import Violation


def run_quality_commands(commands: tuple[str, ...]) -> list[Violation]:
    """Execute deterministic quality commands and report failures as violations."""
    violations: list[Violation] = []
    repo_root = Path.cwd()

    for index, command in enumerate(commands, start=1):
        argv, command_violation = resolve_tool_command(
            command,
            field_name=f"quality.commands[{index - 1}]",
            invalid_rule="quality-command-invalid",
            invalid_suggestion="Fix `quality.commands` in .guardian/config.yaml and retry.",
        )
        if command_violation is not None:
            violations.append(
                command_violation
            )
            continue
        assert argv is not None

        result, execution_violation = run_command(
            argv,
            cwd=repo_root,
            execution_rule="quality-command-execution",
            execution_prefix=f"Failed to execute quality command #{index}: {' '.join(argv)}",
            execution_suggestion="Install required tooling and ensure command paths are valid.",
            violation_file=".guardian/config.yaml",
        )
        if execution_violation is not None:
            violations.append(
                execution_violation
            )
            continue
        assert result is not None

        if result.returncode != 0:
            violations.append(
                Violation(
                    file=".guardian/config.yaml",
                    line=0,
                    column=0,
                    rule="quality-command-failed",
                    message=(
                        f"Quality command #{index} failed with exit code {result.returncode}: "
                        f"{' '.join(argv)}"
                    ),
                    severity="error",
                    suggestion="Run the failing command locally, fix issues, then retry Guardian.",
                )
            )

    return violations
