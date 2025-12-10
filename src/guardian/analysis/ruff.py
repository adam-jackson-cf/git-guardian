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
        # No Ruff config, skip
        return []

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

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

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
    except (json.JSONDecodeError, KeyError):
        # If parsing fails, Ruff might not be installed or config is invalid
        pass

    return violations
