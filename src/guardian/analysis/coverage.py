"""Coverage analysis using diff-cover."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

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
        return [
            Violation(
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
        ]

    try:
        base_cmd = split_command(tool_command, field_name="tools.diff_cover")
    except ConfigValidationError as exc:
        return [
            Violation(
                file=".guardian/config.yaml",
                line=0,
                column=0,
                rule="diff-cover-command-invalid",
                message=str(exc),
                severity="error",
                suggestion="Fix tools.diff_cover in .guardian/config.yaml.",
            )
        ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        report_path = Path(tmp.name)

    try:
        cmd = [
            *base_cmd,
            str(coverage_file),
            "--compare-branch",
            compare_branch,
            "--json-report",
            str(report_path),
            "--fail-under",
            str(threshold),
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
                    file=str(coverage_file),
                    line=0,
                    column=0,
                    rule="diff-cover-execution",
                    message=f"Failed to execute diff-cover: {exc}",
                    severity="error",
                    suggestion="Ensure diff-cover is installed and available to Guardian.",
                )
            ]

        if not report_path.exists():
            stderr_preview = result.stderr.strip().splitlines()
            detail = stderr_preview[0] if stderr_preview else "No stderr output available."
            return [
                Violation(
                    file=str(coverage_file),
                    line=0,
                    column=0,
                    rule="diff-cover-report-missing",
                    message=f"diff-cover did not produce JSON output. {detail}",
                    severity="error",
                    suggestion="Fix diff-cover invocation and ensure coverage report is valid.",
                )
            ]

        try:
            report_text = report_path.read_text()
            if not report_text.strip():
                return [
                    Violation(
                        file=str(coverage_file),
                        line=0,
                        column=0,
                        rule="diff-cover-report-missing",
                        message="diff-cover JSON output file is empty.",
                        severity="error",
                        suggestion="Fix diff-cover invocation and ensure coverage report is valid.",
                    )
                ]
            report_data = json.loads(report_text)
        except (json.JSONDecodeError, OSError) as exc:
            return [
                Violation(
                    file=str(coverage_file),
                    line=0,
                    column=0,
                    rule="diff-cover-output-parse",
                    message=f"Failed to parse diff-cover JSON output: {exc}",
                    severity="error",
                    suggestion=(
                        "Ensure diff-cover can read the coverage artifact and compare branch."
                    ),
                )
            ]

        coverage_value = report_data.get("total_percent_covered")
        if not isinstance(coverage_value, (int, float)):
            return [
                Violation(
                    file=str(coverage_file),
                    line=0,
                    column=0,
                    rule="diff-cover-output-invalid",
                    message="diff-cover JSON output is missing total_percent_covered.",
                    severity="error",
                    suggestion="Use a valid coverage.xml and rerun verification.",
                )
            ]

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
                    message=(f"diff-cover failed with exit code {result.returncode}. {detail}"),
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

    finally:
        if report_path.exists():
            report_path.unlink()
