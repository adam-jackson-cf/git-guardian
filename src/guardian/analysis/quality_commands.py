"""Runner for repository-defined deterministic quality gate commands."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Literal

from guardian.analysis.tool_runner import resolve_tool_command, run_command
from guardian.analysis.violation import Violation
from guardian.configuration import QualityCommand


def run_quality_commands(
    commands: tuple[QualityCommand, ...],
    *,
    changed_files: tuple[str, ...],
    scope: Literal["changed", "full"],
) -> list[Violation]:
    """Execute scoped deterministic quality commands and report failures as violations."""
    violations: list[Violation] = []
    repo_root = Path.cwd()

    for index, command in enumerate(commands, start=1):
        if not _should_run_command(command, changed_files=changed_files, scope=scope):
            continue

        argv, command_violation = resolve_tool_command(
            command.run,
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


def _should_run_command(
    command: QualityCommand,
    *,
    changed_files: tuple[str, ...],
    scope: Literal["changed", "full"],
) -> bool:
    """Decide if a quality command applies to the current execution scope."""
    if scope == "full":
        return command.run_on in {"always", "full"}
    if scope != "changed":
        return False
    if command.run_on not in {"always", "changed"}:
        return False
    if command.run_on == "always":
        return True
    if not changed_files:
        return False
    if not command.include:
        return True
    return any(_matches_include(path, command.include) for path in changed_files)


def _matches_include(path: str, include_patterns: tuple[str, ...]) -> bool:
    """Match one repository-relative path against include patterns."""
    pure_path = PurePosixPath(path)
    return any(pure_path.match(pattern) for pattern in include_patterns)
