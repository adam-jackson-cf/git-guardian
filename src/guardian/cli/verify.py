"""Verify command - run verification without pushing."""

import typer
from rich.console import Console

from guardian.analysis.pipeline import run_verification
from guardian.cli.output import emit_json_result, fail_with_report

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
        emit_json_result(violations)

    if violations:
        fail_with_report(
            console=console,
            violations=violations,
            failure_message=f"Verification failed with {len(violations)} violation(s)",
            hint_message="Read the report and fix violations.",
        )

    console.print("[green]✓ Verification passed[/green]")
