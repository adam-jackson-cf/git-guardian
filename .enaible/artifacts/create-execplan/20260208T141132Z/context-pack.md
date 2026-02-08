# Context Pack: Guardian Completion to Production-Ready Gate

- Created: 2026-02-08
- Repo root: `/Users/adamjackson/Projects/git-guardian`
- Target path: `.`
- Project mode: `brownfield`
- Related links: README.md, guardian-technical-specification-v0.3.1.md, .enaible/artifacts/create-execplan/20260208T141132Z/execplan.md

## Change Brief (1-3 paragraphs)

Guardian already ships a modular v0.3.1 CLI and verification pipeline, but current behavior still permits fail-open outcomes that conflict with its core claim of being a non-circumventable verification layer for AI-assisted workflows. The highest-risk contradictions are nested CLI command UX that differs from README usage, missing compare-branch behavior that returns success, and tool-runner failures that can silently pass.

This plan completes Guardian to an implementation-ready state by hardening fail-closed behavior, aligning command UX with documentation, adding deterministic smoke integration tests, and validating stack recency against official sources. The plan keeps scope minimal by changing only the modules directly responsible for gate integrity, command entry points, and proof of behavior.

The target outcome is a version that demonstrably blocks unsafe push paths when prerequisites are missing or tools fail, with reproducible verification evidence from unit tests plus integration smoke tests in temporary git repositories.

## Requirement Freeze (user-confirmed)

- R1: Deliver a full completion plan package grounded in current implementation state and known defects.
- R2: Include an online research stage that validates stack recency and soundness as of 2026-02-08.
- R3: Address contradictions that weaken non-bypassable verification, including fail-open and CLI UX mismatch.
- R4: Include implementation of a working smoke integration test that exercises end-to-end CLI behavior in a temporary git repo.
- R5: Define deterministic completion criteria with explicit verification commands.
- Confirmed by user at: 2026-02-08T14:09:00Z

## Discovery Inputs

- Intake artifact: `.enaible/artifacts/create-execplan/20260208T141132Z/context-discovery.md`
- Evidence artifact: `.enaible/artifacts/create-execplan/20260208T141132Z/context-evidence.json`
- Codemap artifact: `.enaible/artifacts/create-execplan/20260208T141132Z/context-codemap.md`
- Notes: Brownfield mode selected because objective is completion/hardening of existing behavior, not net-new standalone capability.

## Guardrails (must-follow)

- Quality gates: `uv run ruff check .`, `uv run mypy src/ --ignore-missing-imports`, `uv run pytest`
- Repo rules: no fallback behavior, no bypassing test failures, no `git push`, no destructive git reset/clean/restore workflows
- Prohibited actions: masking verification failures, silently swallowing tool execution errors, or introducing undocumented control paths

## Research Scope & Recency Policy

- Online research allowed: yes
- Approved source types: official docs, official package indexes, maintainer repositories, official release feeds
- Approved domains/APIs: pypi.org, semgrep.dev, docs.astral.sh, github.com
- Recency expectation: prefer sources with published updates or releases in the last 12 months for tooling decisions
- Exception handling: undated sources are acceptable only for official docs/README pages and must include trust rationale

## Evidence Inventory

