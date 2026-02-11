"""
Integration tests configuration.

Re-exports shared utilities from tests.conftest and provides
integration-specific fixtures.
"""

import time
from typing import Generator

import pytest

from tests.conftest import cleanup_test_namespaces


@pytest.fixture(scope="session", autouse=True)
def cleanup_stale_test_resources() -> Generator[None, None, None]:
    """
    Session-level fixture that cleans up stale test resources.

    This runs:
    - Before all tests: Cleanup any leftover resources from previous runs
    - After all tests: Cleanup resources created during this run
    """
    print("\n[Integration Tests] Cleaning up stale test resources before test run...")
    cleanup_test_namespaces()
    time.sleep(5)

    yield

    print("\n[Integration Tests] Cleaning up test resources after test run...")
    cleanup_test_namespaces()
