# ExecPlan: Complete Guardian to fail-closed verified push with integration smoke coverage

- Status: Completed
- Start: 2026-02-08 - Last Updated: 2026-02-08T15:10:00Z
- Artifact root: `.enaible/artifacts/create-execplan/20260208T141132Z/`
- Context Pack: `.enaible/artifacts/create-execplan/20260208T141132Z/context-pack.md`
- Links: README.md, guardian-technical-specification-v0.3.1.md, .enaible/artifacts/create-execplan/20260208T141132Z/context-discovery.md

## Executor Contract

- Allowed inputs: working tree + Context Pack + ExecPlan
- Required output: implemented change + updated ExecPlan + verification evidence
- Forbidden: undefined discovery tasks after requirements are frozen

## Requirements Freeze

- Requirement 1: Completion plan and implementation path are based on current code status and known defects.
- Requirement 2: Include an online-research-backed decision stage validating current stack soundness.
- Requirement 3: Remove fail-open contradictions and command UX inconsistencies that weaken gate integrity.
- Requirement 4: Add working integration smoke tests for end-to-end CLI behavior.
- Requirement 5: Ship with deterministic quality gate commands and clear completion proof.
- Confirmed by user at: 2026-02-08T14:09:00Z

## Purpose / Big Picture

Guardian must enforce quality verification as a hard gate for AI-assisted pushes. Current behavior has strong structure but still allows ambiguous and fail-open outcomes. This plan closes those gaps with targeted edits, validates stack choices against current official sources, and adds integration smoke tests that prove the gateway behavior in realistic repository conditions.

## Success Criteria (how to prove done)

- [x] `uv run guardian --help` shows direct command UX aligned with README examples; no nested `verify verify` pattern required.
- [x] `uv run pytest tests/test_integration_smoke.py -q` passes and covers compare-branch-missing, tool-failure, and happy-path flows.
- [x] `uv run pytest` passes all tests.
- [x] `uv run ruff check .` passes.
- [x] `uv run mypy src/ --ignore-missing-imports` passes.
- [x] `uv run guardian verify --json` fails deterministically when prerequisites fail and passes on healthy setup in integration tests.
- Non-Goals: add new language analyzers, add remote verification service, introduce auto-fix mode, ship IDE extension work.

## Constraints & Guardrails

- No fallback behavior and no silent failure suppression in verification-critical paths.
- No bypass of quality gates, no skipping tests, no suppression of failing checks.
- Keep changes minimal and brownfield-safe, anchored to existing modules.
- Maintain deterministic outputs for CLI, report generation, and test assertions.
- Follow repository command/toolchain conventions using `uv`.

## Plan Overview (phases)

- Phase 1: Research validation and implementation decision freeze. Proof: evidence updated with official recency signals and decisions recorded.
- Phase 2: Fail-closed verification hardening and CLI UX alignment. Proof: targeted CLI and pipeline tests pass.
- Phase 3: Config/baseline enforcement and documentation alignment. Proof: baseline behavior deterministic and docs match runtime.
- Phase 4: Integration smoke test implementation. Proof: new smoke suite passes and reproduces gate-critical scenarios.
- Phase 5: Final quality gates and release readiness pass. Proof: lint, type, tests, and CLI verification checks all green.

## Task Table (single source of truth)

Status keys:

- `@` = in progress
- `X` = complete
- (blank) = outstanding

Task Types:

- Code, Read, Action, Test, Gate, Human

Write each row as an explicit action. Every task must include one or more:

- file anchors: `path/to/file:line`
- commands to run
- expected outputs
- no task may rely on implicit discovery

