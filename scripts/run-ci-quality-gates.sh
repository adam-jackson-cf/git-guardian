#!/usr/bin/env bash
set -euo pipefail

RUNNER_PATH="scripts/run-ci-quality-gates.sh"
PRECOMMIT_CONFIG=".pre-commit-config.yaml"
CI_WORKFLOW=".github/workflows/ci-quality-gates.yml"

fix=false
stage=false

while (($# > 0)); do
  case "$1" in
    --fix)
      fix=true
      shift
      ;;
    --stage)
      stage=true
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

assert_parity() {
  if [[ ! -f "$PRECOMMIT_CONFIG" ]]; then
    echo "Parity check failed: missing $PRECOMMIT_CONFIG" >&2
    exit 1
  fi

  if [[ ! -f "$CI_WORKFLOW" ]]; then
    echo "Parity check failed: missing $CI_WORKFLOW" >&2
    exit 1
  fi

  if ! rg -q "entry:[[:space:]]+bash[[:space:]]+$RUNNER_PATH[[:space:]]+--fix[[:space:]]+--stage" "$PRECOMMIT_CONFIG"; then
    echo "Parity check failed: $PRECOMMIT_CONFIG does not reference $RUNNER_PATH with --fix --stage" >&2
    exit 1
  fi

  if ! rg -q "bash[[:space:]]+$RUNNER_PATH" "$CI_WORKFLOW"; then
    echo "Parity check failed: $CI_WORKFLOW does not reference $RUNNER_PATH" >&2
    exit 1
  fi
}

run_checks() {
  if $fix; then
    uv run ruff check --fix .
    if $stage; then
      git add -A
    fi
  fi

  uv run ruff check .
  uv run mypy src/ --ignore-missing-imports
  uv run pytest
}

assert_parity
run_checks
