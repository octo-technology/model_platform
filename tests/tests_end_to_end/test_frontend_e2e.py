# author: Octo Technology MLOps tribe
import pytest
from playwright.sync_api import Page, expect

from tests.conftest import DEFAULT_TEST_USER, MP_HOSTNAME, is_minikube_running

BASE_URL = f"http://{MP_HOSTNAME}"


@pytest.fixture(scope="session", autouse=True)
def require_minikube():
    if not is_minikube_running():
        pytest.skip("Minikube not running — skipping frontend e2e tests")


@pytest.fixture
def logged_in_page(page: Page) -> Page:
    """Fixture : ouvre la SPA et se connecte avec les credentials de test."""
    page.goto(BASE_URL)
    page.fill("#signin-email", DEFAULT_TEST_USER["username"])
    page.fill("#signin-password", DEFAULT_TEST_USER["password"])
    page.click("#signin-btn")
    page.wait_for_selector("#projects-grid:not(.hidden), #projects-empty:not(.hidden)", timeout=10_000)
    return page


@pytest.mark.e2e
class TestFrontendIsUp:
    """La SPA est servie et redirige correctement."""

    def test_frontend_serves_spa(self, page: Page):
        response = page.goto(BASE_URL)
        assert response.status == 200
        expect(page.locator("#app")).to_be_attached()

    def test_unauthenticated_redirected_to_login(self, page: Page):
        page.goto(f"{BASE_URL}/#projects")
        expect(page.locator("#signin-email")).to_be_visible(timeout=5_000)


@pytest.mark.e2e
class TestAuthentication:
    """Login / logout fonctionnent."""

    def test_login_form_renders(self, page: Page):
        page.goto(BASE_URL)
        expect(page.locator("#signin-email")).to_be_visible()
        expect(page.locator("#signin-password")).to_be_visible()
        expect(page.locator("#signin-btn")).to_be_visible()

    def test_login_with_valid_credentials(self, page: Page):
        page.goto(BASE_URL)
        page.fill("#signin-email", DEFAULT_TEST_USER["username"])
        page.fill("#signin-password", DEFAULT_TEST_USER["password"])
        page.click("#signin-btn")
        expect(page.locator("#projects-grid:not(.hidden), #projects-empty:not(.hidden)")).to_be_visible(timeout=10_000)

    def test_login_with_invalid_credentials_shows_error(self, page: Page):
        page.goto(BASE_URL)
        page.fill("#signin-email", "invalid@example.com")
        page.fill("#signin-password", "wrong_password")
        page.click("#signin-btn")
        expect(page.locator("#signin-error")).to_be_visible(timeout=5_000)

    def test_logout_redirects_to_login(self, logged_in_page: Page):
        logged_in_page.click("#logout-btn")
        expect(logged_in_page.locator("#signin-email")).to_be_visible(timeout=5_000)


@pytest.mark.e2e
class TestNavigation:
    """Navigation de base dans la SPA."""

    def test_projects_page_shows_content(self, logged_in_page: Page):
        expect(logged_in_page.locator("#projects-grid:not(.hidden), #projects-empty:not(.hidden)")).to_be_visible(
            timeout=10_000
        )

    def test_governance_page_loads(self, logged_in_page: Page):
        logged_in_page.click("[data-route='governance']")
        expect(logged_in_page.locator("#gov-project-select")).to_be_visible(timeout=5_000)

    def test_create_project_modal_opens(self, logged_in_page: Page):
        logged_in_page.click("[data-route='projects']")
        logged_in_page.wait_for_selector("#new-project-btn", timeout=5_000)
        logged_in_page.click("#new-project-btn")
        expect(logged_in_page.locator("#new-proj-name")).to_be_visible(timeout=5_000)
