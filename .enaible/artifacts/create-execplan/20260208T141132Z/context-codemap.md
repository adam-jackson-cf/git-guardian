# Context Code Map

- Created: 2026-02-08
- Last updated: 2026-02-08T14:12:55Z

| Area | File anchor | Current behavior | Planned change |
| ---- | ----------- | ---------------- | -------------- |
| Product objective | README.md:3 | Defines Guardian as non-circumventable final verification layer | Keep objective wording aligned with implemented behavior |
| CLI registration | src/guardian/cli/main.py:16 | Registers each command module as sub-apps, causing nested command UX | Flatten command exposure to match documented UX |
| Verify CLI | src/guardian/cli/verify.py:13 | Uses app.command under sub-app, requiring guardian verify verify | Convert to direct guardian verify execution |
| Push CLI | src/guardian/cli/push.py:16 | Uses app.command under sub-app, requiring guardian push push | Convert to direct guardian push execution |
| Verification orchestrator | src/guardian/analysis/pipeline.py:14 | Returns pass when changed file list is empty | Replace fail-open path with explicit status handling |
| Diff source resolution | src/guardian/analysis/git_utils.py:7 | Defaults to origin/main and returns empty list when branch missing | Fail closed with actionable violation when compare branch is invalid |
| ESLint runner | src/guardian/analysis/eslint.py:10 | Swallows JSON/parse failures and returns no violations | Emit deterministic tool-execution violations on failure |
| Ruff runner | src/guardian/analysis/ruff.py:10 | Swallows JSON/parse failures and returns no violations | Emit deterministic tool-execution violations on failure |
| Semgrep runner | src/guardian/analysis/semgrep.py:10 | Swallows JSON/parse failures and returns no violations | Emit deterministic tool-execution violations on failure |
| Config drift check | src/guardian/analysis/config_drift.py:17 | Skips drift check when baseline missing | Enforce baseline existence and explicit setup workflow |
| Init command | src/guardian/cli/init.py:72 | Creates empty baseline JSON by default | Generate baseline hashes or fail verification until baseline updated |
| Report generation | src/guardian/report/generator.py:9 | Generates markdown report and latest symlink | Keep behavior, add coverage for new violation classes |
| Harness install | src/guardian/harness/installer.py:29 | Installs harness files, can overwrite AGENTS.md | Add overwrite policy and explicit user-facing warnings |
| Current tests | tests/test_analysis.py:6 | Covers Violation dataclass only for analysis package | Add integration smoke tests for CLI and pipeline behaviors |
| Current tests | tests/test_smoke.py:4 | Import/version-only smoke test | Keep as package smoke, add runtime integration smoke suite |
