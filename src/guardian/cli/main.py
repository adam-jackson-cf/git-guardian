"""Main CLI entry point for Guardian."""

import typer
from rich.console import Console

from guardian.cli import baseline, config, harness, init, push, report, scan, verify

app = typer.Typer(
    name="guardian",
    help="Guardian - AI Code Verification System",
    add_completion=False,
)

console = Console()

# Register subcommands
app.add_typer(init.app, name="init")
app.add_typer(push.app, name="push")
app.add_typer(verify.app, name="verify")
app.add_typer(scan.app, name="scan")
app.add_typer(harness.app, name="harness")
app.add_typer(report.app, name="report")
app.add_typer(config.app, name="config")
app.add_typer(baseline.app, name="baseline")


def main() -> None:
    """Entry point for guardian CLI."""
    app()


if __name__ == "__main__":
    main()
