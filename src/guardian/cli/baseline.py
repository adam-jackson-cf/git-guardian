"""Baseline command - manage config baseline hashes."""

import hashlib
import json
from pathlib import Path

import typer
from rich.console import Console

from guardian.analysis.config_drift import PROTECTED_CONFIGS

app = typer.Typer(name="baseline", help="Manage config baseline hashes")
console = Console()


def generate_baseline_data(repo_root: Path) -> tuple[dict[str, str], list[str]]:
    """Generate baseline hashes and list files included."""
    baseline_data: dict[str, str] = {}
    included_files: list[str] = []

    for config_file in PROTECTED_CONFIGS:
        config_path = repo_root / config_file
        if config_path.exists():
            current_hash = hashlib.sha256(config_path.read_bytes()).hexdigest()
            baseline_data[config_file] = current_hash
            included_files.append(config_file)

    return baseline_data, included_files


@app.command()
def update() -> None:
    """Generate baseline hashes for config drift detection."""

    repo_root = Path.cwd()
    guardian_dir = repo_root / ".guardian"
    baseline_file = guardian_dir / "baseline.json"

    if not guardian_dir.exists():
        console.print("[red]Error: Guardian not initialized. Run guardian init first.[/red]")
        raise typer.Exit(1)

    baseline_data, included_files = generate_baseline_data(repo_root)
    for config_file in PROTECTED_CONFIGS:
        if config_file in included_files:
            console.print(f"[green]✓ Updated baseline for {config_file}[/green]")
        else:
            console.print(f"[dim]Skipping {config_file} (not found)[/dim]")

    baseline_file.write_text(json.dumps(baseline_data, indent=2) + "\n")
    console.print(f"\n[green]✓ Baseline updated: {baseline_file}[/green]")
