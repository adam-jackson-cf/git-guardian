# AGENTS.md

Project: Guardian (git-guardian)

Guardian is an AI code verification system designed to detect and prevent quality gate bypasses in AI-assisted development workflows. It operates as a final validation layer that cannot be circumvented by AI code assistants, ensuring commits meet quality standards before being pushed to remote repositories.

## Features

- Gated Push System - Blocks direct git push from LLM tools, requiring guardian push for verified pushes
- Multi-Tool Harness Support - Configurations for Claude Code, Codex CLI, Cursor, Gemini CLI, GitHub Copilot
- Tool Orchestration - Integrates ESLint, Ruff, Semgrep, and diff-cover for deterministic analysis
- Actionable Reports - Generates Markdown reports for AI assistants to remediate violations
- Config Drift Detection - Monitors protected configuration files for unauthorized changes
- Human Escape Hatch - Developers retain unrestricted git push access

## Tech Stack

- Language: Python 3.11+
- CLI Framework: Typer with Rich for console output
- Templating: Jinja2 for harness configuration generation
- Git Integration: GitPython
- Package Manager: uv
- Build System: Hatchling
- Linter: Ruff
- Type Checker: mypy (strict mode)
- Testing: pytest with pytest-cov

## Structure

```
git-guardian/
├── src/guardian/              # Main package
│   ├── cli/                   # CLI commands (Typer app)
│   ├── analysis/              # Verification pipeline and tool runners
│   ├── harness/               # LLM harness installer
│   │   └── templates/         # Jinja2 templates for each LLM tool
│   └── report/                # Markdown report generation
├── tests/                     # pytest test suite
├── .guardian/                 # Guardian config (created by init)
├── install.sh                 # Curl-installable installer script
├── pyproject.toml             # Project configuration
└── docs/reference/guardian-technical-spec.md  # Full technical spec
```

### Key Files

- src/guardian/cli/main.py - CLI entry point, registers all subcommands
- src/guardian/analysis/pipeline.py - Verification orchestration
- src/guardian/harness/installer.py - LLM tool configuration installer
- src/guardian/report/generator.py - Markdown report generation

### Entry Points

- guardian = "guardian.cli.main:app" - Main CLI command

## Architecture

Guardian uses a layered security model:

1. Harness Layer: Configures LLM tools to deny git push via sandbox rules (where supported) and instruction files
2. Analysis Layer: Orchestrates deterministic tools (ESLint, Ruff, Semgrep, diff-cover) for code verification
3. Gateway Layer: guardian push is the only push path available to LLMs with mandatory verification

### Key Components

- CLI Commands: init, push, verify, scan, harness, report, config, baseline
- Analysis Pipeline: Aggregates results from ESLint (TS/JS), Ruff (Python), Semgrep (custom patterns), diff-cover (coverage)
- Harness Installer: Generates and installs configurations for 5 LLM tools
- Report Generator: Creates timestamped Markdown reports with violation details

## Backend Patterns and Practices

- Typer for CLI: Use Typer's app composition pattern with add_typer() for subcommands
- Dataclasses for Data: Use Violation dataclass for structured violation data
- Subprocess for Tools: Shell out to external linting tools, parse JSON/SARIF output
- Jinja2 Templates: All harness configurations use .j2 templates
- Path-based Operations: Use pathlib.Path consistently
- Type Annotations: Strict mypy compliance required

## Build & Quality Gate Commands

- Install: `uv sync` - Install dependencies
- Editable Install: `uv pip install -e .` - Install package in dev mode
- Lint: `uv run ruff check .` - Run Ruff linter
- Type Check: `uv run mypy src/ --ignore-missing-imports` - Type checking
- Test: `uv run pytest` - Run test suite
- Run CLI: `uv run guardian --help` - Execute Guardian commands
- Verify: `guardian verify` - Run verification pipeline

## Testing

Framework: pytest with pytest-cov

### Running Tests

```bash
uv run pytest
uv run pytest --cov=src  # With coverage
```

### Test Files

- tests/conftest.py - Fixtures (temp_dir)
- tests/test_analysis.py - Analysis pipeline tests
- tests/test_config_drift.py - Config drift detection tests
- tests/test_report.py - Report generation tests
- tests/test_smoke.py - CLI smoke tests

### Creating New Tests

Tests go in tests/ directory with test_*.py naming. Use the temp_dir fixture for file system tests:

```python
def test_example(temp_dir):
    """Example test with temporary directory."""
    test_file = temp_dir / "test.py"
    test_file.write_text("print('hello')")
    assert test_file.exists()
```

## Git Push Command Restrictions

NEVER execute these commands:
- git push (any variant)
- git push --force
- git push --no-verify

ALWAYS use guardian push for pushing code remote:
- guardian push [remote] [branch]

## On Push Failure

When guardian push fails:
1. Note the report path in the output
2. Read the report file
3. Address each violation
4. Retry guardian push once you have committed local changes
