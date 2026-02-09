"""Git utilities for file detection."""

from dataclasses import dataclass
from pathlib import Path

from guardian.analysis.tool_runner import run_command


@dataclass
class FileDiscoveryResult:
    """Result of attempting to discover repository files."""

    files: list[str]
    error: str | None = None


def get_changed_files(compare_branch: str) -> FileDiscoveryResult:
    """Get files changed since the configured compare branch."""
    repo_root = Path.cwd()

    result, execution_violation = run_command(
        ["git", "rev-parse", "--verify", compare_branch],
        cwd=repo_root,
        execution_rule="git-compare-branch-execution",
        execution_prefix=f"Failed to verify compare branch '{compare_branch}'",
        execution_suggestion="Ensure git is installed and compare_branch is valid.",
    )
    if execution_violation is not None:
        return FileDiscoveryResult(
            files=[],
            error=execution_violation.message,
        )
    assert result is not None

    if result.returncode != 0:
        return FileDiscoveryResult(
            files=[],
            error=(
                f"Compare branch '{compare_branch}' is not available. "
                "Set analysis.compare_branch to a valid ref."
            ),
        )

    result, execution_violation = run_command(
        ["git", "diff", "--name-only", f"{compare_branch}...HEAD"],
        cwd=repo_root,
        execution_rule="git-diff-execution",
        execution_prefix=f"Failed to diff against compare branch '{compare_branch}'",
        execution_suggestion="Ensure git is installed and repository state is healthy.",
    )
    if execution_violation is not None:
        return FileDiscoveryResult(
            files=[],
            error=execution_violation.message,
        )
    assert result is not None

    if result.returncode != 0:
        return FileDiscoveryResult(
            files=[],
            error=(
                f"Git diff failed for compare branch '{compare_branch}'. "
                "Fix repository state and retry."
            ),
        )

    files = [f for f in result.stdout.strip().split("\n") if f]
    return FileDiscoveryResult(files=[f for f in files if (repo_root / f).exists()])


def get_all_files() -> FileDiscoveryResult:
    """Get all tracked files in the repository."""
    repo_root = Path.cwd()

    result, execution_violation = run_command(
        ["git", "ls-files"],
        cwd=repo_root,
        execution_rule="git-ls-files-execution",
        execution_prefix="Failed to list repository files",
        execution_suggestion="Ensure git is installed and run within a repository.",
    )
    if execution_violation is not None:
        return FileDiscoveryResult(files=[], error=execution_violation.message)
    assert result is not None

    if result.returncode != 0:
        return FileDiscoveryResult(files=[], error="git ls-files failed in current repository.")

    files = [f for f in result.stdout.strip().split("\n") if f]
    return FileDiscoveryResult(files=[f for f in files if (repo_root / f).exists()])
