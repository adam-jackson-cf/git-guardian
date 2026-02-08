"""Config drift detection and baseline governance checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from guardian.analysis.violation import Violation

PROTECTED_CONFIGS: tuple[str, ...] = (
    ".guardian/config.yaml",
    ".guardian/eslint.config.js",
    ".guardian/ruff.toml",
    ".guardian/semgrep-rules.yaml",
    "tsconfig.json",
    ".eslintrc.json",
    "eslint.config.js",
    "pyproject.toml",
    ".pre-commit-config.yaml",
    ".github/workflows/ci-quality-gates.yml",
    "scripts/run-ci-quality-gates.sh",
)

BASELINE_FILE = ".guardian/baseline.json"
BASELINE_META_FILE = ".guardian/baseline.meta.json"
POLICY_CHANGE_FILES = set(PROTECTED_CONFIGS) | {BASELINE_FILE, BASELINE_META_FILE}


def check_config_drift(changed_files: list[str] | None = None) -> list[Violation]:
    """Compare protected configuration files against baseline hashes."""
    repo_root = Path.cwd()
    baseline_path = repo_root / BASELINE_FILE

    if not baseline_path.exists():
        return [
            Violation(
                file=str(baseline_path),
                line=0,
                column=0,
                rule="config-baseline-missing",
                message="Config baseline file is missing.",
                severity="error",
                suggestion=(
                    'Run `guardian baseline update --acknowledge-policy-change --reason "..."`.'
                ),
            )
        ]

    try:
        baseline_raw = json.loads(baseline_path.read_text())
    except (json.JSONDecodeError, OSError):
        return [
            Violation(
                file=str(baseline_path),
                line=0,
                column=0,
                rule="config-baseline-invalid",
                message="Config baseline file is invalid JSON.",
                severity="error",
                suggestion="Regenerate baseline metadata with guardian baseline update.",
            )
        ]

    if not isinstance(baseline_raw, dict):
        return [
            Violation(
                file=str(baseline_path),
                line=0,
                column=0,
                rule="config-baseline-invalid",
                message="Config baseline file must be a JSON object mapping files to hashes.",
                severity="error",
                suggestion="Regenerate baseline metadata with guardian baseline update.",
            )
        ]

    baseline: dict[str, str] = {}
    for key, value in baseline_raw.items():
        if isinstance(key, str) and isinstance(value, str):
            baseline[key] = value

    violations: list[Violation] = []

    for config_file in PROTECTED_CONFIGS:
        config_path = repo_root / config_file

        if not config_path.exists():
            if config_file in baseline:
                violations.append(
                    Violation(
                        file=config_file,
                        line=0,
                        column=0,
                        rule="config-drift-missing-file",
                        message=f"Protected config file was removed: {config_file}",
                        severity="error",
                        suggestion=(
                            "Restore the protected file or update policy in a "
                            "dedicated baseline-only change."
                        ),
                    )
                )
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
                    suggestion="Run guardian baseline update in a dedicated policy-only change.",
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
                    message=f"Protected config file modified: {config_file}",
                    severity="error",
                    suggestion="Review policy change and update baseline in a policy-only change.",
                )
            )

    violations.extend(_check_baseline_change_policy(changed_files or [], repo_root))

    return violations


def _check_baseline_change_policy(changed_files: list[str], repo_root: Path) -> list[Violation]:
    """Enforce baseline update governance rules for changed diffs."""
    violations: list[Violation] = []

    baseline_changed = BASELINE_FILE in changed_files
    baseline_meta_changed = BASELINE_META_FILE in changed_files

    if baseline_meta_changed and not baseline_changed:
        violations.append(
            Violation(
                file=BASELINE_META_FILE,
                line=0,
                column=0,
                rule="baseline-meta-without-baseline",
                message="Baseline metadata changed without baseline hash updates.",
                severity="error",
                suggestion="Update baseline metadata only when baseline hashes are updated.",
            )
        )

    if not baseline_changed:
        return violations

    if not baseline_meta_changed:
        violations.append(
            Violation(
                file=BASELINE_FILE,
                line=0,
                column=0,
                rule="baseline-meta-required",
                message=(
                    "Baseline hash updates require matching .guardian/baseline.meta.json changes."
                ),
                severity="error",
                suggestion="Run guardian baseline update with acknowledge and reason flags.",
            )
        )

    non_policy_changes = [
        file_path for file_path in changed_files if file_path not in POLICY_CHANGE_FILES
    ]
    if non_policy_changes:
        violations.append(
            Violation(
                file=BASELINE_FILE,
                line=0,
                column=0,
                rule="baseline-change-mixed-diff",
                message=(
                    "Baseline updates must be policy-only. "
                    f"Found non-policy changes: {', '.join(non_policy_changes[:5])}"
                ),
                severity="error",
                suggestion="Split baseline/policy updates from application code changes.",
            )
        )

    metadata_path = repo_root / BASELINE_META_FILE
    if not metadata_path.exists():
        violations.append(
            Violation(
                file=BASELINE_META_FILE,
                line=0,
                column=0,
                rule="baseline-meta-missing",
                message="Baseline metadata file is missing.",
                severity="error",
                suggestion="Regenerate baseline via guardian baseline update.",
            )
        )
        return violations

    try:
        metadata = json.loads(metadata_path.read_text())
    except (json.JSONDecodeError, OSError):
        violations.append(
            Violation(
                file=BASELINE_META_FILE,
                line=0,
                column=0,
                rule="baseline-meta-invalid",
                message="Baseline metadata file is invalid JSON.",
                severity="error",
                suggestion="Regenerate baseline via guardian baseline update.",
            )
        )
        return violations

    if not isinstance(metadata, dict):
        violations.append(
            Violation(
                file=BASELINE_META_FILE,
                line=0,
                column=0,
                rule="baseline-meta-invalid",
                message="Baseline metadata must be a JSON object.",
                severity="error",
                suggestion="Regenerate baseline via guardian baseline update.",
            )
        )
        return violations

    if metadata.get("acknowledged_policy_change") is not True:
        violations.append(
            Violation(
                file=BASELINE_META_FILE,
                line=0,
                column=0,
                rule="baseline-meta-ack-required",
                message="Baseline metadata must include acknowledged_policy_change=true.",
                severity="error",
                suggestion="Use guardian baseline update --acknowledge-policy-change.",
            )
        )

    reason = metadata.get("reason")
    if not isinstance(reason, str) or len(reason.strip()) < 10:
        violations.append(
            Violation(
                file=BASELINE_META_FILE,
                line=0,
                column=0,
                rule="baseline-meta-reason-required",
                message="Baseline metadata reason must be at least 10 characters.",
                severity="error",
                suggestion="Set --reason with an explicit policy-change explanation.",
            )
        )

    updated_at = metadata.get("updated_at")
    if not isinstance(updated_at, str) or not updated_at.strip():
        violations.append(
            Violation(
                file=BASELINE_META_FILE,
                line=0,
                column=0,
                rule="baseline-meta-timestamp-required",
                message="Baseline metadata must include a non-empty updated_at timestamp.",
                severity="error",
                suggestion="Regenerate baseline metadata with guardian baseline update.",
            )
        )

    return violations
