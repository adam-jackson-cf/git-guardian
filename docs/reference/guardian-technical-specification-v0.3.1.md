# Guardian - AI Code Verification System

## Technical Specification v0.3.1

**Author**: AI Development Standards Working Group
**Date**: 2025-12-08
**Status**: Draft for Review

---

## Executive Summary

Guardian is a verification system designed to detect and prevent quality gate bypasses in AI-assisted development workflows. It operates as a final validation layer that cannot be circumvented by the AI code assistant, ensuring that commits meet quality standards before being pushed to remote repositories.

### Problem Statement

AI code assistants (Claude Code, Codex, Cursor, Copilot, Gemini, Windsurf) can inadvertently or deliberately bypass quality gates through:
- Adding inline disable comments (`@ts-ignore`, `eslint-disable`, `# noqa`)
- Using `--no-verify` flags on git commands
- Stubbing implementations with `NotImplementedError` or `TODO`
- Skipping tests with `skip()` or `pytest.mark.skip`
- Modifying linter/type checker configurations to be more permissive
- Directly calling `git push` to bypass verification

### Solution

A gated push system that:
1. **Configures sandbox deny rules** where supported (Claude Code `permissions.deny`)
2. **Provides instruction files** for all LLM tools denying `git push`
3. **Provides `guardian push`** as the only LLM-accessible push mechanism
4. **Orchestrates existing deterministic tools** (ESLint, Ruff, Semgrep, diff-cover)
5. **Generates actionable reports** for AI assistants to remediate failures
6. **Allows humans to push directly** via standard `git push` (not restricted)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        LLM TOOL HARNESSES                               │
│                                                                         │
│  ┌─────────────────────┐  ┌─────────────────────┐                      │
│  │    Claude Code      │  │   Other Tools       │                      │
│  │  ┌───────────────┐  │  │  ┌───────────────┐  │                      │
│  │  │ settings.json │  │  │  │ AGENTS.md     │  │  ← Soft instructions │
│  │  │ permissions:  │  │  │  │ .cursorrules  │  │    (best effort)     │
│  │  │   deny: [     │  │  │  │ GEMINI.md     │  │                      │
│  │  │     git push  │  │  │  │ .windsurf/    │  │                      │
│  │  │   ]           │  │  │  └───────────────┘  │                      │
│  │  └───────────────┘  │  └─────────────────────┘                      │
│  │  ┌───────────────┐  │                                               │
│  │  │ CLAUDE.md     │  │  ← Soft instructions (backup)                 │
│  │  └───────────────┘  │                                               │
│  └─────────────────────┘                                               │
│                                                                         │
│                    ┌────────────────────────────┐                       │
│                    │   DENY: git push           │                       │
│                    │   ALLOW: guardian push     │                       │
│                    └─────────────┬──────────────┘                       │
└──────────────────────────────────┼──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           GUARDIAN SYSTEM                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐                                                  │
│  │  guardian push   │ ◀── LLM's only path to push                      │
│  └────────┬─────────┘                                                  │
│           │                                                             │
│           ▼                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    TOOL ORCHESTRATION LAYER                       │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │  │
│  │  │ ESLint     │  │ Ruff       │  │ Semgrep    │  │ diff-cover │  │  │
│  │  │ typescript │  │ Python     │  │ Custom     │  │ Coverage   │  │  │
│  │  │ -eslint    │  │ linting    │  │ patterns   │  │ delta      │  │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│           │                                                             │
│           ▼                                                             │
│  ┌──────────────────┐    ┌──────────────────┐                          │
│  │  Result Aggregator│───▶│  Report Generator │                        │
│  │  (SARIF/JSON)    │    │  (Markdown)       │                         │
│  └────────┬─────────┘    └──────────────────┘                          │
│           │                                                             │
│           ▼                                                             │
│  ┌──────────────────┐                                                  │
│  │  Pass?           │                                                  │
│  │  ├─ YES ──▶ Execute `git push`                                     │
│  │  └─ NO  ──▶ Block push, return report path                         │
│  └──────────────────┘                                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

HUMAN WORKFLOW (unrestricted):
┌─────────────────────────────────────────────────────────────────────────┐
│  Developer Terminal                                                     │
│  └── git push  ✓  (humans are not restricted)                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Defense in Depth**: Where sandbox enforcement is available (Claude Code), use it. Always supplement with instruction files as backup.

2. **Tool Orchestration over Custom Code**: Use established linting tools (ESLint, Ruff, Semgrep) rather than implementing custom pattern detection.

3. **Single Gateway**: `guardian push` is the only push path available to LLMs. Verification is mandatory.

