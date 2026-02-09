"""Typed configuration schema and default values."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisConfig:
    """Analysis-related configuration values."""

    languages: tuple[str, ...]
    compare_branch: str
    coverage_threshold: int
    coverage_file: str


@dataclass(frozen=True)
class ToolConfig:
    """External tool command configuration."""

    eslint: str
    ruff: str
    semgrep: str
    diff_cover: str


@dataclass(frozen=True)
class ReportConfig:
    """Report generation configuration."""

    format: str
    keep_count: int


@dataclass(frozen=True)
class QualityConfig:
    """Repository-defined deterministic quality gate commands."""

    commands: tuple[str, ...]


@dataclass(frozen=True)
class HarnessConfig:
    """Enabled harnesses in repository configuration."""

    enabled: tuple[str, ...]


@dataclass(frozen=True)
class GuardianConfig:
    """Full validated Guardian configuration."""

    version: str
    analysis: AnalysisConfig
    tools: ToolConfig
    reports: ReportConfig
    quality: QualityConfig
    harness: HarnessConfig


DEFAULT_LANGUAGES = ("typescript", "python")
DEFAULT_COMPARE_BRANCH = "origin/main"
DEFAULT_COVERAGE_THRESHOLD = 80
DEFAULT_COVERAGE_FILE = "coverage.xml"
DEFAULT_REPORT_FORMAT = "markdown"
DEFAULT_REPORT_KEEP_COUNT = 10
DEFAULT_TOOLS = {
    "eslint": "npx --no-install eslint",
    "ruff": "ruff",
    "semgrep": "semgrep",
    "diff_cover": "diff-cover",
}