| Status | Phase # | Task # | Type | Description |
| ------ | ------- | ------ | ---- | ----------- |
| X | 1 | 1 | Read | Review `.enaible/artifacts/create-execplan/20260208T141132Z/context-pack.md` and confirm risks/constraints before coding. Expected output: decision log entry D1. |
| X | 1 | 2 | Action | Validate external recency references in `.enaible/artifacts/create-execplan/20260208T141132Z/context-evidence.json` for E9-E17 and update decision notes on retain/replace choices. Expected output: updated evidence JSON with no stale claims. |
| X | 1 | 3 | Action | Run baseline commands `uv sync --extra dev`, `uv run guardian --help`, `uv run pytest -q` and attach outputs to Artifacts & Notes. Expected output: baseline snapshot recorded. |
| X | 2 | 4 | Code | Edit `src/guardian/cli/main.py:16` and command modules (`src/guardian/cli/verify.py:13`, `src/guardian/cli/push.py:16`, `src/guardian/cli/scan.py:13`, `src/guardian/cli/report.py:12`) so documented direct invocations are first-class. Expected output: `guardian verify` and `guardian push` work directly. |
| X | 2 | 5 | Test | Add CLI regression tests in `tests/test_cli_commands.py:1` covering help text and direct invocation paths. Command: `uv run pytest tests/test_cli_commands.py -q`. Expected output: pass. |
| X | 2 | 6 | Code | Refactor changed-file discovery in `src/guardian/analysis/git_utils.py:7` to return explicit failure state when compare branch is missing or git diff fails. Expected output: no silent empty-list success path. |
| X | 2 | 7 | Code | Update `src/guardian/analysis/pipeline.py:14` to consume explicit discovery status and emit deterministic violations for setup errors. Expected output: fail-closed behavior for branch/precondition failures. |
| X | 2 | 8 | Code | Update runners `src/guardian/analysis/eslint.py:10`, `src/guardian/analysis/ruff.py:10`, `src/guardian/analysis/semgrep.py:10` so subprocess/parse failures emit tool-execution violations instead of silent pass. Expected output: predictable error reporting for broken tool state. |
| X | 2 | 9 | Test | Add focused tests in `tests/test_analysis_pipeline.py:1` for compare-branch missing and tool-runner failure propagation. Command: `uv run pytest tests/test_analysis_pipeline.py -q`. Expected output: pass. |
| X | 3 | 10 | Code | Harden config drift baseline flow in `src/guardian/analysis/config_drift.py:17`, `src/guardian/cli/init.py:72`, and `src/guardian/cli/baseline.py:16` so baseline requirements are explicit and non-bypassable. Expected output: deterministic behavior when baseline is absent. |
| X | 3 | 11 | Code | Remove unused dependency surface in `pyproject.toml:6` if still unused after code pass (for example GitPython) and update lockfile via `uv sync`. Expected output: dependency graph matches actual runtime use. |
| X | 3 | 12 | Code | Update `README.md:74` quick-start and verification semantics to match final CLI behavior and fail-closed outcomes. Expected output: docs and runtime aligned. |
| X | 4 | 13 | Code | Create `tests/test_integration_smoke.py:1` with temp-repo fixtures and deterministic fake tool executables to simulate ESLint/Ruff/Semgrep/diff-cover outputs. Expected output: hermetic integration harness in tests. |
| X | 4 | 14 | Test | Implement smoke case: compare branch missing leads to failure and actionable message. Command: `uv run pytest tests/test_integration_smoke.py -k compare_branch_missing -q`. Expected output: pass. |
| X | 4 | 15 | Test | Implement smoke case: tool execution/parsing failure leads to failure violation, not pass. Command: `uv run pytest tests/test_integration_smoke.py -k tool_failure -q`. Expected output: pass. |
| X | 4 | 16 | Test | Implement smoke case: healthy path returns passed verification and expected JSON contract. Command: `uv run pytest tests/test_integration_smoke.py -k happy_path -q`. Expected output: pass. |
| X | 4 | 17 | Test | Run full integration smoke suite. Command: `uv run pytest tests/test_integration_smoke.py -q`. Expected output: all smoke scenarios pass. |
| X | 5 | 18 | Gate | Run complete test gate `uv run pytest` and record output artifact path. Expected output: all tests pass. |
| X | 5 | 19 | Gate | Run lint/type gates `uv run ruff check .` and `uv run mypy src/ --ignore-missing-imports`. Expected output: both pass. |
| X | 5 | 20 | Gate | Run final runtime checks `uv run guardian --help`, `uv run guardian verify --json`, and `uv run guardian scan --json` in controlled fixture repo. Expected output: direct CLI UX and deterministic pass/fail semantics confirmed. |

## Progress Log (running)