4. **Human Escape Hatch**: Developers retain full `git push` access. Guardian trusts humans; it verifies AI.

---

## LLM Harness Integration

Guardian's security model uses a layered approach: **sandbox enforcement** where available, plus **instruction files** for all tools.

### Harness Capability Matrix

| Tool | Enforcement Mechanism | Instruction File | Enforcement Level |
|------|----------------------|------------------|-------------------|
| Claude Code | `permissions.deny` in settings.json | CLAUDE.md | ⚠️ Buggy but functional |
| Codex CLI | `.codexpolicy` files with `forbidden` decision | AGENTS.md | ✅ Hard enforcement |
| Cursor | ~~denyList~~ **DEPRECATED v1.3** - use allowList only | .cursorrules | ❌ Bypassable - soft only |
| Copilot CLI | `--deny-tool 'shell(git push)'` flags | .github/copilot-instructions.md | ✅ Hard enforcement |
| VS Code Copilot | `github.copilot.chat.agent.terminal.denyList` | .github/copilot-instructions.md | ⚠️ Prefix matching only |
| Gemini CLI | TOML policy engine with `[[rule]]` blocks | GEMINI.md | ✅ Hard enforcement |
| Windsurf | `windsurf.cascadeCommandsDenyList` setting | .windsurf/rules/*.md | ⚠️ Soft enforcement |

**Enforcement Level Key:**
- ✅ **Hard enforcement**: Commands are blocked at runtime
- ⚠️ **Buggy/Soft**: May work but has known issues or bypass vectors
- ❌ **Deprecated/None**: Cannot rely on this mechanism

### Standardized Instruction Content

All instruction files use this identical content block:

```markdown
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
```

### Claude Code Configuration

**Primary enforcement via `.claude/settings.local.json`:**

```json
{
  "permissions": {
    "deny": [
      "Bash(git push)",
      "Bash(git push *)",
      "Bash(git push:*)",
      "Bash(/usr/bin/git push:*)",
      "Bash(command git push:*)"
    ]
  }
}
```

**Backup via `CLAUDE.md`:**

```markdown
# CLAUDE.md

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

## Guardian Commands

- `guardian push [remote] [branch]` - Verify and push (REQUIRED)
- `guardian verify` - Run verification without pushing
- `guardian scan` - Full codebase audit
- `guardian report` - View latest report
```

### Codex CLI Configuration

**Primary enforcement via `~/.codex/policy/guardian.codexpolicy`:**

```toml
# Guardian policy - blocks git push commands
[[rule]]
pattern = ["git", "push"]
decision = "forbidden"
match = ["git push", "git push origin main", "git push --force"]

[[rule]]
pattern = ["git", "push", "--no-verify"]
decision = "forbidden"

[[rule]]
pattern = ["git", "push", "--force"]
decision = "forbidden"
```

**Test policy before deploying:**
```bash
codex execpolicy check --policy ~/.codex/policy/guardian.codexpolicy "git push origin main"
# Expected: forbidden
```

**Backup via `AGENTS.md`:**

```markdown
# AGENTS.md

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
```

### Cursor Configuration

> ⚠️ **WARNING**: Cursor's denylist was **deprecated in v1.3** due to multiple bypass vectors (base64 encoding, subshells, Bash quoting tricks). The denylist cannot provide reliable protection.

**Recommended approach - Use allowList (whitelist) instead:**

In VS Code settings (`settings.json`):
```json
{
  "cursor.agent.terminal.allowList": {
    "guardian push": true,
    "git add": true,
    "git commit": true,
    "git status": true,
    "git diff": true,
    "npm test": true,
    "npm run": true
  }
}
```

This ensures only approved commands auto-execute. Any `git push` will require manual approval.

**Soft instructions via `.cursorrules`:**

```markdown
# .cursorrules

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
```

### Gemini CLI Configuration

**Primary enforcement via `.gemini/policies/guardian.toml`:**

> Note: Policy engine requires `tools.enableMessageBusIntegration = true` in settings.json

```toml
# Guardian policy - blocks git push commands

[[rule]]
toolName = "run_shell_command"
commandPrefix = "git push"
decision = "deny"
priority = 500

[[rule]]
toolName = "run_shell_command"
commandRegex = "git\\s+push"
decision = "deny"
priority = 500

# Allow guardian push
[[rule]]
toolName = "run_shell_command"
commandPrefix = "guardian push"
decision = "allow"
priority = 600
```

**Enable policy engine in `~/.gemini/settings.json`:**
```json
{
  "tools": {
    "enableMessageBusIntegration": true
  }
}
```

**Backup via `GEMINI.md`:**

```markdown
# GEMINI.md

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
```

### Windsurf Configuration

**Settings enforcement via VS Code settings (`settings.json`):**

```json
{
  "windsurf.cascadeCommandsDenyList": [
    "git push",
    "git push --force",
    "git push --no-verify"
  ],
  "windsurf.cascadeCommandsAllowList": [
    "guardian push",
    "git add",
    "git commit",
    "git status"
  ]
}
```

> Note: In **Turbo mode**, commands not in denyList auto-execute. In **Auto mode**, Cascade decides based on AI judgment.

**Soft instructions via `.windsurf/rules/guardian.md`:**

```markdown
---
trigger: always_on
---

# Guardian Push Rules

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
```

### GitHub Copilot Configuration

**Copilot CLI enforcement via command flags:**

```bash
# Launch Copilot CLI with git push denied
copilot --deny-tool 'shell(git push)' --deny-tool 'shell(git push --force)'

# Or allow all tools except specific ones
copilot --allow-all-tools --deny-tool 'shell(git push)'
```

**VS Code extension enforcement via settings (`settings.json`):**

```json
{
  "github.copilot.chat.agent.terminal.denyList": {
    "git push": true,
    "git push --force": true,
    "git push --no-verify": true
  },
  "github.copilot.chat.agent.terminal.allowList": {
    "guardian push": true,
    "git add": true,
    "git commit": true,
    "git status": true
  }
}
```

> Note: If `github.copilot.chat.agent.terminal.autoApprove` is enabled, denyList is **ignored**. Avoid enabling auto-approve.

**Soft instructions via `.github/copilot-instructions.md`:**

```markdown
# Copilot Instructions

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
```

---

## Analysis Layer (Tool Orchestration)

Guardian orchestrates existing deterministic tools rather than implementing custom analysis. This provides battle-tested accuracy and maintainability.

### Tool Stack

| Check Category | Tool | Language | Output Format |
|----------------|------|----------|---------------|
| TS suppress comments | @typescript-eslint | TypeScript/JS | SARIF/JSON |
| ESLint disables | eslint-plugin-eslint-comments | TypeScript/JS | SARIF/JSON |
| Python suppressions | Ruff | Python | JSON |
| Custom patterns | Semgrep | Multi-language | SARIF/JSON |
| Coverage delta | diff-cover | Language-agnostic | JSON |
| Config drift | Custom (minimal) | YAML/JSON/TOML | JSON |

### TypeScript Analysis

**ESLint configuration for Guardian checks (`.guardian/eslint.config.js`):**

```javascript
import tseslint from '@typescript-eslint/eslint-plugin';
import tsparser from '@typescript-eslint/parser';
import eslintComments from '@eslint-community/eslint-plugin-eslint-comments';

export default [
  {
    files: ['**/*.ts', '**/*.tsx', '**/*.js', '**/*.jsx'],
    languageOptions: {
      parser: tsparser,
    },
    plugins: {
      '@typescript-eslint': tseslint,
      'eslint-comments': eslintComments,
    },
    rules: {
      // Ban all TypeScript suppress comments
      '@typescript-eslint/ban-ts-comment': ['error', {
        'ts-expect-error': true,
        'ts-ignore': true,
        'ts-nocheck': true,
        'ts-check': false,
        minimumDescriptionLength: 0,
      }],

      // Ban explicit 'any' type
      '@typescript-eslint/no-explicit-any': 'error',

      // Require specific rules in eslint-disable comments
      'eslint-comments/no-unlimited-disable': 'error',
      'eslint-comments/require-description': ['error', {
        ignore: [],
      }],

      // Detect .skip() and .only() in tests
      'no-restricted-syntax': ['error', {
        selector: 'CallExpression[callee.property.name=/^(skip|only)$/]',
        message: 'Skipped or focused tests are not allowed',
      }],
    },
  },
];
```

**Execution:**

```bash
npx eslint --config .guardian/eslint.config.js --format json src/
```

### Python Analysis

**Ruff configuration for Guardian checks (`.guardian/ruff.toml`):**

```toml
[lint]
select = [
    "RUF100",   # Unused noqa directive (detects noqa without effect)
    "PGH003",   # Use specific rule codes with type: ignore
    "PGH004",   # Use specific codes with noqa
    "ERA001",   # Found commented-out code
    "FIX001",   # Line contains FIXME
    "FIX002",   # Line contains TODO
    "FIX003",   # Line contains XXX
    "FIX004",   # Line contains HACK
    "T201",     # print found
    "T203",     # pprint found
]

# Report ALL issues, ignoring inline suppressions
# This is the key flag - shows violations despite # noqa
ignore-noqa = true
```

**Execution:**

```bash
ruff check --config .guardian/ruff.toml --output-format json src/
```

**Additional checks with flake8 (shows despite noqa):**

```bash
flake8 --disable-noqa --format json src/
```

### Semgrep Custom Rules

**Custom Semgrep rules for patterns not covered by ESLint/Ruff (`.guardian/semgrep-rules.yaml`):**

```yaml
rules:
  # TypeScript stub implementations
  - id: ts-throw-not-implemented
    patterns:
      - pattern: throw new Error("not implemented")
      - pattern: throw new Error("Not implemented")
      - pattern: throw new Error("TODO")
    message: "Stub implementation detected - throw Error('not implemented')"
    severity: ERROR
    languages: [typescript, javascript]

  - id: ts-throw-unimplemented
    pattern: throw new Error($MSG)
    metavariable-regex:
      metavariable: $MSG
      regex: '(?i).*(not\s+implemented|todo|fixme|stub).*'
    message: "Stub implementation with Error throw"
    severity: ERROR
    languages: [typescript, javascript]

  # Python stub implementations (outside abstract methods)
  - id: py-raise-not-implemented
    pattern: raise NotImplementedError(...)
    message: "NotImplementedError - ensure this is in an abstract method"
    severity: WARNING
    languages: [python]

  - id: py-pass-only-body
    pattern: |
      def $FUNC(...):
          pass
    message: "Function body is only 'pass' - potential stub"
    severity: WARNING
    languages: [python]

  - id: py-ellipsis-body
    pattern: |
      def $FUNC(...):
          ...
    message: "Function body is only '...' - potential stub"
    severity: WARNING
    languages: [python]

  # Test skips (both languages)
  - id: pytest-skip-decorator
    pattern: '@pytest.mark.skip(...)'
    message: "Skipped pytest test"
    severity: ERROR
    languages: [python]

  - id: pytest-skip-call
    pattern: pytest.skip(...)
    message: "Programmatic test skip"
    severity: ERROR
    languages: [python]

  - id: unittest-skip
    pattern: '@unittest.skip(...)'
    message: "Skipped unittest"
    severity: ERROR
    languages: [python]
```

**Execution:**

```bash
semgrep --config .guardian/semgrep-rules.yaml --json src/
```

### Coverage Analysis

**Using diff-cover for coverage delta:**

```bash
# Generate coverage report first (via pytest, vitest, etc.)
pytest --cov=src --cov-report=xml

# Check coverage on changed lines
diff-cover coverage.xml \
    --compare-branch origin/main \
    --fail-under 80 \
    --json-report .guardian/reports/coverage.json
```

### Config Drift Detection

**Minimal custom implementation for config monitoring:**

```python
"""Config drift detection - the only custom analysis in Guardian."""
import hashlib
import json
import tomllib
from pathlib import Path

PROTECTED_CONFIGS = {
    "tsconfig.json": ["compilerOptions.strict", "compilerOptions.noImplicitAny"],
    "pyproject.toml": ["tool.mypy", "tool.ruff.lint.select"],
    ".eslintrc.json": ["rules"],
    "eslint.config.js": None,  # Any change flagged
}

def check_config_drift(repo_root: Path, baseline_path: Path) -> list[dict]:
    """Compare current configs against baseline hashes."""
    violations = []

    baseline = json.loads(baseline_path.read_text()) if baseline_path.exists() else {}

    for config_file, protected_keys in PROTECTED_CONFIGS.items():
        config_path = repo_root / config_file
        if not config_path.exists():
            continue

        current_hash = hashlib.sha256(config_path.read_bytes()).hexdigest()

        if config_file in baseline and baseline[config_file] != current_hash:
            violations.append({
                "file": config_file,
                "message": f"Config file modified: {config_file}",
                "severity": "warning",
                "suggestion": "Review config changes - quality gates may be weakened"
            })

    return violations
```

---

## CLI Commands

### Primary Commands

```bash
# Initialize Guardian in a repository
guardian init

# Verify and push (LLM's required path)
guardian push [remote] [branch]
guardian push origin main
guardian push --force origin feature-branch
guardian push --dry-run  # Verify without pushing

# Run verification without pushing
guardian verify
guardian verify --json  # Output as JSON

# Full codebase audit (all files, not just changed)
guardian scan
guardian scan --json
```

### Harness Management

```bash
# Install harness configuration for specific tool
guardian harness install claude-code
guardian harness install codex
guardian harness install cursor
guardian harness install gemini
guardian harness install windsurf
guardian harness install copilot

# Install for all detected/specified tools
guardian harness install --all

# Check harness status
guardian harness status
```

### Utility Commands

```bash
# View latest report
guardian report
guardian report --path .guardian/reports/2025-12-08T10-45-00.md

# Show current configuration
guardian config show

# Generate baseline hashes for config drift detection
guardian baseline update
```

---

## Push Command Implementation

```python
"""guardian push implementation."""
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console

from guardian.analysis import run_verification
from guardian.report import generate_report

app = typer.Typer()
console = Console()


@app.command()
def push(
    remote: str = typer.Argument("origin", help="Git remote name"),
    branch: str = typer.Argument(None, help="Branch to push (default: current)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force push"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Verify without pushing"),
) -> None:
    """Verify code quality and push to remote."""

    # Get current branch if not specified
    if branch is None:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
        )
        branch = result.stdout.strip()

    console.print(f"[blue]Running Guardian verification...[/blue]")

    # Run verification
    violations = run_verification()

    if violations:
        # Generate report
        report_path = generate_report(violations)

        console.print(f"\n[red]❌ Verification failed with {len(violations)} violation(s)[/red]")
        console.print(f"\n[yellow]Report: {report_path}[/yellow]")
        console.print("\n[dim]Read the report, fix violations, commit changes, then retry.[/dim]")

        sys.exit(1)

    console.print("[green]✓ Verification passed[/green]")

    if dry_run:
        console.print("[dim]Dry run - skipping push[/dim]")
        sys.exit(0)

    # Execute git push
    push_cmd = ["git", "push"]
    if force:
        push_cmd.append("--force")
    push_cmd.extend([remote, branch])

    console.print(f"\n[blue]Pushing to {remote}/{branch}...[/blue]")

    result = subprocess.run(push_cmd)

    if result.returncode != 0:
        console.print("[red]❌ Git push failed[/red]")
        sys.exit(2)

    console.print(f"[green]✓ Successfully pushed to {remote}/{branch}[/green]")
```

---

## Verification Pipeline

```python
"""Verification pipeline - orchestrates external tools."""
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Violation:
    file: str
    line: int
    column: int
    rule: str
    message: str
    severity: str
    suggestion: str | None = None


def run_verification() -> list[Violation]:
    """Run all verification tools and aggregate results."""
    violations = []

    # 1. Get changed files
    changed_files = get_changed_files()

    if not changed_files:
        return []

    ts_files = [f for f in changed_files if f.endswith(('.ts', '.tsx', '.js', '.jsx'))]
    py_files = [f for f in changed_files if f.endswith('.py')]

    # 2. Run ESLint for TypeScript
    if ts_files:
        violations.extend(run_eslint(ts_files))

    # 3. Run Ruff for Python
    if py_files:
        violations.extend(run_ruff(py_files))

    # 4. Run Semgrep for custom patterns
    violations.extend(run_semgrep(changed_files))

    # 5. Check coverage delta (if coverage.xml exists)
    coverage_file = Path("coverage.xml")
    if coverage_file.exists():
        violations.extend(run_diff_cover(coverage_file))

    # 6. Check config drift
    violations.extend(check_config_drift())

    return violations


def get_changed_files() -> list[str]:
    """Get files changed since origin/main."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        capture_output=True,
        text=True,
    )
    return [f for f in result.stdout.strip().split('\n') if f]


def run_eslint(files: list[str]) -> list[Violation]:
    """Run ESLint with Guardian config."""
    result = subprocess.run(
        [
            "npx", "eslint",
            "--config", ".guardian/eslint.config.js",
            "--format", "json",
            *files,
        ],
        capture_output=True,
        text=True,
    )

    violations = []

    try:
        data = json.loads(result.stdout)
        for file_result in data:
            for msg in file_result.get("messages", []):
                violations.append(Violation(
                    file=file_result["filePath"],
                    line=msg.get("line", 0),
                    column=msg.get("column", 0),
                    rule=msg.get("ruleId", "unknown"),
                    message=msg.get("message", ""),
                    severity="error" if msg.get("severity") == 2 else "warning",
                ))
    except json.JSONDecodeError:
        pass

    return violations


def run_ruff(files: list[str]) -> list[Violation]:
    """Run Ruff with Guardian config."""
    result = subprocess.run(
        [
            "ruff", "check",
            "--config", ".guardian/ruff.toml",
            "--output-format", "json",
            *files,
        ],
        capture_output=True,
        text=True,
    )

    violations = []

    try:
        data = json.loads(result.stdout)
        for item in data:
            violations.append(Violation(
                file=item["filename"],
                line=item["location"]["row"],
                column=item["location"]["column"],
                rule=item["code"],
                message=item["message"],
                severity="error",
            ))
    except json.JSONDecodeError:
        pass

    return violations


def run_semgrep(files: list[str]) -> list[Violation]:
    """Run Semgrep with Guardian rules."""
    rules_file = Path(".guardian/semgrep-rules.yaml")
    if not rules_file.exists():
        return []

    result = subprocess.run(
        [
            "semgrep",
            "--config", str(rules_file),
            "--json",
            *files,
        ],
        capture_output=True,
        text=True,
    )

    violations = []

    try:
        data = json.loads(result.stdout)
        for item in data.get("results", []):
            violations.append(Violation(
                file=item["path"],
                line=item["start"]["line"],
                column=item["start"]["col"],
                rule=item["check_id"],
                message=item["extra"]["message"],
                severity=item["extra"]["severity"].lower(),
            ))
    except json.JSONDecodeError:
        pass

    return violations


def run_diff_cover(coverage_file: Path) -> list[Violation]:
    """Run diff-cover for coverage analysis."""
    result = subprocess.run(
        [
            "diff-cover", str(coverage_file),
            "--compare-branch", "origin/main",
            "--json-report", "/dev/stdout",
            "--fail-under", "80",
        ],
        capture_output=True,
        text=True,
    )

    violations = []

    if result.returncode != 0:
        try:
            data = json.loads(result.stdout)
            coverage = data.get("total_percent_covered", 0)
            violations.append(Violation(
                file="coverage",
                line=0,
                column=0,
                rule="coverage-delta",
                message=f"Coverage on changed lines is {coverage:.1f}%, below threshold of 80%",
                severity="error",
            ))
        except json.JSONDecodeError:
            pass

    return violations
```

---

## Report Generation

```python
"""Report generation - produces Markdown reports for LLMs."""
from datetime import datetime
from pathlib import Path

from guardian.analysis import Violation


def generate_report(violations: list[Violation]) -> Path:
    """Generate Markdown report from violations."""

    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    report_dir = Path(".guardian/reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    report_path = report_dir / f"{timestamp}.md"

    # Group by severity
    errors = [v for v in violations if v.severity == "error"]
    warnings = [v for v in violations if v.severity == "warning"]

    content = f"""# Guardian Verification Report

**Generated**: {datetime.now().isoformat()}
**Status**: ❌ FAILED

## Summary

| Check | Status | Count |
|-------|--------|-------|
| Errors | {'❌ Fail' if errors else '✅ Pass'} | {len(errors)} |
| Warnings | {'⚠️ Warn' if warnings else '✅ Pass'} | {len(warnings)} |
| **Total** | | **{len(violations)}** |

## Violations

"""

    for i, v in enumerate(violations, 1):
        icon = "❌" if v.severity == "error" else "⚠️"
        content += f"""### {i}. {icon} {v.file}:{v.line}

**Rule**: `{v.rule}`
**Message**: {v.message}

"""
        if v.suggestion:
            content += f"**Suggestion**: {v.suggestion}\n\n"

    content += """## Next Steps

1. Review each violation above
2. Fix the issues in your code
3. Commit the fixes: `git add . && git commit -m "fix: address guardian violations"`
4. Retry: `guardian push`

---

*If you believe a violation is a false positive, consult with a human developer.*
"""

    report_path.write_text(content)

    # Update symlink to latest
    latest_link = report_dir / "latest.md"
    if latest_link.exists():
        latest_link.unlink()
    latest_link.symlink_to(report_path.name)

    return report_path
```

---

## File Structure

```
project-root/
├── .guardian/
│   ├── config.yaml              # Guardian configuration
│   ├── baseline.json            # Config file hashes for drift detection
│   ├── eslint.config.js         # ESLint config for Guardian checks
│   ├── ruff.toml                # Ruff config for Guardian checks
│   ├── semgrep-rules.yaml       # Custom Semgrep patterns
│   └── reports/
│       ├── latest.md            # Symlink to most recent report
│       └── 2025-12-08T10-45-00.md
│
├── .claude/
│   └── settings.local.json      # Claude Code permissions (deny git push)
│
├── CLAUDE.md                    # Claude Code instructions
├── AGENTS.md                    # Codex instructions
├── .cursorrules                 # Cursor instructions
├── GEMINI.md                    # Gemini instructions
├── .windsurf/
│   └── rules/
│       └── guardian.md          # Windsurf instructions
└── .github/
    └── copilot-instructions.md  # Copilot instructions
```

---

## Configuration

**`.guardian/config.yaml`:**

```yaml
# Guardian Configuration

version: "0.3"

# Analysis settings
analysis:
  # Languages to check
  languages:
    - typescript
    - python

  # Coverage threshold for diff-cover
  coverage_threshold: 80

  # Compare branch for diff operations
  compare_branch: origin/main

# Tool paths (auto-detected if not specified)
tools:
  eslint: npx eslint
  ruff: ruff
  semgrep: semgrep
  diff_cover: diff-cover

# Report settings
reports:
  format: markdown
  keep_count: 10  # Number of reports to retain

# Harness configuration
harness:
  # Which tools are in use
  enabled:
    - claude-code
    - codex
    - cursor
```

---

## Package Structure

```
guardian/
├── pyproject.toml
├── src/
│   └── guardian/
│       ├── __init__.py
│       ├── __main__.py           # Entry point
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py           # Typer app
│       │   ├── push.py           # guardian push
│       │   ├── verify.py         # guardian verify
│       │   ├── scan.py           # guardian scan
│       │   ├── harness.py        # guardian harness
│       │   └── init.py           # guardian init
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── pipeline.py       # Orchestration
│       │   ├── eslint.py         # ESLint runner
│       │   ├── ruff.py           # Ruff runner
│       │   ├── semgrep.py        # Semgrep runner
│       │   ├── coverage.py       # diff-cover runner
│       │   └── config_drift.py   # Config monitoring
│       ├── harness/
│       │   ├── __init__.py
│       │   ├── installer.py      # Harness installation
│       │   └── templates/        # Jinja2 templates
│       │       ├── claude_settings.json.j2
│       │       ├── CLAUDE.md.j2
│       │       ├── codex_policy.codexpolicy.j2
│       │       ├── AGENTS.md.j2
│       │       ├── cursor_settings.json.j2
│       │       ├── cursorrules.j2
│       │       ├── gemini_policy.toml.j2
│       │       ├── gemini_settings.json.j2
│       │       ├── GEMINI.md.j2
│       │       ├── windsurf_settings.json.j2
│       │       ├── windsurf_guardian.md.j2
│       │       ├── copilot_settings.json.j2
│       │       └── copilot_instructions.md.j2
│       └── report/
│           ├── __init__.py
│           └── generator.py      # Markdown generation
└── tests/
    ├── conftest.py
    ├── test_cli/
    ├── test_analysis/
    └── test_harness/
```

---

## Dependencies

**`pyproject.toml`:**

```toml
[project]
name = "git-guardian"
version = "0.3.1"
description = "AI code verification system"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.9.0",
    "rich>=13.0.0",
    "pyyaml>=6.0",
    "jinja2>=3.1.0",
    "gitpython>=3.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]

[project.scripts]
guardian = "guardian.cli.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "C4", "SIM"]

[tool.mypy]
python_version = "3.11"
strict = true
```

---

## External Tool Requirements

Guardian requires these tools to be installed in the project:

**For TypeScript projects:**
```bash
npm install -D eslint @typescript-eslint/eslint-plugin @typescript-eslint/parser @eslint-community/eslint-plugin-eslint-comments
```

**For Python projects:**
```bash
pip install ruff diff-cover
# or with uv
uv add --dev ruff diff-cover
```

**For both (custom patterns):**
```bash
pip install semgrep
# or
brew install semgrep
```

---

## Installation

```bash
# Install Guardian
pipx install git-guardian

# Initialize in repository
cd your-project
guardian init

# Install harness configurations for your tools
guardian harness install --all
# or specific tools:
guardian harness install claude-code
guardian harness install codex

# Verify installation
guardian verify
```

---

## Security Model

### Why This Approach Works

1. **Multi-layer enforcement**: Most tools now have actual command blocking:
   - **Codex**: `forbidden` decision in `.codexpolicy` files
   - **Copilot CLI**: `--deny-tool 'shell(git push)'` flags
   - **Gemini**: TOML policy engine with `deny` decision
   - **Claude Code**: `permissions.deny` (buggy but functional)
   - **Windsurf/VS Code Copilot**: denyList settings

2. **Instruction files as backup**: Even if enforcement fails, instruction files make it clear to the LLM that `git push` is prohibited.

3. **Single gateway**: `guardian push` is the only documented push path. There's no `--skip-verification` flag.

4. **Deterministic tooling**: All verification is done by established tools (ESLint, Ruff, Semgrep) - no AI/LLM-based analysis that could be tricked.

5. **Version-controlled config**: Harness files are committed to git, so any changes are visible in PRs.

6. **Human escape hatch**: Developers can always use `git push` directly. We trust humans; we verify AI.

### Threat Model

| Threat | Mitigation |
|--------|------------|
| LLM runs `git push` | Hard block: Codex (forbidden), Copilot CLI (deny-tool), Gemini (policy deny). Soft block: Claude, Windsurf, Cursor (allowList) |
| LLM modifies harness files | Changes visible in git diff/PR review |
| LLM uses path bypass (`/usr/bin/git`) | Claude Code denies all variants; Codex/Gemini pattern matching catches it |
| LLM disables linting rules | Caught by Semgrep/config drift detection |
| LLM adds `# noqa` / `@ts-ignore` | Caught by Ruff/ESLint with ignore-noqa flags |
| LLM skips tests | Caught by Semgrep rules |
| LLM uses obfuscation (base64) | Cursor deprecated denylist for this reason; use allowList pattern |
| LLM uses subshells | Codex/Gemini pattern matching; allowList approach safer |

---

## Future Considerations

### Out of Scope

- **Remote verification server**: Could provide webhook-based verification for CI/CD
- **IDE extensions**: VS Code, JetBrains integration
- **Auto-fix capabilities**: Some tools support `--fix`, could be integrated
- **Custom tool plugins**: Allow users to add verification tools
- **MCP server**: Direct integration with Claude Code via MCP

### Additional Languages (Future)

- Go: `golangci-lint`
- Rust: `clippy`
- Kotlin: `detekt`
- C#: `dotnet-format`

---

## Appendix: Harness Research Summary

### Claude Code

**Settings file**: `.claude/settings.local.json` (project) or `~/.claude/settings.json` (global)

**Permission format**:
```json
{
  "permissions": {
    "deny": ["Bash(git push:*)"]
  }
}
```

**Known issues**:
- GitHub issues #6631, #6699 report deny rules not enforced in some versions
- Workaround: Use both permissions.deny AND CLAUDE.md instructions (defense in depth)

### Codex CLI

**Execpolicy system**: `~/.codex/policy/*.codexpolicy` files

**Policy format** (pattern-based with decisions):
```toml
[[rule]]
pattern = ["git", "push"]
decision = "forbidden"
match = ["git push origin main"]
```

**Decisions hierarchy**: `forbidden` > `prompt` > `allow` (strictest wins)

**Test command**:
```bash
codex execpolicy check --policy ~/.codex/policy/guardian.codexpolicy "git push"
```

**Documentation**: https://github.com/openai/codex/blob/main/codex-rs/execpolicy/README.md

### Cursor

**Denylist DEPRECATED in v1.3**: Removed due to multiple bypass vectors:
1. Base64 encoding bypasses
2. Subshell execution `$(git push)`
3. Shell script indirection
4. Bash quoting tricks `"g"it push` → infinite variations

**Recommendation**: Use allowList (whitelist) approach in settings instead. Commands not in allowList require manual approval.

**Setting**: `cursor.agent.terminal.allowList` in VS Code settings

### GitHub Copilot

**Copilot CLI** (`@github/copilot`):
- Hard enforcement via `--deny-tool 'shell(git push)'` flags
- Supports `--allow-tool` and `--deny-tool` with pattern matching
- Pattern syntax: `shell(command)`, `shell` (all), `write`, MCP server tools

**VS Code Extension**:
- Settings: `github.copilot.chat.agent.terminal.allowList` and `denyList`
- Prefix-based matching (not regex)
- ⚠️ `denyList` ignored if `autoApprove` is enabled

**Documentation**: https://docs.github.com/en/copilot/concepts/agents/about-copilot-cli

### Gemini CLI

**Policy engine**: TOML-based rules with priority system

**Location**: User policies in `~/.gemini/policies/`, project policies in `.gemini/policies/`

**Policy format**:
```toml
[[rule]]
toolName = "run_shell_command"
commandPrefix = "git push"
decision = "deny"
priority = 500
```

**Decisions**: `allow`, `deny`, `ask_user`

**Priority tiers**: Admin (3.x) > User (2.x) > Default (1.x)

**Enable policy engine**: Set `tools.enableMessageBusIntegration = true` in settings.json

**Documentation**: https://geminicli.com/docs/core/policy-engine/

### Windsurf

**Settings-based enforcement**:
- `windsurf.cascadeCommandsDenyList` - commands that always require approval
- `windsurf.cascadeCommandsAllowList` - commands that auto-execute

**Execution modes**:
- **Turbo mode**: Auto-execute unless in denyList
- **Auto mode**: AI decides based on context

**Soft rules**: `.windsurf/rules/*.md` with frontmatter `trigger: always_on`

**Documentation**: https://docs.windsurf.com/windsurf/terminal
