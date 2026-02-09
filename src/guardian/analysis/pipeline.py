"""Verification pipeline - orchestrates external tools."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import Literal

from guardian.analysis.config_drift import check_config_drift
from guardian.analysis.coverage import run_diff_cover
from guardian.analysis.eslint import run_eslint
from guardian.analysis.git_utils import get_all_files, get_changed_files
from guardian.analysis.quality_commands import run_quality_commands
from guardian.analysis.ruff import run_ruff
from guardian.analysis.semgrep import run_semgrep
from guardian.analysis.violation import Violation
from guardian.configuration import ConfigValidationError, GuardianConfig, load_guardian_config


def run_verification(*, quality_scope: Literal["changed", "full"] = "changed") -> list[Violation]:
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
    violations.extend(
        run_quality_commands(
            config.quality.commands,
            changed_files=tuple(changed_files),
            scope=quality_scope,
        )
    )
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
    violations.extend(
        run_quality_commands(
            config.quality.commands,
            changed_files=tuple(all_file_result.files),
            scope="full",
        )
    )
    violations.extend(check_config_drift([]))

    return violations


def _run_analysis_for_files(files: list[str], config: GuardianConfig) -> list[Violation]:
    """Run language-aware analyzers for a target file set."""
    ts_enabled = "typescript" in config.analysis.languages
    py_enabled = "python" in config.analysis.languages

    ts_files = [f for f in files if f.endswith((".ts", ".tsx", ".js", ".jsx"))]
    py_files = [f for f in files if f.endswith(".py")]

    tool_jobs: list[tuple[str, Callable[[], list[Violation]]]] = []
    if ts_enabled and ts_files:
        tool_jobs.append(
            ("eslint", partial(run_eslint, ts_files, tool_command=config.tools.eslint))
        )

    if py_enabled and py_files:
        tool_jobs.append(("ruff", partial(run_ruff, py_files, tool_command=config.tools.ruff)))

    if files:
        tool_jobs.append(
            ("semgrep", partial(run_semgrep, files, tool_command=config.tools.semgrep))
        )

    if not tool_jobs:
        return []

    results_by_tool: dict[str, list[Violation]] = {}
    with ThreadPoolExecutor(max_workers=len(tool_jobs)) as executor:
        futures: dict[Future[list[Violation]], str] = {
            executor.submit(job): name for name, job in tool_jobs
        }
        for future, name in futures.items():
            try:
                results_by_tool[name] = future.result()
            except Exception as exc:  # pragma: no cover - defensive fail-closed path
                results_by_tool[name] = [
                    Violation(
                        file=".",
                        line=0,
                        column=0,
                        rule=f"{name}-runner-crash",
                        message=f"{name} runner crashed: {exc}",
                        severity="error",
                        suggestion="Fix the tool runner crash and retry Guardian verification.",
                    )
                ]

    merged: list[Violation] = []
    for name, _ in tool_jobs:
        merged.extend(results_by_tool.get(name, []))
    return _sort_violations(merged)


def _sort_violations(violations: list[Violation]) -> list[Violation]:
    """Keep violation order deterministic regardless of execution concurrency."""
    return sorted(
        violations,
        key=lambda violation: (
            violation.file,
            violation.line,
            violation.column,
            violation.rule,
            violation.message,
        ),
    )


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