- (2026-02-08T14:12Z) Scaffolded execplan artifact set, captured repo state, captured external recency evidence, and authored deterministic completion plan.
- (2026-02-08T14:30Z) Implemented fail-closed pipeline behavior and direct CLI invocation paths; added CLI and pipeline regression tests.
- (2026-02-08T14:50Z) Hardened config baseline semantics, initialized baseline hashes during `guardian init`, and removed unused GitPython dependency.
- (2026-02-08T15:00Z) Added hermetic integration smoke tests covering compare-branch-missing, tool-failure, and happy-path verification.
- (2026-02-08T15:05Z) Completed full quality gates (`pytest`, `ruff`, `mypy`) and runtime checks for `guardian --help`, `guardian verify --json`, and `guardian scan --json`.

## Decision Log

- Decision: Use brownfield minimal-change path.
  - Rationale: Core structure already exists and required outcome is hardening, not rewrite.
  - Date: 2026-02-08
- Decision: Keep Typer/Ruff/Semgrep/pytest/mypy/uv stack with recency validation.
  - Rationale: Official sources show active releases and direct fit with current architecture.
  - Date: 2026-02-08
- Decision: Treat compare-branch and tool-runner failures as explicit violations.
  - Rationale: Objective requires fail-closed gate behavior.
  - Date: 2026-02-08

## Execution Findings

- Finding: Current command exposure uses nested subcommands for verify/push/scan/report.
- Evidence: `.enaible/artifacts/create-execplan/20260208T141132Z/context-evidence.json` E18
- Decision link: Decision 3
- User approval (required if this introduces new discovery scope): covered by requirements freeze in this turn

## Test Plan

- Commands:
  - `uv run pytest tests/test_cli_commands.py -q`
  - `uv run pytest tests/test_analysis_pipeline.py -q`
  - `uv run pytest tests/test_integration_smoke.py -q`
  - `uv run pytest`
- Expected:
  - CLI behavior is direct and documented.
  - Verification fails closed for missing compare branch and tool failures.
  - Verification passes on healthy scenarios with deterministic output.
  - Full suite passes with no regressions.

## Quality Gates

| Gate | Command | Expectation |
| ---- | ------- | ----------- |
| Lint | `uv run ruff check .` | 0 errors |
| Type | `uv run mypy src/ --ignore-missing-imports` | 0 type errors |
| Test | `uv run pytest` | full suite passes including new integration smoke tests |
| Runtime UX | `uv run guardian --help` | direct command UX matches docs |

## Idempotence & Recovery

Most tasks are idempotent: repeated test/lint/type commands should remain stable. CLI and pipeline edits are reversible with standard git commit rollback strategy. For risky semantic changes, execute in small commits per phase and re-run targeted tests before proceeding to next phase.

## Artifacts & Notes

- Context Pack: `.enaible/artifacts/create-execplan/20260208T141132Z/context-pack.md`
- Evidence: `.enaible/artifacts/create-execplan/20260208T141132Z/context-evidence.json`
- Draft review: `.enaible/artifacts/create-execplan/20260208T141132Z/draft-review.md`
- Baseline snapshot:
  - `uv sync --extra dev` -> dependency environment resolved
  - `uv run guardian --help` -> direct command surface for `verify|push|scan|report`
  - `uv run pytest -q` -> passing baseline before implementation
- Completion gates:
  - `uv run pytest` -> `15 passed`
  - `uv run ruff check .` -> `All checks passed!`
  - `uv run mypy src/ --ignore-missing-imports` -> `Success: no issues found in 25 source files`
  - Controlled fixture runtime checks for `guardian verify --json` and `guardian scan --json` -> deterministic pass output

## Outcomes & Retrospective (on completion)

- What shipped:
- Fail-closed git discovery and tool-runner behavior in verification pipeline.
- Direct top-level CLI invocation for verify/push/scan/report.
- Baseline enforcement hardening with explicit missing/invalid/incomplete baseline violations.
- Hermetic integration smoke suite for critical CLI verification paths.
- Dependency cleanup by removing unused `GitPython`.
- What went well:
- Existing architecture allowed minimal, targeted edits without broad refactors.
- Typer CLI and subprocess-based runners were straightforward to harden with deterministic violations.
- Integration smoke tests provided reliable end-to-end coverage without external tool dependencies.
- What to improve next time:
- Expand integration smoke coverage to include diff-cover failure modes and config drift mutation flows.
- Add artifact capture automation for baseline/quality-gate outputs to reduce manual status updates.
