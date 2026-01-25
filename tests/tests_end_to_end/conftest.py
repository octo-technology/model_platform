"""
End-to-end tests configuration.

Re-exports shared utilities from tests.conftest and provides
E2E-specific fixtures.

These tests require a full environment with:
- Backend deployed
- Frontend deployed (optional)
- PostgreSQL deployed
- MinIO deployed
- Nginx ingress configured
"""

import pytest

from tests.conftest import is_cluster_available


@pytest.fixture(scope="session", autouse=True)
def check_e2e_environment():
    """Skip all tests if no cluster is available."""
    if not is_cluster_available():
        pytest.skip("No Kubernetes cluster available. Please start Kind or Minikube.")
