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

    violations = []

    # Run Semgrep
    cmd = [
        "semgrep",
        "--config",
        str(rules_file),
        "--json",
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
                rule="semgrep-execution",
                message=f"Failed to execute Semgrep: {exc}",
                severity="error",
                suggestion="Ensure `semgrep` is installed and available in PATH.",
            )
        ]

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
    except (json.JSONDecodeError, KeyError) as exc:
        return [
            Violation(
                file=".",
                line=0,
                column=0,
                rule="semgrep-output-parse",
                message=f"Failed to parse Semgrep output: {exc}",
                severity="error",
                suggestion="Fix Semgrep configuration or runtime errors and retry.",
            )
        ]

    return violations
