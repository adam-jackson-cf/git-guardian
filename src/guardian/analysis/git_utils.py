"""Git utilities for file detection."""

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileDiscoveryResult:
    """Result of attempting to discover repository files."""

    files: list[str]
    error: str | None = None


def get_changed_files(compare_branch: str) -> FileDiscoveryResult:
    """Get files changed since the configured compare branch."""
    repo_root = Path.cwd()

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", compare_branch],
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return FileDiscoveryResult(
            files=[],
            error=f"Failed to verify compare branch '{compare_branch}': {exc}",
        )

    if result.returncode != 0:
        return FileDiscoveryResult(
            files=[],
            error=(
                f"Compare branch '{compare_branch}' is not available. "
                "Set analysis.compare_branch to a valid ref."
            ),
        )

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{compare_branch}...HEAD"],
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return FileDiscoveryResult(
            files=[],
            error=f"Failed to diff against compare branch '{compare_branch}': {exc}",
        )

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

    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return FileDiscoveryResult(files=[], error=f"Failed to list repository files: {exc}")

    if result.returncode != 0:
        return FileDiscoveryResult(files=[], error="git ls-files failed in current repository.")

    files = [f for f in result.stdout.strip().split("\n") if f]
    return FileDiscoveryResult(files=[f for f in files if (repo_root / f).exists()])
