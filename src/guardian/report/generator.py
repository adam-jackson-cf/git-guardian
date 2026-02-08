"""Report generation - produces Markdown reports for LLMs."""

from datetime import datetime
from pathlib import Path

from guardian.analysis.violation import Violation
from guardian.configuration import ConfigValidationError, load_guardian_config


def generate_report(violations: list[Violation]) -> Path:
    """Generate Markdown report from violations."""

    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    repo_root = Path.cwd()
    report_dir = repo_root / ".guardian" / "reports"
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
| Errors | {"❌ Fail" if errors else "✅ Pass"} | {len(errors)} |
| Warnings | {"⚠️ Warn" if warnings else "✅ Pass"} | {len(warnings)} |
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

    # Clean up old reports (keep last 10)
    _cleanup_old_reports(report_dir)

    return report_path


def _cleanup_old_reports(report_dir: Path) -> None:
    """Remove old reports, keeping only the most recent ones."""
    keep_count = 10

    try:
        config = load_guardian_config(Path.cwd())
        keep_count = config.reports.keep_count
    except ConfigValidationError:
        keep_count = 10

    # Get all report files sorted by modification time
    reports = sorted(
        report_dir.glob("*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    # Remove symlink from list if present
    reports = [r for r in reports if not r.is_symlink()]

    # Keep only the most recent ones
    for old_report in reports[keep_count:]:
        old_report.unlink()
