"""CLI regression tests for direct command invocation paths."""

from typer.testing import CliRunner

from guardian.cli.main import app

runner = CliRunner()


def test_verify_direct_invocation(monkeypatch):
    """guardian verify should run directly without nested subcommand."""
    monkeypatch.setattr("guardian.cli.verify.run_verification", lambda: [])

    result = runner.invoke(app, ["verify", "--json"])

    assert result.exit_code == 0
    assert '"status": "passed"' in result.stdout


def test_push_direct_invocation(monkeypatch):
    """guardian push should run directly without nested subcommand."""
    monkeypatch.setattr("guardian.cli.push.run_verification", lambda **kwargs: [])
    monkeypatch.setattr(
        "guardian.cli.push.run_command",
        lambda *args, **kwargs: (
            type("Result", (), {"returncode": 0, "stdout": "main\n"})(),
            None,
        ),
    )

    result = runner.invoke(app, ["push", "--dry-run"])

    assert result.exit_code == 0
    assert "Verification passed" in result.stdout


def test_scan_direct_invocation(monkeypatch):
    """guardian scan should run directly without nested subcommand."""
    monkeypatch.setattr("guardian.cli.scan.run_full_scan", lambda: [])

    result = runner.invoke(app, ["scan", "--json"])

    assert result.exit_code == 0
    assert '"status": "passed"' in result.stdout
