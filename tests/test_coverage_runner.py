"""Tests for strict diff-cover coverage behavior."""

from __future__ import annotations

from guardian.analysis.coverage import run_diff_cover


def test_coverage_missing_artifact(temp_dir, monkeypatch) -> None:
    """Missing coverage artifact must fail closed."""
    monkeypatch.chdir(temp_dir)

    violations = run_diff_cover(
        temp_dir / "coverage.xml",
        compare_branch="origin/main",
        threshold=80,
        tool_command="diff-cover",
    )

    assert len(violations) == 1
    assert violations[0].rule == "coverage-artifact-missing"
    assert violations[0].severity == "error"


def test_coverage_missing_report_fails_closed(temp_dir, monkeypatch) -> None:
    """Tool executions that do not emit JSON report must fail verification."""
    monkeypatch.chdir(temp_dir)
    (temp_dir / "coverage.xml").write_text("<coverage line-rate='1.0'></coverage>\n")

    violations = run_diff_cover(
        temp_dir / "coverage.xml",
        compare_branch="origin/main",
        threshold=80,
        tool_command="true",
    )

    assert len(violations) == 1
    assert violations[0].rule == "diff-cover-report-missing"
    assert violations[0].severity == "error"
