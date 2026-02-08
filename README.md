# Guardian - AI Code Verification System

Guardian is a verification system designed to detect and prevent quality gate bypasses in AI-assisted development workflows. It operates as a final validation layer that cannot be circumvented by AI code assistants, ensuring commits meet quality standards before being pushed to remote repositories.

## Prerequisites

- **Python 3.11+** - Guardian requires Python 3.11 or higher
- **Git** - Must be in a git repository to use Guardian
- **uv** (recommended) or **pip** - For installing from source

## Installation

### Option 0: Quick Install (curl)

The fastest way to install Guardian is using our installer script:

```bash
# Basic installation (interactive)
curl -fsSL "https://raw.githubusercontent.com/your-org/git-guardian/master/install.sh?$(date +%s)" | bash

# Easy mode (auto-install everything without prompts)
curl -fsSL "https://raw.githubusercontent.com/your-org/git-guardian/master/install.sh?$(date +%s)" | bash -s -- --easy-mode

# Dry run (preview what would be installed)
curl -fsSL "https://raw.githubusercontent.com/your-org/git-guardian/master/install.sh?$(date +%s)" | bash -s -- --dry-run
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

**Security Note:** For security, you can review the script before executing:

```bash
curl -fsSL "https://raw.githubusercontent.com/your-org/git-guardian/master/install.sh" -o install.sh
cat install.sh  # Review the script
bash install.sh
```

### Option 1: Install from Source (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/your-org/git-guardian.git
cd git-guardian

# Install using uv (recommended)
uv sync
uv pip install -e .

# Or install using pip
pip install -e .
```

### Option 2: Install via pipx (When Published)

Once Guardian is published to PyPI, you can install it globally:

```bash
pipx install git-guardian
```

> **Note**: Guardian is not yet published to PyPI. Use Option 0 or Option 1 for now.

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

See [guardian-technical-specification-v0.3.1.md](guardian-technical-specification-v0.3.1.md) for full technical specification.

## Development

To contribute to Guardian:

```bash
# Clone and navigate to repository
git clone https://github.com/your-org/git-guardian.git
cd git-guardian

# Install development dependencies
uv sync --dev

# Run quality gates
uv run ruff check .
uv run mypy src/ --ignore-missing-imports
uv run pytest

# Run Guardian on itself
uv run guardian verify
```

## License

MIT License - see LICENSE file
