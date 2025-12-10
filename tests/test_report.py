"""Tests for report generation."""

from guardian.analysis.violation import Violation
from guardian.report.generator import generate_report


def test_generate_report(temp_dir, monkeypatch):
    """Test report generation."""
    monkeypatch.chdir(temp_dir)

    # Create .guardian directory
    guardian_dir = temp_dir / ".guardian"
    guardian_dir.mkdir()
    reports_dir = guardian_dir / "reports"
    reports_dir.mkdir()

    # Create violations
    violations = [
        Violation(
            file="test.py",
            line=10,
            column=5,
            rule="test-rule",
            message="Test error",
            severity="error",
        ),
        Violation(
            file="test2.py",
            line=20,
            column=10,
            rule="test-rule-2",
            message="Test warning",
            severity="warning",
            suggestion="Fix this",
        ),
    ]

    # Generate report
    report_path = generate_report(violations)

    # Check report exists
    assert report_path.exists()
    assert report_path.suffix == ".md"

    # Check report content
    content = report_path.read_text()
    assert "Guardian Verification Report" in content
    assert "test.py" in content
    assert "test2.py" in content
    assert "Test error" in content
    assert "Test warning" in content
    assert "Fix this" in content

    # Check latest symlink
    latest_link = reports_dir / "latest.md"
    assert latest_link.exists()
    assert latest_link.is_symlink()
