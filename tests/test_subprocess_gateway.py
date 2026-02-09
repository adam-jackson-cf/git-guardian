"""Guardrail tests for subprocess gateway usage."""

from __future__ import annotations

from pathlib import Path


def test_subprocess_run_only_in_tool_runner() -> None:
    """Direct subprocess.run usage must stay centralized in tool_runner."""
    repo_root = Path(__file__).resolve().parents[1]
    src_root = repo_root / "src" / "guardian"
    allowed = {src_root / "analysis" / "tool_runner.py"}

    violations: list[str] = []
    for path in src_root.rglob("*.py"):
        if path in allowed:
            continue
        if "subprocess.run(" in path.read_text():
            violations.append(str(path))

    assert violations == [], (
        "Direct subprocess.run usage found outside tool_runner:\n"
        + "\n".join(sorted(violations))
    )
