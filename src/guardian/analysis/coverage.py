"""Coverage analysis using diff-cover."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from guardian.analysis.tool_runner import run_command
from guardian.analysis.violation import Violation
from guardian.configuration import ConfigValidationError, split_command


def run_diff_cover(
    coverage_file: Path,
    *,
    compare_branch: str,
    threshold: int,
    tool_command: str,
) -> list[Violation]:
    """Run diff-cover for coverage analysis in fail-closed mode."""
    repo_root = Path.cwd()

    if not coverage_file.exists():
        return [_coverage_artifact_missing_violation(coverage_file)]

    base_cmd, command_violation = _resolve_diff_cover_command(tool_command)
    if command_violation is not None:
        return [command_violation]
    assert base_cmd is not None

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        report_path = Path(tmp.name)

    try:
        cmd = _build_diff_cover_command(
            base_cmd,
            coverage_file=coverage_file,
            compare_branch=compare_branch,
            threshold=threshold,
            report_path=report_path,
        )
        result, execution_violation = _run_diff_cover(cmd, repo_root, coverage_file)
        if execution_violation is not None:
            return [execution_violation]
        assert result is not None

        report_data, report_violation = _load_diff_cover_report(report_path, coverage_file, result)
        if report_violation is not None:
            return [report_violation]
        assert report_data is not None

        coverage_value, coverage_violation = _extract_coverage_value(report_data, coverage_file)
        if coverage_violation is not None:
            return [coverage_violation]
        assert coverage_value is not None

        return _build_coverage_violations(
            result=result,
            coverage_file=coverage_file,
            coverage_value=coverage_value,
            threshold=threshold,
        )

    finally:
        if report_path.exists():
            report_path.unlink()


def _coverage_artifact_missing_violation(coverage_file: Path) -> Violation:
    return Violation(
        file=str(coverage_file),
        line=0,
        column=0,
        rule="coverage-artifact-missing",
        message=(
            f"Coverage artifact is missing at {coverage_file}. "
            "Guardian requires coverage data before push."
        ),
        severity="error",
        suggestion="Generate fresh coverage (for example: pytest --cov --cov-report=xml).",
    )


def _resolve_diff_cover_command(
    tool_command: str,
) -> tuple[list[str], None] | tuple[None, Violation]:
    try:
        return split_command(tool_command, field_name="tools.diff_cover"), None
    except ConfigValidationError as exc:
        return None, Violation(
            file=".guardian/config.yaml",
            line=0,
            column=0,
            rule="diff-cover-command-invalid",
            message=str(exc),
            severity="error",
            suggestion="Fix tools.diff_cover in .guardian/config.yaml.",
        )


def _build_diff_cover_command(
    base_cmd: list[str],
    *,
    coverage_file: Path,
    compare_branch: str,
    threshold: int,
    report_path: Path,
) -> list[str]:
    return [
        *base_cmd,
        str(coverage_file),
        "--compare-branch",
        compare_branch,
        "--json-report",
        str(report_path),
        "--fail-under",
        str(threshold),
    ]


def _run_diff_cover(
    cmd: list[str],
    repo_root: Path,
    coverage_file: Path,
) -> tuple[subprocess.CompletedProcess[str], None] | tuple[None, Violation]:
    result, execution_violation = run_command(
        cmd,
        cwd=repo_root,
        execution_rule="diff-cover-execution",
        execution_prefix="Failed to execute diff-cover",
        execution_suggestion="Ensure diff-cover is installed and available to Guardian.",
        violation_file=str(coverage_file),
    )
    if execution_violation is not None:
        return None, execution_violation
    assert result is not None
    return result, None


def _load_diff_cover_report(
    report_path: Path,
    coverage_file: Path,
    result: subprocess.CompletedProcess[str],
) -> tuple[dict[str, object], None] | tuple[None, Violation]:
    if not report_path.exists():
        stderr_preview = result.stderr.strip().splitlines()
        detail = stderr_preview[0] if stderr_preview else "No stderr output available."
        return None, Violation(
            file=str(coverage_file),
            line=0,
            column=0,
            rule="diff-cover-report-missing",
            message=f"diff-cover did not produce JSON output. {detail}",
            severity="error",
            suggestion="Fix diff-cover invocation and ensure coverage report is valid.",
        )

    try:
        report_text = report_path.read_text()
        if not report_text.strip():
            return None, Violation(
                file=str(coverage_file),
                line=0,
                column=0,
                rule="diff-cover-report-missing",
                message="diff-cover JSON output file is empty.",
                severity="error",
                suggestion="Fix diff-cover invocation and ensure coverage report is valid.",
            )
        report_data = json.loads(report_text)
    except (json.JSONDecodeError, OSError) as exc:
        return None, Violation(
            file=str(coverage_file),
            line=0,
            column=0,
            rule="diff-cover-output-parse",
            message=f"Failed to parse diff-cover JSON output: {exc}",
            severity="error",
            suggestion="Ensure diff-cover can read the coverage artifact and compare branch.",
        )

    if not isinstance(report_data, dict):
        return None, Violation(
            file=str(coverage_file),
            line=0,
            column=0,
            rule="diff-cover-output-invalid",
            message="diff-cover JSON output must be an object.",
            severity="error",
            suggestion="Use a valid coverage.xml and rerun verification.",
        )
    return report_data, None


def _extract_coverage_value(
    report_data: dict[str, object],
    coverage_file: Path,
) -> tuple[float, None] | tuple[None, Violation]:
    coverage_value = report_data.get("total_percent_covered")
    if not isinstance(coverage_value, (int, float)):
        return None, Violation(
            file=str(coverage_file),
            line=0,
            column=0,
            rule="diff-cover-output-invalid",
            message="diff-cover JSON output is missing total_percent_covered.",
            severity="error",
            suggestion="Use a valid coverage.xml and rerun verification.",
        )
    return float(coverage_value), None


def _build_coverage_violations(
    *,
    result: subprocess.CompletedProcess[str],
    coverage_file: Path,
    coverage_value: float,
    threshold: int,
) -> list[Violation]:
    violations: list[Violation] = []

    if coverage_value < threshold:
        violations.append(
            Violation(
                file="coverage",
                line=0,
                column=0,
                rule="coverage-delta",
                message=(
                    f"Coverage on changed lines is {coverage_value:.1f}%, "
                    f"below threshold of {threshold}%"
                ),
                severity="error",
            )
        )

    if result.returncode not in (0, 1):
        stderr_preview = result.stderr.strip().splitlines()
        detail = stderr_preview[0] if stderr_preview else "No stderr output available."
        violations.append(
            Violation(
                file=str(coverage_file),
                line=0,
                column=0,
                rule="diff-cover-execution",
                message=f"diff-cover failed with exit code {result.returncode}. {detail}",
                severity="error",
                suggestion="Fix diff-cover runtime errors before pushing.",
            )
        )

    if result.returncode == 1 and coverage_value >= threshold:
        violations.append(
            Violation(
                file=str(coverage_file),
                line=0,
                column=0,
                rule="diff-cover-execution",
                message=(
                    "diff-cover returned a failure code without an actual "
                    "coverage threshold violation."
                ),
                severity="error",
                suggestion="Review diff-cover diagnostics and compare-branch configuration.",
            )
        )

    return violations
