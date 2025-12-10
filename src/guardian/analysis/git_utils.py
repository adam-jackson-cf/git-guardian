"""Git utilities for file detection."""

import subprocess
from pathlib import Path


def get_changed_files() -> list[str]:
    """Get files changed since origin/main."""
    repo_root = Path.cwd()

    # Try to get compare branch from config
    config_file = repo_root / ".guardian" / "config.yaml"
    compare_branch = "origin/main"

    if config_file.exists():
        import yaml

        config = yaml.safe_load(config_file.read_text())
        compare_branch = config.get("analysis", {}).get("compare_branch", "origin/main")

    # Check if branch exists
    result = subprocess.run(
        ["git", "rev-parse", "--verify", compare_branch],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        # Branch doesn't exist, return empty list
        return []

    result = subprocess.run(
        ["git", "diff", "--name-only", f"{compare_branch}...HEAD"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return []

    files = [f for f in result.stdout.strip().split("\n") if f]
    # Filter to only files that exist
    return [f for f in files if (repo_root / f).exists()]


def get_all_files() -> list[str]:
    """Get all tracked files in the repository."""
    repo_root = Path.cwd()

    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return []

    files = [f for f in result.stdout.strip().split("\n") if f]
    # Filter to only files that exist
    return [f for f in files if (repo_root / f).exists()]
