"""Centralized Guardian configuration loading and validation."""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigValidationError(ValueError):
    """Raised when Guardian configuration is missing or invalid."""


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


def load_guardian_config(repo_root: Path) -> GuardianConfig:
    """Load and validate .guardian/config.yaml from repository root."""
    config_path = repo_root / ".guardian" / "config.yaml"

    if not config_path.exists():
        raise ConfigValidationError(
            "Guardian config is missing at .guardian/config.yaml. Run `guardian init`."
        )

    try:
        raw = yaml.safe_load(config_path.read_text())
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigValidationError(f"Failed to read .guardian/config.yaml: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigValidationError(".guardian/config.yaml must contain a YAML mapping.")

    version = _read_string(raw, "version", required=False, default="0.3")

    analysis_raw = _read_mapping(raw, "analysis", required=False, default={})
    tools_raw = _read_mapping(raw, "tools", required=False, default={})
    reports_raw = _read_mapping(raw, "reports", required=False, default={})
    quality_raw = _read_mapping(raw, "quality", required=True)
    harness_raw = _read_mapping(raw, "harness", required=False, default={})

    languages = _read_string_list(
        analysis_raw,
        "languages",
        required=False,
        default=list(DEFAULT_LANGUAGES),
        allow_empty=False,
    )
    compare_branch = _read_string(
        analysis_raw,
        "compare_branch",
        required=False,
        default=DEFAULT_COMPARE_BRANCH,
    )
    coverage_threshold = _read_int(
        analysis_raw,
        "coverage_threshold",
        required=False,
        default=DEFAULT_COVERAGE_THRESHOLD,
        minimum=0,
        maximum=100,
    )
    coverage_file = _read_string(
        analysis_raw,
        "coverage_file",
        required=False,
        default=DEFAULT_COVERAGE_FILE,
    )

    tools = ToolConfig(
        eslint=_read_string(
            tools_raw,
            "eslint",
            required=False,
            default=DEFAULT_TOOLS["eslint"],
        ),
        ruff=_read_string(tools_raw, "ruff", required=False, default=DEFAULT_TOOLS["ruff"]),
        semgrep=_read_string(
            tools_raw,
            "semgrep",
            required=False,
            default=DEFAULT_TOOLS["semgrep"],
        ),
        diff_cover=_read_string(
            tools_raw,
            "diff_cover",
            required=False,
            default=DEFAULT_TOOLS["diff_cover"],
        ),
    )

    reports = ReportConfig(
        format=_read_string(reports_raw, "format", required=False, default=DEFAULT_REPORT_FORMAT),
        keep_count=_read_int(
            reports_raw,
            "keep_count",
            required=False,
            default=DEFAULT_REPORT_KEEP_COUNT,
            minimum=1,
        ),
    )

    quality_commands = _read_string_list(
        quality_raw,
        "commands",
        required=True,
        allow_empty=False,
    )

    harness = HarnessConfig(
        enabled=tuple(
            _read_string_list(
                harness_raw,
                "enabled",
                required=False,
                default=[],
                allow_empty=True,
            )
        )
    )

    return GuardianConfig(
        version=version,
        analysis=AnalysisConfig(
            languages=tuple(languages),
            compare_branch=compare_branch,
            coverage_threshold=coverage_threshold,
            coverage_file=coverage_file,
        ),
        tools=tools,
        reports=reports,
        quality=QualityConfig(commands=tuple(quality_commands)),
        harness=harness,
    )


def split_command(command: str, *, field_name: str) -> list[str]:
    """Parse a configured command string into deterministic argv."""
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        raise ConfigValidationError(f"Invalid command for {field_name}: {exc}") from exc

    if not argv:
        raise ConfigValidationError(f"Command for {field_name} cannot be empty.")

    # Prevent nondeterministic installs when using npx.
    if argv[0] == "npx" and "--no-install" not in argv[1:]:
        argv.insert(1, "--no-install")

    return argv


def _read_mapping(
    raw: dict[str, Any],
    key: str,
    *,
    required: bool,
    default: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = raw.get(key)
    if value is None:
        if required:
            raise ConfigValidationError(
                f"Missing required section '{key}' in .guardian/config.yaml."
            )
        return {} if default is None else default
    if not isinstance(value, dict):
        raise ConfigValidationError(f"Section '{key}' must be a mapping in .guardian/config.yaml.")
    return value


def _read_string(
    raw: dict[str, Any],
    key: str,
    *,
    required: bool,
    default: str | None = None,
) -> str:
    value = raw.get(key)
    if value is None:
        if required or default is None:
            raise ConfigValidationError(f"Missing required key '{key}' in .guardian/config.yaml.")
        return default
    if not isinstance(value, str):
        raise ConfigValidationError(f"Key '{key}' must be a string in .guardian/config.yaml.")
    normalized = value.strip()
    if not normalized:
        raise ConfigValidationError(f"Key '{key}' cannot be empty in .guardian/config.yaml.")
    return normalized


def _read_int(
    raw: dict[str, Any],
    key: str,
    *,
    required: bool,
    default: int | None = None,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    value = raw.get(key)
    if value is None:
        if required or default is None:
            raise ConfigValidationError(f"Missing required key '{key}' in .guardian/config.yaml.")
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigValidationError(f"Key '{key}' must be an integer in .guardian/config.yaml.")
    if minimum is not None and value < minimum:
        raise ConfigValidationError(f"Key '{key}' must be >= {minimum} in .guardian/config.yaml.")
    if maximum is not None and value > maximum:
        raise ConfigValidationError(f"Key '{key}' must be <= {maximum} in .guardian/config.yaml.")
    return int(value)


def _read_string_list(
    raw: dict[str, Any],
    key: str,
    *,
    required: bool,
    default: list[str] | None = None,
    allow_empty: bool,
) -> list[str]:
    value = raw.get(key)
    if value is None:
        if required and default is None:
            raise ConfigValidationError(f"Missing required key '{key}' in .guardian/config.yaml.")
        return [] if default is None else list(default)
    if not isinstance(value, list):
        raise ConfigValidationError(f"Key '{key}' must be a list in .guardian/config.yaml.")

    normalized: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise ConfigValidationError(
                f"Key '{key}' item at index {index} must be a string in .guardian/config.yaml."
            )
        candidate = item.strip()
        if not candidate:
            raise ConfigValidationError(
                f"Key '{key}' item at index {index} cannot be empty in .guardian/config.yaml."
            )
        normalized.append(candidate)

    if not allow_empty and not normalized:
        raise ConfigValidationError(f"Key '{key}' must contain at least one entry.")

    return normalized
