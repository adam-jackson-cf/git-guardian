"""Shared output rendering helpers for CLI verification commands."""

from __future__ import annotations

import json
from typing import NoReturn

import typer
from rich.console import Console

from guardian.analysis.violation import Violation
from guardian.report.generator import generate_report


def emit_json_result(violations: list[Violation]) -> NoReturn:
    """Print normalized JSON output and exit with verification status."""
    output = {
        "status": "passed" if not violations else "failed",
        "violation_count": len(violations),
        "violations": [
            {
                "file": violation.file,
                "line": violation.line,
                "column": violation.column,
                "rule": violation.rule,
                "message": violation.message,
                "severity": violation.severity,
                "suggestion": violation.suggestion,
            }
            for violation in violations
        ],
    }
    print(json.dumps(output, indent=2))
    raise typer.Exit(0 if not violations else 1)


def fail_with_report(
    *,
    console: Console,
    violations: list[Violation],
    failure_message: str,
    hint_message: str,
) -> NoReturn:
    """Generate a report, print guidance, and exit non-zero."""
    report_path = generate_report(violations)
    console.print(f"\n[red]❌ {failure_message}[/red]")
    console.print(f"\n[yellow]Report: {report_path}[/yellow]")
    console.print(f"\n[dim]{hint_message}[/dim]")
    raise typer.Exit(1)
