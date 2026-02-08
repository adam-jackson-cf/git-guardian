# Contributing to Guardian

## Development Setup

```bash
# Install development dependencies
uv sync --dev

# Install editable package
uv pip install -e .
```

## Quality Gates

Run all quality gates before opening a pull request:

```bash
uv run ruff check .
uv run mypy src/ --ignore-missing-imports
uv run pytest
uv run guardian verify
```
