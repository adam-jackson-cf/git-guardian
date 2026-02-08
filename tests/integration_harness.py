"""Reusable integration harness for fixture-driven verification scenarios."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
from contextlib import chdir
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from guardian.analysis.config_drift import PROTECTED_CONFIGS
from guardian.cli.main import app

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "integration"
runner = CliRunner()


@dataclass(frozen=True)
class ScenarioManifest:
    """Fixture scenario contract loaded from manifest.json."""

    name: str
    description: str
    expected_status: str
    expected_exit_code: int
    expected_rules: tuple[str, ...]
    forbidden_rules: tuple[str, ...]
    min_violations: int | None
    compare_branch: str
    include_coverage_file: bool
    auto_change_app: bool
    head_delete: tuple[str, ...]
    tool_env: dict[str, str]

    @classmethod
    def from_fixture(cls, fixture_dir: Path) -> ScenarioManifest:
        """Load and normalize fixture manifest from disk."""
        manifest_path = fixture_dir / "manifest.json"
        raw = json.loads(manifest_path.read_text())

        expected_raw = raw.get("expected", {})
        repo_raw = raw.get("repo", {})
        tool_env_raw = raw.get("tool_env", {})

        expected_status = str(expected_raw.get("status", "failed"))
        if expected_status not in {"passed", "failed"}:
            raise ValueError(f"{manifest_path}: expected.status must be 'passed' or 'failed'.")

        expected_exit_code = int(
            expected_raw.get("exit_code", 0 if expected_status == "passed" else 1)
        )

        expected_rules = tuple(str(item) for item in expected_raw.get("rules", []))
        forbidden_rules = tuple(str(item) for item in expected_raw.get("forbidden_rules", []))

        min_violations_raw = expected_raw.get("min_violations")
        min_violations = int(min_violations_raw) if min_violations_raw is not None else None

        tool_env = {str(key): str(value) for key, value in tool_env_raw.items()}

        return cls(
            name=fixture_dir.name,
            description=str(raw.get("description", "")),
            expected_status=expected_status,
            expected_exit_code=expected_exit_code,
            expected_rules=expected_rules,
            forbidden_rules=forbidden_rules,
            min_violations=min_violations,
            compare_branch=str(repo_raw.get("compare_branch", "origin/main")),
            include_coverage_file=bool(repo_raw.get("include_coverage_file", True)),
            auto_change_app=bool(repo_raw.get("auto_change_app", True)),
            head_delete=tuple(str(item) for item in repo_raw.get("head_delete", [])),
            tool_env=tool_env,
        )


@dataclass(frozen=True)
class ScenarioResult:
    """Result payload for one executed fixture scenario."""

    manifest: ScenarioManifest
    exit_code: int
    payload: dict[str, Any]


def discover_scenarios() -> list[Path]:
    """Discover fixture scenarios with manifest.json files."""
    if not FIXTURE_ROOT.exists():
        return []

    scenarios = [
        path
        for path in sorted(FIXTURE_ROOT.iterdir())
        if path.is_dir() and (path / "manifest.json").exists()
    ]
    return scenarios


def run_fixture_scenario(temp_dir: Path, fixture_dir: Path) -> ScenarioResult:
    """Build repository from fixture and run guardian verify --json."""
    manifest = ScenarioManifest.from_fixture(fixture_dir)
    repo = _setup_repository(temp_dir / fixture_dir.name, fixture_dir, manifest)
    env = _build_fake_tool_environment(repo, manifest.tool_env)

    with chdir(repo):
        result = runner.invoke(app, ["verify", "--json"], env=env)

    payload = _extract_json_payload(result.stdout)

    return ScenarioResult(
        manifest=manifest,
        exit_code=result.exit_code,
        payload=payload,
    )


def _setup_repository(repo: Path, fixture_dir: Path, manifest: ScenarioManifest) -> Path:
    """Create git repository state for a fixture scenario."""
    repo.mkdir(parents=True, exist_ok=True)
    _run(["git", "init", "-b", "main"], cwd=repo)
    _run(["git", "config", "user.email", "test@example.com"], cwd=repo)
    _run(["git", "config", "user.name", "Test User"], cwd=repo)

    _seed_default_repository(repo, manifest)
    _copy_overlay(fixture_dir / "base", repo)
    _write_baseline_files(repo)

    _run(["git", "add", "."], cwd=repo)
    _run(["git", "commit", "-m", "base"], cwd=repo)
    _run(["git", "update-ref", "refs/remotes/origin/main", "HEAD"], cwd=repo)

    if manifest.auto_change_app:
        (repo / "app.py").write_text("print('changed')\n")

    _copy_overlay(fixture_dir / "head", repo)
    _delete_paths(repo, manifest.head_delete)

    _run(["git", "add", "-A"], cwd=repo)
    _run(["git", "commit", "-m", "head"], cwd=repo)

    return repo


def _seed_default_repository(repo: Path, manifest: ScenarioManifest) -> None:
    """Write baseline repository files used by scenarios."""
    guardian_dir = repo / ".guardian"
    guardian_dir.mkdir(parents=True, exist_ok=True)

    config_text = "\n".join(
        [
            'version: "0.3"',
            "analysis:",
            "  languages:",
            "    - typescript",
            "    - python",
            f"  compare_branch: {manifest.compare_branch}",
            "  coverage_threshold: 80",
            "  coverage_file: coverage.xml",
            "tools:",
            "  eslint: npx --no-install eslint",
            "  ruff: ruff",
            "  semgrep: semgrep",
            "  diff_cover: diff-cover",
            "quality:",
            "  commands:",
            "    - quality-gate",
            "reports:",
            "  format: markdown",
            "  keep_count: 10",
            "harness:",
            "  enabled: []",
            "",
        ]
    )

    (guardian_dir / "config.yaml").write_text(config_text)
    (guardian_dir / "ruff.toml").write_text("line-length = 100\n")
    (guardian_dir / "semgrep-rules.yaml").write_text("rules: []\n")
    (guardian_dir / "eslint.config.js").write_text("export default [];\n")

    if manifest.include_coverage_file:
        (repo / "coverage.xml").write_text("<coverage line-rate='1.0'></coverage>\n")

    (repo / "app.py").write_text("print('base')\n")


def _write_baseline_files(repo: Path) -> None:
    """Generate baseline hash and metadata files for protected configs."""
    baseline_data: dict[str, str] = {}
    for relative_path in PROTECTED_CONFIGS:
        config_path = repo / relative_path
        if config_path.exists():
            baseline_data[relative_path] = hashlib.sha256(config_path.read_bytes()).hexdigest()

    guardian_dir = repo / ".guardian"
    guardian_dir.mkdir(exist_ok=True)
    (guardian_dir / "baseline.json").write_text(json.dumps(baseline_data, indent=2) + "\n")
    (guardian_dir / "baseline.meta.json").write_text(
        json.dumps(
            {
                "acknowledged_policy_change": True,
                "reason": "Fixture baseline setup",
                "updated_at": "2026-01-01T00:00:00+00:00",
            },
            indent=2,
        )
        + "\n"
    )


def _copy_overlay(source_dir: Path, destination: Path) -> None:
    """Copy fixture overlay files into destination repository."""
    if not source_dir.exists():
        return

    for source_path in source_dir.rglob("*"):
        relative = source_path.relative_to(source_dir)
        target = destination / relative
        if source_path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, target)


def _delete_paths(repo: Path, relative_paths: tuple[str, ...]) -> None:
    """Delete listed paths from repository if they exist."""
    for relative_path in relative_paths:
        target = repo / relative_path
        if not target.exists():
            continue
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()


def _run(cmd: list[str], cwd: Path) -> None:
    """Run command in repository with strict error handling."""
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def _build_fake_tool_environment(repo: Path, scenario_env: dict[str, str]) -> dict[str, str]:
    """Create deterministic fake toolchain for scenario execution."""
    bin_dir = repo / "bin"
    bin_dir.mkdir(exist_ok=True)

    _write_executable(
        bin_dir / "npx",
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                'printf "%s\\n" "${NPX_STDOUT:-[]}"',
                'exit "${NPX_EXIT:-0}"',
                "",
            ]
        ),
    )

    _write_executable(
        bin_dir / "ruff",
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                'printf "%s\\n" "${RUFF_STDOUT:-[]}"',
                'exit "${RUFF_EXIT:-0}"',
                "",
            ]
        ),
    )

    _write_executable(
        bin_dir / "semgrep",
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                "default_payload='{\"results\": []}'",
                'printf "%s\\n" "${SEMGREP_STDOUT:-$default_payload}"',
                'exit "${SEMGREP_EXIT:-0}"',
                "",
            ]
        ),
    )

    _write_executable(
        bin_dir / "diff-cover",
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                'report=""',
                "while (($# > 0)); do",
                '  if [[ "$1" == "--json-report" ]]; then',
                '    report="$2"',
                "    shift 2",
                "    continue",
                "  fi",
                "  shift",
                "done",
                'if [[ "${DIFF_COVER_WRITE_REPORT:-1}" == "1" ]]; then',
                "  payload=${DIFF_COVER_REPORT:-'{\"total_percent_covered\": 100}'}",
                '  printf "%s\\n" "$payload" > "$report"',
                "fi",
                'exit "${DIFF_COVER_EXIT:-0}"',
                "",
            ]
        ),
    )

    _write_executable(
        bin_dir / "quality-gate",
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                'exit "${QUALITY_GATE_EXIT:-0}"',
                "",
            ]
        ),
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env.update(scenario_env)
    return env


def _write_executable(path: Path, content: str) -> None:
    """Write an executable helper script."""
    path.write_text(content)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def _extract_json_payload(output: str) -> dict[str, Any]:
    """Extract JSON object from mixed CLI output."""
    json_start = output.find("{")
    if json_start == -1:
        raise AssertionError(f"Expected JSON output from guardian verify --json. Output:\n{output}")

    try:
        data = json.loads(output[json_start:])
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Failed to decode Guardian JSON output: {exc}\n{output}") from exc

    if not isinstance(data, dict):
        raise AssertionError(f"Guardian JSON output must be an object. Output:\n{output}")
    return data
