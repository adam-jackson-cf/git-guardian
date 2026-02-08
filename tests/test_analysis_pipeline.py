"""Pipeline behavior tests for fail-closed verification semantics."""

from guardian.analysis.git_utils import FileDiscoveryResult
from guardian.analysis.pipeline import run_verification
from guardian.analysis.violation import Violation


def test_run_verification_fails_when_compare_branch_missing(monkeypatch):
    """Compare branch discovery failures must fail verification."""
    monkeypatch.setattr(
        "guardian.analysis.pipeline.load_guardian_config",
        lambda _repo_root: type(
            "Config",
            (),
            {
                "analysis": type(
                    "Analysis",
                    (),
                    {
                        "compare_branch": "origin/main",
                        "coverage_file": "coverage.xml",
                        "coverage_threshold": 80,
                        "languages": ("python", "typescript"),
                    },
                )(),
                "tools": type(
                    "Tools",
                    (),
                    {
                        "eslint": "npx --no-install eslint",
                        "ruff": "ruff",
                        "semgrep": "semgrep",
                        "diff_cover": "diff-cover",
                    },
                )(),
                "quality": type("Quality", (), {"commands": ("git status --short",)})(),
            },
        )(),
    )
    monkeypatch.setattr(
        "guardian.analysis.pipeline.get_changed_files",
        lambda _compare_branch: FileDiscoveryResult(files=[], error="Compare branch missing"),
    )

    violations = run_verification()

    assert len(violations) == 1
    assert violations[0].rule == "git-compare-branch"
    assert violations[0].severity == "error"


def test_run_verification_propagates_tool_failures(monkeypatch):
    """Tool execution failures should become explicit violations."""
    monkeypatch.setattr(
        "guardian.analysis.pipeline.load_guardian_config",
        lambda _repo_root: type(
            "Config",
            (),
            {
                "analysis": type(
                    "Analysis",
                    (),
                    {
                        "compare_branch": "origin/main",
                        "coverage_file": "coverage.xml",
                        "coverage_threshold": 80,
                        "languages": ("python",),
                    },
                )(),
                "tools": type(
                    "Tools",
                    (),
                    {
                        "eslint": "npx --no-install eslint",
                        "ruff": "ruff",
                        "semgrep": "semgrep",
                        "diff_cover": "diff-cover",
                    },
                )(),
                "quality": type("Quality", (), {"commands": ("git status --short",)})(),
            },
        )(),
    )
    monkeypatch.setattr(
        "guardian.analysis.pipeline.get_changed_files",
        lambda _compare_branch: FileDiscoveryResult(files=["src/app.py"]),
    )
    monkeypatch.setattr(
        "guardian.analysis.pipeline.run_ruff",
        lambda _files, *, tool_command: [
            Violation(
                file=".",
                line=0,
                column=0,
                rule="ruff-output-parse",
                message="Failed to parse Ruff output",
                severity="error",
            )
        ],
    )
    monkeypatch.setattr(
        "guardian.analysis.pipeline.run_semgrep",
        lambda _files, *, tool_command: [],
    )
    monkeypatch.setattr(
        "guardian.analysis.pipeline.run_diff_cover",
        lambda _coverage_file, *, compare_branch, threshold, tool_command: [],
    )
    monkeypatch.setattr(
        "guardian.analysis.pipeline.run_quality_commands",
        lambda _commands: [],
    )
    monkeypatch.setattr("guardian.analysis.pipeline.check_config_drift", lambda _changed: [])

    violations = run_verification()

    assert len(violations) == 1
    assert violations[0].rule == "ruff-output-parse"
    assert violations[0].severity == "error"
