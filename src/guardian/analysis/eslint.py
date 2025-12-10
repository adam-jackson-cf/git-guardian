"""ESLint runner for TypeScript/JavaScript analysis."""

import json
import subprocess
from pathlib import Path

from guardian.analysis.violation import Violation


def run_eslint(files: list[str]) -> list[Violation]:
    """Run ESLint with Guardian config."""
    repo_root = Path.cwd()
    config_file = repo_root / ".guardian" / "eslint.config.js"

    if not config_file.exists():
        # No ESLint config, skip
        return []

    violations = []

    # Run ESLint
    cmd = [
        "npx",
        "eslint",
        "--config",
        str(config_file),
        "--format",
        "json",
        *files,
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    # ESLint returns non-zero on errors, but we still parse output
    try:
        data = json.loads(result.stdout)
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
    except (json.JSONDecodeError, KeyError):
        # If parsing fails, ESLint might not be installed or config is invalid
        pass

    return violations
