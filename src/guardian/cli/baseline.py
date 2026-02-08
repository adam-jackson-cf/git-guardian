"""Baseline command - manage config baseline hashes."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import typer
from rich.console import Console

from guardian.analysis.config_drift import BASELINE_META_FILE, PROTECTED_CONFIGS

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
def update(
    acknowledge_policy_change: bool = typer.Option(
        False,
        "--acknowledge-policy-change",
        help="Acknowledge that baseline updates are policy changes.",
    ),
    reason: str = typer.Option(
        "",
        "--reason",
        help="Why this baseline update is required (minimum 10 characters).",
    ),
) -> None:
    """Generate baseline hashes for config drift detection."""

    repo_root = Path.cwd()
    guardian_dir = repo_root / ".guardian"
    baseline_file = guardian_dir / "baseline.json"
    baseline_meta_file = repo_root / BASELINE_META_FILE

    if not guardian_dir.exists():
        console.print("[red]Error: Guardian not initialized. Run guardian init first.[/red]")
        raise typer.Exit(1)

    if not acknowledge_policy_change:
        console.print("[red]Error: baseline updates require --acknowledge-policy-change[/red]")
        raise typer.Exit(1)

    normalized_reason = reason.strip()
    if len(normalized_reason) < 10:
        console.print("[red]Error: --reason must be at least 10 characters for auditability.[/red]")
        raise typer.Exit(1)

    baseline_data, included_files = generate_baseline_data(repo_root)
    for config_file in PROTECTED_CONFIGS:
        if config_file in included_files:
            console.print(f"[green]✓ Updated baseline for {config_file}[/green]")
        else:
            console.print(f"[dim]Skipping {config_file} (not found)[/dim]")

    baseline_file.write_text(json.dumps(baseline_data, indent=2) + "\n")
    metadata = {
        "acknowledged_policy_change": True,
        "reason": normalized_reason,
        "updated_at": datetime.now(UTC).isoformat(),
    }
    baseline_meta_file.parent.mkdir(parents=True, exist_ok=True)
    baseline_meta_file.write_text(json.dumps(metadata, indent=2) + "\n")
    console.print(f"\n[green]✓ Baseline updated: {baseline_file}[/green]")
    console.print(f"[green]✓ Baseline metadata updated: {baseline_meta_file}[/green]")
