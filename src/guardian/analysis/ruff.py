"""Ruff runner for Python analysis."""

import json
import subprocess
from pathlib import Path

from guardian.analysis.violation import Violation


def run_ruff(files: list[str]) -> list[Violation]:
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

    violations = []

    # Run Ruff with --ignore-noqa to show violations despite # noqa
    cmd = [
        "ruff",
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
                suggestion="Ensure `ruff` is installed and available in PATH.",
            )
        ]

    # Ruff returns non-zero on errors, but we still parse output
    try:
        data = json.loads(result.stdout)
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
    except (json.JSONDecodeError, KeyError) as exc:
        return [
            Violation(
                file=".",
                line=0,
                column=0,
                rule="ruff-output-parse",
                message=f"Failed to parse Ruff output: {exc}",
                severity="error",
                suggestion="Fix Ruff configuration or runtime errors and retry.",
            )
        ]

    return violations
