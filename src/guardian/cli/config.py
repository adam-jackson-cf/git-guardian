"""Config command - show current configuration."""

from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.syntax import Syntax

from guardian.configuration import ConfigValidationError, load_guardian_config

app = typer.Typer(name="config", help="Show current configuration")
console = Console()


@app.command()
def show() -> None:
    """Show current Guardian configuration."""

    config_file = Path.cwd() / ".guardian" / "config.yaml"

    if not config_file.exists():
        console.print("[yellow]No configuration file found. Run guardian init first.[/yellow]")
        raise typer.Exit(0)

    try:
        load_guardian_config(Path.cwd())
    except ConfigValidationError as exc:
        console.print(f"[red]Invalid Guardian config: {exc}[/red]")
        raise typer.Exit(1) from None

    config_data = yaml.safe_load(config_file.read_text())
    config_yaml = yaml.dump(config_data, default_flow_style=False, sort_keys=False)

    syntax = Syntax(config_yaml, "yaml", theme="monokai")
    console.print(syntax)
