"""Guardian configuration loader."""

from __future__ import annotations

from pathlib import Path

import yaml

from guardian.configuration.schema import (
    DEFAULT_COMPARE_BRANCH,
    DEFAULT_COVERAGE_FILE,
    DEFAULT_COVERAGE_THRESHOLD,
    DEFAULT_LANGUAGES,
    DEFAULT_REPORT_FORMAT,
    DEFAULT_REPORT_KEEP_COUNT,
    DEFAULT_TOOLS,
    AnalysisConfig,
    GuardianConfig,
    HarnessConfig,
    QualityCommand,
    QualityConfig,
    ReportConfig,
    ToolConfig,
)
from guardian.configuration.validation import (
    ConfigValidationError,
    read_int,
    read_mapping,
    read_string,
    read_string_list,
)


def _parse_quality_commands(quality_raw: dict[str, object]) -> tuple[QualityCommand, ...]:
    """Parse and validate quality.commands entries."""
    quality_commands_raw = quality_raw.get("commands")
    if not isinstance(quality_commands_raw, list):
        raise ConfigValidationError(
            "Key 'quality.commands' must be a list in .guardian/config.yaml."
        )
    if not quality_commands_raw:
        raise ConfigValidationError("Key 'quality.commands' must contain at least one entry.")

    commands: list[QualityCommand] = []
    for index, command_raw in enumerate(quality_commands_raw):
        commands.append(_parse_quality_command(command_raw, index=index))
    return tuple(commands)


def _parse_quality_command(command_raw: object, *, index: int) -> QualityCommand:
    """Parse one quality.commands item."""
    if not isinstance(command_raw, dict):
        raise ConfigValidationError(
            f"Key 'quality.commands' item at index {index} must be a mapping."
        )

    command_name = read_string(command_raw, "name", required=True)
    command_run = read_string(command_raw, "run", required=True)
    run_on = _parse_quality_run_on(command_raw, index=index)
    include = tuple(
        read_string_list(
            command_raw,
            "include",
            required=False,
            default=[],
            allow_empty=True,
        )
    )
    return QualityCommand(
        name=command_name,
        run=command_run,
        run_on=run_on,
        include=include,
    )


def _parse_quality_run_on(command_raw: dict[str, object], *, index: int) -> str:
    """Validate quality.commands[i].run_on enum."""
    run_on = read_string(command_raw, "run_on", required=False, default="always")
    if run_on not in {"always", "changed", "full"}:
        raise ConfigValidationError(
            f"Key 'quality.commands[{index}].run_on' must be one of: always, changed, full."
        )
    return run_on


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

    version = read_string(raw, "version", required=False, default="0.3")

    analysis_raw = read_mapping(raw, "analysis", required=False, default={})
    tools_raw = read_mapping(raw, "tools", required=False, default={})
    reports_raw = read_mapping(raw, "reports", required=False, default={})
    quality_raw = read_mapping(raw, "quality", required=True)
    harness_raw = read_mapping(raw, "harness", required=False, default={})

    languages = read_string_list(
        analysis_raw,
        "languages",
        required=False,
        default=list(DEFAULT_LANGUAGES),
        allow_empty=False,
    )
    compare_branch = read_string(
        analysis_raw,
        "compare_branch",
        required=False,
        default=DEFAULT_COMPARE_BRANCH,
    )
    coverage_threshold = read_int(
        analysis_raw,
        "coverage_threshold",
        required=False,
        default=DEFAULT_COVERAGE_THRESHOLD,
        minimum=0,
        maximum=100,
    )
    coverage_file = read_string(
        analysis_raw,
        "coverage_file",
        required=False,
        default=DEFAULT_COVERAGE_FILE,
    )

    tools = ToolConfig(
        eslint=read_string(
            tools_raw,
            "eslint",
            required=False,
            default=DEFAULT_TOOLS["eslint"],
        ),
        ruff=read_string(tools_raw, "ruff", required=False, default=DEFAULT_TOOLS["ruff"]),
        semgrep=read_string(
            tools_raw,
            "semgrep",
            required=False,
            default=DEFAULT_TOOLS["semgrep"],
        ),
        diff_cover=read_string(
            tools_raw,
            "diff_cover",
            required=False,
            default=DEFAULT_TOOLS["diff_cover"],
        ),
    )

    reports = ReportConfig(
        format=read_string(reports_raw, "format", required=False, default=DEFAULT_REPORT_FORMAT),
        keep_count=read_int(
            reports_raw,
            "keep_count",
            required=False,
            default=DEFAULT_REPORT_KEEP_COUNT,
            minimum=1,
        ),
    )

    quality_commands = _parse_quality_commands(quality_raw)

    harness = HarnessConfig(
        enabled=tuple(
            read_string_list(
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
        quality=QualityConfig(commands=quality_commands),
        harness=harness,
    )
