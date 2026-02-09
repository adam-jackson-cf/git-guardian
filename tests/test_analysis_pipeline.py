"""Pipeline behavior tests for fail-closed verification semantics."""

from guardian.analysis.git_utils import FileDiscoveryResult
from guardian.analysis.pipeline import _run_analysis_for_files, run_verification
from guardian.analysis.violation import Violation
from guardian.configuration import QualityCommand


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
                "quality": type(
                    "Quality",
                    (),
                    {
                        "commands": (
                            QualityCommand(
                                name="git-status",
                                run="git status --short",
                                run_on="always",
                                include=(),
                            ),
                        )
                    },
                )(),
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
                "quality": type(
                    "Quality",
                    (),
                    {
                        "commands": (
                            QualityCommand(
                                name="git-status",
                                run="git status --short",
                                run_on="always",
                                include=(),
                            ),
                        )
                    },
                )(),
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
        lambda _commands, *, changed_files, scope: [],
    )
    monkeypatch.setattr("guardian.analysis.pipeline.check_config_drift", lambda _changed: [])

    violations = run_verification()

    assert len(violations) == 1
    assert violations[0].rule == "ruff-output-parse"
    assert violations[0].severity == "error"


def test_run_verification_uses_changed_quality_scope(monkeypatch):
    """verify should run quality commands in changed-file scope."""
    captured: dict[str, object] = {}
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
                "quality": type(
                    "Quality",
                    (),
                    {
                        "commands": (
                            QualityCommand(
                                name="gate",
                                run="git status --short",
                                run_on="always",
                                include=(),
                            ),
                        )
                    },
                )(),
            },
        )(),
    )
    monkeypatch.setattr(
        "guardian.analysis.pipeline.get_changed_files",
        lambda _compare_branch: FileDiscoveryResult(files=["src/app.py"]),
    )
    monkeypatch.setattr("guardian.analysis.pipeline.run_ruff", lambda _files, *, tool_command: [])
    monkeypatch.setattr(
        "guardian.analysis.pipeline.run_semgrep",
        lambda _files, *, tool_command: [],
    )
    monkeypatch.setattr(
        "guardian.analysis.pipeline.run_diff_cover",
        lambda _coverage_file, *, compare_branch, threshold, tool_command: [],
    )
    monkeypatch.setattr("guardian.analysis.pipeline.check_config_drift", lambda _changed: [])

    def _capture_quality(commands, *, changed_files, scope):
        captured["changed_files"] = changed_files
        captured["scope"] = scope
        return []

    monkeypatch.setattr("guardian.analysis.pipeline.run_quality_commands", _capture_quality)

    violations = run_verification()

    assert violations == []
    assert captured["scope"] == "changed"
    assert captured["changed_files"] == ("src/app.py",)


def test_run_analysis_for_files_sorts_violations_deterministically(monkeypatch):
    """Concurrent analyzer execution must still produce stable violation ordering."""
    config = type(
        "Config",
        (),
        {
            "analysis": type("Analysis", (), {"languages": ("python", "typescript")})(),
            "tools": type(
                "Tools",
                (),
                {
                    "eslint": "npx --no-install eslint",
                    "ruff": "ruff",
                    "semgrep": "semgrep",
                },
            )(),
        },
    )()
    monkeypatch.setattr(
        "guardian.analysis.pipeline.run_eslint",
        lambda _files, *, tool_command: [
            Violation(
                file="z.ts",
                line=20,
                column=1,
                rule="eslint-z",
                message="z",
                severity="error",
            )
        ],
    )
    monkeypatch.setattr(
        "guardian.analysis.pipeline.run_ruff",
        lambda _files, *, tool_command: [
            Violation(
                file="a.py",
                line=1,
                column=1,
                rule="ruff-a",
                message="a",
                severity="error",
            )
        ],
    )
    monkeypatch.setattr(
        "guardian.analysis.pipeline.run_semgrep",
        lambda _files, *, tool_command: [
            Violation(
                file="m.py",
                line=2,
                column=2,
                rule="semgrep-m",
                message="m",
                severity="error",
            )
        ],
    )

    violations = _run_analysis_for_files(["z.ts", "a.py"], config)

    assert [violation.file for violation in violations] == ["a.py", "m.py", "z.ts"]
