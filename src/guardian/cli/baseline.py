"""Baseline command - manage config baseline hashes."""

import hashlib
import json
from pathlib import Path

import typer
from rich.console import Console

from guardian.analysis.config_drift import PROTECTED_CONFIGS

app = typer.Typer(name="baseline", help="Manage config baseline hashes")
console = Console()


@app.command()
def update() -> None:
    """Generate baseline hashes for config drift detection."""

    repo_root = Path.cwd()
    guardian_dir = repo_root / ".guardian"
    baseline_file = guardian_dir / "baseline.json"

    if not guardian_dir.exists():
        console.print("[red]Error: Guardian not initialized. Run guardian init first.[/red]")
        raise typer.Exit(1)

    baseline_data = {}

    for config_file, _ in PROTECTED_CONFIGS.items():
        config_path = repo_root / config_file
        if config_path.exists():
            current_hash = hashlib.sha256(config_path.read_bytes()).hexdigest()
            baseline_data[config_file] = current_hash
            console.print(f"[green]✓ Updated baseline for {config_file}[/green]")
        else:
            console.print(f"[dim]Skipping {config_file} (not found)[/dim]")

    baseline_file.write_text(json.dumps(baseline_data, indent=2) + "\n")
    console.print(f"\n[green]✓ Baseline updated: {baseline_file}[/green]")
