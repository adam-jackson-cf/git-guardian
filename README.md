# Guardian - AI Code Verification System

Guardian is a verification system designed to detect and prevent quality gate bypasses in AI-assisted development workflows. It operates as a final validation layer that cannot be circumvented by AI code assistants, ensuring commits meet quality standards before being pushed to remote repositories.

## Prerequisites

- **Python 3.11+** - Guardian requires Python 3.11 or higher
- **Git** - Must be in a git repository to use Guardian
- **uv** - Required for installation and command execution

## Installation

### Option 0: Quick Install (local script)

Run the installer script directly from the repository:

```bash
# Basic installation (interactive)
bash install.sh

# Easy mode (auto-install everything without prompts)
bash install.sh --easy-mode

# Dry run (preview what would be installed)
bash install.sh --dry-run
```

**Installation Options:**

| Flag | Description |
|------|-------------|
| `--easy-mode` | Auto-install everything without prompts |
| `--dry-run` | Show what would be installed without making changes |
| `--non-interactive` | Fail if prompts would be required (CI-friendly) |
| `--minimal` | Skip harness installation and init |
| `--skip-init` | Skip running `guardian init` |
| `--skip-harness` | Skip installing harness configurations |
| `--uninstall` | Uninstall git-guardian and remove configurations |
| `--help` | Show full help message |

**Security Note:** Review the script before executing:

```bash
cat install.sh  # Review the script
bash install.sh
```

### Option 1: Install from Source

```bash
# From the repository root, install using uv
uv sync
uv pip install -e .

# Install git pre-commit gate
pre-commit install
```

## Quick Start

After installation, navigate to your project repository and initialize Guardian:

```bash
# Navigate to your project
cd /path/to/your-project

# Initialize Guardian (must be in a git repository)
guardian init

# Install harness configurations for your LLM tools
guardian harness install --all
# Or install specific tools:
guardian harness install claude-code
guardian harness install cursor

# Verify code quality
guardian verify

# Push with verification (blocks push if violations found)
guardian push origin main

# JSON output for CI/automation
guardian verify --json
```

## What Guardian Does

Guardian prevents AI code assistants from bypassing quality gates by:

- **Blocking `git push`** - LLM tools are configured to deny direct `git push` commands
- **Requiring `guardian push`** - The only way for LLMs to push code is through Guardian's verification
- **Running quality checks** - ESLint, Ruff, Semgrep, and coverage analysis before allowing pushes
- **Failing closed on setup/tool errors** - Missing compare branches, invalid baselines, and tool execution failures are reported as violations
- **Generating reports** - Actionable Markdown reports for fixing violations

## Supported LLM Tools

Guardian provides harness configurations for:

- **Claude Code** - Via `.claude/settings.local.json` and `CLAUDE.md`
- **Codex CLI** - Via `~/.codex/policy/guardian.codexpolicy` and `AGENTS.md`
- **Cursor** - Via `.cursorrules` (uses allowList approach)
- **Gemini CLI** - Via `.gemini/policies/guardian.toml` and `GEMINI.md`
- **GitHub Copilot** - Via `.github/copilot-instructions.md` and `.vscode/settings.json` (VS Code terminal denyList/allowList)

Install all harnesses with:
```bash
guardian harness install --all
```

Check installation status:
```bash
guardian harness status
```

## Documentation

See [docs/reference/guardian-technical-spec.md](docs/reference/guardian-technical-spec.md) for full technical specification.
See [CONTRIBUTING.md](CONTRIBUTING.md) for development and contribution workflow.

## License

MIT License - see LICENSE file
