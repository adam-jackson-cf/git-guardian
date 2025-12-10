"""Smoke tests to verify baseline setup."""


def test_import():
    """Test that guardian can be imported."""
    import guardian

    assert guardian.__version__ == "0.3.1"
