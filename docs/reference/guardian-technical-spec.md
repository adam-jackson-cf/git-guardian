# Guardian - AI Code Verification System

## Technical Specification v0.3.1

**Author**: AI Development Standards Working Group  
**Date**: 2025-12-08  
**Status**: Draft for Review

---

## 1. Purpose

Guardian prevents quality-gate bypass in AI-assisted development by making verification mandatory before AI-initiated push operations.

The system enforces one invariant:
- AI assistants must use `guardian push` for remote pushes.

Humans are not restricted from using native `git push`.

---

## 2. Scope

This specification defines:
- System architecture and trust boundaries
- Harness integration model for AI tools
- Verification pipeline behavior and result contracts
- Push gateway behavior
- Configuration and security requirements

This specification does not define:
- End-user installation/runbook steps
- Per-tool setup tutorials and command recipes
- Full source-level implementation listings
- Packaging/dependency manifests

---

## 3. Architecture Overview

Guardian has three layers:

1. Harness Layer  
AI tool policies and instruction files block or discourage direct `git push` and direct agents to `guardian push`.

2. Analysis Layer  
Deterministic tools evaluate changed code and produce normalized violations.

3. Gateway Layer  
`guardian push` executes verification and only calls `git push` when verification passes.

### 3.1 Design Principles

- Defense in depth: use hard command controls where available, instruction controls everywhere.
- Deterministic analysis only: no LLM scoring in pass/fail decisions.
- Single push gateway for AI: verification is not optional.
- Minimal custom logic: orchestration and normalization only; detection delegated to established tools.
- Human escape hatch: developers retain direct git control.

---

## 4. Harness Integration Specification

### 4.1 Required Behavior

For each supported assistant, Guardian configuration MUST:
- Deny or require approval for `git push` variants.
- Permit `guardian push`.
- Provide instruction text stating push restrictions and remediation flow.

### 4.2 Canonical Instruction Contract

All harness instruction files MUST communicate:
- Never run `git push` directly.
- Use `guardian push [remote] [branch]`.
- On verification failure: read report, fix violations, commit, retry.

### 4.3 Capability Model

Harnesses are classified as:
- Hard enforcement: runtime command policy can deny push.
- Soft enforcement: instruction-only or bypassable controls.

Guardian MUST treat harness controls as advisory defense and rely on gateway verification for correctness.

### 4.4 Supported Assistants

The specification supports these harness families:
- Claude Code
- Codex CLI
- Cursor
- Gemini CLI
- Windsurf
- GitHub Copilot (CLI/IDE agent modes)

Tool-specific templates and policy snippets are implementation artifacts and are defined in repository templates, not in this specification.

---

## 5. Verification Pipeline Specification

### 5.1 Inputs

- Repository working tree and git metadata
- Changed files relative to configured compare branch
- Guardian configuration
- Optional baseline hash file for drift checks

### 5.2 Outputs

- `violations: list[Violation]`
- Structured report artifact (Markdown)
- Exit status suitable for CLI gating

### 5.3 Violation Contract

Each violation MUST include:
- `file: str`
- `line: int`
- `column: int`
- `rule: str`
- `message: str`
- `severity: error|warning`
- `suggestion: str | None`

### 5.4 Pipeline Stages

1. Determine changed files from compare branch.
2. Partition files by language/tool applicability.
3. Execute configured analyzers.
4. Normalize analyzer output to `Violation` records.
5. Run config drift detection against protected files.
6. Aggregate and return all violations.

### 5.5 Analyzer Requirements

Guardian orchestrates deterministic tools:
- ESLint (+ TypeScript and eslint-comments rules) for JS/TS suppression and rule bypass patterns
- Ruff for Python suppression and quality bypass patterns
- Semgrep custom rules for cross-language anti-patterns and test skipping
- diff-cover for changed-line coverage threshold enforcement

### 5.6 Config Drift Detection

Guardian MUST support protected-file drift checks using baseline hashes.

Minimum protected set:
- TypeScript and ESLint config surfaces
- Python lint/type-check config surfaces
- Guardian config surfaces

A protected file hash delta MUST emit at least a warning violation.

---

## 6. Push Gateway Specification

### 6.1 Command Contract

`guardian push [remote] [branch]` MUST:
1. Resolve target branch if omitted.
2. Execute verification pipeline.
3. On violations, block push and generate report path output.
4. On no violations, execute native `git push` with requested flags.

### 6.2 Exit Semantics

- `0`: verification passed and push succeeded, or dry-run passed.
- Non-zero: verification failed or push execution failed.

### 6.3 Non-Bypass Requirement

No Guardian CLI path may provide a verification-skip mode for AI push workflows.

---

## 7. Reporting Specification

### 7.1 Report Requirements

Verification failure MUST produce a Markdown report containing:
- Generation timestamp
- Summary counts by severity
- Enumerated violations with file location and rule
- Remediation-oriented next steps

### 7.2 Report Retention

Guardian MUST maintain a latest-report pointer and bounded historical retention per configuration.

---

## 8. Configuration Specification

### 8.1 Core Configuration Domains

Guardian configuration MUST include:
- Analysis scope (languages, compare branch)
- Coverage threshold
- Tool command paths
- Report format/retention
- Enabled harness set

### 8.2 Defaults

Default compare branch is `origin/main` unless overridden.

### 8.3 Determinism Requirement

For the same repository state, configuration, and tool versions, Guardian SHOULD produce stable violation sets.

---

## 9. Security Model

### 9.1 Trust Boundaries

- Assistant process is untrusted for policy compliance.
- Deterministic analyzers are trusted for findings generation.
- Guardian push gateway is trusted for pass/fail enforcement.
- Human developer remains final authority for direct pushes.

### 9.2 Threats Addressed

- Direct AI push bypass
- Lint/test suppression patterns
- Stubbed or placeholder implementations submitted as complete work
- Drift toward permissive analysis configuration

### 9.3 Out-of-Scope Threats

- Malicious human actor with direct repository access
- Remote CI enforcement design
- Non-deterministic semantic correctness guarantees

---

## 10. Implementation Mapping

Reference implementation modules:
- CLI entry and command routing: `src/guardian/cli/`
- Verification orchestration: `src/guardian/analysis/`
- Harness generation/installation: `src/guardian/harness/`
- Report generation: `src/guardian/report/`

Detailed templates, command examples, and operational instructions are intentionally maintained in code, harness templates, and project docs to avoid specification drift.

---

## 11. Future Evolution

Potential future extensions:
- Additional language analyzers (Go, Rust, Kotlin, C#)
- Centralized policy/report backends
- IDE-native Guardian integrations

Any extension MUST preserve:
- deterministic pass/fail behavior
- single AI push gateway model
- no verification bypass path
