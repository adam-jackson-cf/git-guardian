"""Harness installer - installs LLM tool configurations."""

import contextlib
import json
from pathlib import Path

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

    # Install settings.local.json
    claude_dir = repo_root / ".claude"
    claude_dir.mkdir(exist_ok=True)

    template = env.get_template("claude_settings.json.j2")
    settings_content = template.render()
    settings_file = claude_dir / "settings.local.json"
    settings_file.write_text(settings_content)

    # Install CLAUDE.md
    template = env.get_template("CLAUDE.md.j2")
    claude_md_content = template.render()
    claude_md_file = repo_root / "CLAUDE.md"
    claude_md_file.write_text(claude_md_content)


def _install_codex(repo_root: Path) -> None:
    """Install Codex CLI harness configuration."""
    env = get_template_env()

    # Install policy file in user home
    codex_policy_dir = Path.home() / ".codex" / "policy"
    codex_policy_dir.mkdir(parents=True, exist_ok=True)

    template = env.get_template("codex_policy.codexpolicy.j2")
    policy_content = template.render()
    policy_file = codex_policy_dir / "guardian.codexpolicy"
    policy_file.write_text(policy_content)

    # Install AGENTS.md
    template = env.get_template("AGENTS.md.j2")
    agents_md_content = template.render()
    agents_md_file = repo_root / "AGENTS.md"
    agents_md_file.write_text(agents_md_content)


def _install_cursor(repo_root: Path) -> None:
    """Install Cursor harness configuration."""
    env = get_template_env()

    # Install .cursorrules
    template = env.get_template("cursorrules.j2")
    cursorrules_content = template.render()
    cursorrules_file = repo_root / ".cursorrules"
    cursorrules_file.write_text(cursorrules_content)

    # Note: settings.json would need to be manually added to VS Code settings
    # We can create a note file or just document it


def _install_gemini(repo_root: Path) -> None:
    """Install Gemini CLI harness configuration."""
    env = get_template_env()

    # Install policy file
    gemini_policy_dir = repo_root / ".gemini" / "policies"
    gemini_policy_dir.mkdir(parents=True, exist_ok=True)

    template = env.get_template("gemini_policy.toml.j2")
    policy_content = template.render()
    policy_file = gemini_policy_dir / "guardian.toml"
    policy_file.write_text(policy_content)

    # Install GEMINI.md
    template = env.get_template("GEMINI.md.j2")
    gemini_md_content = template.render()
    gemini_md_file = repo_root / "GEMINI.md"
    gemini_md_file.write_text(gemini_md_content)


def _install_copilot(repo_root: Path) -> None:
    """Install GitHub Copilot harness configuration."""
    env = get_template_env()

    # Install instructions file
    github_dir = repo_root / ".github"
    github_dir.mkdir(exist_ok=True)

    template = env.get_template("copilot_instructions.md.j2")
    instructions_content = template.render()
    instructions_file = github_dir / "copilot-instructions.md"
    instructions_file.write_text(instructions_content)

    # Install VS Code settings file
    vscode_dir = repo_root / ".vscode"
    vscode_dir.mkdir(exist_ok=True)

    template = env.get_template("copilot_settings.json.j2")
    settings_content = template.render()
    settings_file = vscode_dir / "settings.json"

    # Merge with existing settings if present
    existing_settings = {}
    if settings_file.exists():
        with contextlib.suppress(json.JSONDecodeError):
            existing_settings = json.loads(settings_file.read_text())

    # Merge Copilot settings
    copilot_settings = json.loads(settings_content)
    if "github.copilot.chat.agent.terminal" not in existing_settings:
        existing_settings["github.copilot.chat.agent.terminal"] = {}

    existing_settings["github.copilot.chat.agent.terminal"].update(
        copilot_settings["github.copilot.chat.agent.terminal"]
    )

    settings_file.write_text(json.dumps(existing_settings, indent=2) + "\n")


def list_installed_harnesses() -> dict[str, list[str]]:
    """List which harness configurations are installed."""
    repo_root = Path.cwd()
    installed = {}

    # Check Claude Code
    claude_settings = repo_root / ".claude" / "settings.local.json"
    claude_md = repo_root / "CLAUDE.md"
    if claude_settings.exists() or claude_md.exists():
        files = []
        if claude_settings.exists():
            files.append(".claude/settings.local.json")
        if claude_md.exists():
            files.append("CLAUDE.md")
        installed["claude-code"] = files

    # Check Codex
    codex_policy = Path.home() / ".codex" / "policy" / "guardian.codexpolicy"
    agents_md = repo_root / "AGENTS.md"
    if codex_policy.exists() or agents_md.exists():
        files = []
        if codex_policy.exists():
            files.append("~/.codex/policy/guardian.codexpolicy")
        if agents_md.exists():
            files.append("AGENTS.md")
        installed["codex"] = files

    # Check Cursor
    if (repo_root / ".cursorrules").exists():
        installed["cursor"] = [".cursorrules"]

    # Check Gemini
    gemini_policy = repo_root / ".gemini" / "policies" / "guardian.toml"
    gemini_md = repo_root / "GEMINI.md"
    if gemini_policy.exists() or gemini_md.exists():
        files = []
        if gemini_policy.exists():
            files.append(".gemini/policies/guardian.toml")
        if gemini_md.exists():
            files.append("GEMINI.md")
        installed["gemini"] = files

    # Check Copilot
    copilot_instructions = repo_root / ".github" / "copilot-instructions.md"
    copilot_settings = repo_root / ".vscode" / "settings.json"
    if copilot_instructions.exists() or copilot_settings.exists():
        files = []
        if copilot_instructions.exists():
            files.append(".github/copilot-instructions.md")
        if copilot_settings.exists():
            files.append(".vscode/settings.json")
        installed["copilot"] = files

    return installed
