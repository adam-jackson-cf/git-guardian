"""Validation helpers for reading .guardian/config.yaml."""

from __future__ import annotations

from typing import Any


class ConfigValidationError(ValueError):
    """Raised when Guardian configuration is missing or invalid."""


def read_mapping(
    raw: dict[str, Any],
    key: str,
    *,
    required: bool,
    default: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Read a nested mapping value from a config document."""
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


def read_string(
    raw: dict[str, Any],
    key: str,
    *,
    required: bool,
    default: str | None = None,
) -> str:
    """Read and normalize a required or optional string field."""
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


def read_int(
    raw: dict[str, Any],
    key: str,
    *,
    required: bool,
    default: int | None = None,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    """Read an integer field with optional bounds validation."""
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


def read_string_list(
    raw: dict[str, Any],
    key: str,
    *,
    required: bool,
    default: list[str] | None = None,
    allow_empty: bool,
) -> list[str]:
    """Read a string list field and normalize each entry."""
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
