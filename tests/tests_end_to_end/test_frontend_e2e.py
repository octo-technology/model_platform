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


@pytest.fixture
def logged_in_and_reloaded_page(logged_in_page: Page) -> Page:
    """Recharge la page pour déclencher checkHealth() avec le token en localStorage."""
    logged_in_page.reload()
    logged_in_page.wait_for_selector("#projects-grid:not(.hidden), #projects-empty:not(.hidden)", timeout=10_000)
    return logged_in_page


@pytest.fixture
def first_project_page(logged_in_page: Page) -> Page:
    """Fixture : navigue sur la page de détail du premier projet disponible, skip si aucun."""
    logged_in_page.click("[data-route='projects']")
    logged_in_page.wait_for_selector("#projects-grid:not(.hidden), #projects-empty:not(.hidden)", timeout=10_000)
    cards = logged_in_page.locator(".project-card")
    if cards.count() == 0:
        pytest.skip("No projects available — skipping project detail tests")
    cards.first.click()
    logged_in_page.wait_for_selector("#project-tabs", timeout=10_000)
    return logged_in_page


@pytest.mark.e2e
class TestStatus:
    """Indicateurs de santé backend et storage dans la sidebar."""

    def test_backend_status_becomes_ok(self, logged_in_and_reloaded_page: Page):
        expect(logged_in_and_reloaded_page.locator("#backend-status-dot[data-status='ok']")).to_be_attached(
            timeout=15_000
        )

    def test_storage_status_is_set(self, logged_in_and_reloaded_page: Page):
        """Le statut storage doit être renseigné (ok ou error) après le health check."""
        expect(logged_in_and_reloaded_page.locator("#storage-status-dot:not([data-status='unknown'])")).to_be_attached(
            timeout=15_000
        )


@pytest.mark.e2e
class TestProjectDetail:
    """Navigation et onglets de la page de détail d'un projet."""

    def test_settings_tab_shows_project_info(self, first_project_page: Page):
        expect(first_project_page.locator("#tab-settings .card").first).to_be_visible(timeout=5_000)

    def test_models_tab_renders(self, first_project_page: Page):
        first_project_page.click("[data-tab='models']")
        expect(first_project_page.locator("#tab-models .table-wrap, #tab-models .empty-state").first).to_be_attached(
            timeout=10_000
        )

    def test_deployed_tab_renders(self, first_project_page: Page):
        first_project_page.click("[data-tab='deployed']")
        expect(
            first_project_page.locator("#tab-deployed .table-wrap, #tab-deployed .empty-state").first
        ).to_be_attached(timeout=10_000)

    def test_breadcrumb_back_to_projects(self, first_project_page: Page):
        first_project_page.click("[data-nav='projects']")
        expect(first_project_page.locator("#projects-grid:not(.hidden), #projects-empty:not(.hidden)")).to_be_visible(
            timeout=5_000
        )


def _governance_project_options_count(page: Page) -> int:
    """Attend la fin du chargement du select gouvernance, retourne le nombre de projets disponibles."""
    page.locator("#gov-project-select").wait_for(state="visible", timeout=5_000)
    page.wait_for_function(
        "() => { const opt = document.querySelector('#gov-project-select option'); return opt && !opt.textContent.includes('Loading'); }",
        timeout=10_000,
    )
    return page.locator("#gov-project-select option:not([value=''])").count()


@pytest.mark.e2e
class TestGovernanceExtended:
    """Tests étendus de la page gouvernance."""

    def test_governance_project_select_populates(self, logged_in_page: Page):
        logged_in_page.click("[data-route='governance']")
        count = _governance_project_options_count(logged_in_page)
        if count == 0:
            pytest.skip("No projects available for governance test")
        expect(logged_in_page.locator("#gov-project-select option:not([value=''])").first).to_be_attached()

    def test_governance_selecting_project_loads_content(self, logged_in_page: Page):
        logged_in_page.click("[data-route='governance']")
        if _governance_project_options_count(logged_in_page) == 0:
            pytest.skip("No projects available for governance test")
        first_value = logged_in_page.locator("#gov-project-select option:not([value=''])").first.get_attribute("value")
        logged_in_page.select_option("#gov-project-select", value=first_value)
        expect(logged_in_page.locator("#gov-content .card, #gov-content .empty-state").first).to_be_attached(
            timeout=15_000
        )

    def test_governance_download_button_visible_after_project_selected(self, logged_in_page: Page):
        logged_in_page.click("[data-route='governance']")
        if _governance_project_options_count(logged_in_page) == 0:
            pytest.skip("No projects available for governance test")
        first_value = logged_in_page.locator("#gov-project-select option:not([value=''])").first.get_attribute("value")
        logged_in_page.select_option("#gov-project-select", value=first_value)
        expect(logged_in_page.locator("#download-gov-btn")).to_be_visible(timeout=15_000)
