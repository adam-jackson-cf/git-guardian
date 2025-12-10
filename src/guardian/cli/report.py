"""Report command - view latest report."""

from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(name="report", help="View latest report")
console = Console()


@app.command()
def report(
    path: str = typer.Option(None, "--path", help="Path to specific report file"),
) -> None:
    """View latest report or specific report by path."""

    guardian_dir = Path.cwd() / ".guardian"
    reports_dir = guardian_dir / "reports"

    if not reports_dir.exists():
        console.print("[red]Error: No reports directory found. Run guardian verify first.[/red]")
        raise typer.Exit(1)

    if path:
        report_file = Path(path)
        if not report_file.exists():
            console.print(f"[red]Error: Report file not found: {path}[/red]")
            raise typer.Exit(1)
    else:
        # Try to find latest.md symlink
        latest_link = reports_dir / "latest.md"
        if latest_link.exists() and latest_link.is_symlink():
            report_file = latest_link.resolve()
        else:
            # Find most recent report
            reports = sorted(
                reports_dir.glob("*.md"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if not reports:
                console.print("[red]Error: No reports found. Run guardian verify first.[/red]")
                raise typer.Exit(1)
            report_file = reports[0]

    console.print(f"[blue]Report: {report_file}[/blue]\n")
    console.print(report_file.read_text())
