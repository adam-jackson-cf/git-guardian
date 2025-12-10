"""Violation data structure."""

from dataclasses import dataclass


@dataclass
class Violation:
    """Represents a code quality violation."""

    file: str
    line: int
    column: int
    rule: str
    message: str
    severity: str
    suggestion: str | None = None
