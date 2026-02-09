"""Parsing helpers for deterministic command execution."""

from __future__ import annotations

import shlex

from guardian.configuration.validation import ConfigValidationError


def split_command(command: str, *, field_name: str) -> list[str]:
    """Parse a configured command string into deterministic argv."""
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        raise ConfigValidationError(f"Invalid command for {field_name}: {exc}") from exc

    if not argv:
        raise ConfigValidationError(f"Command for {field_name} cannot be empty.")

    # Prevent nondeterministic installs when using npx.
    if argv[0] == "npx" and "--no-install" not in argv[1:]:
        argv.insert(1, "--no-install")

    return argv
