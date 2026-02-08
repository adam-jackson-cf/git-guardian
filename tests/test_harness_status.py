"""Tests for strict harness status auditing."""

from __future__ import annotations

import json

from guardian.harness.installer import list_installed_harnesses


def test_claude_status_requires_all_files(temp_dir, monkeypatch) -> None:
    """Harness is incomplete when one required artifact is missing."""
    monkeypatch.chdir(temp_dir)

    claude_dir = temp_dir / ".claude"
    claude_dir.mkdir()
    (claude_dir / "settings.local.json").write_text(
        json.dumps({"permissions": {"deny": ["Bash(git push:*)"]}})
    )

    statuses = list_installed_harnesses()
    claude_status = statuses["claude-code"]

    assert claude_status.installed is False
    assert any("CLAUDE.md" in missing for missing in claude_status.missing_files)
