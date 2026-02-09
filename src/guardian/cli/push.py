"""Push command with verification."""

import sys
from pathlib import Path

import typer
from rich.console import Console

from guardian.analysis.pipeline import run_verification
from guardian.analysis.tool_runner import run_command
from guardian.report.generator import generate_report

app = typer.Typer(name="push", help="Verify code quality and push to remote")
console = Console()


@app.callback(invoke_without_command=True)
def push(
    remote: str = typer.Argument("origin", help="Git remote name"),
    branch: str = typer.Argument(None, help="Branch to push (default: current)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Verify without pushing"),
) -> None:
    """Verify code quality and push to remote."""

    # Get current branch if not specified
    if branch is None:
        result, execution_violation = run_command(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=Path.cwd(),
            execution_rule="git-current-branch-execution",
            execution_prefix="Failed to determine current branch",
            execution_suggestion="Ensure git is installed and run inside a repository.",
        )
        if execution_violation is not None:
            console.print(f"[red]Error: {execution_violation.message}[/red]")
            raise typer.Exit(1)
        assert result is not None
        if result.returncode != 0:
            console.print("[red]Error: Could not determine current branch[/red]")
            raise typer.Exit(1)
        branch = result.stdout.strip()

    console.print("[blue]Running Guardian verification...[/blue]")

    # Run verification
    violations = run_verification(quality_scope="full")

    if violations:
        # Generate report
        report_path = generate_report(violations)

        console.print(f"\n[red]❌ Verification failed with {len(violations)} violation(s)[/red]")
        console.print(f"\n[yellow]Report: {report_path}[/yellow]")
        console.print("\n[dim]Read the report, fix violations, commit changes, then retry.[/dim]")

        sys.exit(1)

    console.print("[green]✓ Verification passed[/green]")

    if dry_run:
        console.print("[dim]Dry run - skipping push[/dim]")
        sys.exit(0)

    # Execute git push
    push_cmd = ["git", "push"]
    push_cmd.extend([remote, branch])

    console.print(f"\n[blue]Pushing to {remote}/{branch}...[/blue]")

    push_result, push_execution_violation = run_command(
        push_cmd,
        cwd=Path.cwd(),
        execution_rule="git-push-execution",
        execution_prefix="Failed to execute git push",
        execution_suggestion="Ensure git is installed and remote is reachable.",
    )
    if push_execution_violation is not None:
        console.print(f"[red]❌ {push_execution_violation.message}[/red]")
        sys.exit(2)
    assert push_result is not None

    if push_result.returncode != 0:
        console.print("[red]❌ Git push failed[/red]")
        sys.exit(2)

    console.print(f"[green]✓ Successfully pushed to {remote}/{branch}[/green]")
