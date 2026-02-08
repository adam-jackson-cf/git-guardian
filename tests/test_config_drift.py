"""Tests for config drift detection."""

import hashlib
import json

from guardian.analysis.config_drift import check_config_drift


def test_config_drift_no_baseline(temp_dir, monkeypatch):
    """Test config drift with no baseline file."""
    monkeypatch.chdir(temp_dir)

    # No baseline file must fail closed.
    violations = check_config_drift()
    assert len(violations) == 1
    assert violations[0].rule == "config-baseline-missing"
    assert violations[0].severity == "error"


def test_config_drift_no_changes(temp_dir, monkeypatch):
    """Test config drift with no changes."""
    monkeypatch.chdir(temp_dir)

    # Create .guardian directory and baseline
    guardian_dir = temp_dir / ".guardian"
    guardian_dir.mkdir()
    baseline_file = guardian_dir / "baseline.json"

    # Create a config file
    config_file = temp_dir / "tsconfig.json"
    config_file.write_text('{"compilerOptions": {}}')

    # Create baseline with current hash
    current_hash = hashlib.sha256(config_file.read_bytes()).hexdigest()
    baseline_file.write_text(json.dumps({"tsconfig.json": current_hash}))

    # Check drift - should be no violations
    violations = check_config_drift()
    assert len(violations) == 0


def test_config_drift_with_changes(temp_dir, monkeypatch):
    """Test config drift with changes."""
    monkeypatch.chdir(temp_dir)

    # Create .guardian directory and baseline
    guardian_dir = temp_dir / ".guardian"
    guardian_dir.mkdir()
    baseline_file = guardian_dir / "baseline.json"

    # Create a config file
    config_file = temp_dir / "tsconfig.json"
    config_file.write_text('{"compilerOptions": {}}')

    # Create baseline with old hash
    old_hash = "old_hash_value"
    baseline_file.write_text(json.dumps({"tsconfig.json": old_hash}))

    # Check drift - should detect change
    violations = check_config_drift()
    assert len(violations) == 1
    assert violations[0].file == "tsconfig.json"
    assert violations[0].rule == "config-drift"
    assert violations[0].severity == "error"