| Evidence ID | Type | Source | Published | Retrieved | Trust rationale |
| ----------- | ---- | ------ | --------- | --------- | --------------- |
| E1 | repo-file | README.md:3 | 2025-12-10 | 2026-02-08 | Core objective statement in repository docs |
| E2 | repo-file | src/guardian/cli/main.py:16 | 2025-12-10 | 2026-02-08 | Direct command registration behavior |
| E3 | repo-file | src/guardian/analysis/pipeline.py:21 | 2025-12-10 | 2026-02-08 | Direct verification pass/fail short-circuit |
| E4 | repo-file | src/guardian/analysis/git_utils.py:28 | 2025-12-10 | 2026-02-08 | Compare-branch missing behavior |
| E5 | repo-file | src/guardian/analysis/eslint.py:54 | 2025-12-10 | 2026-02-08 | Tool-runner parse failure suppression |
| E6 | repo-file | pyproject.toml:14 | 2025-12-10 | 2026-02-08 | Quality gate dependency declarations |
| E7 | repo-file | tests/test_smoke.py:4 | 2025-12-10 | 2026-02-08 | Current smoke scope is import-only |
| E8 | repo-file | src/guardian/analysis/semgrep.py:50 | 2025-12-10 | 2026-02-08 | Confirms additional parser failure suppression |
| E9 | official-package-index | https://pypi.org/project/typer/ | 2025-09-19 | 2026-02-08 | Current Typer release recency |
| E10 | official-package-index | https://pypi.org/project/ruff/ | 2025-11-07 | 2026-02-08 | Current Ruff release recency |
| E11 | official-package-index | https://pypi.org/project/semgrep/ | 2026-02-06 | 2026-02-08 | Current Semgrep release recency |
| E12 | official-docs | https://semgrep.dev/docs/kb/semgrep-code/exit-status | 2025-10-29 | 2026-02-08 | Official exit-status semantics for gating |
| E13 | official-package-index | https://pypi.org/project/diff-cover/ | 2024-09-18 | 2026-02-08 | Diff-cover release recency signal |
| E14 | official-repo-docs | https://github.com/Bachmann1234/diff_cover/blob/main/README.md | undated:README page | 2026-02-08 | Maintainer-documented CLI flags used by project |
| E15 | official-package-index | https://pypi.org/project/mypy/ | 2025-09-18 | 2026-02-08 | Type-check tooling recency |
| E16 | official-package-index | https://pypi.org/project/pytest/ | 2025-06-17 | 2026-02-08 | Test framework recency |
| E17 | official-docs | https://docs.astral.sh/uv/ | undated:docs page | 2026-02-08 | Maintainer docs signal production intent |
| E18 | local-command-output | uv run guardian verify --help | undated:runtime output | 2026-02-08 | Confirms nested subcommand UX at runtime |
| E19 | local-command-output | uv run pytest | undated:runtime output | 2026-02-08 | Current baseline test pass status |
| E20 | local-command-output | uv run ruff check . and uv run mypy src/ --ignore-missing-imports | undated:runtime output | 2026-02-08 | Baseline lint/type gate status |

## Established Library Comparison (required for greenfield; optional for brownfield)

| Option | Maturity signal | Last release/reference | Compatibility | Reuse decision | Evidence IDs |
| ------ | --------------- | ---------------------- | ------------- | -------------- | ------------ |
| Typer | Active release in 2025 | 2025-09-19 | Already integrated in CLI modules | adopt and retain | E2,E9 |
| Ruff | Active release in 2025 | 2025-11-07 | Already integrated and in quality gates | adopt and retain | E10,E20 |
| Semgrep | Active release in 2026 | 2026-02-06 | Already integrated for policy rules | adopt and retain | E11,E12 |
| diff-cover | Latest release older than core stack | 2024-09-18 | Integrated for changed-line coverage | retain with explicit revalidation task | E13,E14 |
| GitPython | Present dependency but not used in runtime path | 2025-12-10 | Increases dependency surface without current value | remove unless added to active code path | E6 |

## Existing Change Surface (required for brownfield; optional for greenfield)

| Area | File anchor | Current behavior | Integration concern | Evidence IDs |
| ---- | ----------- | ---------------- | ------------------- | ------------ |
| CLI command root | src/guardian/cli/main.py:16 | Sub-app registration for each command group | User-facing command mismatch against docs and scripts | E2,E18 |
| Verify command | src/guardian/cli/verify.py:13 | Nested command callback style under verify group | Automation scripts expecting guardian verify fail | E18 |
| Push command | src/guardian/cli/push.py:16 | Nested command callback style under push group | Gateway workflow friction and confusion | E18 |
| Verification orchestrator | src/guardian/analysis/pipeline.py:21 | Empty changed set returns pass | Missing branch can silently bypass checks | E3,E4 |
| Git diff discovery | src/guardian/analysis/git_utils.py:28 | Missing compare branch returns empty list | Silent pass risk and hidden misconfiguration | E4 |
| Tool runner error handling | src/guardian/analysis/eslint.py:54 | Parse/exec failures swallowed | Missing tools may be interpreted as clean results | E5 |
| Tool runner error handling | src/guardian/analysis/ruff.py:54 | Parse/exec failures swallowed | Same fail-open risk as ESLint | E5 |
| Tool runner error handling | src/guardian/analysis/semgrep.py:50 | Parse/exec failures swallowed | Same fail-open risk for custom policy checks | E8 |
| Config drift baseline | src/guardian/analysis/config_drift.py:23 | Missing baseline skips check | Protective drift gate can be bypassed initially | E3 |
| Test surface | tests/test_smoke.py:4 | Smoke only validates import/version | Lacks end-to-end assurance of gateway behavior | E7,E19 |

