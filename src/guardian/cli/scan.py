"""Scan command - full codebase audit."""

import typer
from rich.console import Console

from guardian.analysis.pipeline import run_full_scan
from guardian.cli.output import emit_json_result, fail_with_report

app = typer.Typer(name="scan", help="Full codebase audit")
console = Console()


@app.callback(invoke_without_command=True)
def scan(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Run full codebase audit (all files, not just changed)."""

    console.print("[blue]Running full Guardian scan...[/blue]")

    violations = run_full_scan()

    if json_output:
        emit_json_result(violations)

    if violations:
        fail_with_report(
            console=console,
            violations=violations,
            failure_message=f"Scan found {len(violations)} violation(s)",
            hint_message="Read the report and fix violations.",
        )

    console.print("[green]✓ Scan passed - no violations found[/green]")
