"""Verification pipeline - orchestrates external tools."""

from __future__ import annotations

from pathlib import Path

from guardian.analysis.config_drift import check_config_drift
from guardian.analysis.coverage import run_diff_cover
from guardian.analysis.eslint import run_eslint
from guardian.analysis.git_utils import get_all_files, get_changed_files
from guardian.analysis.quality_commands import run_quality_commands
from guardian.analysis.ruff import run_ruff
from guardian.analysis.semgrep import run_semgrep
from guardian.analysis.violation import Violation
from guardian.configuration import ConfigValidationError, GuardianConfig, load_guardian_config


def run_verification() -> list[Violation]:
    """Run all verification tools and aggregate results."""
    config_or_error = _load_config_or_violation()
    if isinstance(config_or_error, list):
        return config_or_error

    config = config_or_error
    changed_file_result = get_changed_files(config.analysis.compare_branch)
    if changed_file_result.error:
        return [
            Violation(
                file=".guardian/config.yaml",
                line=0,
                column=0,
                rule="git-compare-branch",
                message=changed_file_result.error,
                severity="error",
                suggestion="Fix compare_branch or fetch the configured branch before verifying.",
            )
        ]

    changed_files = changed_file_result.files
    violations = _run_analysis_for_files(changed_files, config)

    violations.extend(
        run_diff_cover(
            Path.cwd() / config.analysis.coverage_file,
            compare_branch=config.analysis.compare_branch,
            threshold=config.analysis.coverage_threshold,
            tool_command=config.tools.diff_cover,
        )
    )
    violations.extend(run_quality_commands(config.quality.commands))
    violations.extend(check_config_drift(changed_files))

    return violations


def run_full_scan() -> list[Violation]:
    """Run full codebase scan (all files, not just changed)."""
    config_or_error = _load_config_or_violation()
    if isinstance(config_or_error, list):
        return config_or_error

    config = config_or_error

    all_file_result = get_all_files()
    if all_file_result.error:
        return [
            Violation(
                file=".",
                line=0,
                column=0,
                rule="git-file-discovery",
                message=all_file_result.error,
                severity="error",
                suggestion="Resolve git file discovery errors and rerun scan.",
            )
        ]

    violations = _run_analysis_for_files(all_file_result.files, config)

    violations.extend(
        run_diff_cover(
            Path.cwd() / config.analysis.coverage_file,
            compare_branch=config.analysis.compare_branch,
            threshold=config.analysis.coverage_threshold,
            tool_command=config.tools.diff_cover,
        )
    )
    violations.extend(run_quality_commands(config.quality.commands))
    violations.extend(check_config_drift([]))

    return violations


def _run_analysis_for_files(files: list[str], config: GuardianConfig) -> list[Violation]:
    """Run language-aware analyzers for a target file set."""
    violations: list[Violation] = []

    ts_enabled = "typescript" in config.analysis.languages
    py_enabled = "python" in config.analysis.languages

    ts_files = [f for f in files if f.endswith((".ts", ".tsx", ".js", ".jsx"))]
    py_files = [f for f in files if f.endswith(".py")]

    if ts_enabled and ts_files:
        violations.extend(run_eslint(ts_files, tool_command=config.tools.eslint))

    if py_enabled and py_files:
        violations.extend(run_ruff(py_files, tool_command=config.tools.ruff))

    if files:
        violations.extend(run_semgrep(files, tool_command=config.tools.semgrep))

    return violations


def _load_config_or_violation() -> GuardianConfig | list[Violation]:
    """Load validated config or return a single structured violation."""
    try:
        return load_guardian_config(Path.cwd())
    except ConfigValidationError as exc:
        return [
            Violation(
                file=".guardian/config.yaml",
                line=0,
                column=0,
                rule="guardian-config-invalid",
                message=str(exc),
                severity="error",
                suggestion="Fix .guardian/config.yaml and rerun Guardian.",
            )
        ]
