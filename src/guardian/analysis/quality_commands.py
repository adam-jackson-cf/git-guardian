"""Runner for repository-defined deterministic quality gate commands."""

from __future__ import annotations

import subprocess

from guardian.analysis.violation import Violation
from guardian.configuration import ConfigValidationError, split_command


def run_quality_commands(commands: tuple[str, ...]) -> list[Violation]:
    """Execute deterministic quality commands and report failures as violations."""
    violations: list[Violation] = []

    for index, command in enumerate(commands, start=1):
        try:
            argv = split_command(command, field_name=f"quality.commands[{index - 1}]")
        except ConfigValidationError as exc:
            violations.append(
                Violation(
                    file=".guardian/config.yaml",
                    line=0,
                    column=0,
                    rule="quality-command-invalid",
                    message=str(exc),
                    severity="error",
                    suggestion="Fix `quality.commands` in .guardian/config.yaml and retry.",
                )
            )
            continue

        try:
            result = subprocess.run(
                argv,
                capture_output=True,
                text=True,
            )
        except OSError as exc:
            violations.append(
                Violation(
                    file=".guardian/config.yaml",
                    line=0,
                    column=0,
                    rule="quality-command-execution",
                    message=(
                        f"Failed to execute quality command #{index}: {' '.join(argv)} ({exc})"
                    ),
                    severity="error",
                    suggestion="Install required tooling and ensure command paths are valid.",
                )
            )
            continue

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
