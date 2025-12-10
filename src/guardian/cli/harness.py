"""Harness command - install and manage LLM harness configurations."""

import typer
from rich.console import Console
from rich.table import Table

from guardian.harness.installer import (
    SUPPORTED_HARNESSES,
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
        for name in SUPPORTED_HARNESSES:
            try:
                install_harness(name)
                console.print(f"[green]✓ Installed {name}[/green]")
            except Exception as e:
                console.print(f"[red]✗ Failed to install {name}: {e}[/red]")
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

    installed = list_installed_harnesses()

    table = Table(title="Harness Status")
    table.add_column("Harness", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Files", style="yellow")

    for name in SUPPORTED_HARNESSES:
        status_text = "Installed" if name in installed else "Not installed"
        files = installed.get(name, [])
        files_text = ", ".join(files) if files else "-"
        table.add_row(name, status_text, files_text)

    console.print(table)
