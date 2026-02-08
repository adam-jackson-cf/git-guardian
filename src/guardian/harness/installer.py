"""Harness installer - installs and validates LLM tool configurations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

SUPPORTED_HARNESSES = [
    "claude-code",
    "codex",
    "cursor",
    "gemini",
    "copilot",
]

# Template directory
TEMPLATE_DIR = Path(__file__).parent / "templates"


@dataclass(frozen=True)
class HarnessStatus:
    """Auditable harness installation status."""

    installed: bool
    files: tuple[str, ...]
    missing_files: tuple[str, ...]
    issues: tuple[str, ...]


def get_template_env() -> Environment:
    """Get Jinja2 template environment."""
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=False,
    )


def install_harness(harness_name: str) -> None:
    """Install harness configuration for a specific tool."""
    repo_root = Path.cwd()

    if harness_name == "claude-code":
        _install_claude_code(repo_root)
    elif harness_name == "codex":
        _install_codex(repo_root)
    elif harness_name == "cursor":
        _install_cursor(repo_root)
    elif harness_name == "gemini":
        _install_gemini(repo_root)
    elif harness_name == "copilot":
        _install_copilot(repo_root)
    else:
        raise ValueError(f"Unknown harness: {harness_name}")


def _install_claude_code(repo_root: Path) -> None:
    """Install Claude Code harness configuration."""
    env = get_template_env()

    claude_dir = repo_root / ".claude"
    claude_dir.mkdir(exist_ok=True)

    settings_content = env.get_template("claude_settings.json.j2").render()
    (claude_dir / "settings.local.json").write_text(settings_content)

    claude_md_content = env.get_template("CLAUDE.md.j2").render()
    (repo_root / "CLAUDE.md").write_text(claude_md_content)


def _install_codex(repo_root: Path) -> None:
    """Install Codex CLI harness configuration."""
    env = get_template_env()

    codex_policy_dir = Path.home() / ".codex" / "policy"
    codex_policy_dir.mkdir(parents=True, exist_ok=True)

    policy_content = env.get_template("codex_policy.codexpolicy.j2").render()
    (codex_policy_dir / "guardian.codexpolicy").write_text(policy_content)

    agents_md_content = env.get_template("AGENTS.md.j2").render()
    (repo_root / "AGENTS.md").write_text(agents_md_content)


def _install_cursor(repo_root: Path) -> None:
    """Install Cursor harness configuration."""
    env = get_template_env()

    cursorrules_content = env.get_template("cursorrules.j2").render()
    (repo_root / ".cursorrules").write_text(cursorrules_content)

    vscode_dir = repo_root / ".vscode"
    vscode_dir.mkdir(exist_ok=True)
    settings_file = vscode_dir / "settings.json"

    cursor_settings = json.loads(env.get_template("cursor_settings.json.j2").render())
    _merge_dotted_settings(settings_file, "cursor.agent.terminal.allowList", cursor_settings)


def _install_gemini(repo_root: Path) -> None:
    """Install Gemini CLI harness configuration."""
    env = get_template_env()

    gemini_policy_dir = repo_root / ".gemini" / "policies"
    gemini_policy_dir.mkdir(parents=True, exist_ok=True)

    policy_content = env.get_template("gemini_policy.toml.j2").render()
    (gemini_policy_dir / "guardian.toml").write_text(policy_content)

    gemini_md_content = env.get_template("GEMINI.md.j2").render()
    (repo_root / "GEMINI.md").write_text(gemini_md_content)


def _install_copilot(repo_root: Path) -> None:
    """Install GitHub Copilot harness configuration."""
    env = get_template_env()

    github_dir = repo_root / ".github"
    github_dir.mkdir(exist_ok=True)

    instructions_content = env.get_template("copilot_instructions.md.j2").render()
    (github_dir / "copilot-instructions.md").write_text(instructions_content)

    vscode_dir = repo_root / ".vscode"
    vscode_dir.mkdir(exist_ok=True)
    settings_file = vscode_dir / "settings.json"

    copilot_settings = json.loads(env.get_template("copilot_settings.json.j2").render())
    _merge_dotted_settings(
        settings_file,
        "github.copilot.chat.agent.terminal",
        copilot_settings,
    )


def _merge_dotted_settings(settings_file: Path, key: str, source: dict[str, Any]) -> None:
    """Merge a dotted-key settings payload into VS Code settings.json."""
    existing_settings: dict[str, Any] = {}
    if settings_file.exists():
        existing_raw = json.loads(settings_file.read_text())
        if not isinstance(existing_raw, dict):
            raise ValueError(f"{settings_file} must contain a JSON object.")
        existing_settings = existing_raw

    source_value = source.get(key)
    if not isinstance(source_value, dict):
        raise ValueError(f"Template settings for '{key}' must be a JSON object.")

    existing_value = existing_settings.get(key)
    if existing_value is None:
        existing_settings[key] = source_value
    elif isinstance(existing_value, dict):
        existing_value.update(source_value)
    else:
        raise ValueError(f"Existing settings key '{key}' must be a JSON object.")

    settings_file.write_text(json.dumps(existing_settings, indent=2) + "\n")


def list_installed_harnesses() -> dict[str, HarnessStatus]:
    """Return strict install status for all supported harnesses."""
    repo_root = Path.cwd()
    return {
        "claude-code": _status_claude(repo_root),
        "codex": _status_codex(repo_root),
        "cursor": _status_cursor(repo_root),
        "gemini": _status_gemini(repo_root),
        "copilot": _status_copilot(repo_root),
    }


def _status_claude(repo_root: Path) -> HarnessStatus:
    settings = repo_root / ".claude" / "settings.local.json"
    instructions = repo_root / "CLAUDE.md"

    missing = _missing_files((settings, instructions))
    issues: list[str] = []

    settings_json = _read_json(settings)
    if settings_json is None:
        issues.append("Invalid or unreadable .claude/settings.local.json")
    else:
        permissions = settings_json.get("permissions")
        deny = permissions.get("deny") if isinstance(permissions, dict) else None
        if not isinstance(deny, list) or not any("git push" in str(item) for item in deny):
            issues.append("Claude deny rules do not include git push")

    if not _file_contains(instructions, "guardian push"):
        issues.append("CLAUDE.md is missing guardian push instructions")

    return _build_status((settings, instructions), missing, issues)


def _status_codex(repo_root: Path) -> HarnessStatus:
    policy = Path.home() / ".codex" / "policy" / "guardian.codexpolicy"
    instructions = repo_root / "AGENTS.md"

    missing = _missing_files((policy, instructions))
    issues: list[str] = []

    if not _file_contains(policy, 'decision = "forbidden"') or not _file_contains(
        policy, 'pattern = ["git", "push"]'
    ):
        issues.append("Codex policy does not forbid git push")

    if not _file_contains(instructions, "guardian push"):
        issues.append("AGENTS.md is missing guardian push instructions")

    return _build_status((policy, instructions), missing, issues)


def _status_cursor(repo_root: Path) -> HarnessStatus:
    rules = repo_root / ".cursorrules"
    settings = repo_root / ".vscode" / "settings.json"

    missing = _missing_files((rules, settings))
    issues: list[str] = []

    if not _file_contains(rules, "guardian push"):
        issues.append(".cursorrules is missing guardian push instructions")

    settings_json = _read_json(settings)
    if settings_json is None:
        issues.append("Invalid or unreadable .vscode/settings.json")
    else:
        allow_list = settings_json.get("cursor.agent.terminal.allowList")
        if not isinstance(allow_list, dict) or allow_list.get("guardian push") is not True:
            issues.append("Cursor allowList is missing guardian push=true")

    return _build_status((rules, settings), missing, issues)


def _status_gemini(repo_root: Path) -> HarnessStatus:
    policy = repo_root / ".gemini" / "policies" / "guardian.toml"
    instructions = repo_root / "GEMINI.md"

    missing = _missing_files((policy, instructions))
    issues: list[str] = []

    if not _file_contains(policy, 'decision = "deny"') or not _file_contains(
        policy, 'commandPrefix = "git push"'
    ):
        issues.append("Gemini policy does not deny git push")

    if not _file_contains(instructions, "guardian push"):
        issues.append("GEMINI.md is missing guardian push instructions")

    return _build_status((policy, instructions), missing, issues)


def _status_copilot(repo_root: Path) -> HarnessStatus:
    instructions = repo_root / ".github" / "copilot-instructions.md"
    settings = repo_root / ".vscode" / "settings.json"

    missing = _missing_files((instructions, settings))
    issues: list[str] = []

    if not _file_contains(instructions, "guardian push"):
        issues.append("Copilot instructions are missing guardian push guidance")

    settings_json = _read_json(settings)
    if settings_json is None:
        issues.append("Invalid or unreadable .vscode/settings.json")
    else:
        terminal = settings_json.get("github.copilot.chat.agent.terminal")
        if not isinstance(terminal, dict):
            issues.append("Copilot terminal settings key is missing")
        else:
            deny_list = terminal.get("denyList")
            allow_list = terminal.get("allowList")
            if not isinstance(deny_list, dict) or deny_list.get("git push") is not True:
                issues.append("Copilot denyList is missing git push=true")
            if not isinstance(allow_list, dict) or allow_list.get("guardian push") is not True:
                issues.append("Copilot allowList is missing guardian push=true")

    return _build_status((instructions, settings), missing, issues)


def _build_status(
    files: tuple[Path, ...],
    missing_files: tuple[str, ...],
    issues: list[str],
) -> HarnessStatus:
    """Create consistent status output for CLI rendering."""
    return HarnessStatus(
        installed=not missing_files and not issues,
        files=tuple(str(path) for path in files if path.exists()),
        missing_files=missing_files,
        issues=tuple(issues),
    )


def _missing_files(paths: tuple[Path, ...]) -> tuple[str, ...]:
    """Return missing file paths as strings."""
    return tuple(str(path) for path in paths if not path.exists())


def _read_json(path: Path) -> dict[str, Any] | None:
    """Read a JSON object from file path."""
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    return raw


def _file_contains(path: Path, needle: str) -> bool:
    """Check whether a file exists and contains expected text."""
    if not path.exists():
        return False
    try:
        return needle in path.read_text()
    except OSError:
        return False
