"""Config drift detection - the only custom analysis in Guardian."""

import hashlib
import json
from pathlib import Path

from guardian.analysis.violation import Violation

PROTECTED_CONFIGS = {
    "tsconfig.json": None,  # Any change flagged
    "pyproject.toml": None,  # Any change flagged
    ".eslintrc.json": None,  # Any change flagged
    "eslint.config.js": None,  # Any change flagged
}


def check_config_drift() -> list[Violation]:
    """Compare current configs against baseline hashes."""
    repo_root = Path.cwd()
    guardian_dir = repo_root / ".guardian"
    baseline_file = guardian_dir / "baseline.json"

    if not baseline_file.exists():
        return [
            Violation(
                file=str(baseline_file),
                line=0,
                column=0,
                rule="config-baseline-missing",
                message="Config baseline file is missing.",
                severity="error",
                suggestion="Run `guardian baseline update` to create baseline hashes.",
            )
        ]

    violations = []

    try:
        baseline = json.loads(baseline_file.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return [
            Violation(
                file=str(baseline_file),
                line=0,
                column=0,
                rule="config-baseline-invalid",
                message="Config baseline file is invalid JSON.",
                severity="error",
                suggestion="Run `guardian baseline update` to regenerate a valid baseline.",
            )
        ]

    for config_file in PROTECTED_CONFIGS:
        config_path = repo_root / config_file
        if not config_path.exists():
            continue

        current_hash = hashlib.sha256(config_path.read_bytes()).hexdigest()

        if config_file not in baseline:
            violations.append(
                Violation(
                    file=config_file,
                    line=0,
                    column=0,
                    rule="config-baseline-incomplete",
                    message=f"Config file missing from baseline: {config_file}",
                    severity="error",
                    suggestion="Run `guardian baseline update` to capture all protected configs.",
                )
            )
            continue

        if baseline[config_file] != current_hash:
            violations.append(
                Violation(
                    file=config_file,
                    line=0,
                    column=0,
                    rule="config-drift",
                    message=f"Config file modified: {config_file}",
                    severity="warning",
                    suggestion="Review config changes - quality gates may be weakened",
                )
            )

    return violations
