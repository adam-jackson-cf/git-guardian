#!/usr/bin/env python3
"""Deterministic code-quality metrics for CI guardrails and trend reporting."""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class FunctionMetric:
    """Per-function metric snapshot."""

    file: str
    name: str
    line: int
    cyclomatic_complexity: int
    length: int
    parameter_count: int


def _collect_python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if path.is_file())


def _function_metrics(path: Path, repo_root: Path) -> list[FunctionMetric]:
    tree = ast.parse(path.read_text())
    metrics: list[FunctionMetric] = []
    relative = str(path.relative_to(repo_root))
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        end_lineno = getattr(node, "end_lineno", node.lineno)
        metrics.append(
            FunctionMetric(
                file=relative,
                name=node.name,
                line=node.lineno,
                cyclomatic_complexity=_cyclomatic_complexity(node),
                length=max(1, end_lineno - node.lineno + 1),
                parameter_count=_parameter_count(node),
            )
        )
    return metrics


def _cyclomatic_complexity(node: ast.AST) -> int:
    score = 1
    for child in ast.walk(node):
        if isinstance(
            child,
            (
                ast.If,
                ast.For,
                ast.AsyncFor,
                ast.While,
                ast.With,
                ast.AsyncWith,
                ast.Try,
                ast.ExceptHandler,
                ast.IfExp,
                ast.Assert,
            ),
        ):
            score += 1
        elif isinstance(child, ast.BoolOp):
            score += max(0, len(child.values) - 1)
        elif isinstance(child, ast.Match):
            score += len(child.cases)
    return score


def _parameter_count(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    args = node.args
    total = len(args.args) + len(args.posonlyargs) + len(args.kwonlyargs)
    if args.vararg is not None:
        total += 1
    if args.kwarg is not None:
        total += 1
    return total


def _duplicate_lines(files: list[Path], repo_root: Path) -> tuple[int, list[dict[str, object]]]:
    line_counts: Counter[str] = Counter()
    line_sources: dict[str, set[str]] = {}
    for path in files:
        rel = str(path.relative_to(repo_root))
        for raw_line in path.read_text().splitlines():
            normalized = raw_line.strip()
            if not normalized or normalized.startswith("#"):
                continue
            if len(normalized) < 12 or not any(char.isalpha() for char in normalized):
                continue
            line_counts[normalized] += 1
            line_sources.setdefault(normalized, set()).add(rel)

    duplicate_total = sum(count - 1 for count in line_counts.values() if count > 1)
    top_duplicates = [
        {
            "line": line,
            "occurrences": count,
            "files": sorted(line_sources[line])[:5],
        }
        for line, count in line_counts.most_common()
        if count > 1
    ][:10]
    return duplicate_total, top_duplicates


def _build_metrics(repo_root: Path, source_root: Path) -> dict[str, object]:
    files = _collect_python_files(source_root)
    function_metrics: list[FunctionMetric] = []
    for file_path in files:
        function_metrics.extend(_function_metrics(file_path, repo_root))

    if not function_metrics:
        raise SystemExit("No Python functions found under source scope.")

    max_complexity = max(function_metrics, key=lambda metric: metric.cyclomatic_complexity)
    max_length = max(function_metrics, key=lambda metric: metric.length)
    max_parameters = max(function_metrics, key=lambda metric: metric.parameter_count)
    long_functions_over_80 = [metric for metric in function_metrics if metric.length > 80]
    duplicate_lines, top_duplicates = _duplicate_lines(files, repo_root)

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": str(source_root.relative_to(repo_root)),
        "file_count": len(files),
        "function_count": len(function_metrics),
        "max_cyclomatic_complexity": max_complexity.cyclomatic_complexity,
        "max_cyclomatic_complexity_offender": _format_offender(max_complexity),
        "max_function_length": max_length.length,
        "max_function_length_offender": _format_offender(max_length),
        "max_parameter_count": max_parameters.parameter_count,
        "max_parameter_count_offender": _format_offender(max_parameters),
        "long_functions_over_80_lines": len(long_functions_over_80),
        "duplicate_lines_source_scope": duplicate_lines,
        "top_duplicate_lines": top_duplicates,
    }


def _format_offender(metric: FunctionMetric) -> str:
    return f"{metric.file}:{metric.line}::{metric.name}"


def _check_budget(metrics: dict[str, object], budget_file: Path) -> list[str]:
    budget = json.loads(budget_file.read_text())
    if not isinstance(budget, dict):
        raise SystemExit(f"Budget file must be a JSON object: {budget_file}")

    comparisons = (
        "max_cyclomatic_complexity",
        "max_function_length",
        "max_parameter_count",
        "long_functions_over_80_lines",
    )
    failures: list[str] = []
    for key in comparisons:
        budget_value = budget.get(key)
        metric_value = metrics.get(key)
        if not isinstance(budget_value, int) or not isinstance(metric_value, int):
            raise SystemExit(f"Missing integer key '{key}' in metrics or budget data.")
        if metric_value > budget_value:
            failures.append(f"{key}: {metric_value} > budget {budget_value}")
    return failures


def _write_trend(metrics: dict[str, object], trend_dir: Path) -> Path:
    trend_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    trend_path = trend_dir / f"{timestamp}.json"
    trend_path.write_text(json.dumps(metrics, indent=2) + "\n")
    (trend_dir / "latest.json").write_text(json.dumps(metrics, indent=2) + "\n")
    return trend_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root",
        default="src/guardian",
        help="Source path to analyze (relative to repo root).",
    )
    parser.add_argument(
        "--budget-file",
        required=True,
        help="JSON file containing upper bounds for quality metrics.",
    )
    parser.add_argument(
        "--trend-dir",
        required=True,
        help="Directory where timestamped trend artifacts will be written.",
    )
    args = parser.parse_args()

    repo_root = Path.cwd()
    source_root = (repo_root / args.source_root).resolve()
    budget_file = (repo_root / args.budget_file).resolve()
    trend_dir = (repo_root / args.trend_dir).resolve()

    if not source_root.exists():
        raise SystemExit(f"Source root does not exist: {source_root}")
    if not budget_file.exists():
        raise SystemExit(f"Budget file does not exist: {budget_file}")

    metrics = _build_metrics(repo_root, source_root)
    trend_path = _write_trend(metrics, trend_dir)

    failures = _check_budget(metrics, budget_file)
    if failures:
        details = "; ".join(failures)
        raise SystemExit(f"Complexity budget exceeded: {details}")

    print(f"Quality metrics trend written to {trend_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