## Repo Facts (execution-relevant only)

- Languages/frameworks: Python 3.11+, Typer CLI, Rich console output
- Package manager(s): uv (primary), pip supported for local editable install
- Build tooling: hatchling
- Test tooling: pytest, pytest-cov
- Key environment variables/config files: `.guardian/config.yaml`, `.guardian/baseline.json`, `.guardian/reports`, harness policy files under repo and home directories

## Execution Command Catalog

| Purpose | Command | Expected success signal |
| ------- | ------- | ----------------------- |
| Install/setup | uv sync --extra dev | Environment resolves and installs with exit 0 |
| CLI baseline | uv run guardian --help | Shows top-level commands without nested invocation confusion |
| Unit tests | uv run pytest tests/test_analysis.py tests/test_config_drift.py tests/test_report.py tests/test_smoke.py | Existing suite passes |
| Integration smoke tests | uv run pytest tests/test_integration_smoke.py -q | New integration suite passes on clean run |
| Lint gate | uv run ruff check . | No Ruff violations |
| Type gate | uv run mypy src/ --ignore-missing-imports | Success with no type errors |
| Full test gate | uv run pytest | All tests pass |
| Self verification | uv run guardian verify --json | JSON output status passed for green path and failed for targeted failure path tests |

## Code Map (line-numbered)

List only the places the executor must touch. Prefer path:line anchors.

| Area | File anchor | What it contains | Why it matters | Planned change |
| ---- | ----------- | ---------------- | -------------- | -------------- |
| CLI wiring | src/guardian/cli/main.py:16 | Registers command groups | Controls public command UX | Flatten command exposure and keep grouped commands where multi-action exists |
| Verify entrypoint | src/guardian/cli/verify.py:13 | verify command declaration | Current UX mismatch and nested command requirement | Convert to callback-style direct command entry |
| Push entrypoint | src/guardian/cli/push.py:16 | push command declaration | Current UX mismatch and nested command requirement | Convert to callback-style direct command entry |
| Scan entrypoint | src/guardian/cli/scan.py:13 | scan command declaration | Same nested pattern | Convert to callback-style direct command entry |
| Report entrypoint | src/guardian/cli/report.py:12 | report command declaration | Same nested pattern | Convert to callback-style direct command entry |
| Config entrypoint | src/guardian/cli/config.py:13 | config show command | May stay grouped or flatten with explicit decision | Keep grouped and verify UX documentation clarity |
| Baseline entrypoint | src/guardian/cli/baseline.py:16 | baseline update command | Needed for drift behavior hardening | Keep grouped and enforce baseline setup workflow |
| Changed-file detection | src/guardian/analysis/git_utils.py:7 | branch resolution and changed file discovery | Current fail-open path source | Return structured failure info and enforce fail-closed behavior |
| Verification orchestration | src/guardian/analysis/pipeline.py:14 | aggregation and early returns | Current pass criteria are insufficiently strict | Handle discovery/tool errors as explicit violations |
| ESLint runner | src/guardian/analysis/eslint.py:10 | ESLint subprocess and JSON parsing | Suppressed failures | Emit tool-execution violations with actionable messages |
| Ruff runner | src/guardian/analysis/ruff.py:10 | Ruff subprocess and JSON parsing | Suppressed failures | Emit tool-execution violations with actionable messages |
| Semgrep runner | src/guardian/analysis/semgrep.py:10 | Semgrep subprocess and JSON parsing | Suppressed failures | Emit tool-execution violations with actionable messages |
| Drift detection | src/guardian/analysis/config_drift.py:17 | baseline-based config drift | Baseline absence weakens gate | Add mandatory baseline policy or explicit failing check |
| Init flow | src/guardian/cli/init.py:72 | baseline initialization | Empty baseline allows unguarded start | Seed hashes or require baseline update before pass |
| Integration tests | tests/test_integration_smoke.py:1 | New end-to-end CLI behavior tests | Proves no regressions in gate-critical paths | Add deterministic subprocess/mocked-tool based tests |
| CLI tests | tests/test_cli_commands.py:1 | New command UX tests | Guards against nested command regressions | Add command invocation and exit-code assertions |
| Docs | README.md:74 | Quick start command examples | Must match real CLI behavior | Update examples and failure semantics |

