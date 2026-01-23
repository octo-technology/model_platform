"""
Pytest configuration and shared fixtures for end-to-end tests.

These tests require a full Minikube environment with:
- Backend deployed
- Frontend deployed (optional)
- PostgreSQL deployed
- MinIO deployed
- Nginx ingress configured
"""

import os
import subprocess

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "destructive: marks tests that modify cluster state significantly")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests requiring full infrastructure")


@pytest.fixture(scope="session")
def mp_hostname():
    """Get the Model Platform hostname from environment or default."""
    return os.environ.get("MP_HOSTNAME", "model-platform.com")


@pytest.fixture(scope="session")
def test_user_credentials():
    """Get test user credentials."""
    return {
        "username": os.environ.get("MP_TEST_USERNAME", "alice@example.com"),
        "password": os.environ.get("MP_TEST_PASSWORD", "pass!"),
    }


def is_minikube_running():
    """Check if Minikube is running."""
    try:
        result = subprocess.run(
            ["minikube", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return "Running" in result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


@pytest.fixture(scope="session", autouse=True)
def check_minikube_environment():
    """Skip all tests if Minikube is not running."""
    if not is_minikube_running():
        pytest.skip("Minikube is not running. Please start it with `minikube start`.")
