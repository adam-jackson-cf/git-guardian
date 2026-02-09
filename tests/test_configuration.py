"""Tests for centralized Guardian config validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from guardian.configuration import ConfigValidationError, load_guardian_config, split_command


def _write_config(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_config_requires_quality_commands(temp_dir) -> None:
    """Missing quality.commands should be rejected."""
    config_file = temp_dir / ".guardian" / "config.yaml"
    _write_config(
        config_file,
        """
version: "0.3"
analysis:
  compare_branch: origin/main
""",
    )

    with pytest.raises(ConfigValidationError):
        load_guardian_config(temp_dir)


def test_npx_command_is_normalized() -> None:
    """npx commands must include --no-install for determinism."""
    argv = split_command("npx eslint", field_name="tools.eslint")
    assert argv[:3] == ["npx", "--no-install", "eslint"]


def test_config_rejects_legacy_string_quality_commands(temp_dir) -> None:
    """Legacy string-only quality.commands entries should be rejected."""
    config_file = temp_dir / ".guardian" / "config.yaml"
    _write_config(
        config_file,
        """
version: "0.3"
quality:
  commands:
    - uv run pytest
""",
    )

    with pytest.raises(ConfigValidationError):
        load_guardian_config(temp_dir)
