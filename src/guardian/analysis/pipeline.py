"""Verification pipeline - orchestrates external tools."""

from pathlib import Path

from guardian.analysis.config_drift import check_config_drift
from guardian.analysis.coverage import run_diff_cover
from guardian.analysis.eslint import run_eslint
from guardian.analysis.git_utils import get_all_files, get_changed_files
from guardian.analysis.ruff import run_ruff
from guardian.analysis.semgrep import run_semgrep
from guardian.analysis.violation import Violation


def run_verification() -> list[Violation]:
    """Run all verification tools and aggregate results."""
    violations = []

    # 1. Get changed files
    changed_files = get_changed_files()

    if not changed_files:
        return []

    ts_files = [f for f in changed_files if f.endswith((".ts", ".tsx", ".js", ".jsx"))]
    py_files = [f for f in changed_files if f.endswith(".py")]

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


def run_full_scan() -> list[Violation]:
    """Run full codebase scan (all files, not just changed)."""
    violations = []

    # 1. Get all files
    all_files = get_all_files()

    if not all_files:
        return []

    ts_files = [f for f in all_files if f.endswith((".ts", ".tsx", ".js", ".jsx"))]
    py_files = [f for f in all_files if f.endswith(".py")]

    # 2. Run ESLint for TypeScript
    if ts_files:
        violations.extend(run_eslint(ts_files))

    # 3. Run Ruff for Python
    if py_files:
        violations.extend(run_ruff(py_files))

    # 4. Run Semgrep for custom patterns
    violations.extend(run_semgrep(all_files))

    # 5. Check config drift
    violations.extend(check_config_drift())

    return violations
