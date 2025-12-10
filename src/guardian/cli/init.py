"""Initialize Guardian in a repository."""

import subprocess
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(name="init", help="Initialize Guardian in a repository")
console = Console()


def _initialize_guardian() -> None:
    """Initialize Guardian configuration in the current repository."""
    repo_root = Path.cwd()

    # Check if we're in a git repository
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        console.print("[red]Error: Not in a git repository[/red]")
        raise typer.Exit(1) from None

    guardian_dir = repo_root / ".guardian"
    guardian_dir.mkdir(exist_ok=True)
    reports_dir = guardian_dir / "reports"
    reports_dir.mkdir(exist_ok=True)

    # Create default config if it doesn't exist
    config_file = guardian_dir / "config.yaml"
    if not config_file.exists():
        config_file.write_text("""# Guardian Configuration

version: "0.3"

# Analysis settings
analysis:
  # Languages to check
  languages:
    - typescript
    - python

  # Coverage threshold for diff-cover
  coverage_threshold: 80

  # Compare branch for diff operations
  compare_branch: origin/main

# Tool paths (auto-detected if not specified)
tools:
  eslint: npx eslint
  ruff: ruff
  semgrep: semgrep
  diff_cover: diff-cover

# Report settings
reports:
  format: markdown
  keep_count: 10  # Number of reports to retain

# Harness configuration
harness:
  # Which tools are in use
  enabled: []
""")
        console.print(f"[green]✓ Created {config_file}[/green]")

    # Create baseline.json if it doesn't exist
    baseline_file = guardian_dir / "baseline.json"
    if not baseline_file.exists():
        baseline_file.write_text("""{}
""")
        console.print(f"[green]✓ Created {baseline_file}[/green]")

    # Copy analysis config files from templates
    from guardian.harness.installer import TEMPLATE_DIR

    config_files = {
        "eslint.config.js": guardian_dir / "eslint.config.js",
        "ruff.toml": guardian_dir / "ruff.toml",
        "semgrep-rules.yaml": guardian_dir / "semgrep-rules.yaml",
    }

    for template_name, target_file in config_files.items():
        if not target_file.exists():
            template_file = TEMPLATE_DIR / template_name
            if template_file.exists():
                target_file.write_text(template_file.read_text())
                console.print(f"[green]✓ Created {target_file}[/green]")

    console.print(f"\n[green]✓ Guardian initialized in {repo_root}[/green]")
    console.print("\n[yellow]Next steps:[/yellow]")
    console.print(
        "  1. Install harness configurations: " "[cyan]guardian harness install --all[/cyan]"
    )
    console.print("  2. Run verification: [cyan]guardian verify[/cyan]")


@app.callback(invoke_without_command=True)
def init() -> None:
    """Initialize Guardian configuration in the current repository."""
    _initialize_guardian()
