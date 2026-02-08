"""Verify command - run verification without pushing."""

import json
import sys

import typer
from rich.console import Console

from guardian.analysis.pipeline import run_verification
from guardian.report.generator import generate_report

app = typer.Typer(name="verify", help="Run verification without pushing")
console = Console()


@app.callback(invoke_without_command=True)
def verify(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Run verification without pushing."""

    console.print("[blue]Running Guardian verification...[/blue]")

    violations = run_verification()

    if json_output:
        output = {
            "status": "passed" if not violations else "failed",
            "violation_count": len(violations),
            "violations": [
                {
                    "file": v.file,
                    "line": v.line,
                    "column": v.column,
                    "rule": v.rule,
                    "message": v.message,
                    "severity": v.severity,
                    "suggestion": v.suggestion,
                }
                for v in violations
            ],
        }
        print(json.dumps(output, indent=2))
        sys.exit(0 if not violations else 1)

    if violations:
        report_path = generate_report(violations)

        console.print(f"\n[red]❌ Verification failed with {len(violations)} violation(s)[/red]")
        console.print(f"\n[yellow]Report: {report_path}[/yellow]")
        console.print("\n[dim]Read the report and fix violations.[/dim]")

        sys.exit(1)

    console.print("[green]✓ Verification passed[/green]")
