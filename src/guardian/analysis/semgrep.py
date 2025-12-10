"""Semgrep runner for custom pattern detection."""

import json
import subprocess
from pathlib import Path

from guardian.analysis.violation import Violation


def run_semgrep(files: list[str]) -> list[Violation]:
    """Run Semgrep with Guardian rules."""
    repo_root = Path.cwd()
    rules_file = repo_root / ".guardian" / "semgrep-rules.yaml"

    if not rules_file.exists():
        return []

    violations = []

    # Run Semgrep
    cmd = [
        "semgrep",
        "--config",
        str(rules_file),
        "--json",
        *files,
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    # Semgrep returns non-zero on matches, but we still parse output
    try:
        data = json.loads(result.stdout)
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
    except (json.JSONDecodeError, KeyError):
        # If parsing fails, Semgrep might not be installed or config is invalid
        pass

    return violations
