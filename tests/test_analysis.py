"""Tests for analysis modules."""

from guardian.analysis.violation import Violation


def test_violation_creation():
    """Test Violation dataclass creation."""
    v = Violation(
        file="test.py",
        line=10,
        column=5,
        rule="test-rule",
        message="Test message",
        severity="error",
    )

    assert v.file == "test.py"
    assert v.line == 10
    assert v.column == 5
    assert v.rule == "test-rule"
    assert v.message == "Test message"
    assert v.severity == "error"
    assert v.suggestion is None


def test_violation_with_suggestion():
    """Test Violation with suggestion."""
    v = Violation(
        file="test.py",
        line=10,
        column=5,
        rule="test-rule",
        message="Test message",
        severity="warning",
        suggestion="Fix this",
    )

    assert v.suggestion == "Fix this"