## Requirement to Evidence Traceability

| Requirement ID | Requirement | Evidence IDs | Context section(s) | Planned ExecPlan linkage |
| -------------- | ----------- | ------------ | ------------------ | ------------------------ |
| R1 | Completion plan reflects real project progress and defects | E1,E2,E3,E4,E5,E6,E7 | Change Brief, Existing Change Surface, Code Map | Phase 1 Task 1-3 and Phase 2 Task 4-7 |
| R2 | Online research validates stack recency and approach | E9,E10,E11,E12,E13,E14,E15,E16,E17 | Research Scope, Evidence Inventory, Library Comparison | Phase 1 Task 1-2 |
| R3 | Contradictions and fail-open paths are addressed | E2,E3,E4,E5,E8,E18 | Existing Change Surface, Risk Register, Code Map | Phase 2 Task 4-9 and Phase 3 Task 10-12 |
| R4 | Working smoke integration test exists and proves behavior | E7,E19 | Code Map, Execution Command Catalog | Phase 4 Task 13-17 |
| R5 | Deterministic quality gates and completion proofs are defined | E6,E19,E20 | Guardrails, Execution Command Catalog, Success Criteria | Phase 5 Task 18-20 |

## Contracts & Interfaces

Only include what the change touches:

- CLI contract:
  - `guardian verify`
  - `guardian push [remote] [branch]`
  - `guardian scan`
  - `guardian report`
  - `guardian harness install|status`
  - `guardian config show`
  - `guardian baseline update`
- Verification result contract:
  - `list[Violation]` with deterministic severity and rule identifiers
  - JSON output from verify/scan remains machine-readable and stable
- Config interface:
  - `.guardian/config.yaml` keys `analysis.compare_branch`, `analysis.coverage_threshold`, `reports.keep_count`
  - `.guardian/baseline.json` required for drift enforcement

## Risk Register

| Risk | Impact | Mitigation | Verification command | Evidence IDs |
| ---- | ------ | ---------- | -------------------- | ------------ |
| CLI flattening breaks existing scripts that used nested commands | Medium | Add explicit CLI tests and update README examples in same change set | uv run pytest tests/test_cli_commands.py -q | E2,E18 |
| Fail-closed compare-branch logic blocks legitimate first-run repos | High | Emit explicit actionable violation with setup instructions instead of silent pass | uv run pytest tests/test_integration_smoke.py -k compare_branch_missing -q | E3,E4 |
| Strict tool-runner error handling increases false negatives from environment issues | Medium | Classify as tool-execution errors with remediation text and deterministic exit code | uv run pytest tests/test_integration_smoke.py -k tool_failure -q | E5,E8,E12 |
| Baseline enforcement creates initialization friction | Medium | Ensure init or baseline update path is explicit and documented | uv run guardian init && uv run guardian baseline update | E6 |
| diff-cover staleness may reduce long-term reliability | Medium | Revalidate current usage in research phase and consider migration criteria in decision log | uv run pytest tests/test_integration_smoke.py -k coverage_gate -q | E13,E14 |
| Documentation drift reintroduces contradictions | Medium | Tie doc updates to CLI behavior tests in same phase | uv run guardian --help | E1,E18 |
