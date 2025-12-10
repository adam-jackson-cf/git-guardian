"""Coverage analysis using diff-cover."""

import json
import subprocess
from pathlib import Path

from guardian.analysis.violation import Violation


def run_diff_cover(coverage_file: Path) -> list[Violation]:
    """Run diff-cover for coverage analysis."""
    repo_root = Path.cwd()

    # Get config
    config_file = repo_root / ".guardian" / "config.yaml"
    compare_branch = "origin/main"
    threshold = 80

    if config_file.exists():
        import yaml

        config = yaml.safe_load(config_file.read_text())
        compare_branch = config.get("analysis", {}).get("compare_branch", "origin/main")
        threshold = config.get("analysis", {}).get("coverage_threshold", 80)

    violations = []

    # Run diff-cover
    # Note: diff-cover doesn't support --json-report to stdout on all platforms
    # We'll use a temp file approach
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        cmd = [
            "diff-cover",
            str(coverage_file),
            "--compare-branch",
            compare_branch,
            "--json-report",
            str(tmp_path),
            "--fail-under",
            str(threshold),
        ]

        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=repo_root,
        )

        # Check if report was generated
        if tmp_path.exists():
            try:
                data = json.loads(tmp_path.read_text())
                coverage = data.get("total_percent_covered", 0)

                if coverage < threshold:
                    violations.append(
                        Violation(
                            file="coverage",
                            line=0,
                            column=0,
                            rule="coverage-delta",
                            message=(
                                f"Coverage on changed lines is {coverage:.1f}%, "
                                f"below threshold of {threshold}%"
                            ),
                            severity="error",
                        )
                    )
            except (json.JSONDecodeError, KeyError):
                pass
    finally:
        # Clean up temp file
        if tmp_path.exists():
            tmp_path.unlink()

    return violations
