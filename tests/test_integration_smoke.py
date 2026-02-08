"""Integration smoke tests for end-to-end Guardian CLI verification behavior."""

import json
import os
import stat
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from guardian.cli.main import app

runner = CliRunner()


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def _setup_repo(temp_dir: Path, compare_branch: str) -> Path:
    repo = temp_dir / "repo"
    repo.mkdir()
    _run(["git", "init", "-b", "main"], cwd=repo)
    _run(["git", "config", "user.email", "test@example.com"], cwd=repo)
    _run(["git", "config", "user.name", "Test User"], cwd=repo)

    guardian_dir = repo / ".guardian"
    guardian_dir.mkdir()
    (guardian_dir / "config.yaml").write_text(
        f"analysis:\n  compare_branch: {compare_branch}\n  coverage_threshold: 80\n"
    )
    (guardian_dir / "ruff.toml").write_text("line-length = 100\n")
    (guardian_dir / "semgrep-rules.yaml").write_text("rules: []\n")
    (guardian_dir / "eslint.config.js").write_text("export default [];\n")
    (guardian_dir / "baseline.json").write_text("{}\n")

    app_file = repo / "app.py"
    app_file.write_text("print('base')\n")
    _run(["git", "add", "."], cwd=repo)
    _run(["git", "commit", "-m", "base"], cwd=repo)
    _run(["git", "update-ref", "refs/remotes/origin/main", "HEAD"], cwd=repo)

    app_file.write_text("print('changed')\n")
    _run(["git", "add", "app.py"], cwd=repo)
    _run(["git", "commit", "-m", "change"], cwd=repo)
    return repo


def _setup_fake_tools(repo: Path, ruff_json: str) -> dict[str, str]:
    bin_dir = repo / "bin"
    bin_dir.mkdir()

    _write_executable(
        bin_dir / "ruff",
        f"#!/usr/bin/env bash\necho '{ruff_json}'\nexit 0\n",
    )
    _write_executable(
        bin_dir / "semgrep",
        "#!/usr/bin/env bash\necho '{\"results\": []}'\nexit 0\n",
    )
    _write_executable(
        bin_dir / "npx",
        "#!/usr/bin/env bash\necho '[]'\nexit 0\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    return env


def test_compare_branch_missing(temp_dir, monkeypatch):
    """Verification fails when compare branch cannot be resolved."""
    repo = _setup_repo(temp_dir, "origin/missing")
    env = _setup_fake_tools(repo, "[]")
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["verify", "--json"], env=env)

    assert result.exit_code == 1
    json_start = result.stdout.find("{")
    output = json.loads(result.stdout[json_start:])
    assert output["status"] == "failed"
    assert output["violation_count"] == 1
    assert output["violations"][0]["rule"] == "git-compare-branch"
    assert output["violations"][0]["severity"] == "error"
    assert output["violations"][0]["suggestion"] == (
        "Fix compare_branch or fetch the configured branch before verifying."
    )


def test_tool_failure(temp_dir, monkeypatch):
    """Tool output failures are reported as violations instead of pass."""
    repo = _setup_repo(temp_dir, "origin/main")
    env = _setup_fake_tools(repo, "not-json")
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["verify", "--json"], env=env)

    assert result.exit_code == 1
    assert '"status": "failed"' in result.stdout
    assert "ruff-output-parse" in result.stdout


def test_happy_path(temp_dir, monkeypatch):
    """Healthy tool outputs produce a passing verification result."""
    repo = _setup_repo(temp_dir, "origin/main")
    env = _setup_fake_tools(repo, "[]")
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["verify", "--json"], env=env)

    assert result.exit_code == 0
    assert '"status": "passed"' in result.stdout
    assert '"violation_count": 0' in result.stdout
