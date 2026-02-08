"""Harness command - install and manage LLM harness configurations."""

import typer
from rich.console import Console
from rich.table import Table

from guardian.harness.installer import (
    SUPPORTED_HARNESSES,
    HarnessStatus,
    install_harness,
    list_installed_harnesses,
)

app = typer.Typer(name="harness", help="Install and manage LLM harness configurations")
console = Console()


@app.command()
def install(
    harness_name: str = typer.Argument(None, help="Harness name to install"),
    all_harnesses: bool = typer.Option(False, "--all", help="Install all harnesses"),
) -> None:
    """Install harness configuration for specific tool or all tools."""

    if all_harnesses:
        failures: list[str] = []
        for name in SUPPORTED_HARNESSES:
            try:
                install_harness(name)
                console.print(f"[green]✓ Installed {name}[/green]")
            except Exception as e:
                console.print(f"[red]✗ Failed to install {name}: {e}[/red]")
                failures.append(name)
        if failures:
            raise typer.Exit(1)
    elif harness_name:
        if harness_name not in SUPPORTED_HARNESSES:
            console.print(f"[red]Error: Unknown harness '{harness_name}'[/red]")
            console.print(f"\nSupported harnesses: {', '.join(SUPPORTED_HARNESSES)}")
            raise typer.Exit(1)

        try:
            install_harness(harness_name)
            console.print(f"[green]✓ Installed {harness_name}[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to install {harness_name}: {e}[/red]")
            raise typer.Exit(1) from e
    else:
        console.print("[red]Error: Specify harness name or use --all[/red]")
        raise typer.Exit(1)


@app.command()
def status() -> None:
    """Check status of installed harness configurations."""

    statuses = list_installed_harnesses()

    table = Table(title="Harness Status")
    table.add_column("Harness", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Files", style="yellow")
    table.add_column("Issues", style="red")

    for name in SUPPORTED_HARNESSES:
        harness_status = statuses.get(
            name,
            HarnessStatus(installed=False, files=(), missing_files=(), issues=("No status data.",)),
        )

        if harness_status.installed:
            status_text = "Installed"
        elif harness_status.files or harness_status.issues or harness_status.missing_files:
            status_text = "Incomplete"
        else:
            status_text = "Not installed"

        files_text = ", ".join(harness_status.files) if harness_status.files else "-"
        issues: list[str] = []
        issues.extend(f"Missing: {item}" for item in harness_status.missing_files)
        issues.extend(harness_status.issues)
        issues_text = "; ".join(issues) if issues else "-"
        table.add_row(name, status_text, files_text, issues_text)

    console.print(table)
