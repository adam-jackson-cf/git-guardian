"""Fixture-driven integration scenarios for Guardian verification."""

from __future__ import annotations

import pytest

from tests.integration_harness import discover_scenarios, run_fixture_scenario

SCENARIO_DIRS = discover_scenarios()


@pytest.mark.parametrize(
    "scenario_dir",
    SCENARIO_DIRS,
    ids=[scenario.name for scenario in SCENARIO_DIRS],
)
def test_fixture_integration_scenarios(temp_dir, scenario_dir):
    """Execute each integration fixture and validate expected outcomes."""
    scenario = run_fixture_scenario(temp_dir, scenario_dir)
    payload = scenario.payload
    manifest = scenario.manifest

    assert payload.get("status") == manifest.expected_status
    assert scenario.exit_code == manifest.expected_exit_code

    violations = payload.get("violations", [])
    rules = {str(item.get("rule")) for item in violations}

    for expected_rule in manifest.expected_rules:
        assert expected_rule in rules

    for forbidden_rule in manifest.forbidden_rules:
        assert forbidden_rule not in rules

    if manifest.min_violations is not None:
        assert int(payload.get("violation_count", 0)) >= manifest.min_violations
