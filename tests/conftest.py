"""Root test configuration.

- Registers the shared fixtures plugin.
- Enforces the quarantine policy: tests marked ``@pytest.mark.quarantine`` are
  known-flaky and are skipped in default and CI-gate runs, so a single flaky
  test can never block a merge. To run them deliberately: ``pytest -m quarantine``.
"""

import pytest

# Register the fixtures defined in tests/fixtures/conftest.py for every test.
pytest_plugins = ["tests.fixtures.conftest"]


def pytest_collection_modifyitems(config, items):
    """Skip quarantined tests unless they are explicitly selected via `-m`."""
    marker_expr = config.getoption("markexpr") or ""
    if "quarantine" in marker_expr:
        return  # caller explicitly asked for quarantined tests

    skip_quarantined = pytest.mark.skip(
        reason="quarantined (known-flaky) — excluded from default/gate runs; run with `-m quarantine`"
    )
    for item in items:
        if "quarantine" in item.keywords:
            item.add_marker(skip_quarantined)
