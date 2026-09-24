"""Smoke test - verifies the package is importable and the project skeleton works."""


def test_package_importable() -> None:
    """cfpb_mlops must be importable after `uv sync` + editable install."""
    import cfpb_mlops  # noqa: F401


def test_trivial() -> None:
    """Baseline: pytest discovers and runs tests."""
    assert 1 + 1 == 2
