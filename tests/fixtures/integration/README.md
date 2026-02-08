# Integration Scenario Fixtures

Each fixture directory contains `manifest.json` and optional `base/` and `head/` overlays.

- `base/` overlays are applied before the base commit and baseline generation.
- `head/` overlays are applied for the head commit under test.
- `repo.head_delete` can remove files in the head commit.

`manifest.json` schema:

```json
{
  "description": "Scenario intent",
  "expected": {
    "status": "passed|failed",
    "exit_code": 0,
    "rules": ["required-rule-id"],
    "forbidden_rules": ["rule-that-must-not-appear"],
    "min_violations": 1
  },
  "repo": {
    "compare_branch": "origin/main",
    "include_coverage_file": true,
    "auto_change_app": true,
    "head_delete": ["relative/path"]
  },
  "tool_env": {
    "QUALITY_GATE_EXIT": "0",
    "RUFF_STDOUT": "[]",
    "SEMGREP_STDOUT": "{\"results\": []}",
    "NPX_STDOUT": "[]",
    "DIFF_COVER_REPORT": "{\"total_percent_covered\": 100}",
    "DIFF_COVER_EXIT": "0",
    "DIFF_COVER_WRITE_REPORT": "1"
  }
}
```
